#!/bin/bash
# Atlas-India v1.0 (the all-India league). Kaggle CPU notebook with the atlas-india-long output attached.
#   SEEDS="400" bash kaggle_india.sh                 # train one seed (about 2-3 h)
#   SCORE=1 bash kaggle_india.sh                     # score: attach atlas-india-long and the seeds' outputs
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
ls -la $PW_RAW
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef'
if [ -n "$SCORE" ]; then
  python -u score_india.py ${RUN_FLAGS} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_score.txt
else
  for s in ${SEEDS:-400}; do
    python -u run_atlas_india.py --seed $s ${RUN_FLAGS} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_s$s.txt
  done
fi
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
