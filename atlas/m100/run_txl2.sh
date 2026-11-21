#!/bin/bash
# Atlas-100M-TXL2 (PREREG_TRAFFIC.md addendum C): train, score once on Track B, check W, copy results.
# Run inside the TXL Colab session (Drive mounted, data fetched, V06 set up by atlas_100m_traffic_xl_colab.ipynb).
S=/content/drive/MyDrive/PWM-100M; OUT=$S/out; TP=$S/traffic_plus; V06=/content/pwm/v0.6-conference
DST=/content/drive/MyDrive/PWM-10M/m100_out; LOG=$DST/txl2_run.txt
exec > >(tee -a $LOG) 2>&1
echo "== $(date -u) TXL2 start"; cd /content/pwm && git log --oneline -1
rm -f $V06/submissions/*Atlas-100M-T* $V06/results/paradoxbench/*Atlas-100M-T*     # family fixed by addendum C
echo "submissions in family: $(ls $V06/submissions/*.npz | wc -l)"
cd $OUT && sha256sum -c <(grep -E "best|weather_view|aq_view" /content/pwm/atlas/m100/results/SHA256SUMS) || { echo "CHECK W before FAILED"; exit 1; }
cd $V06 && python -u ../atlas/m100/traffic_plus.py train --base $OUT/atlas100m_traffic_view.pt --out $TP --r 128 \
  --alpha 64 --E 64 --ctx 288 --steps 60000 --cap 360 --name Atlas-100M-TXL2 --tag atlas100mTXL2 2>&1 \
  | grep --line-buffered -v "Warning\|warn("
[ -f $TP/atlas100mTXL2_best.pt ] || { echo "no TXL2 checkpoint"; exit 1; }
python -u ../atlas/m100/score_traffic.py --plus $TP/atlas100mTXL2_best.pt --name Atlas-100M-TXL2 \
  --summary $OUT/atlas100m_summary.json --out $TP 2>&1 | grep --line-buffered "ParadoxBench\|TEST\|Error\|Traceback"
cp $V06/submissions/*Atlas-100M-TXL2* $S/v06/submissions/; cp $V06/results/paradoxbench/*Atlas-100M-TXL2* $S/v06/results/paradoxbench/
cd $OUT && sha256sum -c <(grep -E "best|weather_view|aq_view" /content/pwm/atlas/m100/results/SHA256SUMS) && echo "CHECK W after: OK"
cp $TP/atlas100mTXL2_log.jsonl $TP/atlas100mTXL2_summary.json $TP/atlas100mtxl2_traffic_results.json $DST/
echo "== $(date -u) TXL2-DONE"
