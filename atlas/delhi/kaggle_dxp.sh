#!/bin/bash
# Atlas v3 (README): the data x size threshold function. Kaggle GPU notebook with atlas-india-long and atlas-wx-fetch
# attached. Every run: weather forcing (ATLAS_WX=1), seed 400, all 14 networks, 60,000 steps, the code's defaults.
#   JOBS="1m:0.125 1m:0.25 1m:0.5 3m:1" bash kaggle_dxp.sh          # size:share pairs, run one after another
#   SCORE=1 bash kaggle_dxp.sh   # CPU; attach atlas-dxp-*, atlas-w1-s400..402 and atlas-w10-s400
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out ATLAS_WX=1
mkdir -p $PW_RAW $ATLAS_OUT
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|_ureduce\|reshape(D'
if [ -n "$SCORE" ]; then
  python -u score_dxp.py 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_score_dxp.txt
  exit 0
fi
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
find /kaggle/input -name "INDIA_WX.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
nvidia-smi -L || true
declare -A SIZE=( [1m]=1000000 [3m]=3000000 [10m]=9990000 )
for j in ${JOBS:?}; do
  k=${j%%:*}; f=${j##*:}; t=dxp_${k}_f$(echo $f | tr -d .)
  python -u run_atlas_india.py --seed 400 --size ${SIZE[$k]} --steps 60000 --cap 650 --frac $f --tag $t 2>&1 \
    | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_${t}_s400.txt
  rm -f $ATLAS_OUT/atlas_${t}_s400.pt                   # forecasts and metadata are kept; weights are not needed
done
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/INDIA_WX.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
