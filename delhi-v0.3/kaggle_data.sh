#!/bin/bash
# Kaggle (CPU, internet on): build every weather-league input. Output: /kaggle/working/raw
# Outputs of an earlier run attached as input are reused (including the forecast request cache).
set -x
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out
mkdir -p $PW_RAW/nwp_cache $PW_OUT
for f in /kaggle/input/*/raw/*.npz; do [ -f "$f" ] && cp -n "$f" $PW_RAW/; done
for f in /kaggle/input/*/raw/nwp_cache/*; do [ -f "$f" ] && cp -n "$f" $PW_RAW/nwp_cache/; done
for f in /kaggle/input/*/out/*; do [ -f "$f" ] && cp -n "$f" $PW_OUT/; done
ls $PW_RAW
[ -f $PW_RAW/WX_WMO.npz ] || python tools/fetch_isd.py
[ -f $PW_RAW/WX_WMO.npz ] && python tools/fetch_nwp.py --league WMO       # cached requests are not repeated
[ -f $PW_RAW/DELHI.npz ] || python tools/fetch_delhi.py
[ -f $PW_RAW/WX_CPCB.npz ] || python tools/fetch_cpcb_wx.py
python tools/fetch_nwp.py --league CPCB
cd $PW_RAW && find . -maxdepth 1 -type d ! -name . ! -name nwp_cache -exec rm -rf {} +
ls -la $PW_RAW $PW_OUT
