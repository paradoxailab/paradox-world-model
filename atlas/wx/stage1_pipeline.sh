#!/bin/bash
# Atlas-WX Stage 1, end to end on ONE Colab runtime (atlas/PREREG_WX.md section 3): an A100, or a TPU (v5e-1 / v6e-1,
# native TorchTPU). With Drive mounted everything is kept in PWM-WX on Drive; without Drive it runs from /content/PWM-WX,
# which is lost when the runtime ends (mount Drive for long runs).
#   1. fetch GHCNh to the local disk (skipped if the packed data are already on Drive; resumable)
#   2. copy the packed data to Drive (PWM-WX/isd) so later runtimes do not fetch again
#   3. train 10M, then 28.5M (--grow 1,7,7), 97.6M (--grow 2,6,6) and 251.9M (--grow 3,7,7) from the trained 10M
# Every step is resumable: if the runtime ends, run the notebook cell again and it continues where it stopped.
# Progress: PWM-WX/runs/pipeline.log on Drive.
set -u
D=/content/drive/MyDrive/PWM-WX; [ -d /content/drive/MyDrive ] || D=/content/PWM-WX
RUNS=$D/runs; DATA=$D/isd; LOCAL=/content/wx_out
mkdir -p "$RUNS" "$DATA"
cd "$(dirname "$0")"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$RUNS/pipeline.log"; }

if [ -f "$DATA/summary.json" ] && [ -f "$DATA/wx_2023.npz" ]; then
  say "data already on Drive"
  if [ ! -f "$LOCAL/wx_2023.npz" ]; then
    say "copying data from Drive to the local disk"; mkdir -p "$LOCAL"; rsync -a "$DATA/" "$LOCAL/"
  fi
else
  say "fetching GHCNh (about 100 min)"
  python -u fetch_ghcnh_all.py --raw /content/gh_raw --out "$LOCAL" > "$RUNS/fetch.log" 2>&1 || { say "fetch failed: see fetch.log"; exit 1; }
  grep -q '^WX-DATA' "$RUNS/fetch.log" || { say "fetch ended without WX-DATA: see fetch.log"; exit 1; }
  want=$(python -c "import json;print(json.load(open('$LOCAL/summary.json'))['sha256'])")
  [ "$want" = "dd1da8fc8a755c46fb5af043af5d021639293a5809895097f984a83fb7123ab1" ] \
    && say "station list matches the frozen SHA-256" || say "WARNING: station list SHA-256 $want differs from the frozen one (record a deviation)"
  [ -d /content/drive/MyDrive ] && { say "copying the packed data to Drive"; rsync -a "$LOCAL/" "$DATA/"; }
  rm -rf /content/gh_raw                                            # 100+ GB of raw files no longer needed
fi

export WX_DATA=$LOCAL ATLAS_OUT=$RUNS
if python -c "import torch_tpu" 2>/dev/null; then
  export ATLAS_DEVICE=tpu TORCH_TPU_DEFER_AND_FUSE=0; DEVNAME=TPU      # tpu_smoke.sh, 24 Nov 2026: float32, strict eager
  M10=1; M30=2; M100=4; M250=16                                       # v5e-1 (16 GB): 10M fits whole, 97.6M in 4 parts
elif python -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)"; then
  DEVNAME=GPU; GB=$(python -c "import torch;print(int(torch.cuda.get_device_properties(0).total_memory/1e9))")
  M10=1; M30=1; M100=1; M250=$([ "$GB" -ge 70 ] && echo 2 || echo 4)  # build_250m.py
else
  say "no GPU or TPU on this runtime: data are ready; switch the runtime to A100 or TPU and run the cell again to train"; exit 0
fi
say "training on $DEVNAME"
run() {   # tag, first --micro, then the trainer's arguments; the split doubles on an out-of-memory error (PREREG_WX)
  local tag=$1 m=$2; shift 2
  if [ -f "$RUNS/${tag}_s600.json" ]; then say "$tag already finished"; return 0; fi
  [ -f "$RUNS/${tag}.micro" ] && m=$(cat "$RUNS/${tag}.micro")
  while :; do
    say "training $tag (batch 256 in $m part(s))"; echo $m > "$RUNS/${tag}.micro"
    python -u run_atlas_wx.py --tag "$tag" --pause-at-cap --cap 600 --micro $m "$@" >> "$RUNS/log_${tag}.txt" 2>&1
    [ -f "$RUNS/${tag}_s600.json" ] && { say "$tag finished"; return 0; }
    if tail -60 "$RUNS/log_${tag}.txt" | grep -q -i -E "out of memory|Error allocating device buffer|Error loading program" && [ $m -lt 32 ]; then
      m=$((m * 2)); continue; fi
    say "$tag paused or stopped (see log_${tag}.txt); run the cell again to resume"; exit 0
  done
}
run wx_s1_10m $M10 --size 10000000
run wx_s1_30m $M30 --init "$RUNS/wx_s1_10m_s600.pt" --grow 1,7,7 --lr 3e-4
export WX_DATA_CPU=1                                   # 97.6M and 251.9M: data in CPU memory, GPU for the model
run wx_s1_100m $M100 --init "$RUNS/wx_s1_10m_s600.pt" --grow 2,6,6 --lr 3e-4
run wx_s1_250m $M250 --init "$RUNS/wx_s1_10m_s600.pt" --grow 3,7,7 --lr 2e-4 --max-params 260000000
say "Stage 1 complete: all four candidates trained"
