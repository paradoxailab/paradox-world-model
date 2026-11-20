#!/bin/bash
# Atlas-100M air quality, last step (PREREG deviations 1 and 5). Waits until the traffic stage has left the GPU
# (Time-MoE needs most of the L4, and sharing it would also slow the time-budgeted traffic specialists), then runs
# Time-MoE 200M with transformers 4.40.1, keeps the first seven-opponent score, and scores the full family once.
S=/content/drive/MyDrive/PWM-100M; O=$S/out; L=/content/drive/MyDrive/PWM-10M/m100_out/aq_opp2.txt
while pgrep -f "stage traffic" > /dev/null; do sleep 120; done
echo "== $(date -u) traffic stage finished; Time-MoE re-run" >> $L
cd /content/pwm/atlas/delhi && PYTHONPATH=/content/tf440 PW_RAW=/content/raw ATLAS_OUT=$O \
  python -u india_opponents.py --keys timemoe200 >> $L 2>&1
[ -f $O/atlas100m_aq_results_first7.json ] || cp $O/atlas100m_aq_results.json $O/atlas100m_aq_results_first7.json
cd /content && PW_RAW=/content/raw ATLAS_OUT=$O python -u /content/pwm/atlas/m100/score_aq.py \
  --view $O/atlas100m_aq_view.pt --india-v1 /content/pwm/models/series/40_atlas_india_v1.0.pt \
  --opp-dir $O --out $O > $S/logs/aq_score_full.txt 2>&1 && echo "$(date -u)" > $S/done/aq_score_full
cp $O/atlas100m_aq_results*.json $S/logs/aq_score_full.txt /content/drive/MyDrive/PWM-10M/m100_out/
echo "== $(date -u) AQ-FINISH-DONE" >> $L
