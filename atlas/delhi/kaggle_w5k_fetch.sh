#!/bin/bash
# World benchmark WB1 (README): download WEATHER-5K from the authors' public share and convert it (Kaggle CPU, internet on).
set -x
df -h /kaggle/working /kaggle/tmp 2>/dev/null; free -g
mkdir -p /kaggle/working/out /kaggle/tmp
python -u tools/fetch_weather5k.py --out /kaggle/working/out --tmp /kaggle/tmp --workers 4 2>&1 | tee /kaggle/working/out/log_w5k_fetch.txt
ls -la /kaggle/working/out
