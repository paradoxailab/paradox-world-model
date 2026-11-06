#!/bin/bash
# Kaggle (CPU, internet on): build every weather-league input. Output: /kaggle/working/raw
# Outputs of an earlier run attached as input are reused (including the forecast request cache).
set -x
find /kaggle/input -maxdepth 4 | head -40
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out
mkdir -p $PW_RAW/nwp_cache $PW_OUT
find /kaggle/input -path "*raw/*.npz" -exec cp -n {} $PW_RAW/ \;
find /kaggle/input -path "*raw/nwp_cache/*" -type f -exec cp -n {} $PW_RAW/nwp_cache/ \;
find /kaggle/input -path "*out/*" -maxdepth 6 -type f ! -path "*cache*" -exec cp -n {} $PW_OUT/ \;
ls $PW_RAW
[ -f $PW_RAW/WX_WMO.npz ] || python tools/fetch_isd.py
[ -f $PW_RAW/WX_WMO.npz ] && python tools/fetch_nwp.py --league WMO       # cached requests are not repeated
[ -f $PW_RAW/DELHI.npz ] || python tools/fetch_delhi.py
[ -f $PW_RAW/WX_CPCB.npz ] || python tools/fetch_cpcb_wx.py
python tools/fetch_nwp.py --league CPCB
cd $PW_RAW && find . -maxdepth 1 -type d ! -name . ! -name nwp_cache -exec rm -rf {} +
ls -la $PW_RAW $PW_OUT
