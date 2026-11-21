# Atlas-100M results: v1.0 (weather, air quality and traffic complete; hybrid pending)

ParadoxAI Lab · Aditya Kumar, Anupam Singh · 2026-11-21

This file reports every finished comparison of the pre-registered Atlas-100M study (`PREREG.md`, committed before the
first GPU run) as it came out: wins, ties and losses. **The hybrid comparison with ECMWF / GFS is still waiting for its
forecast archive and is marked pending; nothing below is a projection.** Raw outputs are in `results/` (copied unchanged from the run's Drive store);
deviations from the plan are listed in `PREREG.md` (1–6, each dated, with the reason). Weights:
[huggingface.co/paradoxailab/atlas-100m](https://huggingface.co/paradoxailab/atlas-100m) (SHA-256 in `results/SHA256SUMS`,
verified against Hugging Face after upload).

**Verdict rule (section 6 of PREREG):** WIN = lower error, Holm-adjusted p < 0.01 and a 95% interval of the difference
that excludes 0; LOSS = the mirror image; anything else TIE. Percentages are Atlas-100M's error relative to the
opponent's (negative = Atlas-100M better).

## Summary

| Domain | Against zero-shot foundation models | Against trained specialists / our single-domain models |
|---|---|---|
| Weather | **WIN 100 / 100** (10 models, 2023 and 2024–25) | better than PhysicsFormer on 4/5 (not pressure); equal to Atlas-5K 24.1M |
| Air quality | WIN 7/9 on trained stations, 2/9 on never-trained (rest TIE) | TIE with Atlas-India v1.0 |
| Traffic | WIN 7, TIE 11, LOSS 12 (5 models × 6 networks) | **LOSS** 22 / 24 against STID, Graph WaveNet, STAEformer, PWM-Dyn |
| Hybrid vs ECMWF / GFS | pending | pending |
| *Traffic, follow-up Atlas-100M-T (4.84M traffic parameters)* | *WIN 14, TIE 16, LOSS 0* | *WIN 2, TIE 8, LOSS 14* |
| *Traffic, follow-up Atlas-100M-TXL2 (20.45M traffic parameters)* | ***WIN 18, TIE 12, LOSS 0*** | *WIN 4, TIE 13, LOSS 7* |

Predictions: 4 of 13 scored so far held (P1, P2, P4, P6); 9 failed; P14–P17 pending. The rows above are Atlas-100M
v1.0 and stay as published; Atlas-100M-T is a separate, separately pre-registered model (`PREREG_TRAFFIC.md`).

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

## Traffic (ParadoxBench-1.1: six road networks, next 12 steps of 5 min from the last 12, MAE)

**Atlas-100M loses traffic.** Every forecast below is Atlas-100M's single traffic view (80K adapter parameters on the
shared core, context 12 steps). Track A opponents are specialists trained on each network with their authors' code and
paper 1's time budgets (here on Colab L4 / A100 GPUs, which gives them as many or more epochs than in paper 1), plus our
own PWM-Dyn v0.6r (paper 1's recipe, three fresh seeds); Track B adds five zero-shot foundation models with 512 steps of
context. One Holm family of 72 comparisons (Diebold–Mariano and day-block bootstrap).

| Opponent | PEMS08 | PEMS04 | PEMS03 | PEMS07 | METR-LA | PEMS-BAY | W/T/L |
|---|---|---|---|---|---|---|---|
| **Atlas-100M MAE** | **17.170** | **21.688** | **16.181** | **23.261** | **3.310** | **1.699** | |
| Chronos-Bolt | 18.443 (-6.9%) TIE | 22.866 (-5.2%) TIE | 17.177 (-5.8%) TIE | 25.664 (-9.4%) WIN | 3.875 (-14.6%) WIN | 1.996 (-14.9%) WIN | 3/3/0 |
| Chronos-2 | 17.148 (+0.1%) TIE | 21.524 (+0.8%) TIE | 15.913 (+1.7%) TIE | 23.566 (-1.3%) TIE | 3.674 (-9.9%) WIN | 1.829 (-7.1%) WIN | 2/4/0 |
| TimesFM 2.5 | 15.038 (+14.2%) LOSS | 19.702 (+10.1%) LOSS | 14.609 (+10.8%) LOSS | 20.894 (+11.3%) LOSS | 3.491 (-5.2%) WIN | 1.692 (+0.4%) TIE | 1/1/4 |
| TimesFM 3.0 | 14.629 (+17.4%) LOSS | 19.273 (+12.5%) LOSS | 14.331 (+12.9%) LOSS | 20.464 (+13.7%) LOSS | 3.491 (-5.2%) WIN | 1.708 (-0.5%) TIE | 1/1/4 |
| TimesFM 3.0 mv | 14.549 (+18.0%) LOSS | 19.135 (+13.3%) LOSS | 14.148 (+14.4%) LOSS | 20.270 (+14.8%) LOSS | 3.401 (-2.7%) TIE | 1.661 (+2.3%) TIE | 0/2/4 |
| STID | 14.234 (+20.6%) LOSS | 18.484 (+17.3%) LOSS | 15.393 (+5.1%) TIE | 19.617 (+18.6%) LOSS | 3.124 (+6.0%) LOSS | 1.562 (+8.8%) LOSS | 0/1/5 |
| Graph WaveNet | 14.674 (+17.0%) LOSS | 18.984 (+14.2%) LOSS | 14.552 (+11.2%) LOSS | 22.416 (+3.8%) LOSS | 3.066 (+8.0%) LOSS | 1.574 (+8.0%) LOSS | 0/0/6 |
| STAEformer | 13.500 (+27.2%) LOSS | 18.281 (+18.6%) LOSS | 15.218 (+6.3%) TIE | 21.506 (+8.2%) LOSS | 2.970 (+11.5%) LOSS | 1.530 (+11.1%) LOSS | 0/1/5 |
| PWM-Dyn v0.6r | 14.336 (+19.8%) LOSS | 18.692 (+16.0%) LOSS | 14.299 (+13.2%) LOSS | 19.929 (+16.7%) LOSS | 2.920 (+13.3%) LOSS | 1.524 (+11.5%) LOSS | 0/0/6 |

Cells: opponent MAE (Atlas-100M's error relative to it) and the verdict. Specialists and PWM-Dyn are entered on both
tracks with identical verdicts; they are listed once.

- Against the trained specialists and PWM-Dyn: **LOSS in 22 of 24 comparisons**, TIE in 2 (STID and STAEformer on
  PEMS03); Atlas-100M is 4–27% worse.
- Against the zero-shot foundation models: WIN 7, TIE 11, LOSS 12. Five of the seven wins are against Chronos-Bolt
  and Chronos-2; against TimesFM it wins only on METR-LA and loses to all three TimesFM configurations on the four
  PeMS networks.
- PWM-Dyn v0.6r, our own single-domain traffic model (paper 1), is better than Atlas-100M on every network (11–20%).
- The first scoring ran before PWM-Dyn had finished (deviation 6) and is kept as
  `results/atlas100m_traffic_results_without_pwmdyn.json`; adding PWM-Dyn changed no other verdict.

## Follow-up: Atlas-100M-T, a larger traffic share on the frozen core (`PREREG_TRAFFIC.md`)

Pre-registered on 2026-11-21 after the traffic loss above, before any training. The shared core (94,755,808 weights)
is frozen and the weather and air-quality files are not touched; traffic gets its own **4,843,778** trainable
parameters (LoRA rank 32 on every linear layer of the core 4,666,368, a 32-number embedding per sensor 72,000, the
traffic adapter 105,410). Whole system 103,363,450. Context stays at 12 steps (Track A protocol). Trained 40,000 steps
(135 minutes, A100 80GB), validation ratio 0.7210 → **0.6476**; scored once on the official test windows against every
ParadoxBench submission, Atlas-100M included, in one Holm family of 84 comparisons.

- **Check T0:** at the start Atlas-100M-T scored 0.721011 against Atlas-100M's 0.721011 (same function).
- **Check W:** after training and scoring, the SHA-256 of `atlas100m_best.pt`, `atlas100m_weather_view.pt` and
  `atlas100m_aq_view.pt` equals `results/SHA256SUMS` (checked in the run and again by hand on 2026-11-21 14:10 UTC).
  Weather and air-quality results are therefore unchanged.

| Opponent | PEMS08 | PEMS04 | PEMS03 | PEMS07 | METR-LA | PEMS-BAY | W/T/L |
|---|---|---|---|---|---|---|---|
| **Atlas-100M-T MAE** | **15.475** | **19.474** | **14.717** | **20.813** | **3.079** | **1.582** | |
| Atlas-100M (v1.0) | 17.170 (-9.9%) WIN | 21.688 (-10.2%) WIN | 16.181 (-9.0%) WIN | 23.261 (-10.5%) WIN | 3.310 (-7.0%) WIN | 1.699 (-6.9%) WIN | 6/0/0 |
| Chronos-Bolt | 18.443 (-16.1%) WIN | 22.866 (-14.8%) WIN | 17.177 (-14.3%) WIN | 25.664 (-18.9%) WIN | 3.875 (-20.5%) WIN | 1.996 (-20.7%) WIN | 6/0/0 |
| Chronos-2 | 17.148 (-9.8%) TIE | 21.524 (-9.5%) TIE | 15.913 (-7.5%) TIE | 23.566 (-11.7%) WIN | 3.674 (-16.2%) WIN | 1.829 (-13.5%) WIN | 3/3/0 |
| TimesFM 2.5 | 15.038 (+2.9%) TIE | 19.702 (-1.2%) TIE | 14.609 (+0.7%) TIE | 20.894 (-0.4%) TIE | 3.491 (-11.8%) WIN | 1.692 (-6.5%) WIN | 2/4/0 |
| TimesFM 3.0 | 14.629 (+5.8%) TIE | 19.273 (+1.0%) TIE | 14.331 (+2.7%) TIE | 20.464 (+1.7%) TIE | 3.491 (-11.8%) WIN | 1.708 (-7.4%) WIN | 2/4/0 |
| TimesFM 3.0 mv | 14.549 (+6.4%) TIE | 19.135 (+1.8%) TIE | 14.148 (+4.0%) TIE | 20.270 (+2.7%) TIE | 3.401 (-9.5%) WIN | 1.661 (-4.7%) TIE | 1/5/0 |
| STID | 14.234 (+8.7%) LOSS | 18.484 (+5.4%) LOSS | 15.393 (-4.4%) TIE | 19.617 (+6.1%) LOSS | 3.124 (-1.5%) TIE | 1.562 (+1.3%) TIE | 0/3/3 |
| Graph WaveNet | 14.674 (+5.5%) LOSS | 18.984 (+2.6%) LOSS | 14.552 (+1.1%) TIE | 22.416 (-7.1%) WIN | 3.066 (+0.4%) TIE | 1.574 (+0.5%) TIE | 1/3/2 |
| STAEformer | 13.500 (+14.6%) LOSS | 18.281 (+6.5%) LOSS | 15.218 (-3.3%) TIE | 21.506 (-3.2%) WIN | 2.970 (+3.7%) LOSS | 1.530 (+3.4%) LOSS | 1/1/4 |
| PWM-Dyn v0.6r | 14.336 (+7.9%) LOSS | 18.692 (+4.2%) LOSS | 14.299 (+2.9%) TIE | 19.929 (+4.4%) LOSS | 2.920 (+5.4%) LOSS | 1.524 (+3.8%) LOSS | 0/1/5 |

Cells as above (percentages are Atlas-100M-T's error relative to the opponent). The same forecast is entered on both
tracks; specialists and Atlas-100M carry identical verdicts on both and are listed once.

- **6–10% better than Atlas-100M on every network (WIN 6/6).** Weather and air quality did not change.
- **No loss to any foundation model** (WIN 14, TIE 16, LOSS 0; Atlas-100M had 12 losses), although it reads 12 steps
  and they read 512. On the four PeMS networks it ties all three TimesFM configurations instead of losing to them.
- Against the trained specialists and PWM-Dyn it is closer but still behind: WIN 2 (Graph WaveNet and STAEformer on
  PEMS07), TIE 8, LOSS 14 (Atlas-100M: 0 / 2 / 22). PWM-Dyn v0.6r is still better on five networks (4–8%), tied on PEMS03.
- Raw output: `results/atlas100mt_traffic_results.json`, `atlas100mT_summary.json`, `atlas100mT_log.jsonl`.

| # | Prediction (PREREG_TRAFFIC section 5) | Probability | Result |
|---|---|---|---|
| T1 | Check T0 holds | 0.99 | **held** (difference 1e-7) |
| T2 | Check W holds | 0.99 | **held** |
| T3 | Best validation ratio below 0.7210 | 0.90 | **held** (0.6476) |
| T4 | WIN against Atlas-100M on at least 5 of 6 networks | 0.70 | **held** (6 of 6) |
| T5 | Track A: WIN against all three specialists on at least 4 of 6 networks | 0.10 | failed (0 of 6) |
| T6 | Lower MAE than PWM-Dyn v0.6r on at least 3 of 6 networks | 0.15 | failed (0 of 6) |
| T7 | Track B: WIN against every foundation model on at least 3 of 6 networks | 0.30 | failed (1 of 6: METR-LA) |

### Atlas-100M-T1d: one day of look-back (addendum A)

Atlas-100M-T reading **288 steps (one day)** instead of 12; traffic-only parameters **6,358,742**, whole system
104,878,414. Track B only. Trained 40,000 steps (135 minutes, A100), validation ratio 0.7210 → 0.6486 (Atlas-100M-T:
0.6476). Check T0: 0.721092 at the start against 0.721011. One Holm family of 66 comparisons (every Track B
submission, Atlas-100M and Atlas-100M-T included).

| Opponent | PEMS08 | PEMS04 | PEMS03 | PEMS07 | METR-LA | PEMS-BAY | W/T/L |
|---|---|---|---|---|---|---|---|
| **Atlas-100M-T1d MAE** | **15.293** | **19.416** | **14.828** | **20.634** | **3.140** | **1.539** | |
| Atlas-100M-T | 15.475 (-1.2%) TIE | 19.474 (-0.3%) TIE | 14.717 (+0.8%) TIE | 20.813 (-0.9%) TIE | 3.079 (+2.0%) TIE | 1.582 (-2.7%) WIN | 1/5/0 |
| Atlas-100M (v1.0) | 17.170 (-10.9%) WIN | 21.688 (-10.5%) WIN | 16.181 (-8.4%) WIN | 23.261 (-11.3%) WIN | 3.310 (-5.1%) WIN | 1.699 (-9.5%) WIN | 6/0/0 |
| Chronos-Bolt | 18.443 (-17.1%) WIN | 22.866 (-15.1%) WIN | 17.177 (-13.7%) WIN | 25.664 (-19.6%) WIN | 3.875 (-19.0%) WIN | 1.996 (-22.9%) WIN | 6/0/0 |
| Chronos-2 | 17.148 (-10.8%) WIN | 21.524 (-9.8%) WIN | 15.913 (-6.8%) TIE | 23.566 (-12.4%) WIN | 3.674 (-14.5%) WIN | 1.829 (-15.9%) WIN | 5/1/0 |
| TimesFM 2.5 | 15.038 (+1.7%) TIE | 19.702 (-1.4%) TIE | 14.609 (+1.5%) TIE | 20.894 (-1.2%) TIE | 3.491 (-10.1%) WIN | 1.692 (-9.1%) WIN | 2/4/0 |
| TimesFM 3.0 | 14.629 (+4.5%) LOSS | 19.273 (+0.7%) TIE | 14.331 (+3.5%) TIE | 20.464 (+0.8%) TIE | 3.491 (-10.1%) WIN | 1.708 (-9.9%) WIN | 2/3/1 |
| TimesFM 3.0 mv | 14.549 (+5.1%) LOSS | 19.135 (+1.5%) TIE | 14.148 (+4.8%) TIE | 20.270 (+1.8%) LOSS | 3.401 (-7.7%) WIN | 1.661 (-7.4%) WIN | 2/2/2 |
| STID | 14.234 (+7.4%) LOSS | 18.484 (+5.0%) LOSS | 15.393 (-3.7%) TIE | 19.617 (+5.2%) LOSS | 3.124 (+0.5%) TIE | 1.562 (-1.5%) TIE | 0/3/3 |
| Graph WaveNet | 14.674 (+4.2%) LOSS | 18.984 (+2.3%) TIE | 14.552 (+1.9%) TIE | 22.416 (-8.0%) WIN | 3.066 (+2.4%) TIE | 1.574 (-2.3%) WIN | 2/3/1 |
| STAEformer | 13.500 (+13.3%) LOSS | 18.281 (+6.2%) LOSS | 15.218 (-2.6%) TIE | 21.506 (-4.1%) WIN | 2.970 (+5.7%) LOSS | 1.530 (+0.6%) TIE | 1/2/3 |
| PWM-Dyn v0.6r | 14.336 (+6.7%) LOSS | 18.692 (+3.9%) LOSS | 14.299 (+3.7%) TIE | 19.929 (+3.5%) LOSS | 2.920 (+7.5%) LOSS | 1.524 (+1.0%) TIE | 0/2/4 |

- A day of look-back changes little overall: T1d ties Atlas-100M-T on five networks and wins on PEMS-BAY.
- Against the foundation models WIN 17, TIE 10, LOSS 3: more wins than Atlas-100M-T (Chronos-2 now loses on four
  networks), but also three losses to TimesFM 3.0 on PEMS08 and PEMS07 that Atlas-100M-T did not have.
- Against the specialists and PWM-Dyn WIN 3, TIE 10, LOSS 11; the first win over a specialist outside PEMS07 (Graph
  WaveNet on PEMS-BAY). PWM-Dyn is still not beaten on any network (tied on PEMS03 and PEMS-BAY).

| # | Prediction (addendum A) | Probability | Result |
|---|---|---|---|
| T8 | Best validation ratio below Atlas-100M-T's | 0.65 | failed (0.6486 vs 0.6476) |
| T9 | Track B: WIN against every foundation model on at least 4 of 6 networks | 0.35 | failed (2 of 6: METR-LA, PEMS-BAY) |
| T10 | Lower MAE than PWM-Dyn v0.6r on at least 3 of 6 networks | 0.25 | failed (0 of 6) |

### Atlas-100M-TXL: 20.45M traffic parameters (addendum B), did not train

LoRA rank 128 (alpha 128), 64-number sensor embeddings, one day of look-back: 20,454,934 traffic-only parameters,
whole system 118,974,606 (L4 GPU). The validation ratio rose from 0.7210 to 0.868, 1.142 and 6.22 in the first 6,000
steps, recovered to 0.732 and never went below the start; patience stopped it at step 12,000 and the kept checkpoint
is the starting one, i.e. Atlas-100M's traffic view. Scored as registered it ties Atlas-100M on all six networks
(`results/atlas100mtxl_traffic_results.json`). T11 (validation below T1d's), T12, T13 and T14 **failed**. Addendum C
(committed before it ran) retries the same size with rank-stabilised LoRA scaling (alpha 64) as Atlas-100M-TXL2.

### Atlas-100M-TXL2: the same 20.45M traffic share, trained (addendum C)

TXL with alpha 64 instead of 128 and nothing else changed; chosen after TXL failed and reported as a second attempt.
20,454,934 traffic-only parameters, whole system **118,974,606**. Trained the full 60,000 steps (206 minutes, L4) with
no blow-up (highest validation ratio 0.80); validation ratio 0.7210 → **0.6302**, the best of the four variants, still
improving when the step limit was reached. Check T0 at the start; check W before and after (SHA-256, in the run log
`results/txl2_run.txt`). Holm family of 60: the published Track B submissions (Atlas-100M-T and T1d by MAE only).

| Opponent | PEMS08 | PEMS04 | PEMS03 | PEMS07 | METR-LA | PEMS-BAY | W/T/L |
|---|---|---|---|---|---|---|---|
| **Atlas-100M-TXL2 MAE** | **14.837** | **18.935** | **14.496** | **20.089** | **3.094** | **1.522** | |
| *Atlas-100M-T (MAE only)* | *15.475* | *19.474* | *14.717* | *20.813* | *3.079* | *1.582* | |
| *Atlas-100M-T1d (MAE only)* | *15.293* | *19.416* | *14.828* | *20.634* | *3.140* | *1.539* | |
| Atlas-100M (v1.0) | 17.170 (-13.6%) WIN | 21.688 (-12.7%) WIN | 16.181 (-10.4%) WIN | 23.261 (-13.6%) WIN | 3.310 (-6.5%) WIN | 1.699 (-10.4%) WIN | 6/0/0 |
| Chronos-Bolt | 18.443 (-19.6%) WIN | 22.866 (-17.2%) WIN | 17.177 (-15.6%) WIN | 25.664 (-21.7%) WIN | 3.875 (-20.2%) WIN | 1.996 (-23.7%) WIN | 6/0/0 |
| Chronos-2 | 17.148 (-13.5%) WIN | 21.524 (-12.0%) WIN | 15.913 (-8.9%) TIE | 23.566 (-14.8%) WIN | 3.674 (-15.8%) WIN | 1.829 (-16.8%) WIN | 5/1/0 |
| TimesFM 2.5 | 15.038 (-1.3%) TIE | 19.702 (-3.9%) TIE | 14.609 (-0.8%) TIE | 20.894 (-3.9%) WIN | 3.491 (-11.4%) WIN | 1.692 (-10.0%) WIN | 3/3/0 |
| TimesFM 3.0 | 14.629 (+1.4%) TIE | 19.273 (-1.8%) TIE | 14.331 (+1.2%) TIE | 20.464 (-1.8%) TIE | 3.491 (-11.4%) WIN | 1.708 (-10.9%) WIN | 2/4/0 |
| TimesFM 3.0 mv | 14.549 (+2.0%) TIE | 19.135 (-1.0%) TIE | 14.148 (+2.5%) TIE | 20.270 (-0.9%) TIE | 3.401 (-9.0%) WIN | 1.661 (-8.3%) WIN | 2/4/0 |
| STID | 14.234 (+4.2%) LOSS | 18.484 (+2.4%) TIE | 15.393 (-5.8%) TIE | 19.617 (+2.4%) LOSS | 3.124 (-1.0%) TIE | 1.562 (-2.5%) WIN | 1/3/2 |
| Graph WaveNet | 14.674 (+1.1%) TIE | 18.984 (-0.3%) TIE | 14.552 (-0.4%) TIE | 22.416 (-10.4%) WIN | 3.066 (+0.9%) TIE | 1.574 (-3.3%) WIN | 2/4/0 |
| STAEformer | 13.500 (+9.9%) LOSS | 18.281 (+3.6%) LOSS | 15.218 (-4.7%) TIE | 21.506 (-6.6%) WIN | 2.970 (+4.2%) LOSS | 1.530 (-0.5%) TIE | 1/2/3 |
| PWM-Dyn v0.6r | 14.336 (+3.5%) LOSS | 18.692 (+1.3%) TIE | 14.299 (+1.4%) TIE | 19.929 (+0.8%) TIE | 2.920 (+5.9%) LOSS | 1.524 (-0.1%) TIE | 0/4/2 |

- **Lowest MAE of the four Atlas variants on five of six networks** and 6–14% better than Atlas-100M on all six.
- **No loss to any foundation model** (WIN 18, TIE 12, LOSS 0), with one day of look-back against their 512 steps.
- Against the specialists and PWM-Dyn: **WIN 4, TIE 13, LOSS 7** (Atlas-100M: 0 / 2 / 22). It now ties PWM-Dyn on four
  networks and is never beaten by Graph WaveNet; STAEformer (PEMS08, PEMS04, METR-LA) and PWM-Dyn (PEMS08, METR-LA)
  are still better where they win.

| # | Prediction (addendum C) | Probability | Result |
|---|---|---|---|
| T15 | Training is stable: no validation ratio above 1.0 | 0.80 | **held** (highest 0.80) |
| T16 | Best validation ratio below Atlas-100M-T's 0.6476 | 0.50 | **held** (0.6302) |
| T17 | Track B: no LOSS against any foundation model | 0.55 | **held** (0 of 30) |
| T18 | Lower MAE than PWM-Dyn v0.6r on at least 3 of 6 networks | 0.20 | failed (1 of 6: PEMS-BAY, 1.522 vs 1.524) |
| T19 | Track B: WIN against all three specialists on at least 3 of 6 networks | 0.10 | failed (0 of 6) |

**Traffic follow-up, overall.** Giving traffic its own parameters on the frozen core turned Atlas-100M's clear traffic
loss into no losses against the zero-shot foundation models and a much smaller gap to the trained specialists, without
changing a byte of the weather or air-quality model. It did not make Atlas the best traffic model: STAEformer and our
own single-domain PWM-Dyn are still ahead on some networks. Of 19 traffic predictions, 7 held (T1–T4, T15–T17).

## Hybrid against ECMWF IFS, AIFS, GFS and GraphCast (interim; final scoring pending)

The archive of IFS, AIFS and GFS was complete on 2026-11-21 (coverage of hours 0.93, 0.60, 0.97); GraphCast was
wrongly reported missing and is being fetched (deviation 7). Both hybrids were trained: the registered one (section H)
and Atlas-100M-H2 (addendum H2, the freshest published run). Check H0 held exactly for both (0.0). Validation error E
(every station, 2024-11-01 – 12-31): pure Atlas-100M 0.3227, hybrid 0.2477, **H2 0.2380**.

**Interim test, 2025-01-01 – 08-23, 178 stations, 940 forecast starts, 24 h ahead.** Not the final result: it lacks
GraphCast, and its pairing inflated our error wherever an opponent's archive had gaps (deviation 8, found after this
score was seen; fixed). The final scoring (full family, fixed pairing) replaces it; the interim files stay published in
`results/interim_no_graphcast/`. MAE (own units; wind direction in degrees):

| Forecast | Temperature | Dewpoint | Wind dir. | Wind speed | Sea-level pressure |
|---|---|---|---|---|---|
| Atlas-100M pure | 1.462 | 1.491 | 65.6 | 1.181 | 1.628 |
| Atlas-100M hybrid | 1.308 | 1.281 | 55.6 | 1.022 | 0.925 |
| **Atlas-100M-H2** | **1.270** | **1.247** | **55.0** | **1.007** | 0.808 |
| ECMWF IFS raw / bias-corrected | 1.572 / 1.434 | 1.651 / 1.476 | 70.3 / 70.3 | 1.444 / 1.212 | 0.923 / **0.719** |
| ECMWF AIFS raw / bias-corrected | 1.782 / 1.682 | 1.809 / 1.650 | 73.6 / 73.6 | 1.538 / 1.313 | 1.862 / 1.674 |
| NOAA GFS raw / bias-corrected | 1.848 / 1.673 | 2.067 / 1.669 | 72.4 / 72.4 | 1.518 / 1.255 | 1.135 / 0.910 |

Each system's MAE is on its own available hours; the paired tests use shared hours only. Interim verdicts for H2:
WIN against IFS raw and bias-corrected and GFS raw and bias-corrected on temperature, dewpoint, wind direction and wind
speed; against IFS on sea-level pressure TIE (raw) and **LOSS (bias-corrected, +12%)**; AIFS all TIE (the comparison the
pairing error affected most). No prediction is scored on these interim numbers.

## India: all 68 Indian WEATHER-5K stations (addendum I)

**I1, pure Atlas-100M against the ten zero-shot foundation models.** Same code and settings as the global head-to-head,
run fresh on the 68 stations. Cells: Atlas-100M's error relative to the opponent (negative = Atlas-100M better) and the
verdict; one Holm family of 50 per period.

*2023 test* (182 starts every 48 h; Atlas-100M MAE: temperature 1.173, dewpoint 1.311, wind direction 53.3, wind speed
0.751, pressure 0.755):

| Opponent | Temperature | Dewpoint | Wind direction | Wind speed | Sea-level pressure | W/T/L |
|---|---|---|---|---|---|---|
| Persistence | -72.7% WIN | -35.7% WIN | -27.2% WIN | -35.2% WIN | -45.0% WIN | 5/0/0 |
| Chronos-Bolt | +1.4% TIE | +2.9% TIE | -4.0% WIN | +3.5% TIE | +1.8% TIE | 1/4/0 |
| Chronos-2 | -0.6% TIE | +4.9% TIE | -2.2% TIE | +6.6% TIE | +1.5% TIE | 0/5/0 |
| Chronos-2 multivariate | -0.1% TIE | +6.6% TIE | -2.4% TIE | +5.5% TIE | -0.7% TIE | 0/5/0 |
| TimesFM 2.5 | -3.8% TIE | +4.4% TIE | -3.2% TIE | +5.8% TIE | -1.4% TIE | 0/5/0 |
| TimesFM 3.0 | +1.6% TIE | +6.1% TIE | -1.6% TIE | +7.2% LOSS | +2.8% TIE | 0/4/1 |
| TTM r2 | -12.8% WIN | -6.2% TIE | -6.6% WIN | +0.2% TIE | -21.4% WIN | 3/2/0 |
| TiRex | +0.6% TIE | +7.1% TIE | -3.5% TIE | +7.1% LOSS | +4.8% TIE | 0/4/1 |
| Sundial | -0.1% TIE | +3.7% TIE | -3.9% TIE | +5.1% TIE | +0.5% TIE | 0/5/0 |
| Time-MoE 200M | +0.2% TIE | +3.1% TIE | -6.6% WIN | +2.3% TIE | +0.3% TIE | 1/4/0 |

*2024-25 live period* (145 starts every 96 h, 2024-01-23 – 2025-08-21; Atlas-100M MAE: temperature 1.293, dewpoint
1.278, wind direction 73.7, wind speed 0.845, pressure 0.900):

| Opponent | Temperature | Dewpoint | Wind direction | Wind speed | Sea-level pressure | W/T/L |
|---|---|---|---|---|---|---|
| Persistence | -66.0% WIN | -20.9% WIN | -23.3% WIN | -29.9% WIN | -39.8% WIN | 5/0/0 |
| Chronos-Bolt | +2.7% TIE | -3.5% TIE | +8.1% LOSS | +2.4% TIE | +2.1% TIE | 0/4/1 |
| Chronos-2 | +4.4% TIE | -1.8% TIE | +9.4% LOSS | +3.9% TIE | +4.1% TIE | 0/4/1 |
| Chronos-2 multivariate | +2.2% TIE | -1.9% TIE | +10.2% LOSS | +3.1% TIE | +1.6% TIE | 0/4/1 |
| TimesFM 2.5 | +1.2% TIE | -3.9% TIE | +5.4% TIE | +2.0% TIE | +1.8% TIE | 0/5/0 |
| TimesFM 3.0 | +5.4% LOSS | -1.8% TIE | +9.6% LOSS | +3.8% TIE | +2.1% TIE | 0/3/2 |
| TTM r2 | -7.2% WIN | -8.6% WIN | +2.9% TIE | +0.6% TIE | -14.4% WIN | 3/2/0 |
| TiRex | -1.3% TIE | -2.5% TIE | +6.4% TIE | +2.0% TIE | +4.8% TIE | 0/5/0 |
| Sundial | +2.5% TIE | -3.4% TIE | +5.5% TIE | +2.5% TIE | +2.0% TIE | 0/5/0 |
| Time-MoE 200M | -1.2% TIE | -6.0% WIN | -1.1% TIE | -2.1% TIE | -1.4% TIE | 1/4/0 |

- **In India, Atlas-100M is level with the leading foundation models, not ahead of them:** over both periods WIN 19,
  TIE 74, LOSS 7 of 100 (worldwide, on the 709 head-to-head stations, it won all 100). It clearly beats persistence
  and TTM, ties TimesFM, Chronos, TiRex and Sundial on almost every variable, and loses seven comparisons, mostly wind
  direction in the live period and wind speed in 2023.
- We do not yet know why India differs from the global result; with 68 stations the intervals are wider, but the point
  estimates themselves are near zero. Nothing here compares with the India Meteorological Department's forecasts.
- **I2, the hybrids at the Indian stations,** waits for their archive (fetched after GraphCast under the free limit).

| # | Prediction (addendum I) | Probability | Result |
|---|---|---|---|
| P23 | I1: WIN against all ten foundation models on temperature, 2023 test | 0.85 | **failed** (2 of 10: persistence, TTM) |
| P24 | I1: at least 90 of the 100 comparisons are WIN | 0.55 | **failed** (19 of 100) |
| P25–P27 | I2 (hybrids vs IFS at Indian stations) | | pending |

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
| P11 | Traffic Track B: WIN against every foundation model on ≥ 5 of 6 networks | 0.60 | FAILED (0 of 6 networks) |
| P12 | Traffic Track A: WIN against all three specialists on ≥ 4 of 6 networks | 0.25 | FAILED (0 of 6; 16 LOSS, 2 TIE) |
| P13 | Traffic: lower MAE than PWM-Dyn v0.6r on ≥ 4 of 6 networks | 0.35 | FAILED (0 of 6) |
| P14–P17 | Hybrid | | pending |

## What these results do and do not show

- **Task-trained against zero-shot.** Every foundation model above is used zero-shot under its documented settings;
  Atlas-100M trained on these stations' earlier years and sees each station's neighbours. The weather and air-quality
  wins show that a compact model trained for the task beats general models used without training on it. They do not
  show a better general-purpose model.
- **Where it is weak:** traffic (loses to every trained specialist, to PWM-Dyn and to TimesFM on most networks),
  sea-level pressure (worse than PhysicsFormer, much worse than ECMWF-HRES), stations it never trained on (mostly
  ties), and TimesFM 3.0 multivariate on air quality (tie, slightly worse).
- **One set of weights for three systems did not pay off.** Weather stayed equal to the 24.1M single-domain model,
  air quality equalled the single-domain Atlas-India v1.0, and traffic fell well short of the single-domain PWM-Dyn.
  The shared core carried weather; the small traffic adapter with 12 steps of context was not enough.
- **Scale did not help weather.** The 100M is equal to the 24.1M within 0.1% except pressure.
- **One training seed** (700); seed variance is not measured.
- Not compared: video or robotics world models, or global gridded weather models on their own grids. No claim of
  "the best world model" is made.
