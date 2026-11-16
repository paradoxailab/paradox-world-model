#!/bin/bash
# World benchmark WB1 (README): WEATHER-5K runs. Kaggle GPU notebook with the atlas-w5k-fetch output attached.
#   JOBS="persist:24 dlinear:24 atlas:24:1000000:0.125 ..." bash kaggle_w5k.sh   # model:H[:size[:share]], in turn
set -x
export ATLAS_OUT=/kaggle/working/out
export PW_RAW=$(dirname $(find /kaggle/input -name W5K_X.npy | head -1))
mkdir -p $ATLAS_OUT; ls -la $PW_RAW; nvidia-smi -L || true; free -g
for j in ${JOBS:?}; do
  IFS=: read m h sz fr <<< "$j"; sz=${sz:-1000000}; fr=${fr:-1}
  t=w5k_${m}$( [ "$m" = atlas ] && echo _$((sz / 1000000))m )_h$h
  extra=""; [ "$m" = dlinear ] && extra="--steps ${DL_STEPS:-30000} --bs 1024 --lr 5e-3 --every 3000"
  if [ "$fr" != "1" ]; then t=${t}_f$(echo $fr | tr -d .); extra="$extra --frac $fr --no-test"; fi   # WB1-T: validation only
  python -u run_atlas_5k.py --model $m --H $h --size $sz --seed ${SEED:-600} --tag $t ${extra} ${EXTRA} 2>&1 \
    | grep --line-buffered -v "Warning\|warn(" | tee $ATLAS_OUT/log_${t}.txt
done
ls -la $ATLAS_OUT
