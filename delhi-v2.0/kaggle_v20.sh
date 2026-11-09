#!/bin/bash
# PWM-India v2.0 on Kaggle (GPU). Inputs: pwm-weather-data output (WX_*.npz, NWP_*.npz), pwm-india-data output
# (raw/WX_INDIA.npz), optionally pwm-x-cpcb / earlier outputs (*_v6 foundation-model caches) and an earlier v2.0 output
# holding out/pwm_india_pretrained.pt (then pretraining is skipped).
#   LEAGUES="CPCB" VARIANTS="P10,P11,P12" PRE_STEPS=24000 bash kaggle_v20.sh
set -x
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out PW_CACHE=/kaggle/working/out/cache
mkdir -p $PW_RAW/nwp_cache $PW_CACHE
find /kaggle/input -path "*raw/WX_*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*raw/NWP_*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*out/cache/wx_*_v6.npz" -type f -exec cp -n {} $PW_CACHE/ \;
find /kaggle/input -name "pwm_india_pretrained.pt" -exec cp -n {} $PW_OUT/ \;
ls -la $PW_RAW $PW_CACHE $PW_OUT
pip install -q timesfm chronos-forecasting 2>&1 | tail -2
if [ ! -f $PW_OUT/pwm_india_pretrained.pt ]; then
  python pretrain_india.py --steps ${PRE_STEPS:-24000} 2>&1 | tee $PW_OUT/pretrain_india.log
fi
for L in ${LEAGUES:-CPCB}; do
  have=$(python -c "import numpy as np; z=np.load('$PW_RAW/NWP_$L.npz'); print('score' if 'score' in z.files else '')" 2>/dev/null)
  python tools/fetch_nwp.py --league $L --parts $([ "$have" = score ] && echo hybrid || echo score,hybrid)
  python run_weather.py --league $L --variants ${VARIANTS:-P10,P11,P12} --init $PW_OUT/pwm_india_pretrained.pt 2>&1 \
    | tee $PW_OUT/run_$L.log
  python tools/summarize.py $PW_OUT/wx_$(echo $L | tr A-Z a-z)_results.json > $PW_OUT/tests_$L.txt
done
rm -rf $PW_RAW/nwp_cache
ls -la $PW_OUT
