#!/bin/bash
# Atlas v2 data step: weather for every all-India league station (tools/fetch_weather_india.py). Kaggle CPU notebook,
# internet on, atlas-india-long attached (and this notebook's own earlier output, if a run stopped at the daily allowance).
set -x
export PW_RAW=/kaggle/working/raw WX_CACHE=/kaggle/working/wx_cache
mkdir -p $PW_RAW $WX_CACHE
find /kaggle/input -name "INDIA_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
for z in $(find /kaggle/input -name "wx_cache.zip" 2>/dev/null); do unzip -q -n $z -d $WX_CACHE; done
python -u tools/fetch_weather_india.py 2>&1 | tee /kaggle/working/log_wx.txt
mkdir -p /kaggle/working/out && mv $PW_RAW/INDIA_WX.npz $PW_RAW/DELHI_FC_*.npz /kaggle/working/out/ 2>/dev/null
rm -rf $PW_RAW/INDIA_LONG.npz $WX_CACHE
ls -la /kaggle/working /kaggle/working/out
