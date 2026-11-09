#!/bin/bash
# PWM-F (v1.1) on Kaggle (GPU T4, internet on). Inputs: the pwm-india-data output (WX_IN*.npz), pwm-weather-data
# (WX_METAR/WMO/CPCB.npz, NWP_*.npz); optionally earlier run outputs with *_v6 foundation-model caches.
# 1) pretrain the ~10M-parameter model on all Indian networks (data end 2024-11-30);
# 2) run each league with P0 (seed noise), P8 (graph family, ensemble partner) and P11 (PWM-F fine-tuned).
#   STEPS=40000 LEAGUES="CPCB METAR WMO" VARIANTS="P8,P11" bash kaggle_pwmf.sh
set -x
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out PW_CACHE=/kaggle/working/out/cache
mkdir -p $PW_RAW/nwp_cache $PW_CACHE
find /kaggle/input -path "*raw/WX_*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*raw/NWP_*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*out/cache/wx_*_v6.npz" -type f -exec cp -n {} $PW_CACHE/ \;
find /kaggle/input -name "pwmf_pretrained.pt" -exec cp -n {} $PW_OUT/ \;
ls -la $PW_RAW $PW_CACHE $PW_OUT
pip install -q timesfm chronos-forecasting 2>&1 | tail -2
if [ ! -f $PW_OUT/pwmf_pretrained.pt ]; then
  python run_pretrain.py --steps ${STEPS:-40000} 2>&1 | tee $PW_OUT/pretrain.log
fi
for L in ${LEAGUES:-CPCB METAR WMO}; do
  have=$(python -c "import numpy as np; z=np.load('$PW_RAW/NWP_$L.npz'); print('score' if 'score' in z.files else '')" 2>/dev/null)
  python tools/fetch_nwp.py --league $L --parts $([ "$have" = score ] && echo hybrid || echo score,hybrid)
  python run_weather.py --league $L --variants ${VARIANTS:-P8,P11} 2>&1 | tee $PW_OUT/run_$L.log
  python tools/summarize.py $PW_OUT/wx_$(echo $L | tr A-Z a-z)_results.json > $PW_OUT/tests_$L.txt
done
rm -rf $PW_RAW/nwp_cache
ls -la $PW_OUT
