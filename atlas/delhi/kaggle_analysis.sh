#!/bin/bash
# Post-hoc analyses for the follow-up paper (not pre-registered; no recorded verdict changes). Kaggle CPU notebook with
# atlas-india-long, atlas-india-s400..402, atlas-india-opp-gpu (Atlas-F inputs) and atlas-delhi-long, atlas-i1-s320..322.
#   bash kaggle_analysis.sh
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
find /kaggle/input -name "DELHI_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|_ureduce\|reshape(D\|Mean of empty\|All-NaN'
for f in $(find /kaggle/input -name "india_s*.npz" -not -name "asrun_*"); do   # Atlas-India with the input fix, as in Atlas-F
  s=$(basename $f .npz | sed 's/india_s//'); d=$(dirname $f)
  cp -n $f $ATLAS_OUT/ && cp -n $d/atlas_india_s$s.pt $ATLAS_OUT/ 2>/dev/null
  python -u run_atlas_india.py --seed $s --reforecast 2>&1 | grep --line-buffered "REFORECAST \|TEST " | tee -a $ATLAS_OUT/log_reforecast.txt
done
python -u analyze_f.py 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_analysis_f.txt
PW_SPLIT="2024-08-01,2024-10-01,2025-03-01" python -u score_i1.py --extra 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_i1_extra.txt
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/DELHI_LONG.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
