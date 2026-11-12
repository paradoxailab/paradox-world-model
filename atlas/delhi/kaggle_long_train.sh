#!/bin/bash
# Atlas-Delhi v1.1: one seed of the all-history Atlas. Kaggle CPU notebook with the atlas-delhi-long output attached.
#   SEED=300 bash kaggle_long_train.sh
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "DELHI_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
ls -la $PW_RAW
python -u run_atlas_long.py --seed ${SEED:-300} ${RUN_FLAGS} 2>&1 | grep --line-buffered -v "Warning\|warn(\|nanmean" | tee $ATLAS_OUT/log_s${SEED:-300}.txt
rm -f $PW_RAW/DELHI_LONG.npz
ls -la $ATLAS_OUT
