#!/bin/bash
# Kaggle (CPU), with the data, Earth-2 and league notebook outputs attached: add the Earth-2 comparisons.
set -x
find /kaggle/input -maxdepth 4 | head -40
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out
mkdir -p $PW_RAW $PW_OUT
find /kaggle/input -path "*raw/*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -name "wx_*" -type f -exec cp -n {} $PW_OUT/ \;
python run_weather.py --league WMO --e2_only
cat $PW_OUT/wx_wmo_report.md | head -120
