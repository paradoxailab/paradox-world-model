#!/bin/bash
# ATF v1.0 learning curves on Kaggle (CPU). Attach as inputs: pwm-india-data (WX_INDIA.npz), pwm-v21-data
# (WX_CPCBIN.npz) and atlas-delhi (raw/DELHI.npz). SHARD = 0..3.
set -x
export PW_RAW=/kaggle/working/raw ATF_OUT=/kaggle/working/out_atf
mkdir -p $PW_RAW $ATF_OUT
for f in WX_INDIA.npz WX_CPCBIN.npz DELHI.npz; do find /kaggle/input -name $f -exec cp -n {} $PW_RAW/ \; 2>/dev/null; done
if [ "${SHARD:-0}" = "0" ] && [ ! -f $PW_RAW/DELHI.npz ]; then (cd ../delhi && python tools/fetch_delhi.py 2>&1 | tail -3); fi
ls -la $PW_RAW
python -u curves.py --shard ${SHARD:-0} --nshards 4 ${RUN_FLAGS} 2>&1 | grep --line-buffered -v "Warning\|warn(" | tee $ATF_OUT/log_s${SHARD:-0}.txt
rm -rf $PW_RAW
du -sh $ATF_OUT
