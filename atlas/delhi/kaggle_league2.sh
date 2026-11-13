#!/bin/bash
# Atlas League v2.0 (rules: atlas/README.md). Kaggle notebook, internet on, with the outputs of atlas-delhi-fusion-v13
# (raw/DELHI.npz, out/fusion_members_atlas.npz, out/opponents/*.npz) and atlas-delhi-long (DELHI_LONG.npz) attached;
# for scoring, also attach every notebook that wrote out/league2/*.npz.
#   JOB="cams score" bash kaggle_league2.sh                      # CPU: CAMS, then score everything found
#   JOB=spec SPECS="stid gwnet mtgnn" MIN=100 bash kaggle_league2.sh   # GPU: graph architectures, authors' code
#   JOB=tsfm KEYS="ttm moirai2 tirex" bash kaggle_league2.sh     # foundation models, zero-shot (small ones run on CPU)
#   JOB=weather bash kaggle_league2.sh    # also attach atlas-v13-s320/s321/s322 (weights) and atlas-league2-cams (positions)
#   JOB=score bash kaggle_league2.sh
set -x
export PW_RAW=/kaggle/working/raw ATLAS_OUT=/kaggle/working/out
mkdir -p $PW_RAW $ATLAS_OUT
find /kaggle/input -name "DELHI.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
find /kaggle/input -name "DELHI_LONG.npz" -exec cp -n {} $PW_RAW/ \; 2>/dev/null
ls -la $PW_RAW
F='Warning\|warn(\|nanmean\|invalid value\|c /= \|stddev\|corrcoef\|_ureduce'
for job in ${JOB:-score}; do
  case $job in
    cams)  python -u league_v2.py --cams 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_cams.txt ;;
    spec)
      pip install -q torchinfo 2>&1 | tail -1
      EXT=/kaggle/working/ext; mkdir -p $EXT
      # the authors' repositories, pinned to the commits read when this league was written (2026-11-13)
      for r in "GestaltCogTeam/STID e8b313b" "nnzhan/Graph-WaveNet 6b162e8" "XDZhelheim/STAEformer fc49d39" \
               "LeiBAI/AGCRN 7fbbf2a" "nnzhan/MTGNN f811746"; do
        set -- $r; d=$EXT/$(basename $1)
        [ -d $d ] || { git clone -q https://github.com/$1.git $d && git -C $d checkout -q $2; }
        git -C $d log --oneline -1
      done
      for m in ${SPECS:-stid gwnet staeformer agcrn mtgnn}; do
        python -u league_v2.py --spec $m --ext $EXT --minutes ${MIN:-100} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_spec_$m.txt
      done
      rm -rf $EXT ;;
    tsfm)
      for k in ${KEYS:-ttm moirai2 tirex}; do
        case $k in                      # each model's own package; --no-deps where its pins would replace Kaggle's torch
          tfm3|tfm3mv) pip install -q timesfm 2>&1 | tail -1 ;;
          moirai2) pip install -q --no-deps uni2ts==2.0.0 && pip install -q einops jaxtyping gluonts lightning hydra-core python-dotenv 2>&1 | tail -1 ;;
          toto) pip install -q --no-deps toto-ts==0.2.0 && pip install -q einops jaxtyping gluonts lightning rotary-embedding-torch 2>&1 | tail -1 ;;
          tirex) pip install -q tirex-ts 2>&1 | tail -1 ;;
          ttm) pip install -q --no-deps granite-tsfm && pip install -q deprecated 2>&1 | tail -1 ;;
        esac
        python -u league_v2.py --tsfm $k --chunk ${CHUNK:-256} 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_tsfm_$k.txt
      done ;;
    weather) python -u league_v2.py --weather 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_weather.txt ;;
    score) python -u league_v2.py --score 2>&1 | grep --line-buffered -v "$F" | tee $ATLAS_OUT/log_score.txt ;;
  esac
done
rm -f $PW_RAW/DELHI_LONG.npz
ls -la $ATLAS_OUT $ATLAS_OUT/league2 2>/dev/null
