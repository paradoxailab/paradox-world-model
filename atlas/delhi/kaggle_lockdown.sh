#!/bin/bash
# Atlas what-if test 1: the 2020 lockdown in Delhi. Kaggle CPU notebook with the atlas-delhi-long output attached.
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "DELHI_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
ls -la $PW_RAW
python -u run_lockdown.py ${RUN_FLAGS} 2>&1 | grep --line-buffered -v 'Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|Mean of empty' | tee $ATLAS_OUT/log_lockdown.txt
rm -f $PW_RAW/DELHI_LONG.npz
ls -la $ATLAS_OUT
