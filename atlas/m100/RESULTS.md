# Atlas-100M results: interim release (weather and air quality complete, traffic and hybrid pending)

ParadoxAI Lab · Aditya Kumar, Anupam Singh · 2026-11-21

This file reports every finished comparison of the pre-registered Atlas-100M study (`PREREG.md`, committed before the
first GPU run) as it came out: wins, ties and losses. **Traffic and the hybrid stage are still running and are marked
pending; nothing below is a projection.** Raw outputs are in `results/` (copied unchanged from the run's Drive store);
deviations from the plan are listed in `PREREG.md` (1–5, each dated, with the reason). Weights:
[huggingface.co/paradoxailab/atlas-100m](https://huggingface.co/paradoxailab/atlas-100m) (SHA-256 in `results/SHA256SUMS`,
verified against Hugging Face after upload).

**Verdict rule (section 6 of PREREG):** WIN = lower error, Holm-adjusted p < 0.01 and a 95% interval of the difference
that excludes 0; LOSS = the mirror image; anything else TIE. Percentages are Atlas-100M's error relative to the
opponent's (negative = Atlas-100M better).

## The model

- **98,599,994 parameters** in one set of weights: a shared core of 94.76M (8 encoder blocks, geometry-biased
  attention between stations, 7 latent-dynamics blocks; width 784, 16 heads) plus small per-domain adapters
  (weather 0.78M, air quality 2.98M, traffic 0.08M).
- Grown exactly from the adopted Atlas-5K 24.1M (paper 5): check G0 passed (the grown model reproduced the 24.1M's
  validation error before training).
- Trained 100,000 steps on real station data only (weather 50%, air quality 25%, traffic 25%), one A100, 317.6 min.
  Best checkpoint at step 100,000 (`results/atlas100m_summary.json`).

## Weather

### Full 2023 test (all 5,672 stations, every hourly window, ≈ 1.18 × 10⁹ values per variable, MAE)

| Model | Params | Temp. | Dew pt. | Wind dir. | Wind spd. | Pressure |
|---|---|---|---|---|---|---|
| **Atlas-100M (this study)** | 98.6M (95.5M weather view) | **1.396** | **1.466** | **53.23** | **1.172** | 1.474 |
| Atlas-5K 25M (paper 5) | 24.1M | 1.400 | 1.468 | 53.33 | 1.173 | 1.473 |
| Atlas-5K 10M | 9.64M | 1.429 | 1.486 | 53.93 | 1.183 | 1.477 |
| Atlas-5K v2c | 0.97M | 1.474 | 1.520 | 54.84 | 1.202 | 1.533 |
| PhysicsFormer (WEATHER-5K paper, published) | 19.3M | 1.55 | 1.59 | 57.37 | 1.21 | **1.43** |
| ECMWF-HRES at stations (WEATHER-5K paper, published) | – | 1.76 | 1.85 | 63.8 | 1.48 | **0.86** |
| Atlas-100M vs PhysicsFormer | | −9.9% | −7.8% | −7.2% | −3.1% | **+3.1%** |
| Atlas-100M vs ECMWF-HRES | | −20.7% | −20.8% | −16.6% | −20.8% | **+71.4%** |

Published rows are compared by number only (no paired test is possible). Validation E (all stations):
Atlas-100M 0.27275, Atlas-5K 24.1M 0.27307.

### Head-to-head against ten zero-shot foundation models (709 stations; paired tests)

2023 test (every 48 h) and the live period 1 Jan 2024 – 24 Aug 2025 (NOAA ISD-Lite, every 96 h):

| Opponent | Temp. | Dew pt. | Wind dir. | Wind spd. | Pressure | Wins |
|---|---|---|---|---|---|---|
| Persistence | −62.8% / −62.7% | −34.4% / −33.3% | −28.9% / −26.1% | −31.6% / −32.4% | −47.2% / −42.3% | 5/5, 5/5 |
| Chronos-Bolt | −26.7% / −25.2% | −27.7% / −27.6% | −16.4% / −10.3% | −13.2% / −12.3% | −26.1% / −21.6% | 5/5, 5/5 |
| Chronos-2 | −26.8% / −25.3% | −25.8% / −25.9% | −15.1% / −10.4% | −12.5% / −13.0% | −27.4% / −23.1% | 5/5, 5/5 |
| Chronos-2 multivariate | −24.6% / −23.2% | −24.0% / −24.2% | −14.2% / −9.1% | −11.6% / −12.1% | −28.8% / −24.6% | 5/5, 5/5 |
| TimesFM 2.5 | −29.4% / −28.1% | −27.0% / −27.1% | −15.6% / −11.2% | −11.7% / −12.0% | −26.9% / −22.9% | 5/5, 5/5 |
| TimesFM 3.0 | −25.9% / −24.5% | −25.6% / −25.6% | −14.6% / −9.7% | −11.2% / −11.2% | −25.1% / −20.8% | 5/5, 5/5 |
| TTM r2 | −36.1% / −34.7% | −32.4% / −31.5% | −18.1% / −13.4% | −13.2% / −12.6% | −48.0% / −42.5% | 5/5, 5/5 |
| TiRex | −26.8% / −26.3% | −25.4% / −25.7% | −16.4% / −12.3% | −11.0% / −11.4% | −24.5% / −20.3% | 5/5, 5/5 |
| Sundial | −27.7% / −26.5% | −27.4% / −27.3% | −16.0% / −11.6% | −11.8% / −11.8% | −27.4% / −22.6% | 5/5, 5/5 |
| Time-MoE 200M | −28.9% / −28.7% | −28.4% / −29.1% | −17.8% / −14.5% | −13.5% / −14.0% | −26.0% / −22.4% | 5/5, 5/5 |

Each cell: 2023 test / live period. **All 100 comparisons are WINs.**

### Against our own 24.1M model (same windows)

| | Temp. | Dew pt. | Wind dir. | Wind spd. | Pressure |
|---|---|---|---|---|---|
| 2023 test | −0.03% TIE | −0.09% TIE | −0.14% WIN | +0.07% TIE | +0.40% TIE |
| Live 2024–25 | −0.1% TIE | −0.1% TIE | −0.1% TIE | −0.1% TIE | **+1.0% LOSS** |

Growing to 100M and sharing the weights with air quality and traffic gave weather essentially nothing, and cost
pressure in the live period.

## Air quality (all-India PM2.5: 14 networks, 263 stations, test Oct 2022 – Mar 2023, next 24 h, MAE µg/m³)

Track S = stations trained on; Track U = stations never trained on. Nine zero-shot foundation models with 512 h of
context, paper 3's Atlas-India v1.0, and two baselines; one Holm family of 24 comparisons.

| Opponent | Track S: Atlas-100M 21.58 vs | Verdict | Track U: Atlas-100M 21.31 vs | Verdict |
|---|---|---|---|---|
| Last observed value | 32.01 (−32.6%) | WIN | 31.13 (−31.6%) | WIN |
| Same hour yesterday | 29.86 (−27.7%) | WIN | 29.30 (−27.3%) | WIN |
| TTM r2 (IBM) | 23.19 (−7.0%) | WIN | 22.72 (−6.2%) | WIN |
| Time-MoE 200M | 23.08 (−6.5%) | WIN | 22.54 (−5.5%) | WIN |
| Sundial (Tsinghua) | 22.67 (−4.8%) | WIN | 22.11 (−3.7%) | TIE |
| Chronos-Bolt (Amazon) | 22.61 (−4.6%) | WIN | 22.30 (−4.5%) | TIE |
| TimesFM 2.5 (Google) | 22.35 (−3.4%) | WIN | 21.93 (−2.8%) | TIE |
| Chronos-2 (Amazon) | 22.30 (−3.2%) | WIN | 22.03 (−3.3%) | TIE |
| TiRex (NX-AI) | 22.16 (−2.6%) | WIN | 21.73 (−2.0%) | TIE |
| TimesFM 3.0 (Google) | 22.00 (−1.9%) | TIE (p_holm 0.048) | 21.63 (−1.5%) | TIE |
| **TimesFM 3.0 multivariate** | 21.41 (**+0.8%**) | TIE | 20.95 (**+1.7%**) | TIE |
| **Atlas-India v1.0 (paper 3)** | 21.47 (**+0.5%**) | TIE | 21.32 (−0.0%) | TIE |

Sundial and Time-MoE were re-run with the `transformers` version their code needs (deviations 1 and 5); the first,
seven-opponent score is kept unchanged in `results/atlas100m_aq_results_first7.json`.

## Traffic (pending)

ParadoxBench-1.1, six networks, 12 → 12 steps. At this release 44 of 48 opponent and specialist jobs have finished
(PEMS08, PEMS04, PEMS03, PEMS07 and METR-LA complete; PEMS-BAY running); PWM-Dyn v0.6r and the paired scoring follow.
No traffic result is reported until the scoring has run.

## Hybrid against ECMWF IFS, AIFS, GFS and GraphCast (pending)

Waits for the Open-Meteo forecast archive (free daily limit; several days).

## Predictions (scored as written in PREREG section 7)

| # | Prediction | Prob. | Result |
|---|---|---|---|
| P1 | G0 holds | 0.99 | **HELD** |
| P2 | Weather validation E ≤ 0.27307 | 0.55 | **HELD** (0.27275; deviation 3) |
| P3 | Weather validation E ≤ 0.2700 | 0.20 | FAILED |
| P4 | WIN in all 50 comparisons, both periods | 0.85 | **HELD** (100/100) |
| P5 | Head-to-head test E lower than the 24.1M | 0.55 | FAILED (0.274180 vs 0.274173) |
| P6 | Beats PhysicsFormer on ≥ 4 of 5 variables | 0.75 | **HELD** (4/5) |
| P7 | Beats PhysicsFormer on pressure | 0.15 | FAILED (1.474 vs 1.43) |
| P8 | AQ Track S: WIN against every foundation model | 0.60 | FAILED (7/9; ties with TimesFM 3.0 and 3.0 multivariate) |
| P9 | AQ Track U: WIN against every foundation model | 0.35 | FAILED (2/9) |
| P10 | AQ Track S: WIN against Atlas-India v1.0 | 0.45 | FAILED (tie, 0.5% worse) |
| P11–P13 | Traffic | | pending |
| P14–P17 | Hybrid | | pending |

## What these results do and do not show

- **Task-trained against zero-shot.** Every foundation model above is used zero-shot under its documented settings;
  Atlas-100M trained on these stations' earlier years and sees each station's neighbours. The weather and air-quality
  wins show that a compact model trained for the task beats general models used without training on it. They do not
  show a better general-purpose model.
- **Where it is weak:** sea-level pressure (worse than PhysicsFormer, much worse than ECMWF-HRES), stations it never
  trained on (mostly ties), and TimesFM 3.0 multivariate on air quality (tie, slightly worse).
- **Scale did not help weather.** The 100M is equal to the 24.1M within 0.1% except pressure.
- **One training seed** (700); seed variance is not measured.
- Not compared: video or robotics world models, or global gridded weather models on their own grids. No claim of
  "the best world model" is made.
