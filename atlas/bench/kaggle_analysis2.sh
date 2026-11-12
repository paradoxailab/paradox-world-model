#!/bin/bash
# ATF v2.0 analysis (CPU, minutes). Inputs: atf2-bench-s0..s3 and atf2-diag notebook outputs.
set -x
export ATF_OUT=/kaggle/working/out_atf
mkdir -p $ATF_OUT
for d in $(find /kaggle/input -type d -name out_atf); do cp -rn $d/* $ATF_OUT/; done
ls $ATF_OUT
python -u atf.py --law atf_law.json "$ATF_OUT/log_bench_s*.txt" 2>&1 | tee $ATF_OUT/atf2_log.txt
[ -f $ATF_OUT/log_india_diag_s0.txt ] && python -u diag_report.py $ATF_OUT/log_india_diag_s0.txt ../results/atf/curves_v10.txt 2>&1 | tee $ATF_OUT/diag_log.txt
