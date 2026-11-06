#!/bin/bash
# Kaggle (GPU, internet on), with the data (and, if done, Earth-2) notebook outputs attached.
set -x
find /kaggle/input -maxdepth 4 | head -40
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out PW_CACHE=/kaggle/working/out/cache
mkdir -p $PW_RAW $PW_CACHE
find /kaggle/input -path "*raw/*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*out/cache/*" -type f -exec cp -n {} $PW_CACHE/ \;
ls -la $PW_RAW
pip install -q timesfm chronos-forecasting 2>&1 | tail -2
python run_weather.py --league WMO
[ -f $PW_RAW/WX_CPCB.npz ] && python run_weather.py --league CPCB
ls -la $PW_OUT
