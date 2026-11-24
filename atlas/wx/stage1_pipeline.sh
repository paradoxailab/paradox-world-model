#!/bin/bash
# Atlas-WX Stage 1, end to end on ONE Colab GPU runtime with Drive mounted (atlas/PREREG_WX.md section 3).
#   1. fetch GHCNh to the local disk (skipped if the packed data are already on Drive; resumable)
#   2. copy the packed data to Drive (PWM-WX/isd) so later runtimes do not fetch again
#   3. train 10M, then 28.5M (--grow 1,7,7), 97.6M (--grow 2,6,6) and 251.9M (--grow 3,7,7) from the trained 10M
# Every step is resumable: if the runtime ends, run the notebook cell again and it continues where it stopped.
# Progress: PWM-WX/runs/pipeline.log on Drive.
set -u
D=/content/drive/MyDrive/PWM-WX
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
  say "copying the packed data to Drive"; rsync -a "$LOCAL/" "$DATA/"
  rm -rf /content/gh_raw                                            # 100+ GB of raw files no longer needed
fi

export WX_DATA=$LOCAL ATLAS_OUT=$RUNS
if ! python -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)"; then
  say "no GPU on this runtime: data are on Drive; switch the runtime to A100 and run the cell again to train"; exit 0
fi
run() {   # tag, then the trainer's arguments
  local tag=$1; shift
  if [ -f "$RUNS/${tag}_s600.json" ]; then say "$tag already finished"; return 0; fi
  say "training $tag"
  python -u run_atlas_wx.py --tag "$tag" --pause-at-cap --cap 600 "$@" >> "$RUNS/log_${tag}.txt" 2>&1
  if [ -f "$RUNS/${tag}_s600.json" ]; then say "$tag finished"; else say "$tag paused or stopped (see log_${tag}.txt); run the cell again to resume"; exit 0; fi
}
run wx_s1_10m --size 10000000
run wx_s1_30m --init "$RUNS/wx_s1_10m_s600.pt" --grow 1,7,7 --lr 3e-4
export WX_DATA_CPU=1                                   # 97.6M and 251.9M: data in CPU memory, GPU for the model
run wx_s1_100m --init "$RUNS/wx_s1_10m_s600.pt" --grow 2,6,6 --lr 3e-4
run wx_s1_250m --init "$RUNS/wx_s1_10m_s600.pt" --grow 3,7,7 --lr 2e-4 --max-params 260000000
say "Stage 1 complete: all four candidates trained"
