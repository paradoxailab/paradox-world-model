#!/bin/bash
# PWM-W v0.9 real-time forecast for the Indian airport stations (GPU or CPU). Inputs: pwm-weather-data output
# (WX_METAR.npz) and, optionally, the previous live run's output (live_log.csv carried forward; live_models.pt
# reused unless RETRAIN=1 or the stations changed).
#   bash kaggle_live.sh
set -x
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out
mkdir -p $PW_RAW $PW_OUT
find /kaggle/input -path "*raw/WX_METAR.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -name "live_log.csv" -exec cp -n {} $PW_OUT/ \;
[ "${RETRAIN:-0}" = "1" ] || find /kaggle/input -name "live_models.pt" -exec cp -n {} $PW_OUT/ \;
python tools/fetch_live_metar.py || exit 1
if [ ! -f $PW_OUT/live_models.pt ]; then python tools/train_live.py --steps ${STEPS:-6000}; fi
python tools/live_forecast.py || { python tools/train_live.py --steps ${STEPS:-6000} && python tools/live_forecast.py; }
cat $PW_OUT/live_scores.json
ls -la $PW_OUT
