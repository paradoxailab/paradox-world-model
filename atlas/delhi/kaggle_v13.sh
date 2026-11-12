#!/bin/bash
# Atlas-Delhi v1.3: pre-train on the rest of India (no Delhi station), then v1.1's two stages on Delhi.
# Kaggle CPU notebook with the outputs of atlas-india-long (INDIA_LONG.npz) and atlas-delhi-long (DELHI_LONG.npz) attached.
#   SEEDS="320" bash kaggle_v13.sh        # one seed: about 100 min of pre-training and up to 45 min on Delhi
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
find /kaggle/input -name "DELHI_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
ls -la $PW_RAW
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|_ureduce'
for s in ${SEEDS:-320}; do
  python -u run_atlas_india.py --seed $s --skip Delhi --tag india13 --pretrain-only ${PRE_FLAGS} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_pre_s$s.txt
  python -u run_atlas_long.py --seed $s --init $ATLAS_OUT/atlas_india13_s$s.pt --tag long3 --lr-b 0.3 --steps 12000 ${RUN_FLAGS} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_s$s.txt
done
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/DELHI_LONG.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
