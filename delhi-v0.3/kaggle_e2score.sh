#!/bin/bash
# Kaggle (CPU), with the data, Earth-2 and league notebook outputs attached: add the Earth-2 comparisons.
set -x
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out
mkdir -p $PW_RAW $PW_OUT
for f in /kaggle/input/*/raw/*.npz; do cp -n "$f" $PW_RAW/; done
for f in /kaggle/input/*/out/wx_*; do cp -n "$f" $PW_OUT/; done
python run_weather.py --league WMO --e2_only
cat $PW_OUT/wx_wmo_report.md | head -120
