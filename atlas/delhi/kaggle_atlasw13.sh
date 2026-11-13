#!/bin/bash
# Atlas-W v1 (README, "Atlas-W days 2 and 3"): Atlas v1.3's recipe with Atlas-W width 32 in place of Atlas.
# Pre-train on the rest of India (no Delhi station), then stage B (all Delhi history) and stage C (the league's 16 months).
# Kaggle CPU notebook with the outputs of atlas-india-long (INDIA_LONG.npz) and atlas-delhi-long (DELHI_LONG.npz) attached.
#   SEEDS="320" bash kaggle_atlasw13.sh
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out ATLAS_MODEL=atlasw:32
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
find /kaggle/input -name "DELHI_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
ls -la $PW_RAW
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|_ureduce'
for s in ${SEEDS:-320}; do
  python -u run_atlas_india.py --seed $s --skip Delhi --tag windia13 --pretrain-only ${PRE_FLAGS} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_pre_s$s.txt
  python -u run_atlas_long.py --seed $s --init $ATLAS_OUT/atlas_windia13_s$s.pt --tag wlong3 --lr-b 0.3 --steps 12000 ${RUN_FLAGS} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_s$s.txt
done
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/DELHI_LONG.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
