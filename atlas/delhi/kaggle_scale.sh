#!/bin/bash
# Atlas v2 programme: the parameter ladder (README). Kaggle GPU notebook with atlas-india-long attached.
#   SIZE=3000000 SEEDS=400 TAG=scale3m bash kaggle_scale.sh
#   SIZE=9990000 SEEDS=400 TAG=scale10m [STEPS=120000] bash kaggle_scale.sh
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
nvidia-smi -L || true
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|_ureduce\|reshape(D'
for s in ${SEEDS:-400}; do
  python -u run_atlas_india.py --seed $s --size ${SIZE:?} --steps ${STEPS:-60000} --cap ${CAP:-650} --tag ${TAG:?} 2>&1 \
    | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_${TAG}_s$s.txt
done
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
