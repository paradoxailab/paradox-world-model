#!/bin/bash
# PWM-W v0.4 weather league on Kaggle (CPU is enough for METAR). Inputs: pwm-weather-data output (and, optionally,
# an earlier league output whose out/cache holds the time-series foundation-model forecasts).
#   LEAGUES="METAR" bash kaggle_v04.sh
set -x
find /kaggle/input -maxdepth 4 | head -30
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out PW_CACHE=/kaggle/working/out/cache
mkdir -p $PW_RAW/nwp_cache $PW_CACHE
find /kaggle/input -path "*raw/WX_*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*raw/NWP_*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*raw/nwp_cache/*" -type f -exec cp -n {} $PW_RAW/nwp_cache/ \;
find /kaggle/input -path "*out/cache/wx_*" -type f -exec cp -n {} $PW_CACHE/ \;
ls -la $PW_RAW $PW_CACHE
pip install -q timesfm chronos-forecasting 2>&1 | tail -2
for L in ${LEAGUES:-METAR}; do
  python tools/fetch_nwp.py --league $L --parts hybrid            # day1/day2 runs of IFS, AIFS, ICON, GFS
  python run_weather.py --league $L 2>&1 | tee $PW_OUT/run_$L.log
  python tools/summarize.py $PW_OUT/wx_$(echo $L | tr A-Z a-z)_results.json > $PW_OUT/tests_$L.txt
done
rm -rf $PW_RAW/nwp_cache
ls -la $PW_OUT
