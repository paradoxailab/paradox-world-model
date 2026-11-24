#!/bin/bash
# Atlas-WX on a Colab TPU: install PyTorch/XLA if missing, then time short runs on synthetic data (no Drive needed).
# Prints seconds per step for 10M and the grown 97.6M model, so the TPU can be compared with an A100 before real runs.
set -u
cd "$(dirname "$0")"
python -c "import torch_xla" 2>/dev/null || pip -q install "torch_xla[tpu]==$(python -c 'import torch;print(torch.__version__.split("+")[0])')" 2>&1 | tail -2
python -c "import torch, torch_xla, torch_xla.core.xla_model as xm; print('torch', torch.__version__, 'torch_xla', torch_xla.__version__, 'device', xm.xla_device(), xm.xla_device_hw(xm.xla_device()))" || exit 1
[ -f /content/wx_synth/wx_2025.npz ] || python make_synth_wx.py --out /content/wx_synth --stations 300
export ATLAS_DEVICE=xla WX_DATA=/content/wx_synth ATLAS_OUT=/content/wx_synth_runs
rm -rf /content/wx_synth_runs
python -u run_atlas_wx.py --size 10000000 --steps 400 --every 200 --tag tpu10m --cap 1000 2>&1 | grep -E "parameters|step|VAL|Error|error" | tail -8
python -u run_atlas_wx.py --init /content/wx_synth_runs/tpu10m_s600.pt --grow 2,6,6 --lr 3e-4 --steps 200 --every 100 --tag tpu100m --cap 1000 2>&1 | grep -E "parameters|step|VAL|Error|error" | tail -8
