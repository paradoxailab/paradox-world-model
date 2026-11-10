#!/bin/bash
# PWM-W v2.1 step 1 (Kaggle CPU, internet on): CPCB rooftop stations in six more Indian cities (OpenCity, no key).
#   bash kaggle_v21_data.sh        -> /kaggle/working/raw/WX_CPCBIN.npz
set -x
export PW_RAW=/kaggle/working/raw
mkdir -p $PW_RAW
python tools/fetch_cpcb_india.py
rm -rf $PW_RAW/cpcbin_csv
ls -la $PW_RAW
