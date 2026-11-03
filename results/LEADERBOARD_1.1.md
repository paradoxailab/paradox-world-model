# ParadoxBench-1.1 leaderboard

Official windows: every 2nd test window (PEMS08, PEMS04, IMD-CI, IMD-WC) or every 6th (PEMS03, PEMS07, METR-LA, PEMS-BAY). Ranked by MAE.
Specialists (STID, Graph WaveNet, STAEformer) were trained with their official code under a per-run wall-clock budget; `budget` marks runs it stopped early.
Rainfall PWM-Dyn entries are v0.4. Ablation rows are excluded here (see `v0.6-conference/results/`).

## PEMS08 — Track A: Standard (12 steps / 30 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | STAEformer (CIKM'23, official code) | 13.93 | 23.17 | - | - | - | 25 epochs, budget |
| 2 | PWM-Dyn v0.6 (3-seed, CQR) | 14.12 | 23.46 | 4.589 | 67.07 | 79.7% | seeds 14.219 / 14.236 / 14.524 |
| 3 | STID (CIKM'22, official code) | 14.18 | 23.21 | - | - | - | 100 epochs |
| 4 | PWM-Dyn v0.4 (3-seed, CQR) | 14.53 | 23.91 | 4.719 | 68.94 | 79.7% |  |
| 5 | Graph WaveNet (IJCAI'19, official code) | 14.77 | 23.59 | - | - | - | 100 epochs |
| 6 | Climatology quantiles | 22.18 | 40.77 | 7.625 | 117.83 | 71.4% |  |
| 7 | Last value | 25.30 | 38.66 | - | - | - |  |

## PEMS08 — Track B: Open context (up to 512 steps / 365 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | STAEformer (CIKM'23, official code) | 13.93 | 23.17 | - | - | - | 25 epochs, budget |
| 2 | STID (CIKM'22, official code) | 14.18 | 23.21 | - | - | - | 100 epochs |
| 3 | PWM-Dyn v0.6-LC (3-seed, CQR) | 14.18 | 23.38 | 4.595 | 66.94 | 79.8% | seeds 14.435 / 14.463 / 14.316 |
| 4 | PWM-Dyn v0.4-LC (3-seed, CQR) | 14.38 | 23.48 | 4.660 | 67.91 | 79.7% |  |
| 5 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | 14.55 | 23.57 | 4.686 | 67.84 | 80.7% |  |
| 6 | Graph WaveNet (IJCAI'19, official code) | 14.77 | 23.59 | - | - | - | 100 epochs |
| 7 | TimesFM-2.5 (Google, 200M) (zero-shot, ctx 512) | 15.04 | 24.09 | 4.857 | 70.54 | 82.4% |  |
| 8 | Climatology quantiles | 22.18 | 40.77 | 7.625 | 117.83 | 71.4% |  |
| 9 | Last value | 25.30 | 38.66 | - | - | - |  |
| 10 | Seasonal naive | 36.54 | 60.77 | - | - | - |  |

## PEMS08 — Track R: Dead sensors (30% hidden, scored on hidden only)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.4-LC (3-seed, CQR) | 18.70 | 33.45 | 6.470 | 100.61 | 76.8% |  |
| 2 | PWM-Dyn v0.6-LC (3-seed, CQR) | 19.25 | 34.80 | 6.618 | 102.32 | 76.3% | seeds 19.313 / 19.642 / 19.603 |
| 3 | Climatology quantiles | 21.78 | 41.08 | 7.411 | 113.41 | 72.4% |  |
| 4 | STAEformer (CIKM'23, official code) | 186.51 | 233.65 | - | - | - | 25 epochs, budget |
| 5 | STID (CIKM'22, official code) | 198.09 | 239.66 | - | - | - | 100 epochs |
| 6 | Graph WaveNet (IJCAI'19, official code) | 216.21 | 260.58 | - | - | - | 100 epochs |

## PEMS08 — Track Z: Zero-shot transfer

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.4-LC inductive (trained on PEMS04 only) (3-seed, CQR) | 16.36 | 25.73 | 5.510 | 83.47 | 86.7% |  |

## PEMS04 — Track A: Standard (12 steps / 30 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 18.46 | 30.77 | 5.951 | 86.23 | 80.0% | seeds 18.520 / 18.702 / 18.645 |
| 2 | STID (CIKM'22, official code) | 18.49 | 30.05 | - | - | - | 100 epochs |
| 3 | STAEformer (CIKM'23, official code) | 19.21 | 30.66 | - | - | - | 12 epochs, budget |
| 4 | PWM-Dyn v0.4 (3-seed, CQR) | 19.21 | 31.75 | 6.156 | 88.65 | 79.6% |  |
| 5 | Graph WaveNet (IJCAI'19, official code) | 19.37 | 30.75 | - | - | - | 64 epochs, budget |
| 6 | Climatology quantiles | 25.02 | 41.36 | 8.431 | 127.81 | 71.5% |  |
| 7 | Last value | 31.56 | 48.25 | - | - | - |  |

## PEMS04 — Track B: Open context (up to 512 steps / 365 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 18.46 | 30.77 | 5.951 | 86.23 | 80.0% | seeds 18.520 / 18.702 / 18.645 |
| 2 | STID (CIKM'22, official code) | 18.49 | 30.05 | - | - | - | 100 epochs |
| 3 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | 19.13 | 31.02 | 6.137 | 88.42 | 80.7% |  |
| 4 | PWM-Dyn v0.4-LC (3-seed, CQR) | 19.17 | 31.52 | 6.135 | 88.16 | 80.0% |  |
| 5 | STAEformer (CIKM'23, official code) | 19.21 | 30.66 | - | - | - | 12 epochs, budget |
| 6 | Graph WaveNet (IJCAI'19, official code) | 19.37 | 30.75 | - | - | - | 64 epochs, budget |
| 7 | TimesFM-2.5 (Google, 200M) (zero-shot, ctx 512) | 19.70 | 31.70 | 6.337 | 91.61 | 82.0% |  |
| 8 | Climatology quantiles | 25.02 | 41.36 | 8.431 | 127.81 | 71.5% |  |
| 9 | Last value | 31.56 | 48.25 | - | - | - |  |
| 10 | Seasonal naive | 40.67 | 66.64 | - | - | - |  |

## PEMS04 — Track R: Dead sensors (30% hidden, scored on hidden only)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.4-LC (3-seed, CQR) | 24.99 | 43.03 | 8.484 | 129.58 | 78.1% |  |
| 2 | PWM-Dyn v0.6 (3-seed, CQR) | 25.33 | 42.62 | 8.402 | 125.41 | 78.3% | seeds 25.652 / 25.781 / 25.392 |
| 3 | Climatology quantiles | 27.39 | 45.60 | 9.199 | 139.04 | 71.3% |  |
| 4 | STID (CIKM'22, official code) | 120.58 | 155.19 | - | - | - | 100 epochs |
| 5 | Graph WaveNet (IJCAI'19, official code) | 132.51 | 169.68 | - | - | - | 64 epochs, budget |
| 6 | STAEformer (CIKM'23, official code) | 188.00 | 238.99 | - | - | - | 12 epochs, budget |

## PEMS03 — Track A: Standard (12 steps / 30 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 14.34 | 23.12 | 4.628 | 67.14 | 78.4% | seeds 14.450 / 14.448 / 14.649 |
| 2 | Graph WaveNet (IJCAI'19, official code) | 14.70 | 25.17 | - | - | - | 58 epochs, budget |
| 3 | STAEformer (CIKM'23, official code) | 15.45 | 26.03 | - | - | - | 10 epochs, budget |
| 4 | STID (CIKM'22, official code) | 15.50 | 26.83 | - | - | - | 100 epochs |
| 5 | Last value | 23.89 | 37.31 | - | - | - |  |
| 6 | Climatology quantiles | 25.93 | 47.80 | 9.459 | 154.10 | 61.0% |  |

## PEMS03 — Track B: Open context (up to 512 steps / 365 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | 14.15 | 22.70 | 4.541 | 65.50 | 80.7% |  |
| 2 | PWM-Dyn v0.6 (3-seed, CQR) | 14.34 | 23.12 | 4.628 | 67.14 | 78.4% | seeds 14.450 / 14.448 / 14.649 |
| 3 | Graph WaveNet (IJCAI'19, official code) | 14.70 | 25.17 | - | - | - | 58 epochs, budget |
| 4 | STAEformer (CIKM'23, official code) | 15.45 | 26.03 | - | - | - | 10 epochs, budget |
| 5 | STID (CIKM'22, official code) | 15.50 | 26.83 | - | - | - | 100 epochs |
| 6 | Last value | 23.89 | 37.31 | - | - | - |  |
| 7 | Climatology quantiles | 25.93 | 47.80 | 9.459 | 154.10 | 61.0% |  |
| 8 | Seasonal naive | 30.28 | 56.17 | - | - | - |  |

## PEMS03 — Track R: Dead sensors (30% hidden, scored on hidden only)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 17.71 | 27.94 | 5.784 | 84.96 | 77.7% | seeds 17.919 / 17.542 / 18.373 |
| 2 | Climatology quantiles | 23.31 | 42.90 | 8.531 | 139.41 | 62.4% |  |
| 3 | STID (CIKM'22, official code) | 113.05 | 159.85 | - | - | - | 100 epochs |
| 4 | STAEformer (CIKM'23, official code) | 119.34 | 172.78 | - | - | - | 10 epochs, budget |
| 5 | Graph WaveNet (IJCAI'19, official code) | 138.37 | 190.00 | - | - | - | 58 epochs, budget |

## PEMS07 — Track A: Standard (12 steps / 30 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 19.56 | 32.60 | 6.394 | 93.99 | 79.9% | seeds 20.117 / 19.687 / 19.828 |
| 2 | STID (CIKM'22, official code) | 19.62 | 32.72 | - | - | - | 84 epochs, budget |
| 3 | Graph WaveNet (IJCAI'19, official code) | 23.39 | 36.92 | - | - | - | 20 epochs, budget |
| 4 | Climatology quantiles | 29.98 | 58.67 | 10.319 | 159.70 | 76.2% |  |
| 5 | Last value | 35.63 | 54.37 | - | - | - |  |

## PEMS07 — Track B: Open context (up to 512 steps / 365 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 19.56 | 32.60 | 6.394 | 93.99 | 79.9% | seeds 20.117 / 19.687 / 19.828 |
| 2 | STID (CIKM'22, official code) | 19.62 | 32.72 | - | - | - | 84 epochs, budget |
| 3 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | 20.27 | 33.13 | 6.556 | 95.32 | 81.0% |  |
| 4 | Graph WaveNet (IJCAI'19, official code) | 23.39 | 36.92 | - | - | - | 20 epochs, budget |
| 5 | Climatology quantiles | 29.98 | 58.67 | 10.319 | 159.70 | 76.2% |  |
| 6 | Last value | 35.63 | 54.37 | - | - | - |  |
| 7 | Seasonal naive | 46.77 | 76.07 | - | - | - |  |

## PEMS07 — Track R: Dead sensors (30% hidden, scored on hidden only)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | Climatology quantiles | 29.10 | 56.07 | 10.142 | 158.77 | 77.0% |  |
| 2 | PWM-Dyn v0.6 (3-seed, CQR) | 30.95 | 55.63 | 10.533 | 161.22 | 79.2% | seeds 32.081 / 30.842 / 31.453 |
| 3 | STID (CIKM'22, official code) | 293.03 | 346.25 | - | - | - | 84 epochs, budget |
| 4 | Graph WaveNet (IJCAI'19, official code) | 310.03 | 363.85 | - | - | - | 20 epochs, budget |

## METR-LA — Track A: Standard (12 steps / 30 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 2.92 | 5.88 | 0.965 | 14.34 | 80.6% | seeds 2.960 / 2.959 / 2.956 |
| 2 | Graph WaveNet (IJCAI'19, official code) | 3.05 | 6.15 | - | - | - | 60 epochs, budget |
| 3 | STAEformer (CIKM'23, official code) | 3.09 | 6.33 | - | - | - | 12 epochs, budget |
| 4 | STID (CIKM'22, official code) | 3.12 | 6.50 | - | - | - | 100 epochs |
| 5 | Climatology quantiles | 3.90 | 8.41 | 1.297 | 19.42 | 75.3% |  |
| 6 | Last value | 5.04 | 10.98 | - | - | - |  |

## METR-LA — Track B: Open context (up to 512 steps / 365 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 2.92 | 5.88 | 0.965 | 14.34 | 80.6% | seeds 2.960 / 2.959 / 2.956 |
| 2 | Graph WaveNet (IJCAI'19, official code) | 3.05 | 6.15 | - | - | - | 60 epochs, budget |
| 3 | STAEformer (CIKM'23, official code) | 3.09 | 6.33 | - | - | - | 12 epochs, budget |
| 4 | STID (CIKM'22, official code) | 3.12 | 6.50 | - | - | - | 100 epochs |
| 5 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | 3.40 | 6.97 | 1.146 | 17.37 | 81.3% |  |
| 6 | Climatology quantiles | 3.90 | 8.41 | 1.297 | 19.42 | 75.3% |  |
| 7 | Last value | 5.04 | 10.98 | - | - | - |  |
| 8 | Seasonal naive | 10.35 | 20.72 | - | - | - |  |

## METR-LA — Track R: Dead sensors (30% hidden, scored on hidden only)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 3.36 | 6.69 | 1.116 | 16.66 | 80.6% | seeds 3.407 / 3.438 / 3.410 |
| 2 | Climatology quantiles | 4.07 | 8.76 | 1.354 | 20.26 | 75.0% |  |
| 3 | STID (CIKM'22, official code) | 5.11 | 10.05 | - | - | - | 100 epochs |
| 4 | STAEformer (CIKM'23, official code) | 5.33 | 10.35 | - | - | - | 12 epochs, budget |
| 5 | Graph WaveNet (IJCAI'19, official code) | 5.89 | 10.69 | - | - | - | 60 epochs, budget |

## PEMS-BAY — Track A: Standard (12 steps / 30 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 1.52 | 3.45 | 0.504 | 7.54 | 79.4% | seeds 1.544 / 1.536 / 1.535 |
| 2 | STID (CIKM'22, official code) | 1.56 | 3.60 | - | - | - | 94 epochs, budget |
| 3 | Graph WaveNet (IJCAI'19, official code) | 1.57 | 3.57 | - | - | - | 30 epochs, budget |
| 4 | STAEformer (CIKM'23, official code) | 1.59 | 3.63 | - | - | - | 6 epochs, budget |
| 5 | Last value | 2.17 | 5.11 | - | - | - |  |
| 6 | Climatology quantiles | 2.53 | 5.48 | 0.862 | 13.19 | 74.7% |  |

## PEMS-BAY — Track B: Open context (up to 512 steps / 365 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 1.52 | 3.45 | 0.504 | 7.54 | 79.4% | seeds 1.544 / 1.536 / 1.535 |
| 2 | STID (CIKM'22, official code) | 1.56 | 3.60 | - | - | - | 94 epochs, budget |
| 3 | Graph WaveNet (IJCAI'19, official code) | 1.57 | 3.57 | - | - | - | 30 epochs, budget |
| 4 | STAEformer (CIKM'23, official code) | 1.59 | 3.63 | - | - | - | 6 epochs, budget |
| 5 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | 1.66 | 3.95 | 0.553 | 8.29 | 81.0% |  |
| 6 | Last value | 2.17 | 5.11 | - | - | - |  |
| 7 | Climatology quantiles | 2.53 | 5.48 | 0.862 | 13.19 | 74.7% |  |
| 8 | Seasonal naive | 3.37 | 7.73 | - | - | - |  |

## PEMS-BAY — Track R: Dead sensors (30% hidden, scored on hidden only)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 2.31 | 5.04 | 0.812 | 12.82 | 78.5% | seeds 2.331 / 2.342 / 2.346 |
| 2 | Climatology quantiles | 2.71 | 6.05 | 0.927 | 14.28 | 74.8% |  |
| 3 | STID (CIKM'22, official code) | 42.19 | 45.92 | - | - | - | 94 epochs, budget |
| 4 | STAEformer (CIKM'23, official code) | 44.72 | 46.22 | - | - | - | 6 epochs, budget |
| 5 | Graph WaveNet (IJCAI'19, official code) | 51.76 | 53.17 | - | - | - | 30 epochs, budget |

## IMD-CI — Track A: Standard (12 steps / 30 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.4 (3-seed, CQR) | 2.84 | 10.42 | 1.073 | 18.01 | 84.7% |  |
| 2 | Climatology quantiles | 2.89 | 10.70 | 1.088 | 18.21 | 91.0% |  |
| 3 | Last value | 4.37 | 13.55 | - | - | - |  |

## IMD-CI — Track B: Open context (up to 512 steps / 365 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.4 (3-seed, CQR) | 2.84 | 10.42 | 1.073 | 18.01 | 84.7% |  |
| 2 | Climatology quantiles | 2.89 | 10.70 | 1.088 | 18.21 | 91.0% |  |
| 3 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 365) | 2.92 | 10.65 | 1.147 | 19.79 | 86.3% |  |
| 4 | TimesFM-2.5 (Google, 200M) (zero-shot, ctx 365) | 2.96 | 10.58 | 1.184 | 20.72 | 84.3% |  |
| 5 | Last value | 4.37 | 13.55 | - | - | - |  |
| 6 | Seasonal naive | 4.68 | 14.11 | - | - | - |  |

## IMD-CI — Track R: Dead sensors (30% hidden, scored on hidden only)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.4 (3-seed, CQR) | 2.84 | 10.38 | 1.072 | 17.99 | 85.5% |  |
| 2 | Climatology quantiles | 2.88 | 10.64 | 1.085 | 18.12 | 91.1% |  |

## IMD-WC — Track A: Standard (12 steps / 30 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.4 (3-seed, CQR) | 3.41 | 12.01 | 1.245 | 20.27 | 82.9% |  |
| 2 | Climatology quantiles | 3.65 | 13.00 | 1.312 | 21.09 | 91.0% |  |
| 3 | Last value | 4.88 | 14.94 | - | - | - |  |

## IMD-WC — Track B: Open context (up to 512 steps / 365 days)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.4 (3-seed, CQR) | 3.41 | 12.01 | 1.245 | 20.27 | 82.9% |  |
| 2 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 365) | 3.62 | 12.78 | 1.332 | 21.85 | 87.2% |  |
| 3 | Climatology quantiles | 3.65 | 13.00 | 1.312 | 21.09 | 91.0% |  |
| 4 | TimesFM-2.5 (Google, 200M) (zero-shot, ctx 365) | 3.67 | 12.65 | 1.378 | 23.00 | 85.2% |  |
| 5 | Last value | 4.88 | 14.94 | - | - | - |  |
| 6 | Seasonal naive | 5.69 | 17.07 | - | - | - |  |

## IMD-WC — Track R: Dead sensors (30% hidden, scored on hidden only)

| # | Model | MAE | RMSE | QL | IS80 | COV80 | Note |
|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.4 (3-seed, CQR) | 3.43 | 12.07 | 1.263 | 20.75 | 83.2% |  |
| 2 | Climatology quantiles | 3.60 | 12.85 | 1.300 | 21.00 | 90.8% |  |
