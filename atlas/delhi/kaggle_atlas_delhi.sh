#!/bin/bash
# Atlas on Delhi PM2.5 (stage 7). Kaggle notebook, internet on; CPU is enough for sizes up to 1M (GPU is used if present).
#   bash kaggle_atlas_delhi.sh                       # everything
#   RUN_FLAGS="--sizes 250000,1000000,10000000" bash kaggle_atlas_delhi.sh      # with the 10M model (GPU)
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT/opponents
# reuse an attached copy of the data file or of earlier opponent forecasts, if any; otherwise build from CPCB's files
find /kaggle/input -name "DELHI.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
find /kaggle/input -path "*out/opponents/*.npz" -exec cp -n {} $ATLAS_OUT/opponents/ \; 2>/dev/null
[ -f $PW_RAW/DELHI.npz ] || python tools/fetch_delhi.py 2>&1 | tail -70
pip install -q timesfm chronos-forecasting 2>&1 | tail -2
python run_atlas_delhi.py ${RUN_FLAGS} 2>&1 | grep -v "Warning\|warn(" | tee $ATLAS_OUT/log.txt
rm -rf $PW_RAW/delhi_csv
ls -la $ATLAS_OUT $ATLAS_OUT/opponents
