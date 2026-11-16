# PWM-W Delhi v0.1 results (generated from results/delhi_v01_results.json)

DELHI: 17544 hours x 39 stations, targets ['PM2.5', 'PM10', 'NO2', 'Ozone'] (missing 7.0%, 6.1%, 6.5%, 9.7%), 11 input channels, 376 graph links, 6 regions; splits {'train': ('2024-01-01T00', '2025-05-02T23'), 'val': ('2025-05-03T00', '2025-07-02T23'), 'test': ('2025-07-03T00', '2025-12-31T23')}

Unseen stations (Track U): Aya Nagar, Delhi - IMD, Dr. Karni Singh Shooting Range, Delhi - DPCC, IHBAS, Dilshad Garden, Delhi - CPCB, Lodhi Road, Delhi - IITM, Mandir Marg, Delhi - DPCC, North Campus, DU, Delhi - IMD, Rohini, Delhi - DPCC, Sri Aurobindo Marg, Delhi - DPCC

## PM2.5, Track S: training stations (ug/m3, next 24 h)

| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h |
|---|---|---|---|---|---|---|---|---|---|---|
| TimesFM 3.0 multivariate (Google) zero-shot (+CQR) | 29.95 | 54.09 | 30.5 | 9.85 | 145.9 | 79.2 | 13.21 | 27.61 | 32.09 | 35.09 |
| TimesFM 3.0 (Google) zero-shot (+CQR) | 30.31 | 54.30 | 31.0 | 9.96 | 147.2 | 78.3 | 13.77 | 28.89 | 32.22 | 34.68 |
| TimesFM 2.5 (Google, 200M) zero-shot (+CQR) | 30.83 | 55.52 | 30.8 | 10.15 | 150.3 | 77.6 | 13.95 | 29.17 | 32.91 | 35.34 |
| Chronos-2 (Amazon, 120M) zero-shot (+CQR) | 31.17 | 55.81 | 32.1 | 10.23 | 150.9 | 79.1 | 14.10 | 29.29 | 32.93 | 35.99 |
| Chronos-Bolt base (Amazon, 205M) zero-shot (+CQR) | 31.35 | 56.00 | 32.0 | 10.26 | 150.9 | 78.5 | 14.21 | 29.33 | 33.35 | 36.26 |
| PWM-W Delhi v0.1 | 32.63 | 57.76 | 33.5 | 10.89 | 163.7 | 78.4 | 13.88 | 28.39 | 34.64 | 38.30 |
| Ablation no-aux | 34.00 | 59.52 | 34.1 | 11.19 | 165.7 | 80.1 | 15.18 | 29.45 | 35.88 | 38.91 |
| PWM-W base (seed 0) | 34.51 | 60.09 | 35.8 | 11.59 | 175.1 | 77.3 | 14.93 | 30.49 | 36.15 | 39.46 |
| Ablation pm25-only | 34.84 | 60.77 | 36.1 | 11.56 | 172.6 | 77.7 | 14.29 | 30.03 | 38.65 | 39.45 |
| Ablation no-graph | 36.02 | 63.32 | 36.8 | 11.99 | 179.6 | 78.5 | 15.07 | 32.00 | 37.26 | 42.31 |
| Same hour yesterday | 40.30 | 70.24 | 44.5 | 15.28 | 257.0 | 70.9 | 39.98 | 39.94 | 40.06 | 40.35 |
| Hour x month climatology | 44.60 | 74.67 | 51.8 | 16.89 | 283.6 | 69.8 | 44.42 | 44.43 | 44.46 | 44.79 |
| Last observed value | 46.01 | 81.07 | 47.7 | 18.06 | 311.8 | 66.5 | 16.58 | 47.16 | 54.74 | 38.94 |

## PM2.5, Track U: stations never trained on (ug/m3, next 24 h)

| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h |
|---|---|---|---|---|---|---|---|---|---|---|
| TimesFM 3.0 multivariate (Google) zero-shot (+CQR) | 26.16 | 48.85 | 29.9 | 8.65 | 128.6 | 79.5 | 11.32 | 24.11 | 28.26 | 31.04 |
| TimesFM 3.0 (Google) zero-shot (+CQR) | 26.84 | 50.47 | 30.6 | 8.85 | 131.2 | 78.2 | 11.86 | 25.42 | 28.91 | 31.31 |
| TimesFM 2.5 (Google, 200M) zero-shot (+CQR) | 27.10 | 50.72 | 30.4 | 8.97 | 133.5 | 77.8 | 12.03 | 25.61 | 29.26 | 31.56 |
| Chronos-2 (Amazon, 120M) zero-shot (+CQR) | 27.41 | 50.80 | 31.7 | 9.07 | 135.1 | 79.6 | 12.26 | 25.77 | 29.18 | 32.19 |
| Chronos-Bolt base (Amazon, 205M) zero-shot (+CQR) | 27.94 | 51.57 | 32.1 | 9.17 | 135.5 | 78.6 | 12.39 | 26.05 | 30.04 | 33.00 |
| PWM-W Delhi v0.1 | 28.26 | 51.34 | 33.0 | 9.52 | 144.3 | 78.5 | 12.24 | 25.69 | 30.53 | 32.84 |
| Same hour yesterday | 35.39 | 62.90 | 44.5 | 13.30 | 222.1 | 74.7 | 34.87 | 35.49 | 35.58 | 35.74 |
| Last observed value | 38.69 | 70.25 | 46.3 | 14.91 | 254.0 | 71.2 | 13.82 | 39.06 | 45.10 | 34.80 |
| Hour x month climatology | 39.00 | 65.39 | 52.9 | 14.45 | 238.4 | 73.0 | 38.66 | 39.34 | 39.38 | 39.56 |

## PM2.5, Track D: training stations, 30% dark (ug/m3, next 24 h)

| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h |
|---|---|---|---|---|---|---|---|---|---|---|
| PWM-W Delhi v0.1 | 32.77 | 58.25 | 33.4 | 10.95 | 164.6 | 78.9 | 15.08 | 28.64 | 34.69 | 38.28 |

## All four targets, PWM-W Delhi v0.1 vs the best baseline (Track S)

| Target | PWM-W MAE | PWM-W MAPE % | PWM-W COV80 % | best baseline | its MAE |
|---|---|---|---|---|---|
| PM2.5 | 32.63 | 33.5 | 78.4 | Same hour yesterday | 40.30 |

## Significance, PM2.5 Track S: PWM-W Delhi v0.1 vs each (negative = PWM-W better)

| vs | MAE | RMSE | MAPE | QL | IS80 |
|---|---|---|---|---|---|
| Last observed value | WIN -29.07% | WIN -28.75% | WIN -29.79% | WIN -39.68% | WIN -47.51% |
| Same hour yesterday | WIN -19.02% | WIN -17.77% | WIN -24.78% | WIN -28.71% | WIN -36.31% |
| Hour x month climatology | WIN -26.83% | WIN -22.65% | WIN -35.41% | WIN -35.49% | WIN -42.30% |
| PWM-W base (seed 0) | WIN -5.43% | WIN -3.87% | WIN -6.57% | WIN -5.99% | WIN -6.54% |
| Ablation no-aux | WIN -4.02% | TIE -2.95% | TIE -1.94% | TIE -2.64% | TIE -1.23% |
| Ablation no-graph | WIN -9.41% | WIN -8.78% | WIN -8.95% | WIN -9.14% | WIN -8.87% |
| Ablation pm25-only | WIN -6.33% | WIN -4.95% | WIN -7.27% | WIN -5.76% | WIN -5.18% |
| Chronos-Bolt base (Amazon, 205M) zero-shot | TIE +4.09% | TIE +3.15% | LOSS +4.64% | LOSS +6.21% | LOSS +8.42% |
| Chronos-2 (Amazon, 120M) zero-shot | TIE +4.68% | TIE +3.51% | LOSS +4.19% | LOSS +6.52% | LOSS +8.42% |
| TimesFM 2.5 (Google, 200M) zero-shot | LOSS +5.86% | TIE +4.04% | LOSS +8.60% | LOSS +7.35% | LOSS +8.89% |
| TimesFM 3.0 (Google) zero-shot | LOSS +7.65% | LOSS +6.38% | LOSS +7.84% | LOSS +9.38% | LOSS +11.15% |
| TimesFM 3.0 multivariate (Google) zero-shot | LOSS +8.96% | LOSS +6.79% | LOSS +9.72% | LOSS +10.56% | LOSS +12.20% |

## Significance, PM2.5 Track U: PWM-W Delhi v0.1 vs each (negative = PWM-W better)

| vs | MAE | RMSE | MAPE | QL | IS80 |
|---|---|---|---|---|---|
| Last observed value | WIN -26.94% | WIN -26.91% | WIN -28.87% | WIN -36.17% | WIN -43.19% |
| Same hour yesterday | WIN -20.13% | WIN -18.38% | WIN -25.83% | WIN -28.42% | WIN -35.03% |
| Hour x month climatology | WIN -27.52% | WIN -21.48% | WIN -37.73% | WIN -34.10% | WIN -39.47% |
| Chronos-Bolt base (Amazon, 205M) zero-shot | TIE +1.18% | TIE -0.44% | TIE +2.84% | TIE +3.80% | LOSS +6.51% |
| Chronos-2 (Amazon, 120M) zero-shot | TIE +3.13% | TIE +1.07% | LOSS +4.10% | LOSS +4.97% | LOSS +6.83% |
| TimesFM 2.5 (Google, 200M) zero-shot | LOSS +4.31% | TIE +1.24% | LOSS +8.56% | LOSS +6.17% | LOSS +8.07% |
| TimesFM 3.0 (Google) zero-shot | LOSS +5.31% | TIE +1.72% | LOSS +7.65% | LOSS +7.60% | LOSS +9.94% |
| TimesFM 3.0 multivariate (Google) zero-shot | LOSS +8.04% | LOSS +5.12% | LOSS +10.45% | LOSS +10.12% | LOSS +12.24% |

## Significance, PM2.5 Track D: PWM-W Delhi v0.1 vs each (negative = PWM-W better)

| vs | MAE | RMSE | MAPE | QL | IS80 |
|---|---|---|---|---|---|

## Runs

| Run | val PM2.5 MAE | params | s/step | min |
|---|---|---|---|---|
| base-s0 | 22.242 | 1,073,348 | 0.0816 | 8.2 |
| base-s1 | 22.163 | 1,073,348 | 0.0826 | 8.3 |
| base-s2 | 22.396 | 1,073,348 | 0.0828 | 8.4 |
| no-aux | 22.099 | 938,180 | 0.0777 | 7.8 |
| no-graph | 22.162 | 824,516 | 0.067 | 6.8 |
| pm25-only | 21.511 | 884,204 | 0.0662 | 6.7 |
| final-s100 | 21.354 | 884,204 | 0.0677 | 6.8 |
| final-s101 | 21.349 | 884,204 | 0.0663 | 6.7 |
| final-s102 | 21.224 | 884,204 | 0.0692 | 7.0 |

Decisions: `{"sigma_val_PM25": 0.11868621550950573, "z_removal_gain": {"no-aux": 1.2058189685419545, "no-graph": 0.6751062738992039, "pm25-only": 6.159973118665761}, "drop_aux": false, "drop_graph": false, "single_target": true, "rule": "a component is dropped only if removing it improves validation PM2.5 MAE by > 2 sigma"}`
