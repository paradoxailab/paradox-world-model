#!/bin/bash
# Atlas-WX on a Colab TPU: time short runs on synthetic data (no Drive needed), so the TPU can be compared with an
# A100 before real runs. Colab TPU images from late 2026 ship native TorchTPU (the torch_tpu package, device "tpu");
# older images need PyTorch/XLA. The script uses whichever is present.
# A v5e-1 has 16 GB of TPU memory, so each model is tried with the batch of 256 split into 1, 2, 4, ... parts
# (--micro; same samples, same update) until it fits. Prints the s/step of the second interval (compile time excluded).
#   bash tpu_smoke.sh
set -u
cd "$(dirname "$0")"
filt() { grep -E "parameters|step [0-9]+ loss|WX:|Traceback|RuntimeError|allocate|Error:" | grep -v -E "^I0000|^W0000|^E0000" | tail -6; }
if python -c "import torch_tpu" 2>/dev/null; then
  export ATLAS_DEVICE=tpu TORCH_TPU_DEFER_AND_FUSE=${TORCH_TPU_DEFER_AND_FUSE:-1}
  python - <<'PY' 2>&1 | grep -v -E "^I0000|^W0000|^E0000|PrivateUse1|Registered Python|Device type|Initializing TPU|absl"
import importlib.metadata as md, torch
print("torch", torch.__version__, "| torch_tpu", md.version("torch_tpu"), "| autocast on tpu:", torch.amp.is_autocast_available("tpu"))
t = getattr(torch, "tpu", None)
for f in ("memory_allocated", "max_memory_allocated", "mem_get_info", "get_device_name", "device_count"):
    print(" torch.tpu." + f, "available" if t is not None and hasattr(t, f) else "missing")
PY
else
  python -c "import torch_xla" 2>/dev/null || pip -q install "torch_xla[tpu]==$(python -c 'import torch;print(torch.__version__.split("+")[0])')" 2>&1 | tail -2
  python -c "import torch, torch_xla, torch_xla.core.xla_model as xm; print('torch', torch.__version__, 'torch_xla', torch_xla.__version__, xm.xla_device())" || exit 1
  export ATLAS_DEVICE=xla
fi
[ -f /content/wx_synth/wx_2025.npz ] || python make_synth_wx.py --out /content/wx_synth --stations 300
export WX_DATA=/content/wx_synth ATLAS_OUT=/content/wx_synth_runs
rm -rf /content/wx_synth_runs
try() {   # try(tag, steps, every, args...): smallest --micro that fits
  local tag=$1 steps=$2 every=$3; shift 3
  for m in 1 2 4 8 16 32; do
    echo "== $tag, batch 256 in $m part(s)"
    rm -f /content/wx_synth_runs/${tag}_s600*
    python -u run_atlas_wx.py --tag "$tag" --steps "$steps" --every "$every" --micro $m --cap 1000 "$@" > /content/smoke_$tag.log 2>&1
    filt < /content/smoke_$tag.log
    [ -f /content/wx_synth_runs/${tag}_s600.json ] && { echo "== $tag fits with --micro $m"; FIT_M=$m; return 0; }
  done
  echo "== $tag did not fit"; return 1
}
try tpu10m 60 30 --size 10000000 || exit 1
echo "== 10M strict eager (no DeferAndFuse), the fitting split"
TORCH_TPU_DEFER_AND_FUSE=0 python -u run_atlas_wx.py --tag tpu10m_strict --steps 60 --every 30 --micro ${FIT_M:-1} --size 10000000 --cap 1000 2>&1 | filt
try tpu100m 40 20 --init /content/wx_synth_runs/tpu10m_s600.pt --grow 2,6,6 --lr 3e-4
