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

## 5. WB1-T: the data threshold function at 1M parameters on WEATHER-5K (in progress)

The 1M Atlas-5K at 24 h on nested shares of the 2014–2021 training days (all 5,672 stations). E = mean over the five
variables of validation-2022 MAE divided by the benchmark's scale.

| Share | Station-days n | E | Temperature MAE (°C) |
|---|---|---|---|
| 1/64 | 260,912 | 0.3376 | 1.889 |
| 1/32 | 521,824 | running | |
| 1/16 | 1,037,976 | 0.3129 | 1.681 |
| 1/8 | 2,076,152 | running | |
| 1/4 | 4,140,560 | 0.2971 | 1.585 |
| 1/2 | 8,281,120 | running | |
| all | 16,562,240 | 0.2929 | 1.547 |

The pre-registered test (fit forms A / B / C on the four smallest shares; B verified if it predicts 1/4, 1/2 and
all within 3%) runs when the remaining shares finish. No fit is reported before then. ("WB1-T")

## What the threshold functions say, together

1. **No sudden jump anywhere:** on simulators, Indian stations and global weather stations, error falls smoothly with
   data. The threshold is the amount of data needed for a chosen error, read off a curve.
2. **Data beats parameters at these sizes:** the parameter term is near zero on real stations; 10M did not beat 1M on
   India with or without weather.
3. **Transfer is the largest lever for a single city:** pre-training on the rest of India is worth about 3.5 years of
   local data.
4. **The size threshold moves with data:** whether 10M pays on WEATHER-5K (about 40× India's station-hours) is the
   open, pre-registered question.
