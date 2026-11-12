#!/bin/bash
# ATF learning curves on Kaggle (CPU). SUITE=india (inputs: pwm-india-data, pwm-v21-data, atlas-delhi) or
# SUITE=bench (no inputs: downloads the public benchmarks). DIAG=1 runs the all-India 32-64-month diagnostic.
set -x
export PW_RAW=/kaggle/working/raw ATF_OUT=/kaggle/working/out_atf
mkdir -p $PW_RAW $ATF_OUT
for f in WX_INDIA.npz WX_CPCBIN.npz DELHI.npz; do find /kaggle/input -name $f -exec cp -n {} $PW_RAW/ \; 2>/dev/null; done
if [ "${SUITE:-india}" = "bench" ]; then python -u fetch_bench.py; fi
if [ "${SUITE:-india}" = "india" ] && [ "${SHARD:-0}" = "0" ] && [ -z "$DIAG" ] && [ ! -f $PW_RAW/DELHI.npz ]; then (cd ../delhi && python tools/fetch_delhi.py 2>&1 | tail -3); fi
ls -la $PW_RAW
EXTRA=""; [ -n "$DIAG" ] && EXTRA="--diag --only isd-r0,isd-r1,isd-r2,isd-r3,isd-r4,isd-r5"
python -u curves.py --suite ${SUITE:-india} --shard ${SHARD:-0} --nshards ${NSHARDS:-4} $EXTRA ${RUN_FLAGS} 2>&1 | grep --line-buffered -v "Warning\|warn(\|f\"{self" | tee $ATF_OUT/log_${SUITE:-india}${DIAG:+_diag}_s${SHARD:-0}.txt
rm -rf $PW_RAW
du -sh $ATF_OUT
