#!/bin/bash
# Atlas v1.4 programme (README). Kaggle CPU notebook with atlas-india-long attached.
#   ATLAS_NBR=1 SEEDS=400 TAG=v14n bash kaggle_v14.sh             # a candidate (ATLAS_GATE=1 for the gate; both for v14ng)
#   STAGE=select bash kaggle_v14.sh                               # attach the candidates, atlas-india-s400, atlas-indiap-s400..402
#   STAGE=test TAG=v14ng bash kaggle_v14.sh                       # attach the chosen seeds, atlas-india-s400..402, atlas-india-opp-gpu
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|_ureduce\|reshape(D'
if [ -n "$STAGE" ]; then
  python -u score_v14.py --stage $STAGE --tag ${TAG:-none} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_v14_$STAGE.txt
else
  for s in ${SEEDS:-400}; do
    python -u run_atlas_india.py --seed $s --tag $TAG 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_${TAG}_s$s.txt
  done
fi
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
