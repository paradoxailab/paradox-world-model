#!/bin/bash
# Kaggle (GPU, internet on), with the data (and, if done, Earth-2) notebook outputs attached.
set -x
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out PW_CACHE=/kaggle/working/out/cache
mkdir -p $PW_RAW $PW_CACHE
for f in /kaggle/input/*/raw/*.npz; do cp -n "$f" $PW_RAW/; done
cp -n /kaggle/input/*/out/cache/* $PW_CACHE/ 2>/dev/null
ls -la $PW_RAW
pip install -q timesfm chronos-forecasting 2>&1 | tail -2
python run_weather.py --league METAR
[ -f $PW_RAW/WX_CPCB.npz ] && python run_weather.py --league CPCB
ls -la $PW_OUT
