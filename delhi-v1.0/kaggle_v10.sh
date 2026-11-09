#!/bin/bash
# PWM-W v1.0 weather leagues on Kaggle (GPU).
# Inputs: pwm-weather-data output (WX_*.npz); optionally earlier run outputs holding NWP_*.npz and *_v6 foundation-model
# caches (reused; a league's global-forecast archive is fetched only when no complete NWP file is attached).
#   LEAGUES="CPCB METAR WMO" VARIANTS="P8,P9,P10" bash kaggle_v10.sh
set -x
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out PW_CACHE=/kaggle/working/out/cache
mkdir -p $PW_RAW/nwp_cache $PW_CACHE
find /kaggle/input -path "*raw/WX_*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*raw/NWP_*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*raw/nwp_cache/*" -type f -exec cp -n {} $PW_RAW/nwp_cache/ \;
find /kaggle/input -path "*out/cache/wx_*_v6.npz" -type f -exec cp -n {} $PW_CACHE/ \;
ls -la $PW_RAW $PW_CACHE
pip install -q timesfm chronos-forecasting 2>&1 | tail -2
for L in ${LEAGUES:-CPCB METAR WMO}; do
  have=$(python -c "import numpy as np; z=np.load('$PW_RAW/NWP_$L.npz'); f=set(z.files); print(','.join(p for p in ('score','hybrid') if p in f))" 2>/dev/null)
  need=$(python -c "h=set('$have'.split(',')); print(','.join(p for p in ('score','hybrid') if p not in h))")
  if [ -n "$need" ]; then python tools/fetch_nwp.py --league $L --parts $need; else echo "NWP_$L.npz attached and complete: not refetched"; fi
  python run_weather.py --league $L --variants ${VARIANTS:-P8,P9,P10} 2>&1 | tee $PW_OUT/run_$L.log
  python tools/summarize.py $PW_OUT/wx_$(echo $L | tr A-Z a-z)_results.json > $PW_OUT/tests_$L.txt
done
rm -rf $PW_RAW/nwp_cache
ls -la $PW_OUT
