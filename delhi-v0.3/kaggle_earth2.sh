#!/bin/bash
# Kaggle (GPU, internet on), with the data notebook's output attached. Output: /kaggle/working/raw/E2_METAR.npz
set -x
export PW_RAW=/kaggle/working/raw
mkdir -p $PW_RAW && cp /kaggle/input/*/raw/WX_METAR.npz $PW_RAW/
nvidia-smi
python tools/earth2_run.py --league METAR --models ${E2_MODELS:-fcn3,sfno,graphcast} --budget_h ${E2_HOURS:-7}
ls -la $PW_RAW
