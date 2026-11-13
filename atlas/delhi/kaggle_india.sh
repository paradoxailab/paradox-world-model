#!/bin/bash
# Atlas-India v1.0 (the all-India league). Kaggle CPU notebook with the atlas-india-long output attached.
#   SEEDS="400" bash kaggle_india.sh                 # train one seed (about 2-3 h)
#   SCORE=1 bash kaggle_india.sh                     # score: attach atlas-india-long, the seeds' outputs and atlas-india-opp
#   OPP=1 OPP_FLAGS="--keys chronos-bolt,chronos2,tfm25" bash kaggle_india.sh   # foundation models on the same windows
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
ls -la $PW_RAW
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef'
if [ -n "$OPP" ]; then                                     # foundation models on the league's windows (GPU or CPU)
  pip install -q timesfm chronos-forecasting 2>&1 | tail -2
  python -u india_opponents.py ${OPP_FLAGS} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_opp.txt
elif [ -n "$SCORE" ]; then
  # seeds forecast before the input fix of 2026-11-13 are forecast again from their saved weights first
  for f in $(find /kaggle/input -name "india_s*.npz" -not -name "asrun_*"); do
    s=$(basename $f .npz | sed 's/india_s//'); d=$(dirname $f)
    cp -n $f $ATLAS_OUT/ && cp -n $d/atlas_india_s$s.pt $ATLAS_OUT/ 2>/dev/null
    python -u run_atlas_india.py --seed $s --reforecast 2>&1 | grep --line-buffered "REFORECAST \|TEST " | tee -a $ATLAS_OUT/log_reforecast.txt
  done
  python -u score_india.py ${RUN_FLAGS} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_score.txt
else
  for s in ${SEEDS:-400}; do
    python -u run_atlas_india.py --seed $s ${RUN_FLAGS} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_s$s.txt
  done
fi
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
