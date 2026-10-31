# Paradox World Model — PWM-Dyn v0.4 and the ParadoxBench-1 benchmark

This kit contains two things:

1. **ParadoxBench-1** (`paradoxbench/`), an open benchmark for forecasting physical quantities that move over real
   networks: US highway traffic (PEMS08, PEMS04) and Indian monsoon rainfall (IMD central India,
   IMD Konkan/Western Ghats). Four tracks (standard, open context, robustness, zero-shot transfer),
   one scorer, frozen test windows. See `paradoxbench/SPEC.md`.
2. **PWM-Dyn v0.4** (`pwm/`, `train.py`), Paradox's physical dynamics model, trained from random
   initialisation on each task's training split, and the head-to-head harness against Google
   TimesFM 2.5 / 3.0 (`opponents/`).

## Run the whole study

On a machine with two GPUs (Kaggle "GPU T4 x2" works):

```
pip install imdlib timesfm
# PeMS: put PEMS08/PEMS04 .npz + .csv in data/raw (ASTGNN repository mirrors)
python -c "from pwm.data import download_imd as d; d('central_india'); d('west_coast')"
python run_paradoxbench.py            # ~4 h: trains PWM, runs TimesFM, writes LEADERBOARD.md
python run_paradoxbench.py --quick    # 12-min pipeline check on CPU (stub opponents, never reported)
```

## Submit your own model to ParadoxBench-1

Produce `q10`, `q50`, `q90` arrays of shape `[windows, horizon, locations]` for the official test
windows (`paradoxbench.spec.official_windows`), save them as `.npz`, then:

```
python -m paradoxbench.score --task PEMS08 --track B --sub my_model.npz --model "My model" \
    --type foundation --params 1.2e8 --context 512 --trained-on "what it was trained on"
python paradoxbench/leaderboard.py
```

## What changed in v0.4

| Change | Why |
|---|---|
| Seasonal-lag window (same time yesterday / same days last year), kept inside TimesFM's context budget | Long-context variant for Track B |
| Train-split climatology input, and climatology as the fallback base for dark sensors | Accuracy everywhere; robustness when sensors go offline |
| Split-conformal calibration (CQR) of the 80 % interval on validation, in target space | Fixes v0.3's rainfall under-coverage without touching the median |
| Recipe: batch 64, 40 epochs, peak lr 3e-3 | 3x faster training, same model family |

## Provenance

`python check_provenance.py` proves that every checkpoint contains only PWM-Dyn's own parameters and
that `pwm/`, `paradoxbench/` and `train.py` import no external model library. TimesFM runs only as an
opponent, zero-shot, and is never loaded into PWM.
