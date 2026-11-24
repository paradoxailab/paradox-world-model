**2023 test** (709 stations, 182 forecast starts from 2023-01-03 to 2023-12-31, 24 h each; up to 3,096,912 scored values per variable; hours with no observation are not scored). E = standardised mean error, lower is better.

| Rank | Model | Params | E | Temp. (°C) | Dew pt. (°C) | Wind dir. (°) | Wind spd. (m/s) | Pressure (hPa) |
|---|---|---|---|---|---|---|---|---|
| 1 | **Atlas-5K 25M (ours)** | 24.1M | **0.2742** | 1.391 | 1.460 | 53.93 | 1.179 | 1.466 |
| 2 | Atlas-5K 10M (ours) | 9.64M | 0.2770 | 1.420 | 1.475 | 54.51 | 1.190 | 1.472 |
| 3 | Atlas-5K v2c (ours) | 0.97M | 0.2822 | 1.462 | 1.506 | 55.39 | 1.206 | 1.520 |
| 4 | TimesFM 3.0 (Google) | 0.3B | 0.3303 | 1.876 | 1.960 | 63.06 | 1.327 | 1.965 |
| 5 | Chronos-2 multivariate (Amazon) | 120M | 0.3313 | 1.843 | 1.920 | 62.79 | 1.335 | 2.067 |
| 6 | TiRex (NX-AI) | 35M | 0.3326 | 1.900 | 1.955 | 64.38 | 1.325 | 1.948 |
| 7 | Chronos-2 (Amazon) | 120M | 0.3343 | 1.899 | 1.965 | 63.39 | 1.349 | 2.027 |
| 8 | TimesFM 2.5 (Google) | 200M | 0.3355 | 1.968 | 1.998 | 63.80 | 1.337 | 2.014 |
| 9 | Sundial base (Tsinghua THUML) | 128M | 0.3360 | 1.923 | 2.007 | 64.09 | 1.338 | 2.028 |
| 10 | Chronos-Bolt base (Amazon) | 205M | 0.3372 | 1.897 | 2.016 | 64.40 | 1.359 | 1.990 |
| 11 | Time-MoE (Shi et al.) | 200M | 0.3408 | 1.955 | 2.037 | 65.48 | 1.363 | 1.989 |
| 12 | TTM r2 (IBM Research) | 0.8M | 0.3647 | 2.175 | 2.155 | 65.79 | 1.359 | 2.827 |
| 13 | Persistence | 0 | 0.4361 | 3.738 | 2.224 | 75.69 | 1.724 | 2.785 |

**Live, Jan 2024 – Aug 2025** (709 stations, 145 forecast starts from 2024-01-23 to 2025-08-21, 24 h each; up to 1,914,220 scored values per variable; hours with no observation are not scored). E = standardised mean error, lower is better.

| Rank | Model | Params | E | Temp. (°C) | Dew pt. (°C) | Wind dir. (°) | Wind spd. (m/s) | Pressure (hPa) |
|---|---|---|---|---|---|---|---|---|
| 1 | **Atlas-5K 25M (ours)** | 24.1M | **0.3007** | 1.421 | 1.453 | 64.38 | 1.202 | 1.624 |
| 2 | Atlas-5K 10M (ours) | 9.64M | 0.3028 | 1.448 | 1.469 | 64.76 | 1.210 | 1.623 |
| 3 | Atlas-5K v2c (ours) | 0.97M | 0.3071 | 1.487 | 1.498 | 65.40 | 1.227 | 1.655 |
| 4 | TimesFM 3.0 (Google) | 0.3B | 0.3508 | 1.882 | 1.952 | 71.25 | 1.353 | 2.070 |
| 5 | Chronos-2 multivariate (Amazon) | 120M | 0.3522 | 1.848 | 1.916 | 70.78 | 1.367 | 2.175 |
| 6 | Chronos-Bolt base (Amazon) | 205M | 0.3547 | 1.899 | 2.007 | 71.70 | 1.371 | 2.092 |
| 7 | TiRex (NX-AI) | 35M | 0.3558 | 1.927 | 1.955 | 73.34 | 1.357 | 2.058 |
| 8 | Chronos-2 (Amazon) | 120M | 0.3559 | 1.902 | 1.959 | 71.84 | 1.381 | 2.131 |
| 9 | Sundial base (Tsinghua THUML) | 128M | 0.3572 | 1.931 | 1.998 | 72.74 | 1.363 | 2.120 |
| 10 | TimesFM 2.5 (Google) | 200M | 0.3575 | 1.975 | 1.991 | 72.45 | 1.365 | 2.127 |
| 11 | Time-MoE (Shi et al.) | 200M | 0.3665 | 1.993 | 2.049 | 75.27 | 1.397 | 2.115 |
| 12 | TTM r2 (IBM Research) | 0.8M | 0.3829 | 2.176 | 2.120 | 74.28 | 1.375 | 2.854 |
| 13 | Persistence | 0 | 0.4646 | 3.807 | 2.178 | 87.11 | 1.778 | 2.842 |

**Paired verdicts** (station-block bootstrap, 10,000 resamples, and Diebold–Mariano; the larger p-value, Holm-corrected over the 50 opponent × variable pairs, α = 0.01):

| Our model | Period | Significant wins | Largest Holm p | Margin vs the 9 foundation models (per variable) |
|---|---|---|---|---|
| Atlas-5K 25M (ours) | 2023 test | 50/50 | 0.005 | 11.0% to 48.2% lower MAE |
| Atlas-5K 25M (ours) | Live, Jan 2024 – Aug 2025 | 50/50 | 0.005 | 9.1% to 43.1% lower MAE |
| Atlas-5K 10M (ours) | 2023 test | 50/50 | 0.005 | 10.2% to 47.9% lower MAE |
| Atlas-5K 10M (ours) | Live, Jan 2024 – Aug 2025 | 50/50 | 0.005 | 8.5% to 43.1% lower MAE |

**Against the closest opponent, TimesFM 3.0** (25M's MAE change, paired, with 95% bootstrap interval):

| Period | Temp. | Dew pt. | Wind dir. | Wind spd. | Pressure |
|---|---|---|---|---|---|
| 2023 test | -25.9% [-27.2, -24.6] | -25.5% [-26.8, -24.3] | -14.5% [-15.3, -13.7] | -11.2% [-11.9, -10.5] | -25.4% [-26.6, -24.3] |
| Live, Jan 2024 – Aug 2025 | -24.5% [-25.8, -23.2] | -25.6% [-26.8, -24.2] | -9.6% [-10.7, -8.6] | -11.1% [-11.9, -10.3] | -21.6% [-22.7, -20.4] |

**25M against 10M** (paired, same windows; Holm over the five variables):

| Period | Temp. | Dew pt. | Wind dir. | Wind spd. | Pressure | Significant |
|---|---|---|---|---|---|---|
| 2022 validation | -2.12% (p 0.0005) | -1.19% (p 0.0005) | -1.10% (p 0.0005) | -0.93% (p 0.0005) | -0.42% (p 0.0016) | 5/5 |
| 2023 test | -2.06% (p 0.0005) | -1.04% (p 0.0005) | -1.07% (p 0.0005) | -0.90% (p 0.0005) | -0.45% (p 0.017) | 4/5 |
| Live 2024–25 | -1.86% (p 0.0005) | -1.08% (p 0.0005) | -0.59% (p 0.0005) | -0.66% (p 0.0005) | +0.10% (p 0.56) | 4/5 |

**Full 2023 test** (all 5,672 stations, every hourly window, about 1.18 × 10⁹ values per variable; WEATHER-5K protocol, MAE). Published rows are from the WEATHER-5K paper, compared by number only:

| Model | Params | Temp. | Dew pt. | Wind dir. | Wind spd. | Pressure |
|---|---|---|---|---|---|---|
| **Atlas-5K 25M (ours)** | 24.1M | 1.400 | 1.468 | 53.33 | 1.173 | 1.473 |
| Atlas-5K 10M (ours) | 9.64M | 1.429 | 1.486 | 53.93 | 1.183 | 1.477 |
| Atlas-5K v2c (ours) | 0.97M | 1.474 | 1.520 | 54.84 | 1.202 | 1.533 |
| PhysicsFormer (published) | 19.3M | 1.55 | 1.59 | 57.37 | 1.21 | 1.43 |
| ECMWF-HRES at stations (published) | – | 1.76 | 1.85 | 63.8 | 1.48 | 0.86 |
| 25M vs PhysicsFormer | | -9.7% | -7.7% | -7.0% | -3.1% | +3.0% |
| 25M vs ECMWF-HRES | | -20.5% | -20.7% | -16.4% | -20.8% | +71.2% |
