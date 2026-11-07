#!/bin/bash
# Re-score a finished v0.6 league run against the time-series foundation models only (GPU). Inputs: pwm-weather-data
# output and the league run's output (its out/wx_<league>_preds.npz and results json).
#   LEAGUES="CPCB" bash kaggle_v06_fm.sh
set -x
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out PW_CACHE=/kaggle/working/out/cache
mkdir -p $PW_RAW $PW_CACHE
find /kaggle/input -path "*raw/WX_*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*out/wx_*_preds.npz" -exec cp -n {} $PW_OUT/ \;
find /kaggle/input -path "*out/wx_*_results.json" -exec cp -n {} $PW_OUT/ \;
ls -la $PW_RAW $PW_OUT
pip install -q timesfm chronos-forecasting 2>&1 | tail -2
for L in ${LEAGUES:-CPCB}; do
  python run_weather.py --league $L --fm_only 2>&1 | tee $PW_OUT/fm_$L.log
done
ls -la $PW_OUT
