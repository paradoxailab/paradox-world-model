#!/bin/bash
# PWM-W v2.0 step 1 (Kaggle CPU, internet on): download the all-India NOAA ISD pretraining corpus.
#   bash kaggle_v20_data.sh        -> /kaggle/working/raw/PRE_INDIA.npz
set -x
export PW_RAW=/kaggle/working/raw
mkdir -p $PW_RAW
python tools/fetch_india.py --workers ${WORKERS:-6}
ls -la $PW_RAW
