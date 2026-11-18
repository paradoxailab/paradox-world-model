#!/bin/bash
# Phase 6 rerun of the three opponents whose first run failed for harness reasons (README, "Atlas-5K 25M results,
# part 2"): TTM r2 needs IBM's hourly frequency token; Sundial and Time-MoE need their documented transformers==4.40.1,
# which cannot be installed on Colab's Python 3.13, so they run in a Python 3.11 environment. Nothing else changes:
# same windows, same 512-hour history, same median. Then every paired test of the family is (re)computed.
set -u
H2=/content/drive/MyDrive/PWM-10M/small; LIVE=/content/live; RAW=/content/raw
cd /content/pwm/atlas/delhi
pip install -q uv >/dev/null 2>&1
if [ ! -x /content/py311/bin/python ]; then
  uv venv -q --python 3.11 /content/py311 && uv pip install -q --python /content/py311/bin/python torch "numpy<2" "transformers==4.40.1" accelerate 2>&1 | tail -2
fi
for spec in "test 48 $RAW" "live 96 $LIVE"; do
  set -- $spec; yr=$1; oe=$2; raw=$3
  ATLAS_OUT=$H2 PW_RAW=$raw python -u score_tsfm_w5k.py --stations-every 8 --year $yr --origin-every $oe --models ttm 2>&1 | grep -v Warning | tail -3
  for m in sundial timemoe200; do
    ATLAS_OUT=$H2 PW_RAW=$raw /content/py311/bin/python -u score_tsfm_w5k.py --stations-every 8 --year $yr --origin-every $oe --models $m 2>&1 | grep -v Warning | tail -3
  done
done
OPP="persist chronos-bolt chronos2 chronos2mv tfm25 tfm3 ttm tirex sundial timemoe200"
for yr in test live; do
  have=""; for k in $OPP; do [ -f $H2/h2h/${k}_$yr.npz ] && have="$have,$k"; done; have=${have#,}
  echo "===== $yr: opponents scored: $have"
  for ours in atlas25m atlas10m; do ATLAS_OUT=$H2 python paired_w5k.py --year $yr --ours $ours --vs $have --suffix _r25 | grep -E "vs|FULLY"; done
  ATLAS_OUT=$H2 python paired_w5k.py --year $yr --ours atlas25m --vs atlas10m --suffix _vs10m
done
ATLAS_OUT=$H2 python paired_w5k.py --year val --ours atlas25m --vs atlas10m --suffix _vs10m
echo PHASE6-DONE
