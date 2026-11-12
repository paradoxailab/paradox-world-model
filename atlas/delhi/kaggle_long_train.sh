#!/bin/bash
# Atlas-Delhi v1.1: one seed of the all-history Atlas. Kaggle CPU notebook with the atlas-delhi-long output attached.
#   SEED=300 bash kaggle_long_train.sh                              # v1.1: one seed, recipes B and C
#   SEEDS="310 311" RUN_FLAGS=--full bash kaggle_long_train.sh      # v1.2: whole schedule, recipes E and F
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "DELHI_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
ls -la $PW_RAW
for s in ${SEEDS:-${SEED:-300}}; do
  python -u run_atlas_long.py --seed $s ${RUN_FLAGS} 2>&1 | grep --line-buffered -v "Warning\|warn(\|nanmean" | tee $ATLAS_OUT/log_s$s.txt
done
rm -f $PW_RAW/DELHI_LONG.npz
ls -la $ATLAS_OUT
