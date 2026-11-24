#!/bin/bash
# Atlas-WX Stage 1 on a rented GPU machine (Linux + NVIDIA GPU + PyTorch), with no Google Drive needed.
# Fetches the frozen 8,791-station GHCNh data itself (public, ~2 h, checked against the pre-registered SHA-256),
# then trains 10M -> 28.5M -> 97.6M -> 251.9M (atlas/PREREG_WX.md section 3 and addenda). Resumable: run it again
# after any interruption. Everything goes under $WORK (default /workspace/atlas-wx); progress in $WORK/pipeline.log.
#
#   bash cloud_stage1.sh                 # inside tmux, so it survives a closed terminal
# Optional: export HF_TOKEN=... (a Hugging Face write token, set by you, never written to disk by this script) and
# HF_REPO=PARADOXAIlabs/atlas-wx-runs to upload results after each finished model.
set -u
WORK=${WORK:-/workspace/atlas-wx}
REPO=$WORK/pwm; RAW=$WORK/gh_raw; DATA=$WORK/data; RUNS=$WORK/runs
mkdir -p "$WORK" "$RUNS"
say() { echo "$(date -u +%FT%TZ) $*" | tee -a "$WORK/pipeline.log"; }

python -c "import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)" || { say "no GPU visible to PyTorch"; exit 1; }
say "GPU: $(python -c 'import torch;p=torch.cuda.get_device_properties(0);print(p.name, round(p.total_memory/1e9), "GB")')"
pip -q install numpy pandas pyarrow huggingface_hub 2>&1 | tail -1
[ -d "$REPO" ] || git clone -q -b atlas-v0.1 https://github.com/paradoxailab/paradox-world-model "$REPO"
git -C "$REPO" pull -q; say "code at $(git -C "$REPO" log --oneline -1)"
cd "$REPO/atlas/wx"

if [ ! -f "$DATA/summary.json" ]; then
  free_gb=$(df -BG --output=avail "$WORK" | tail -1 | tr -dc 0-9)
  [ "$free_gb" -ge 180 ] || { say "need >= 180 GB free disk for the fetch, have ${free_gb} GB"; exit 1; }
  say "fetching GHCNh (about 2 h)"
  python -u fetch_ghcnh_all.py --raw "$RAW" --out "$DATA" > "$WORK/fetch.log" 2>&1 || { say "fetch failed: see fetch.log"; exit 1; }
  rm -rf "$RAW"
fi
sha=$(python -c "import json;print(json.load(open('$DATA/summary.json'))['sha256'])")
if [ "$sha" = "dd1da8fc8a755c46fb5af043af5d021639293a5809895097f984a83fb7123ab1" ]; then say "station list matches the frozen SHA-256"
else say "STOP: station list SHA-256 $sha differs from the frozen one; record a deviation before training"; exit 1; fi

export WX_DATA=$DATA ATLAS_OUT=$RUNS
upload() {   # optional: results to Hugging Face (token only from the environment)
  [ -n "${HF_TOKEN:-}" ] && [ -n "${HF_REPO:-}" ] || return 0
  python - "$1" <<'EOF' >> "$WORK/pipeline.log" 2>&1
import os, sys, glob
from huggingface_hub import HfApi
api = HfApi(token=os.environ["HF_TOKEN"]); repo = os.environ["HF_REPO"]
api.create_repo(repo, private=True, exist_ok=True)
for f in glob.glob(os.path.join(os.environ["ATLAS_OUT"], sys.argv[1] + "_s600*")) + glob.glob(os.path.join(os.environ["ATLAS_OUT"], "log_" + sys.argv[1] + ".txt")):
    if not f.endswith("_last.pt"):
        api.upload_file(path_or_fileobj=f, path_in_repo=os.path.basename(f), repo_id=repo)
print("uploaded", sys.argv[1])
EOF
}
run() {
  local tag=$1; shift
  if [ -f "$RUNS/${tag}_s600.json" ]; then say "$tag already finished"; return 0; fi
  say "training $tag"
  python -u run_atlas_wx.py --tag "$tag" --cap 100000 "$@" >> "$RUNS/log_${tag}.txt" 2>&1
  [ -f "$RUNS/${tag}_s600.json" ] || { say "$tag stopped (see runs/log_${tag}.txt); run the script again to resume"; exit 1; }
  say "$tag finished: $(python -c "import json;d=json.load(open('$RUNS/${tag}_s600.json'));print('val E', round(d['val_E'],4), 'params', d['params'], 'best step', d['best_step'])")"
  upload "$tag"
}
run wx_s1_10m --size 10000000
run wx_s1_30m --init "$RUNS/wx_s1_10m_s600.pt" --grow 1,7,7 --lr 3e-4
export WX_DATA_CPU=1
run wx_s1_100m --init "$RUNS/wx_s1_10m_s600.pt" --grow 2,6,6 --lr 3e-4
run wx_s1_250m --init "$RUNS/wx_s1_10m_s600.pt" --grow 3,7,7 --lr 2e-4 --max-params 260000000
say "Stage 1 complete: all four candidates trained"
