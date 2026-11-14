#!/bin/bash
# ICML programme T1 (README): the transfer threshold function. Kaggle notebook with atlas-india-long attached.
#   NET="Uttar Pradesh" ARM=pre bash kaggle_threshold.sh      # CPU; also attach that network's atlas-lono-* output
#   NET="Uttar Pradesh" ARM=scratch bash kaggle_threshold.sh  # GPU (T4) or CPU; random weights
#   SCORE=1 bash kaggle_threshold.sh                          # attach every threshold run, atlas-india-opp-gpu
# Budgets: the most recent B months of the network's training data (statistics from then to the end of validation).
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
ls -la $PW_RAW
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|_ureduce\|reshape(D'
if [ -n "$SCORE" ]; then
  python -u score_threshold.py ${SCORE_FLAGS} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_score_threshold.txt
else
  X=$(echo "$NET" | tr 'A-Z' 'a-z' | sed 's/[^a-z0-9]\+/_/g')
  if [ "$ARM" = "pre" ]; then
    CK=$(find /kaggle/input -name "atlas_lono_${X}_s500.pt" | head -1)
    test -n "$CK" || { echo "attach the atlas-lono run for $NET (atlas_lono_${X}_s500.pt)"; exit 1; }
    for B in ${BUDGETS:-0 0.5 1 2 4 8 16 all}; do
      for S in ${SEEDS:-500 501}; do
        if [ "$B" = "0" ] && [ "$S" != "$(echo ${SEEDS:-500 501} | cut -d' ' -f1)" ]; then continue; fi   # no training: one run
        python -u run_atlas_india.py --seed $S --only "$NET" --init $CK --budget $B --tag thr_${X}_pre_b$B \
          --lr-scale 0.3 --steps 12000 --every 400 --patience 10 2>&1 | grep --line-buffered -v "$F" | tee -a $ATLAS_OUT/log_thr_pre.txt
        rm -f $ATLAS_OUT/atlas_thr_*.pt                     # weights not needed: the forecasts are saved
      done
    done
  else
    for B in ${BUDGETS:-0.5 1 2 4 8 16 all}; do
      for S in ${SEEDS:-500 501}; do
        python -u run_atlas_india.py --seed $S --only "$NET" --budget $B --tag thr_${X}_scratch_b$B \
          --steps 30000 --every 400 --patience 10 2>&1 | grep --line-buffered -v "$F" | tee -a $ATLAS_OUT/log_thr_scratch.txt
        rm -f $ATLAS_OUT/atlas_thr_*.pt
      done
    done
  fi
fi
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
