#!/bin/bash
# Kaggle (CPU, internet on): build every weather-league input. Output: /kaggle/working/raw
set -x
export PW_RAW=/kaggle/working/raw PW_OUT=/kaggle/working/out
mkdir -p $PW_RAW $PW_OUT
python tools/fetch_isd.py
python tools/fetch_nwp.py --league WMO
python tools/fetch_delhi.py && python tools/fetch_cpcb_wx.py && python tools/fetch_nwp.py --league CPCB
cd $PW_RAW && find . -maxdepth 1 -type d ! -name . ! -name nwp_cache -exec rm -rf {} +
ls -la $PW_RAW $PW_OUT
