#!/bin/bash
# PWM-F pretraining data on Kaggle (CPU is enough; internet on). Every Indian NOAA ISD station, 2015-01 .. 2024-11,
# grouped into regional networks WX_IN01.npz ... in /kaggle/working/raw (kept as this notebook's output).
#   bash kaggle_india_data.sh
set -x
export PW_RAW=/kaggle/working/raw
mkdir -p $PW_RAW
python tools/fetch_india_isd.py --workers ${WORKERS:-8} --per ${PER:-30} 2>&1 | tee $PW_RAW/fetch_india.log
ls -la $PW_RAW
du -sh $PW_RAW
