# Atlas threshold functions — every fitted law in one place

ParadoxAI Lab, Atlas project. Status as of 2026-11-17. Each entry gives the form, the fitted numbers, what it was
fitted on, how it was tested, and its status. Full protocols, predictions and run logs are in `README.md` (the section
named in brackets). Code: `atlas/threshold.py` (the data–parameter function), `delhi/score_threshold.py` (T1),
`delhi/score_dxp.py` (v3), `delhi/score_w5k_thr.py` (WB1-T).

## 1. The parameter–data threshold function (simulators)

    error(N, P) = floor + a · N^(−α) + b · P^(−β)

N = independent training trajectories, P = trainable parameters, error = normalised MSE on fresh trajectories.
`atlas/threshold.py` fits it, inverts it (`need_data`, `need_params`) and bootstraps intervals.

* **Damped oscillator, 90 runs:** floor 0.011, **α = 0.377, β = 0.981**, misfit ×1.16. Held-out test: fitted on
  N ≤ 3,000 and P ≤ 1M (65 runs), it predicted the 25 unseen runs within ×1.24 (nearest-cell baseline ×1.31): a small
  but real advantage. ("Findings", 3.)
* **Shape:** no sudden threshold. A smooth power law (error ∝ N^−0.35) fits as well as a step (AICc −55.6 vs −54.4).
  "The threshold" is a point on a smooth curve set by the error you ask for. ("Findings", 1.)
* **Data versus size:** beyond about 50K–500K parameters, more parameters did nothing on the oscillator (10M: 0.100,
  0.5M: 0.091); ten times more data cut the error about 2.4×. Transport systems kept gaining from size to 1M.
  ("Findings", 2.)

## 2. Real stations (Delhi, India): the same function on measured air quality

* **Delhi, 38 runs (Atlas v1.0):** misfit ×1.09; predicted the held-out largest data amount within ×1.10 (8% high);
  floor at its bound (not identified), **α = 0.087, β = 0.308**. Extrapolation: a single 4M model would need about
  12,200–14,900 training windows to reach Chronos-Bolt / Chronos-2 / TimesFM 2.5 (3,673 measured).
* **Atlas-W, 48 runs (widths 16–128):** parameter term essentially zero (b = 0.0016, β = 2.9), data term weak
  (α = 0.045), misfit ×1.046; a 19-fold range of sizes within 0.5 µg/m³ at full data. Poorly determined.
* **ATF law frozen from 46 Indian curves:** α = 0.179, φ = 0.474 (`bench/atf_law.json`).

**Reading:** on real station data the parameter term is near zero at the sizes tested. Data, not size, sets the error.

## 3. Transfer threshold function (T1, all-India; rule CONFIRMED)

    scratch law:  r = c_X + a · n^(−α)          transfer law:  D_T = k · n^γ

r = calibrated test MAE / TimesFM 2.5's; n = the network's own training windows; D_T = the extra local data that
pre-training on the other 13 networks is worth (Hernandez et al. 2021's form).

* **Fitted:** scratch law **r = c_X + 2.18 · n^−0.080** (misfit ×1.057; floors 0.001 Uttar Pradesh, 0.012 Haryana,
  0.041 Karnataka, 0.087 Maharashtra); **transfer law D_T = 1.04 × 10⁴ · n^0.094** (28 points).
* **Meaning:** pre-training is worth about 10,000 local windows (about 3.5 years of a city's data) even with almost
  none of its own. Uttar Pradesh reaches TimesFM 2.5's level with 2 months plus pre-training; trained from scratch it
  never does, even with all its data.
* **Rule:** pre-training lowers n* on 3 of 4 networks: **confirmed** (Maharashtra reached by neither arm).
  ("T1 results")

## 4. Data × size threshold (v3, all-India, 1M / 3M / 10M) — partly run, deferred

The data share at which a larger model starts to beat 1M. Part B (10M at three shares) ran; parts A and C were deferred
when the entry budget was set to 1M (2026-11-16). At all data with weather: 1M 8.684, 10M 8.773 validation MAE
(10M +1.0%). ("Atlas v3")

## 5. WB1-T: the data threshold function at 1M parameters on WEATHER-5K — **verified** (23 Nov 2026)

The 1M Atlas-5K at 24 h on nested shares of the 2014–2021 training days (all 5,672 stations). E = mean over the five
variables of validation-2022 MAE divided by the benchmark's scale. 1/64, 1/16, 1/4, all: Kaggle T4 (16–17 Nov);
1/32, 1/8, 1/2: Colab L4 (23 Nov), same recipe. Files: `results/colab/w5k-thr/`, scorer `delhi/score_w5k_thr.py`.

| Share | Station-days n | E | Temperature MAE (°C) | Predicted before the run (addendum, 22 Nov) |
|---|---|---|---|---|
| 1/64 | 260,912 | 0.3376 | 1.889 | |
| 1/32 | 521,824 | 0.3246 | 1.764 | 0.3227 (+0.6%) |
| 1/16 | 1,037,976 | 0.3129 | 1.681 | |
| 1/8 | 2,070,280 | 0.3041 | 1.625 | 0.3041 (0.0%) |
| 1/4 | 4,140,560 | 0.2971 | 1.585 | |
| 1/2 | 8,281,120 | 0.2934 | 1.557 | 0.2949 (−0.5%) |
| all | 16,562,240 | 0.2929 | 1.547 | |

**Registered test** (fit on 1/64–1/8, predict 1/4, 1/2, all): form B (floor + power law) predicts within 0.3%, 1.2% and
2.9% → **verified** (rule: each within 3%). Form A (no floor) misses by 7.1% at all data. Form C (saturating,
c + a / (1 + (n/n0)^α)) predicts within 0.4%, 0.4% and 0.1% (score 0.003 vs B's 0.015) → **adopted as threshold function v2**
by the rule (beats B's held-out score by more than half).

**Predictions (16 Nov):** 1 smooth, no step — held. 2 B verified, A misses by > 3% at the largest share — held.
3 α between 0.1 and 0.5 (B on four shares: 0.268) — held. 4 all data within 2% of the 1/2 share (−0.18%) — held.
**Addendum (22 Nov):** each of the three predictions within 1.5% — held (3 of 3); all three — held.

**The data threshold n\*(ε)** (definition and determination rule registered 22 Nov: form B on all seven shares,
residual bootstrap 80% interval, "determined" if the interval of n*(5%) spans less than a factor of 3):

| Tolerance ε | n*(ε), form B (registered) | 80% interval | share of WEATHER-5K | form C (adopted v2), for comparison |
|---|---|---|---|---|
| 5% | **4.7M** station-days | 3.0M – 8.8M (factor 2.93 → **determined**) | 28% (≈ 2.3 years of all stations) | 1.8M (11%) |
| 2% | 33M | 17M – 84M | 2.0× all data | 5.1M (31%) |
| 1% | 146M | 62M – 461M | 8.8× all data | 10.3M (62%) |

Both forms agree that a 1M model comes within 5% of its own floor with 11–28% of WEATHER-5K's training days; they
disagree at tight tolerances, where B keeps a slow tail and C saturates (C puts all data 0.6% above its floor of 0.2905).
The floor belongs to this size; the size × data grid gives it per size.

**Size × data grid (running, 23 Nov; validation E):**

| Size | 1/64 | 1/16 | 1/4 | all |
|---|---|---|---|---|
| 0.1M (95,472) | 0.3406 | 0.3321 | 0.3270 | 0.3294 |
| 0.3M (282,672) | 0.3361 | 0.3163 | 0.3072 | running |
| 1M (968,672) | 0.3376 | 0.3129 | 0.2971 | 0.2929 |
| 3M, 10M | pending | | | |

First reading (no fit yet; the rule waits for all 20 cells): with little data, size hardly matters (all three sizes
within 1% at 1/64); with more data the small models stop improving — the 0.1M model is no better with all data than
with a quarter. The floor falls with size, so **below about 1M, parameters do matter**; whether they still matter above
1M is what the 3M and 10M rows decide.

## What the threshold functions say, together

1. **No sudden jump anywhere:** on simulators, Indian stations and global weather stations, error falls smoothly with
   data. The threshold is the amount of data needed for a chosen error, read off a curve.
2. **Data beats parameters at these sizes:** the parameter term is near zero on real stations; 10M did not beat 1M on
   India with or without weather.
3. **Transfer is the largest lever for a single city:** pre-training on the rest of India is worth about 3.5 years of
   local data.
4. **The size threshold moves with data:** whether 10M pays on WEATHER-5K (about 40× India's station-hours) is the
   open, pre-registered question.
