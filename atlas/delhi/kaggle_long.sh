#!/bin/bash
# Delhi long history (Atlas-Delhi v1.1, data step). Kaggle CPU notebook with two inputs attached:
#   the atlas-delhi notebook's output (for DELHI.npz) and the dataset "Time Series Air Quality Data of India (2010-2023)".
set -x
export PW_RAW=/kaggle/working/raw
mkdir -p $PW_RAW
find /kaggle/input -name "DELHI.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
[ -f $PW_RAW/DELHI.npz ] || python tools/fetch_delhi.py 2>&1 | tail -30
ls /kaggle/input/ /kaggle/input/* | head -60
python -u tools/build_delhi_long.py 2>&1 | grep --line-buffered -v "Warning\|warn("
rm -rf $PW_RAW/delhi_csv
ls -la $PW_RAW
