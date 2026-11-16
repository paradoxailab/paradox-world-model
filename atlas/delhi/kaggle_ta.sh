#!/bin/bash
# Atlas v2-W, T-A (README, "Atlas v2-W"): all-India test with perfect weather, criteria B1-B4. Kaggle CPU notebook with
# atlas-india-long, atlas-india-s400..402, atlas-india-opp-gpu (TimesFM 2.5) and atlas-w1-s400..402 attached.
#   bash kaggle_ta.sh
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|_ureduce\|reshape(D\|Mean of empty\|All-NaN'
for f in $(find /kaggle/input -name "india_s*.npz" -not -name "asrun_*"); do   # Atlas-India with the input fix, as in Atlas-F
  s=$(basename $f .npz | sed 's/india_s//'); d=$(dirname $f)
  cp -n $f $ATLAS_OUT/ && cp -n $d/atlas_india_s$s.pt $ATLAS_OUT/ 2>/dev/null
  python -u run_atlas_india.py --seed $s --reforecast 2>&1 | grep --line-buffered "REFORECAST \|TEST " | tee -a $ATLAS_OUT/log_reforecast.txt
done
python -u score_wa.py 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_ta.txt
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
