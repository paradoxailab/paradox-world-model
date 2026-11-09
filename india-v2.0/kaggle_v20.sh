#!/bin/bash
# PWM-W v2.0 step 2 (Kaggle GPU): pretrain PWM-F on the all-India corpus, then fine-tune and score every league.
# Inputs: the v2.0 data notebook's output (raw/PRE_INDIA.npz), pwm-weather-data (WX_*.npz, NWP_*.npz), and optionally
# earlier runs' foundation-model caches (out/cache/wx_*_v6.npz).
#   LEAGUES="CPCB" VARIANTS="P10,P11,P12" PRE_HOURS=1.5 bash kaggle_v20.sh
set -x
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out PW_CACHE=/kaggle/working/out/cache
mkdir -p $PW_RAW/nwp_cache $PW_CACHE
find /kaggle/input -path "*raw/WX_*.npz" -exec cp -n {} $PW_RAW/ \;
# the newest global-forecast archives first (pwm-x-cpcb fetched CPCB's hybrid inputs on 2026-11-09)
for d in /kaggle/input/pwm-x-cpcb /kaggle/input/pwm-v10 /kaggle/input; do find $d -path "*raw/NWP_*.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null; done
find /kaggle/input \( -name "PRE_INDIA.npz" -o -name "WX_INDIA.npz" \) -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*out/cache/wx_*_v6.npz" -type f -exec cp -n {} $PW_CACHE/ \;
find /kaggle/input -path "*out/fenc.pt" -exec cp -n {} $PW_OUT/ \;
ls -la $PW_RAW $PW_CACHE $PW_OUT
pip install -q timesfm chronos-forecasting 2>&1 | tail -2
if [ ! -f $PW_OUT/fenc.pt ]; then
  python pretrain_f.py --steps ${PRE_STEPS:-40000} --batch 512 --hours ${PRE_HOURS:-2} 2>&1 | tee $PW_OUT/pretrain.log
fi
for L in ${LEAGUES:-CPCB METAR}; do
  have=$(python -c "import numpy as np; z=np.load('$PW_RAW/NWP_$L.npz'); f=set(z.files); print(','.join(p for p in ('score','hybrid') if p in f))" 2>/dev/null)
  if [ "${REFETCH:-0}" = 1 ] || [ "$have" != "score,hybrid" ]; then
    python tools/fetch_nwp.py --league $L --parts $([ "$have" = score ] || [ "$have" = "score,hybrid" ] && echo hybrid || echo score,hybrid)
  else
    echo "NWP_$L.npz attached with score and hybrid parts: reused (set REFETCH=1 to refetch)"
  fi
  python run_weather.py --league $L --variants ${VARIANTS:-P10,P11,P12} 2>&1 | tee $PW_OUT/run_$L.log
  python tools/summarize.py $PW_OUT/wx_$(echo $L | tr A-Z a-z)_results.json > $PW_OUT/tests_$L.txt
done
rm -rf $PW_RAW/nwp_cache
ls -la $PW_OUT
