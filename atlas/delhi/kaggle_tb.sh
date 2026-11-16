#!/bin/bash
# Atlas v2-W, T-B (README, "Atlas v2-W"): the adopted weather model (W1) by the I1 recipe, scored on Delhi's winter
# 2024-25 with real day-before forecasts. Kaggle notebook with atlas-india-long, atlas-delhi-long and atlas-wx-fetch
# attached (and, to skip pre-training, an output holding atlas_wx13_s<seed>.pt).
#   SEEDS="320" bash kaggle_tb.sh        # pre-training on the 13 other networks with ERA5, then Delhi to 2024-07-31 with
#                                        # ERA5; in the test window every weather value is the ECMWF forecast of the day before
#   SCORE=1 bash kaggle_tb.sh            # attach atlas-tb-s320..322 and atlas-i1-s320..322 as well: I1 scoring + B5
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
export PW_SPLIT="2024-08-01,2024-10-01,2025-03-01"   # validation from, test from, test to (exclusive); applies to the Delhi file
mkdir -p $PW_RAW $ATLAS_OUT
for f in INDIA_LONG.npz DELHI_LONG.npz INDIA_WX.npz "DELHI_FC_*.npz"; do
  find /kaggle/input -name "$f" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
done
ls -la $PW_RAW
nvidia-smi -L || true
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|_ureduce\|reshape(D'
if [ -n "$SCORE" ]; then                               # scoring reads only the measurements: no weather needed
  python -u score_i1.py --tag wi1 --ref i1 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_score_tb.txt
else
  export ATLAS_WX=1
  for s in ${SEEDS:-320}; do
    CK=$(find /kaggle/input -name "atlas_wx13_s$s.pt" | head -1)
    if [ -z "$CK" ]; then                             # pre-training does not read the Delhi file
      env -u PW_SPLIT python -u run_atlas_india.py --seed $s --size 1000000 --skip Delhi --tag wx13 --pretrain-only 2>&1 \
        | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_pre_s$s.txt
      CK=$ATLAS_OUT/atlas_wx13_s$s.pt
    fi
    ATLAS_WX_FC=DELHI_FC_ecmwf_ifs025.npz python -u run_atlas_long.py --seed $s --size 1000000 --init $CK --tag wi1 --lr-b 0.3 --steps 12000 2>&1 \
      | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_s$s.txt
  done
fi
rm -rf $PW_RAW/INDIA_LONG.npz $PW_RAW/DELHI_LONG.npz $PW_RAW/INDIA_WX.npz $PW_RAW/india_nets
ls -la $ATLAS_OUT
