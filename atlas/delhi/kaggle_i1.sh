#!/bin/bash
# I1 (README, "Atlas v1.4 programme"): Atlas trained on nothing after 2024-09-30, scored on Delhi's winter 2024-25 as CEEW
# scored India's operational forecasts. Kaggle CPU notebook with atlas-india-long and atlas-delhi-long attached
# (and, to skip pre-training, the outputs holding atlas_india13_s<seed>.pt from the v1.3 runs).
#   SEEDS="320" bash kaggle_i1.sh         # one seed (320-322: the v1.3 pre-training seeds): pre-training (about 100 min, skipped if a checkpoint is attached), then Delhi
#   SCORE=1 bash kaggle_i1.sh             # attach the seed runs as well
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
export PW_SPLIT="2024-08-01,2024-10-01,2025-03-01"   # validation from, test from, test to (exclusive); applies to the Delhi file
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
find /kaggle/input -name "DELHI_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
ls -la $PW_RAW
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|_ureduce'
if [ -n "$SCORE" ]; then
  python -u score_i1.py 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_score_i1.txt
else
  for s in ${SEEDS:-320}; do
    CK=$(find /kaggle/input -name "atlas_india13_s$s.pt" | head -1)
    if [ -z "$CK" ]; then                             # pre-training does not read the Delhi file: PW_SPLIT has no effect on it
      env -u PW_SPLIT python -u run_atlas_india.py --seed $s --skip Delhi --tag india13 --pretrain-only 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_pre_s$s.txt
      CK=$ATLAS_OUT/atlas_india13_s$s.pt
    fi
    python -u run_atlas_long.py --seed $s --init $CK --tag i1 --lr-b 0.3 --steps 12000 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_s$s.txt
  done
fi
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/DELHI_LONG.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
