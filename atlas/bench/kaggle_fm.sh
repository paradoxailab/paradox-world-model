#!/bin/bash
# ATF v1.2 part 1 on Kaggle (GPU): foundation models on the curve windows. Inputs: pwm-india-data, pwm-v21-data, atlas-delhi.
set -x
export PW_RAW=/kaggle/working/raw ATF_OUT=/kaggle/working/out_atf
mkdir -p $PW_RAW $ATF_OUT/fm
for f in WX_INDIA.npz WX_CPCBIN.npz DELHI.npz; do find /kaggle/input -name $f -exec cp -n {} $PW_RAW/ \; 2>/dev/null; done
pip install -q timesfm chronos-forecasting 2>&1 | tail -2
python -u fm.py ${RUN_FLAGS} 2>&1 | grep --line-buffered -v "Warning\|warn(" | tee $ATF_OUT/log_fm.txt
rm -rf $PW_RAW
