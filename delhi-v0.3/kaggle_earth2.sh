#!/bin/bash
# Kaggle (GPU, internet on), with the data notebook's output attached. Output: /kaggle/working/raw/E2_WMO.npz
set -x
find /kaggle/input -maxdepth 4 | head -40
export PW_RAW=/kaggle/working/raw
mkdir -p $PW_RAW && find /kaggle/input -name WX_WMO.npz -exec cp -n {} $PW_RAW/ \;
nvidia-smi
python tools/earth2_run.py --league WMO --models ${E2_MODELS:-sfno,graphcast,fcn3,graphcast_small,aurora} --budget_h ${E2_HOURS:-7}
ls -la $PW_RAW
