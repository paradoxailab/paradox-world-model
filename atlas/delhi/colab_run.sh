#!/bin/bash
# Run Atlas jobs on Google Colab (free CPU or T4 GPU) when Kaggle's CPU slots are full.
# Every input is rebuilt from the public sources, so nothing has to be uploaded and no key is needed:
#   * CPCB's 2010-2023 station files: the public Kaggle dataset, fetched with kagglehub (no login for public data);
#   * the Delhi league file: OpenCity, tools/fetch_delhi.py.
#   bash colab_run.sh lockdown            # what-if test 1 (about 10 min on a T4, about 70 min on CPU)
#   bash colab_run.sh india               # the all-India league: seeds 400-402 and the scoring
#   bash colab_run.sh lockdown india      # both, one after the other
#   bash colab_run.sh india-opp           # TimesFM and Chronos on the all-India windows (GPU), then the scoring again
export PW_RAW=/content/raw ATLAS_OUT=/content/out
mkdir -p $PW_RAW $ATLAS_OUT
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|Mean of empty'
python -c "import torch; print('device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu', '| torch', torch.__version__)"
nproc; free -g | head -2
DS=abhisheksjha/time-series-air-quality-data-of-india-2010-2023
python - <<PY
try:
    import kagglehub
    p = kagglehub.dataset_download("$DS")
    open("/content/ds_path.txt", "w").write(p)
    print("CPCB 2010-2023 files at", p)
except Exception as e:
    print("kagglehub did not work:", type(e).__name__, str(e)[:200])
PY
if [ ! -s /content/ds_path.txt ]; then                       # the same public files through the public download address
  mkdir -p /content/cpcb && curl -sL -o /content/cpcb.zip "https://www.kaggle.com/api/v1/datasets/download/$DS" \
    && unzip -q -o /content/cpcb.zip -d /content/cpcb && echo -n /content/cpcb > /content/ds_path.txt
fi
export LONG_SEARCH=$(cat /content/ds_path.txt)
ls $LONG_SEARCH | head -5; find $LONG_SEARCH -name "*.csv" | wc -l
for job in "$@"; do
  echo "=================== $job"
  if [ "$job" = "lockdown" ]; then
    [ -f $PW_RAW/DELHI.npz ] || python tools/fetch_delhi.py 2>&1 | grep -v "$F" | tail -25
    [ -f $PW_RAW/DELHI_LONG.npz ] || python -u tools/build_delhi_long.py 2>&1 | grep -v "$F" | grep "matched\|NO MATCH\|solar-radiation\|DELHI_LONG\|20[12][0-9]:\|ratio\|LONG "
    python -u run_lockdown.py 2>&1 | grep --line-buffered -v "$F" | grep --line-buffered -v "step [0-9]*[1-9]00 \|step [0-9]*[13579]000 " | tee $ATLAS_OUT/log_lockdown.txt
  elif [ "$job" = "india" ]; then
    [ -f $PW_RAW/INDIA_LONG.npz ] || python -u tools/build_india_long.py 2>&1 | grep -v "$F" | grep "read 453\|INDIA_LONG\|usable\|INDIA "
    for s in ${SEEDS:-400 401 402}; do
      [ -f $ATLAS_OUT/india_s$s.npz ] || python -u run_atlas_india.py --seed $s 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_india_s$s.txt
    done
    python -u score_india.py 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_india_score.txt
  elif [ "$job" = "india-opp" ]; then                       # foundation models on the same windows (GPU), then rescore
    [ -f $PW_RAW/INDIA_LONG.npz ] || python -u tools/build_india_long.py 2>&1 | grep -v "$F" | grep "read 453\|INDIA_LONG\|usable\|INDIA "
    pip install -q timesfm chronos-forecasting 2>&1 | tail -2
    python -u india_opponents.py ${OPP_FLAGS} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_india_opp.txt
    python -u score_india.py 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_india_score2.txt
  fi
done
ls -la $ATLAS_OUT
echo "COLAB-DONE $@"
