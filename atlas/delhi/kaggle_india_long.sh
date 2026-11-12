#!/bin/bash
# All-India station history (India-first league, data step). Kaggle CPU notebook with one input attached:
# the dataset "Time Series Air Quality Data of India (2010-2023)".
set -x
export PW_RAW=/kaggle/working/raw
mkdir -p $PW_RAW
python -u tools/build_india_long.py 2>&1 | grep --line-buffered -v "Warning\|warn("
ls -la $PW_RAW
