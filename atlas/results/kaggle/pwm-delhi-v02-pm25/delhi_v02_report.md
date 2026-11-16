# PWM-W Delhi v0.2 results (generated from results/delhi_v02_results.json)

DELHI: 17544 hours x 39 stations, targets ['PM2.5'] (missing 7.0%), 11 input channels, 376 graph links, 6 regions; splits {'train': ('2024-01-01T00', '2025-05-02T23'), 'val': ('2025-05-03T00', '2025-07-02T23'), 'test': ('2025-07-03T00', '2025-12-31T23')}

Unseen stations (Track U): Aya Nagar, Delhi - IMD, Dr. Karni Singh Shooting Range, Delhi - DPCC, IHBAS, Dilshad Garden, Delhi - CPCB, Lodhi Road, Delhi - IITM, Mandir Marg, Delhi - DPCC, North Campus, DU, Delhi - IMD, Rohini, Delhi - DPCC, Sri Aurobindo Marg, Delhi - DPCC

## PM2.5, Track S: training stations (ug/m3, next 24 h)

| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h |
|---|---|---|---|---|---|---|---|---|---|---|
| TimesFM 3.0 multivariate (Google) zero-shot (+CQR) | 29.95 | 54.09 | 30.5 | 9.85 | 145.9 | 79.2 | 13.21 | 27.61 | 32.09 | 35.09 |
| TimesFM 3.0 (Google) zero-shot (+CQR) | 30.31 | 54.30 | 31.0 | 9.96 | 147.2 | 78.3 | 13.77 | 28.89 | 32.22 | 34.68 |
| TimesFM 2.5 (Google, 200M) zero-shot (+CQR) | 30.83 | 55.52 | 30.8 | 10.15 | 150.3 | 77.6 | 13.95 | 29.17 | 32.91 | 35.34 |
| Chronos-2 (Amazon, 120M) zero-shot (+CQR) | 31.17 | 55.81 | 32.1 | 10.23 | 150.9 | 79.1 | 14.10 | 29.29 | 32.93 | 35.99 |
| PWM-W Delhi v0.2 | 31.28 | 57.30 | 30.7 | 10.51 | 158.8 | 77.5 | 13.80 | 29.32 | 34.05 | 35.29 |
| Chronos-Bolt base (Amazon, 205M) zero-shot (+CQR) | 31.35 | 56.00 | 32.0 | 10.26 | 150.9 | 78.5 | 14.21 | 29.33 | 33.35 | 36.26 |
| Variant A3-long+hybrid | 32.88 | 59.23 | 33.4 | 11.07 | 167.7 | 77.3 | 13.88 | 29.16 | 34.46 | 38.70 |
| Variant A4-long+wf+hybrid | 33.41 | 60.64 | 31.7 | 11.20 | 168.8 | 77.7 | 13.75 | 29.84 | 35.66 | 38.84 |
| Variant A1-long | 33.68 | 60.28 | 33.5 | 11.38 | 172.9 | 77.7 | 15.17 | 30.34 | 36.57 | 38.51 |
| Variant A2-long+wf | 34.16 | 61.74 | 33.7 | 11.80 | 183.3 | 75.0 | 14.51 | 31.72 | 38.98 | 38.91 |
| PWM-W v0.1-style (seed 0) | 35.50 | 62.94 | 35.7 | 12.03 | 183.4 | 77.5 | 14.60 | 30.74 | 38.42 | 41.42 |
| Same hour yesterday | 40.30 | 70.24 | 44.5 | 15.28 | 257.0 | 70.9 | 39.98 | 39.94 | 40.06 | 40.35 |
| CAMS global (ECMWF Copernicus), latest forecast + local bias correction zero-shot (+CQR) | 41.87 | 65.92 | 55.8 | 20.94 | 418.7 | 0.0 | 40.90 | 41.66 | 41.73 | 41.84 |
| Hour x month climatology | 44.60 | 74.67 | 51.8 | 16.89 | 283.6 | 69.8 | 44.42 | 44.43 | 44.46 | 44.79 |
| Last observed value | 46.01 | 81.07 | 47.7 | 18.06 | 311.8 | 66.5 | 16.58 | 47.16 | 54.74 | 38.94 |
| CAMS global (ECMWF Copernicus), latest forecast zero-shot (+CQR) | 62.86 | 97.71 | 74.4 | 31.43 | 628.6 | 0.1 | 61.32 | 62.54 | 62.57 | 62.89 |

## PM2.5, Track U: stations never trained on (ug/m3, next 24 h)

| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h |
|---|---|---|---|---|---|---|---|---|---|---|
| TimesFM 3.0 multivariate (Google) zero-shot (+CQR) | 26.16 | 48.85 | 29.9 | 8.65 | 128.6 | 79.5 | 11.32 | 24.11 | 28.26 | 31.04 |
| TimesFM 3.0 (Google) zero-shot (+CQR) | 26.84 | 50.47 | 30.6 | 8.85 | 131.2 | 78.2 | 11.86 | 25.42 | 28.91 | 31.31 |
| TimesFM 2.5 (Google, 200M) zero-shot (+CQR) | 27.10 | 50.72 | 30.4 | 8.97 | 133.5 | 77.8 | 12.04 | 25.61 | 29.26 | 31.55 |
| Chronos-2 (Amazon, 120M) zero-shot (+CQR) | 27.41 | 50.80 | 31.7 | 9.07 | 135.1 | 79.6 | 12.26 | 25.77 | 29.18 | 32.19 |
| PWM-W Delhi v0.2 | 27.59 | 51.94 | 30.8 | 9.38 | 143.4 | 77.3 | 11.97 | 25.72 | 30.23 | 31.73 |
| Chronos-Bolt base (Amazon, 205M) zero-shot (+CQR) | 27.94 | 51.57 | 32.1 | 9.17 | 135.5 | 78.6 | 12.39 | 26.05 | 30.04 | 33.00 |
| Same hour yesterday | 35.39 | 62.90 | 44.5 | 13.30 | 222.1 | 74.7 | 34.87 | 35.49 | 35.58 | 35.74 |
| Last observed value | 38.69 | 70.25 | 46.3 | 14.91 | 254.0 | 71.2 | 13.82 | 39.06 | 45.10 | 34.80 |
| Hour x month climatology | 39.00 | 65.39 | 52.9 | 14.45 | 238.4 | 73.0 | 38.66 | 39.34 | 39.38 | 39.56 |
| CAMS global (ECMWF Copernicus), latest forecast + local bias correction zero-shot (+CQR) | 39.81 | 62.12 | 65.8 | 19.90 | 398.1 | 0.0 | 39.17 | 40.51 | 40.56 | 40.64 |
| CAMS global (ECMWF Copernicus), latest forecast zero-shot (+CQR) | 53.53 | 83.79 | 85.2 | 26.76 | 535.3 | 0.1 | 52.42 | 54.11 | 54.18 | 54.36 |

## PM2.5, Track D: training stations, 30% dark (ug/m3, next 24 h)

| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h |
|---|---|---|---|---|---|---|---|---|---|---|
| PWM-W Delhi v0.2 | 31.44 | 57.62 | 30.6 | 10.56 | 159.7 | 77.6 | 13.80 | 29.39 | 34.22 | 35.37 |

## All four targets, PWM-W Delhi v0.1 vs the best baseline (Track S)

| Target | PWM-W MAE | PWM-W MAPE % | PWM-W COV80 % | best baseline | its MAE |
|---|---|---|---|---|---|
| PM2.5 | 31.28 | 30.7 | 77.5 | Same hour yesterday | 40.30 |

## Significance, PM2.5 Track S: PWM-W Delhi v0.2 vs each (negative = PWM-W better)

| vs | MAE | RMSE | MAPE | QL | IS80 |
|---|---|---|---|---|---|
| Last observed value | WIN -32.01% | WIN -29.32% | WIN -35.64% | WIN -41.82% | WIN -49.06% |
| Same hour yesterday | WIN -22.37% | WIN -18.43% | WIN -31.04% | WIN -31.24% | WIN -38.19% |
| Hour x month climatology | WIN -29.86% | WIN -23.27% | WIN -40.79% | WIN -37.77% | WIN -44.00% |
| PWM-W v0.1-style (seed 0) | WIN -11.88% | WIN -8.96% | WIN -14.12% | WIN -12.64% | WIN -13.38% |
| Variant A1-long | WIN -7.11% | TIE -4.94% | WIN -8.56% | WIN -7.64% | WIN -8.16% |
| Variant A2-long+wf | WIN -8.41% | WIN -7.18% | WIN -8.91% | WIN -10.97% | WIN -13.35% |
| Variant A3-long+hybrid | WIN -4.85% | TIE -3.26% | WIN -8.18% | TIE -5.06% | TIE -5.27% |
| Variant A4-long+wf+hybrid | WIN -6.36% | WIN -5.51% | WIN -3.30% | WIN -6.14% | WIN -5.92% |
| Chronos-Bolt base (Amazon, 205M) zero-shot | TIE -0.22% | TIE +2.33% | WIN -4.07% | TIE +2.45% | TIE +5.23% |
| Chronos-2 (Amazon, 120M) zero-shot | TIE +0.35% | TIE +2.68% | WIN -4.48% | TIE +2.75% | TIE +5.23% |
| TimesFM 2.5 (Google, 200M) zero-shot | TIE +1.47% | TIE +3.21% | TIE -0.44% | TIE +3.55% | TIE +5.68% |
| TimesFM 3.0 (Google) zero-shot | TIE +3.19% | TIE +5.53% | TIE -1.13% | TIE +5.50% | TIE +7.88% |
| TimesFM 3.0 multivariate (Google) zero-shot | TIE +4.45% | TIE +5.94% | TIE +0.59% | LOSS +6.64% | LOSS +8.89% |
| CAMS global (ECMWF Copernicus), latest forecast | WIN -49.79% | WIN -40.91% | WIN -58.93% | WIN -66.28% | WIN -74.53% |
| CAMS global (ECMWF Copernicus), latest forecast + local bias correction | WIN -24.62% | WIN -12.41% | WIN -45.26% | WIN -49.39% | WIN -61.77% |

## Significance, PM2.5 Track U: PWM-W Delhi v0.2 vs each (negative = PWM-W better)

| vs | MAE | RMSE | MAPE | QL | IS80 |
|---|---|---|---|---|---|
| Last observed value | WIN -28.69% | WIN -26.06% | WIN -33.65% | WIN -37.11% | WIN -43.52% |
| Same hour yesterday | WIN -22.03% | WIN -17.42% | WIN -30.82% | WIN -29.48% | WIN -35.41% |
| Hour x month climatology | WIN -29.25% | WIN -20.56% | WIN -41.92% | WIN -35.07% | WIN -39.83% |
| Chronos-Bolt base (Amazon, 205M) zero-shot | TIE -1.24% | TIE +0.72% | WIN -4.07% | TIE +2.27% | TIE +5.89% |
| Chronos-2 (Amazon, 120M) zero-shot | TIE +0.66% | TIE +2.25% | TIE -2.90% | TIE +3.42% | TIE +6.21% |
| TimesFM 2.5 (Google, 200M) zero-shot | TIE +1.82% | TIE +2.42% | TIE +1.26% | TIE +4.61% | LOSS +7.44% |
| TimesFM 3.0 (Google) zero-shot | TIE +2.79% | TIE +2.91% | TIE +0.41% | TIE +6.01% | LOSS +9.30% |
| TimesFM 3.0 multivariate (Google) zero-shot | LOSS +5.46% | LOSS +6.34% | LOSS +3.02% | LOSS +8.50% | LOSS +11.59% |
| CAMS global (ECMWF Copernicus), latest forecast | WIN -47.51% | WIN -37.19% | WIN -63.14% | WIN -64.45% | WIN -72.92% |
| CAMS global (ECMWF Copernicus), latest forecast + local bias correction | WIN -29.42% | WIN -15.28% | WIN -52.25% | WIN -52.19% | WIN -63.58% |

## Significance, PM2.5 Track D: PWM-W Delhi v0.2 vs each (negative = PWM-W better)

| vs | MAE | RMSE | MAPE | QL | IS80 |
|---|---|---|---|---|---|

## Runs

| Run | val PM2.5 MAE | params | s/step | min |
|---|---|---|---|---|
| A0-short-s0 | 21.877 | 884,204 | 0.0229 | 2.3 |
| A0-short-s1 | 21.495 | 884,204 | 0.0227 | 2.3 |
| A0-short-s2 | 21.870 | 884,204 | 0.0227 | 2.3 |
| A1-long | 21.972 | 912,364 | 0.0226 | 2.3 |
| A2-long+wf | 20.835 | 1,022,956 | 0.0227 | 2.3 |
| A3-long+hybrid | 20.474 | 949,484 | 0.0228 | 2.3 |
| A4-long+wf+hybrid | 20.167 | 1,060,076 | 0.0228 | 2.3 |
| final-s100 | 20.089 | 1,060,076 | 0.0228 | 2.3 |
| final-s101 | 19.992 | 1,060,076 | 0.023 | 2.3 |
| final-s102 | 20.155 | 1,060,076 | 0.0231 | 2.3 |

Decisions: `{"sigma_val_PM25": 0.2189202134813253, "val_MAE_PM25": {"A0-short": 21.876924514770508, "A1-long": 21.972204208374023, "A2-long+wf": 20.83517074584961, "A3-long+hybrid": 20.47399139404297, "A4-long+wf+hybrid": 20.16672134399414}, "chosen": "A4-long+wf+hybrid", "rule": "the variant with the lowest validation PM2.5 MAE, if it beats A0-short by > 2 sigma"}`
