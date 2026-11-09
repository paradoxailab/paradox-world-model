#!/bin/bash
# PWM-W v0.9 data-threshold study on Kaggle (GPU). Inputs: pwm-weather-data output; optionally pwm-weather-v06-fm
# (its *_v6 foundation-model caches for CPCB are reused).
#   LEAGUES="CPCB METAR WMO" bash kaggle_v09_threshold.sh
set -x
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out PW_CACHE=/kaggle/working/out/cache
mkdir -p $PW_RAW $PW_CACHE
find /kaggle/input -path "*raw/WX_*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*out/cache/wx_*_v6.npz" -type f -exec cp -n {} $PW_CACHE/ \;
ls -la $PW_RAW $PW_CACHE
pip install -q timesfm chronos-forecasting 2>&1 | tail -2
python run_threshold.py --leagues ${LEAGUES:-CPCB METAR WMO} 2>&1 | tee $PW_OUT/threshold.log
grep -E "^THRESHOLD|NO-LOSS|THRESHOLD-RESULT" $PW_OUT/threshold.log
ls -la $PW_OUT
