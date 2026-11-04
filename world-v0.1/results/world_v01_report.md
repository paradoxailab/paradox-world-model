# Paradox World Model v0.1 results (generated from results/world_v01_results.json)

Data: UK-M25 [flow]: 35040 x 190, 1572 links, missing 7.2%, 11 regions, 151 conservation pairs, origins {'train': 23841, 'val': 3501, 'test': 7005}

## Track S: seen sensors, clean input

| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@15 | MAE@30 | MAE@60 |
|---|---|---|---|---|---|---|---|---|---|
| TimesFM 3.0 (Google) zero-shot (+CQR) | 45.218 | 81.642 | 11.06 | 15.032 | 224.86 | 78.8 | 38.108 | 44.403 | 50.599 |
| PWM-W v0.1 (3-seed, CQR) | 45.311 | 80.653 | 11.22 | 14.993 | 223.22 | 79.3 | 37.937 | 44.143 | 51.301 |
| Scratch base (seed 0) | 45.773 | 81.063 | 11.36 | 15.137 | 225.24 | 79.3 | 38.133 | 44.491 | 52.136 |
| Exp C-fp32 | 45.834 | 80.895 | 11.23 | 15.155 | 225.47 | 79.2 | 38.055 | 44.477 | 52.225 |
| Exp E-physics | 45.843 | 80.905 | 11.34 | 15.141 | 225.00 | 79.4 | 38.504 | 44.557 | 51.967 |
| Exp H-no-hierarchy | 45.871 | 81.054 | 11.23 | 15.171 | 225.77 | 79.5 | 38.333 | 44.753 | 51.943 |
| Chronos-2 (Amazon, 120M) zero-shot (+CQR) | 45.958 | 82.552 | 11.44 | 15.266 | 228.18 | 79.5 | 39.209 | 45.264 | 50.915 |
| Exp W-no-weather | 45.976 | 81.158 | 11.21 | 15.196 | 225.99 | 79.0 | 38.103 | 44.594 | 52.473 |
| TimesFM 2.5 (Google, 200M) zero-shot (+CQR) | 47.094 | 83.606 | 11.56 | 15.693 | 235.31 | 78.5 | 38.685 | 46.112 | 53.228 |
| Exp B-experts | 47.319 | 83.038 | 11.59 | 15.620 | 232.01 | 80.0 | 39.046 | 46.020 | 54.260 |
| PWM-W F-base fine-tuned (seed 0) | 47.333 | 82.133 | 11.89 | 15.569 | 230.41 | 79.7 | 40.013 | 45.735 | 53.900 |
| F-base fine-tuned 30 days | 48.201 | 85.038 | 11.78 | 15.860 | 234.79 | 79.6 | 40.152 | 46.586 | 55.136 |
| Scratch 30 days | 48.350 | 87.394 | 12.05 | 16.169 | 243.33 | 78.6 | 39.788 | 47.113 | 55.136 |
| Chronos-Bolt base (Amazon, 205M) zero-shot (+CQR) | 48.762 | 86.005 | 11.79 | 16.290 | 244.89 | 78.8 | 40.633 | 47.677 | 54.977 |
| F-base fine-tuned 7 days | 50.135 | 88.501 | 12.83 | 16.581 | 246.76 | 80.0 | 41.362 | 48.412 | 57.793 |
| Exp A-ssl | 50.436 | 86.801 | 12.49 | 16.916 | 255.31 | 78.6 | 41.032 | 48.647 | 58.303 |
| PWM-W F-base zero-shot | 50.682 | 86.975 | 12.26 | 16.946 | 254.97 | 66.1 | 42.002 | 48.931 | 58.332 |
| Scratch 7 days | 50.818 | 92.255 | 12.60 | 17.126 | 259.70 | 79.4 | 41.153 | 48.731 | 59.245 |
| Last observed value | 80.536 | 133.771 | 19.62 | 28.688 | 457.96 | 79.3 | 49.778 | 72.671 | 108.359 |
| Same time last week | 83.142 | 162.237 | 19.97 | 31.541 | 530.51 | 80.7 | 83.027 | 83.178 | 83.702 |
| Same time yesterday | 100.260 | 177.987 | 23.39 | 37.540 | 624.91 | 78.7 | 100.917 | 100.797 | 99.488 |

## Track U: unseen locations (never trained on)

| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@15 | MAE@30 | MAE@60 |
|---|---|---|---|---|---|---|---|---|---|
| TimesFM 3.0 (Google) zero-shot (+CQR) | 50.748 | 86.835 | 11.10 | 16.859 | 252.02 | 79.2 | 42.672 | 49.665 | 57.172 |
| PWM-W v0.1 (3-seed, CQR) | 51.234 | 87.005 | 11.23 | 16.946 | 252.21 | 79.5 | 42.722 | 49.641 | 58.727 |
| Chronos-2 (Amazon, 120M) zero-shot (+CQR) | 51.306 | 87.601 | 11.40 | 17.026 | 254.26 | 78.8 | 43.812 | 50.456 | 57.066 |
| TimesFM 2.5 (Google, 200M) zero-shot (+CQR) | 52.678 | 89.027 | 11.55 | 17.567 | 263.62 | 78.7 | 43.263 | 51.376 | 59.829 |
| Chronos-Bolt base (Amazon, 205M) zero-shot (+CQR) | 54.534 | 91.304 | 11.85 | 18.193 | 273.13 | 79.8 | 45.334 | 53.255 | 61.727 |
| F-base fine-tuned 30 days | 54.774 | 92.652 | 11.86 | 17.991 | 265.85 | 78.9 | 45.264 | 52.593 | 63.403 |
| Scratch 30 days | 54.994 | 95.029 | 12.12 | 18.397 | 276.93 | 77.8 | 45.177 | 53.207 | 63.432 |
| PWM-W F-base zero-shot | 56.842 | 93.117 | 12.25 | 18.941 | 284.03 | 66.7 | 47.349 | 54.741 | 65.549 |
| F-base fine-tuned 7 days | 56.899 | 96.780 | 12.92 | 18.781 | 278.95 | 78.5 | 46.747 | 54.791 | 66.023 |
| Scratch 7 days | 58.214 | 101.901 | 12.89 | 19.646 | 298.30 | 78.5 | 47.245 | 55.388 | 68.447 |
| Last observed value | 89.894 | 142.559 | 19.42 | 31.598 | 498.46 | 75.9 | 56.201 | 81.418 | 120.124 |
| Same time last week | 93.834 | 172.693 | 20.52 | 35.131 | 584.74 | 77.2 | 94.115 | 93.946 | 94.508 |
| Same time yesterday | 114.777 | 198.100 | 23.98 | 42.775 | 709.36 | 75.1 | 116.402 | 115.861 | 113.622 |

## Track D: seen sensors, 30% of sensors dark

| Model | MAE | RMSE | MAPE % | QL | IS80 | COV80 % | MAE@15 | MAE@30 | MAE@60 |
|---|---|---|---|---|---|---|---|---|---|
| PWM-W v0.1 (3-seed, CQR) | 48.163 | 85.588 | 12.08 | 16.013 | 239.56 | 79.2 | 42.770 | 47.111 | 52.797 |

## Significance, Track S: PWM-W v0.1 vs each model (negative = PWM-W better)

| vs | MAE | RMSE | MAPE | QL | IS80 |
|---|---|---|---|---|---|
| Last observed value | WIN -43.74% | WIN -39.71% | WIN -42.81% | WIN -47.74% | WIN -51.26% |
| Same time yesterday | WIN -54.81% | WIN -54.69% | WIN -52.02% | WIN -60.06% | WIN -64.28% |
| Same time last week | WIN -45.50% | WIN -50.29% | WIN -43.81% | WIN -52.47% | WIN -57.92% |
| Scratch base (seed 0) | WIN -1.01% | WIN -0.51% | WIN -1.26% | WIN -0.95% | WIN -0.89% |
| PWM-W F-base zero-shot | WIN -10.60% | WIN -7.27% | WIN -8.51% | WIN -11.53% | WIN -12.45% |
| PWM-W F-base fine-tuned (seed 0) | WIN -4.27% | WIN -1.80% | WIN -5.64% | WIN -3.70% | WIN -3.12% |
| Chronos-Bolt base (Amazon, 205M) zero-shot | WIN -7.08% | WIN -6.22% | WIN -4.80% | WIN -7.96% | WIN -8.85% |
| Chronos-2 (Amazon, 120M) zero-shot | TIE -1.41% | WIN -2.30% | WIN -1.95% | WIN -1.79% | WIN -2.17% |
| TimesFM 2.5 (Google, 200M) zero-shot | WIN -3.79% | WIN -3.53% | WIN -2.90% | WIN -4.46% | WIN -5.14% |
| TimesFM 3.0 (Google) zero-shot | TIE +0.21% | WIN -1.21% | LOSS +1.44% | TIE -0.26% | TIE -0.73% |

## Significance, Track U: PWM-W v0.1 vs each model (negative = PWM-W better)

| vs | MAE | RMSE | MAPE | QL | IS80 |
|---|---|---|---|---|---|
| Last observed value | WIN -43.01% | WIN -38.97% | WIN -42.20% | WIN -46.37% | WIN -49.40% |
| Same time yesterday | WIN -55.36% | WIN -56.08% | WIN -53.19% | WIN -60.38% | WIN -64.45% |
| Same time last week | WIN -45.40% | WIN -49.62% | WIN -45.29% | WIN -51.76% | WIN -56.87% |
| PWM-W F-base zero-shot | WIN -9.87% | WIN -6.56% | WIN -8.37% | WIN -10.53% | WIN -11.20% |
| Chronos-Bolt base (Amazon, 205M) zero-shot | WIN -6.05% | WIN -4.71% | WIN -5.26% | WIN -6.86% | WIN -7.66% |
| Chronos-2 (Amazon, 120M) zero-shot | TIE -0.14% | TIE -0.68% | TIE -1.53% | TIE -0.47% | TIE -0.80% |
| TimesFM 2.5 (Google, 200M) zero-shot | WIN -2.74% | WIN -2.27% | WIN -2.79% | WIN -3.53% | WIN -4.33% |
| TimesFM 3.0 (Google) zero-shot | TIE +0.96% | TIE +0.20% | TIE +1.14% | TIE +0.52% | TIE +0.07% |

## Runs (validation MAE, compute)

| Run | val MAE | params | active | s/step | peak MB | min |
|---|---|---|---|---|---|---|
| scratch-base-s0 | 43.3456 | 716,476 | 716,476 | 0.0278 | 193 | 1.4 |
| scratch-base-s1 | 42.8056 | 716,476 | 716,476 | 0.0269 | 198 | 1.4 |
| scratch-base-s2 | 42.6408 | 716,476 | 716,476 | 0.0264 | 204 | 1.4 |
| F-base | 39.6706 | 3,841,248 | 2,064,864 | 0.0726 | 689 | 15.9 |
| F-base-ft-full-s0 | 45.2088 | 3,841,248 | 2,064,864 | 0.0678 | 630 | 2.4 |
| A-ssl | 48.1262 | 716,476 | 716,476 | 0.0247 | 528 | 1.3 |
| B-experts | 45.1742 | 1,311,292 | 718,012 | 0.05 | 559 | 2.6 |
| C-fp32 | 43.1712 | 716,476 | 716,476 | 0.0207 | 560 | 1.1 |
| E-physics | 43.1570 | 716,476 | 716,476 | 0.0254 | 533 | 1.3 |
| H-no-hierarchy | 43.2837 | 467,644 | 467,644 | 0.015 | 520 | 0.8 |
| W-no-weather | 43.1329 | 716,476 | 716,476 | 0.0246 | 531 | 1.3 |
| scratch-14d | 47.3197 | 716,476 | 716,476 | 0.0243 | 533 | 1.3 |
| A-ssl-14d | 49.6867 | 716,476 | 716,476 | 0.0251 | 533 | 1.3 |
| D-random-5pct | 43.9019 | 716,476 | 716,476 | 0.0249 | 533 | 1.3 |
| D-active-5pct | 44.2462 | 716,476 | 716,476 | 0.025 | 539 | 1.3 |
| scratch-7d | 48.4809 | 716,476 | 716,476 | 0.0251 | 539 | 1.3 |
| F-base-ft-7d | 48.0947 | 3,841,248 | 2,064,864 | 0.0677 | 674 | 2.4 |
| scratch-30d | 45.4663 | 716,476 | 716,476 | 0.0253 | 566 | 1.3 |
| F-base-ft-30d | 45.7976 | 3,841,248 | 2,064,864 | 0.0685 | 671 | 2.4 |
| final-s100 | 42.7980 | 716,476 | 716,476 | 0.025 | 565 | 1.3 |
| final-s101 | 42.7990 | 716,476 | 716,476 | 0.0246 | 539 | 1.3 |
| final-s102 | 42.4490 | 716,476 | 716,476 | 0.0241 | 544 | 1.2 |

Decisions (validation rules): `{"ssl": false, "experts": false, "physics": false, "drop_hierarchy": false, "drop_weather": false, "fp32_needed": false, "active_beats_random": false, "ssl_helps_at_14d": false}`

Final choice: `{"candidates_val_MAE": {"scratch-best": 43.34561538696289, "F-base-ft": 45.208805084228516}, "chosen": "scratch-best"}`
