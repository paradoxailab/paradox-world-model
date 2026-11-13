#!/bin/bash
# ICML programme L1 (README): leave one network out. Kaggle CPU notebook with atlas-india-long attached.
#   NET="Uttar Pradesh" bash kaggle_lono.sh     # pre-train on the other 13 networks, then adapt to NET (about 3 h)
#   SCORE=1 bash kaggle_lono.sh                 # score: also attach the four lono runs, atlas-india-opp-gpu, atlas-india-s400..402
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
ls -la $PW_RAW
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef'
S=${SEED:-500}
if [ -n "$SCORE" ]; then
  python -u score_lono.py 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_score_lono.txt
else
  X=$(echo "$NET" | tr 'A-Z' 'a-z' | sed 's/[^a-z0-9]\+/_/g')
  python -u run_atlas_india.py --seed $S --skip "$NET" --tag lono_$X --pretrain-only 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_pre.txt
  python -u run_atlas_india.py --seed $S --only "$NET" --init $ATLAS_OUT/atlas_lono_${X}_s$S.pt --tag lono_${X}_ad \
    --lr-scale 0.3 --steps 12000 --every 400 --patience 10 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_adapt.txt
fi
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
