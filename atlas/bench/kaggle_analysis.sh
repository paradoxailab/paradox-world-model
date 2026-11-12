#!/bin/bash
# ATF v1.1 / v1.2 analysis on Kaggle (CPU, minutes). Inputs: the four atf-curves-s* notebooks (+ the FM notebook for v1.2).
set -x
export ATF_OUT=/kaggle/working/out_atf
mkdir -p $ATF_OUT
for d in $(find /kaggle/input -type d -name out_atf); do cp -rn $d/* $ATF_OUT/; done
ls $ATF_OUT $ATF_OUT/curves | head -50
python -u atf.py "$ATF_OUT/log_s*.txt" 2>&1 | tee $ATF_OUT/atf_log.txt
[ -d $ATF_OUT/fm ] && python -u blend.py 2>&1 | grep -v "Warning\|warn(" | tee $ATF_OUT/blend_log.txt
