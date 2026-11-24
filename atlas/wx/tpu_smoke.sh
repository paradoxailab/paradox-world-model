#!/bin/bash
# Atlas-WX on a Colab TPU: time short runs on synthetic data (no Drive needed), so the TPU can be compared with an
# A100 before real runs. Colab TPU images from late 2026 ship native TorchTPU (the torch_tpu package, device "tpu");
# older images need PyTorch/XLA. The script uses whichever is present.
#   bash tpu_smoke.sh            # prints parameters, s/step and validation lines for 10M (two eager modes) and 97.6M
set -u
cd "$(dirname "$0")"
filt() { grep -E "parameters|step [0-9]|VAL|device|Error|error|Traceback" | grep -v -E "^I0000|^W0000" | tail -8; }
if python -c "import torch_tpu" 2>/dev/null; then
  export ATLAS_DEVICE=tpu
  python -c "import torch; print('torch', torch.__version__, '| native TorchTPU', __import__('torch_tpu').__version__, '| autocast on tpu:', torch.amp.is_autocast_available('tpu'))" 2>&1 | grep -v -E "^I0000|^W0000"
else
  python -c "import torch_xla" 2>/dev/null || pip -q install "torch_xla[tpu]==$(python -c 'import torch;print(torch.__version__.split("+")[0])')" 2>&1 | tail -2
  python -c "import torch, torch_xla, torch_xla.core.xla_model as xm; print('torch', torch.__version__, 'torch_xla', torch_xla.__version__, xm.xla_device())" || exit 1
  export ATLAS_DEVICE=xla
fi
[ -f /content/wx_synth/wx_2025.npz ] || python make_synth_wx.py --out /content/wx_synth --stations 300
export WX_DATA=/content/wx_synth ATLAS_OUT=/content/wx_synth_runs
rm -rf /content/wx_synth_runs
echo "== 10M, default (strict) eager"
python -u run_atlas_wx.py --size 10000000 --steps 300 --every 100 --tag tpu10m --cap 1000 2>&1 | filt
if [ "$ATLAS_DEVICE" = tpu ]; then
  echo "== 10M, DeferAndFuse eager"
  TORCH_TPU_DEFER_AND_FUSE=1 python -u run_atlas_wx.py --size 10000000 --steps 300 --every 100 --tag tpu10m_df --cap 1000 2>&1 | filt
fi
echo "== 97.6M grown from the 10M (DeferAndFuse on TorchTPU)"
TORCH_TPU_DEFER_AND_FUSE=1 python -u run_atlas_wx.py --init /content/wx_synth_runs/tpu10m_s600.pt --grow 2,6,6 --lr 3e-4 --steps 150 --every 50 --tag tpu100m --cap 1000 2>&1 | filt
