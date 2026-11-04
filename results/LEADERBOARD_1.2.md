# ParadoxBench-1.2 leaderboard (traffic tasks)

Scored on the official test windows (every 2nd window on PEMS08/PEMS04, every 6th on the other four). Lower is better for MAE, RMSE, MAPE, QL and IS80; COV80 should be close to 80%.

Rows come from the v0.7 Kaggle run (notebook8ffe55b5c8, 2026-11-04, repo commit b0f6a08), which merged and re-scored the v0.6 sessions' saved forecasts and models. TimesFM rows for PEMS08 and PEMS04 come from the v0.4 study (same official windows), as in `LEADERBOARD_1.1.md`. Opponents with a wall-clock budget stopped before their authors' full training schedule (epochs in `LEADERBOARD_1.1.md`). Rainfall tasks are unchanged from 1.1.

## PEMS08 · Track A: standard 12-step context

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | STAEformer (CIKM'23, official code) | 1.22M | 12 | 13.929 | 23.17 | 9.36% | - | - | - |
| 2 | PWM-Dyn v0.6 (3-seed, CQR) | 0.32M | 12 | 14.120 | 23.46 | 9.24% | 4.589 | 67.07 | 79.7% |
| 3 | STID (CIKM'22, official code) | 0.12M | 12 | 14.182 | 23.21 | 9.27% | - | - | - |
| 4 | PWM-Dyn v0.7 (3-seed, CQR) | 0.32M | 12 | 14.219 | 23.54 | 9.34% | 4.614 | 67.32 | 79.8% |
| 5 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 14.765 | 23.59 | 9.67% | - | - | - |
| 6 | Climatology quantiles | - | 0 | 22.185 | 40.77 | 13.61% | 7.625 | 117.83 | 71.4% |
| 7 | Last value | - | 1 | 25.297 | 38.66 | 15.67% | - | - | - |

## PEMS08 · Track B: open context (up to 512 steps)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | STAEformer (CIKM'23, official code) | 1.22M | 12 | 13.929 | 23.17 | 9.36% | - | - | - |
| 2 | PWM-Dyn v0.7 online (3-seed, CQR) | 0.32M | 312 | 14.002 | 23.22 | 9.15% | 4.553 | 66.57 | 80.1% |
| 3 | STID (CIKM'22, official code) | 0.12M | 12 | 14.182 | 23.21 | 9.27% | - | - | - |
| 4 | PWM-Dyn v0.6-LC (3-seed, CQR) | 0.32M | 300 | 14.184 | 23.38 | 9.27% | 4.595 | 66.94 | 79.8% |
| 5 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | - | 512 | 14.549 | 23.57 | 9.15% | 4.686 | 67.84 | 80.7% |
| 6 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 14.765 | 23.59 | 9.67% | - | - | - |
| 7 | TimesFM-2.5 (Google, 200M) (zero-shot, ctx 512) | - | 512 | 15.037 | 24.09 | 9.44% | 4.857 | 70.54 | 82.4% |
| 8 | Climatology quantiles | - | 0 | 22.185 | 40.77 | 13.61% | 7.625 | 117.83 | 71.4% |
| 9 | Last value | - | 1 | 25.297 | 38.66 | 15.67% | - | - | - |
| 10 | Seasonal naive | - | 300 | 36.543 | 60.77 | 24.62% | - | - | - |

## PEMS08 · Track R: 30% of sensors dark for the whole test period (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.7 (3-seed, CQR) | 0.32M | 12 | 18.857 | 33.68 | 13.14% | 6.568 | 102.76 | 75.7% |
| 2 | PWM-Dyn v0.6-LC (3-seed, CQR) | 0.32M | 300 | 19.245 | 34.80 | 12.75% | 6.618 | 102.32 | 76.3% |
| 3 | Climatology quantiles | - | 0 | 21.782 | 41.08 | 13.91% | 7.411 | 113.41 | 72.4% |
| 4 | STAEformer (CIKM'23, official code) | 1.22M | 12 | 186.512 | 233.65 | 79.95% | - | - | - |
| 5 | STID (CIKM'22, official code) | 0.12M | 12 | 198.091 | 239.66 | 85.31% | - | - | - |
| 6 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 216.206 | 260.58 | 91.97% | - | - | - |

## PEMS08 · Track G (new in 1.2): replayed real METR-LA outages on 30% of sensors per window (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.7 (3-seed, CQR) | 0.32M | 12 | 18.086 | 32.00 | 11.65% | 6.096 | 92.45 | 78.7% |
| 2 | Climatology quantiles | - | 0 | 22.260 | 41.02 | 13.56% | 7.653 | 118.29 | 71.4% |
| 3 | PWM-Dyn v0.6 (3-seed, CQR) | 0.32M | 12 | 23.028 | 37.41 | 19.75% | 7.602 | 112.92 | 79.5% |
| 4 | Last observed value (climatology if none) | - | 12 | 29.173 | 45.95 | 17.99% | - | - | - |

## PEMS04 · Track A: standard 12-step context

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 0.33M | 12 | 18.459 | 30.77 | 12.69% | 5.951 | 86.23 | 80.0% |
| 2 | STID (CIKM'22, official code) | 0.12M | 12 | 18.491 | 30.05 | 12.46% | - | - | - |
| 3 | PWM-Dyn v0.7 (3-seed, CQR) | 0.33M | 12 | 18.534 | 31.02 | 13.00% | 5.977 | 86.64 | 79.6% |
| 4 | STAEformer (CIKM'23, official code) | 1.35M | 12 | 19.206 | 30.66 | 12.92% | - | - | - |
| 5 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 19.368 | 30.75 | 14.61% | - | - | - |
| 6 | Climatology quantiles | - | 0 | 25.022 | 41.36 | 16.13% | 8.431 | 127.81 | 71.5% |
| 7 | Last value | - | 1 | 31.556 | 48.25 | 21.33% | - | - | - |

## PEMS04 · Track B: open context (up to 512 steps)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.7 online (3-seed, CQR) | 0.33M | 312 | 18.332 | 30.29 | 12.81% | 5.900 | 85.35 | 79.8% |
| 2 | PWM-Dyn v0.6 (3-seed, CQR) | 0.33M | 12 | 18.459 | 30.77 | 12.69% | 5.951 | 86.23 | 80.0% |
| 3 | STID (CIKM'22, official code) | 0.12M | 12 | 18.491 | 30.05 | 12.46% | - | - | - |
| 4 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | - | 512 | 19.135 | 31.02 | 12.60% | 6.137 | 88.42 | 80.7% |
| 5 | STAEformer (CIKM'23, official code) | 1.35M | 12 | 19.206 | 30.66 | 12.92% | - | - | - |
| 6 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 19.368 | 30.75 | 14.61% | - | - | - |
| 7 | TimesFM-2.5 (Google, 200M) (zero-shot, ctx 512) | - | 512 | 19.702 | 31.70 | 13.22% | 6.337 | 91.61 | 82.0% |
| 8 | Climatology quantiles | - | 0 | 25.022 | 41.36 | 16.13% | 8.431 | 127.81 | 71.5% |
| 9 | Last value | - | 1 | 31.556 | 48.25 | 21.33% | - | - | - |
| 10 | Seasonal naive | - | 300 | 40.672 | 66.64 | 27.06% | - | - | - |

## PEMS04 · Track R: 30% of sensors dark for the whole test period (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 0.33M | 12 | 25.329 | 42.62 | 16.91% | 8.402 | 125.41 | 78.3% |
| 2 | PWM-Dyn v0.7 (3-seed, CQR) | 0.33M | 12 | 25.420 | 43.10 | 18.14% | 8.524 | 128.62 | 78.1% |
| 3 | Climatology quantiles | - | 0 | 27.387 | 45.60 | 15.89% | 9.199 | 139.04 | 71.3% |
| 4 | STID (CIKM'22, official code) | 0.12M | 12 | 120.581 | 155.19 | 60.95% | - | - | - |
| 5 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 132.505 | 169.68 | 60.28% | - | - | - |
| 6 | STAEformer (CIKM'23, official code) | 1.35M | 12 | 187.997 | 238.99 | 75.21% | - | - | - |

## PEMS04 · Track G (new in 1.2): replayed real METR-LA outages on 30% of sensors per window (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.7 (3-seed, CQR) | 0.33M | 12 | 21.049 | 35.07 | 15.37% | 6.936 | 102.85 | 79.5% |
| 2 | PWM-Dyn v0.6 (3-seed, CQR) | 0.33M | 12 | 24.892 | 38.97 | 21.96% | 8.112 | 118.89 | 79.5% |
| 3 | Climatology quantiles | - | 0 | 25.016 | 41.38 | 16.13% | 8.430 | 127.81 | 71.6% |
| 4 | Last observed value (climatology if none) | - | 12 | 33.046 | 50.75 | 22.51% | - | - | - |

## PEMS03 · Track A: standard 12-step context

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 0.34M | 12 | 14.338 | 23.12 | 15.09% | 4.628 | 67.14 | 78.4% |
| 2 | PWM-Dyn v0.7 (3-seed, CQR) | 0.34M | 12 | 14.603 | 23.64 | 15.32% | 4.715 | 68.43 | 77.9% |
| 3 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 14.699 | 25.17 | 15.61% | - | - | - |
| 4 | STAEformer (CIKM'23, official code) | 1.40M | 12 | 15.446 | 26.03 | 17.75% | - | - | - |
| 5 | STID (CIKM'22, official code) | 0.12M | 12 | 15.498 | 26.83 | 16.59% | - | - | - |
| 6 | Last value | - | 1 | 23.887 | 37.31 | 22.86% | - | - | - |
| 7 | Climatology quantiles | - | 0 | 25.934 | 47.80 | 26.34% | 9.459 | 154.10 | 61.0% |

## PEMS03 · Track B: open context (up to 512 steps)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | - | 512 | 14.148 | 22.70 | 13.39% | 4.541 | 65.50 | 80.7% |
| 2 | PWM-Dyn v0.7 online (3-seed, CQR) | 0.34M | 312 | 14.268 | 22.94 | 15.12% | 4.605 | 66.81 | 78.4% |
| 3 | PWM-Dyn v0.6 (3-seed, CQR) | 0.34M | 12 | 14.338 | 23.12 | 15.09% | 4.628 | 67.14 | 78.4% |
| 4 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 14.699 | 25.17 | 15.61% | - | - | - |
| 5 | STAEformer (CIKM'23, official code) | 1.40M | 12 | 15.446 | 26.03 | 17.75% | - | - | - |
| 6 | STID (CIKM'22, official code) | 0.12M | 12 | 15.498 | 26.83 | 16.59% | - | - | - |
| 7 | Last value | - | 1 | 23.887 | 37.31 | 22.86% | - | - | - |
| 8 | Climatology quantiles | - | 0 | 25.934 | 47.80 | 26.34% | 9.459 | 154.10 | 61.0% |
| 9 | Seasonal naive | - | 300 | 30.283 | 56.17 | 27.05% | - | - | - |

## PEMS03 · Track R: 30% of sensors dark for the whole test period (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 0.34M | 12 | 17.711 | 27.94 | 25.78% | 5.784 | 84.96 | 77.7% |
| 2 | PWM-Dyn v0.7 (3-seed, CQR) | 0.34M | 12 | 19.142 | 31.01 | 22.54% | 6.424 | 97.01 | 74.4% |
| 3 | Climatology quantiles | - | 0 | 23.308 | 42.90 | 26.82% | 8.531 | 139.41 | 62.4% |
| 4 | STID (CIKM'22, official code) | 0.12M | 12 | 113.047 | 159.85 | 72.02% | - | - | - |
| 5 | STAEformer (CIKM'23, official code) | 1.40M | 12 | 119.341 | 172.78 | 67.33% | - | - | - |
| 6 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 138.366 | 190.00 | 83.16% | - | - | - |

## PEMS03 · Track G (new in 1.2): replayed real METR-LA outages on 30% of sensors per window (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.7 (3-seed, CQR) | 0.34M | 12 | 18.392 | 31.40 | 19.44% | 6.135 | 92.09 | 75.4% |
| 2 | PWM-Dyn v0.6 (3-seed, CQR) | 0.34M | 12 | 22.043 | 35.34 | 40.83% | 7.195 | 105.63 | 77.0% |
| 3 | Climatology quantiles | - | 0 | 26.068 | 48.30 | 26.51% | 9.519 | 155.23 | 61.1% |
| 4 | Last observed value (climatology if none) | - | 12 | 29.711 | 48.86 | 28.45% | - | - | - |

## PEMS07 · Track A: standard 12-step context

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 0.41M | 12 | 19.563 | 32.60 | 8.17% | 6.394 | 93.99 | 79.9% |
| 2 | STID (CIKM'22, official code) | 0.14M | 12 | 19.615 | 32.72 | 8.35% | - | - | - |
| 3 | PWM-Dyn v0.7 (3-seed, CQR) | 0.41M | 12 | 19.778 | 32.84 | 8.29% | 6.457 | 94.81 | 79.8% |
| 4 | Graph WaveNet (IJCAI'19, official code) | 0.32M | 12 | 23.389 | 36.92 | 10.06% | - | - | - |
| 5 | Climatology quantiles | - | 0 | 29.977 | 58.67 | 12.45% | 10.319 | 159.70 | 76.2% |
| 6 | Last value | - | 1 | 35.634 | 54.37 | 15.55% | - | - | - |

## PEMS07 · Track B: open context (up to 512 steps)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 0.41M | 12 | 19.563 | 32.60 | 8.17% | 6.394 | 93.99 | 79.9% |
| 2 | PWM-Dyn v0.7 online (3-seed, CQR) | 0.41M | 312 | 19.605 | 32.60 | 8.22% | 6.405 | 94.14 | 79.8% |
| 3 | STID (CIKM'22, official code) | 0.14M | 12 | 19.615 | 32.72 | 8.35% | - | - | - |
| 4 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | - | 512 | 20.270 | 33.13 | 8.47% | 6.556 | 95.32 | 81.0% |
| 5 | Graph WaveNet (IJCAI'19, official code) | 0.32M | 12 | 23.389 | 36.92 | 10.06% | - | - | - |
| 6 | Climatology quantiles | - | 0 | 29.977 | 58.67 | 12.45% | 10.319 | 159.70 | 76.2% |
| 7 | Last value | - | 1 | 35.634 | 54.37 | 15.55% | - | - | - |
| 8 | Seasonal naive | - | 300 | 46.770 | 76.07 | 20.64% | - | - | - |

## PEMS07 · Track R: 30% of sensors dark for the whole test period (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.7 (3-seed, CQR) | 0.41M | 12 | 28.347 | 53.93 | 12.20% | 9.873 | 154.46 | 78.8% |
| 2 | Climatology quantiles | - | 0 | 29.096 | 56.07 | 12.50% | 10.142 | 158.77 | 77.0% |
| 3 | PWM-Dyn v0.6 (3-seed, CQR) | 0.41M | 12 | 30.952 | 55.63 | 15.51% | 10.533 | 161.22 | 79.2% |
| 4 | STID (CIKM'22, official code) | 0.14M | 12 | 293.028 | 346.25 | 92.19% | - | - | - |
| 5 | Graph WaveNet (IJCAI'19, official code) | 0.32M | 12 | 310.035 | 363.85 | 98.47% | - | - | - |

## PEMS07 · Track G (new in 1.2): replayed real METR-LA outages on 30% of sensors per window (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.7 (3-seed, CQR) | 0.41M | 12 | 25.006 | 46.31 | 10.46% | 8.526 | 130.75 | 79.4% |
| 2 | Climatology quantiles | - | 0 | 30.025 | 58.60 | 12.44% | 10.341 | 160.10 | 76.2% |
| 3 | PWM-Dyn v0.6 (3-seed, CQR) | 0.41M | 12 | 31.716 | 53.45 | 18.41% | 10.640 | 160.62 | 79.4% |
| 4 | Last observed value (climatology if none) | - | 12 | 39.495 | 63.88 | 17.38% | - | - | - |

## METR-LA · Track A: standard 12-step context

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.7 (3-seed, CQR) | 0.32M | 12 | 2.918 | 5.87 | 7.91% | 0.964 | 14.33 | 80.3% |
| 2 | PWM-Dyn v0.6 (3-seed, CQR) | 0.32M | 12 | 2.919 | 5.88 | 7.97% | 0.965 | 14.34 | 80.6% |
| 3 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 3.047 | 6.15 | 8.28% | - | - | - |
| 4 | STAEformer (CIKM'23, official code) | 1.26M | 12 | 3.091 | 6.33 | 8.70% | - | - | - |
| 5 | STID (CIKM'22, official code) | 0.12M | 12 | 3.124 | 6.50 | 9.13% | - | - | - |
| 6 | Climatology quantiles | - | 0 | 3.899 | 8.41 | 12.48% | 1.297 | 19.42 | 75.3% |
| 7 | Last value | - | 1 | 5.038 | 10.98 | 12.22% | - | - | - |

## METR-LA · Track B: open context (up to 512 steps)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.7 (3-seed, CQR) | 0.32M | 312 | 2.918 | 5.87 | 7.91% | 0.964 | 14.33 | 80.3% |
| 2 | PWM-Dyn v0.6 (3-seed, CQR) | 0.32M | 12 | 2.919 | 5.88 | 7.97% | 0.965 | 14.34 | 80.6% |
| 3 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 3.047 | 6.15 | 8.28% | - | - | - |
| 4 | STAEformer (CIKM'23, official code) | 1.26M | 12 | 3.091 | 6.33 | 8.70% | - | - | - |
| 5 | STID (CIKM'22, official code) | 0.12M | 12 | 3.124 | 6.50 | 9.13% | - | - | - |
| 6 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | - | 512 | 3.401 | 6.97 | 9.75% | 1.146 | 17.37 | 81.3% |
| 7 | Climatology quantiles | - | 0 | 3.899 | 8.41 | 12.48% | 1.297 | 19.42 | 75.3% |
| 8 | Last value | - | 1 | 5.038 | 10.98 | 12.22% | - | - | - |
| 9 | Seasonal naive | - | 300 | 10.347 | 20.72 | 23.21% | - | - | - |

## METR-LA · Track R: 30% of sensors dark for the whole test period (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 0.32M | 12 | 3.364 | 6.69 | 9.51% | 1.116 | 16.66 | 80.6% |
| 2 | PWM-Dyn v0.7 (3-seed, CQR) | 0.32M | 12 | 3.486 | 6.94 | 10.12% | 1.178 | 17.92 | 81.3% |
| 3 | Climatology quantiles | - | 0 | 4.074 | 8.76 | 13.36% | 1.354 | 20.26 | 75.0% |
| 4 | STID (CIKM'22, official code) | 0.12M | 12 | 5.111 | 10.05 | 16.52% | - | - | - |
| 5 | STAEformer (CIKM'23, official code) | 1.26M | 12 | 5.328 | 10.35 | 16.86% | - | - | - |
| 6 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 5.889 | 10.69 | 19.24% | - | - | - |

## METR-LA · Track G (new in 1.2): replayed real METR-LA outages on 30% of sensors per window (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 0.32M | 12 | 3.101 | 6.17 | 8.46% | 1.025 | 15.24 | 80.5% |
| 2 | PWM-Dyn v0.7 (3-seed, CQR) | 0.32M | 12 | 3.147 | 6.30 | 8.74% | 1.052 | 15.82 | 80.8% |
| 3 | Climatology quantiles | - | 0 | 3.894 | 8.41 | 12.46% | 1.295 | 19.38 | 75.3% |
| 4 | Last observed value (climatology if none) | - | 12 | 4.359 | 8.86 | 12.57% | - | - | - |

## PEMS-BAY · Track A: standard 12-step context

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 0.34M | 12 | 1.519 | 3.45 | 3.34% | 0.504 | 7.54 | 79.4% |
| 2 | PWM-Dyn v0.7 (3-seed, CQR) | 0.34M | 12 | 1.533 | 3.47 | 3.40% | 0.509 | 7.60 | 79.1% |
| 3 | STID (CIKM'22, official code) | 0.12M | 12 | 1.561 | 3.60 | 3.54% | - | - | - |
| 4 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 1.569 | 3.57 | 3.48% | - | - | - |
| 5 | STAEformer (CIKM'23, official code) | 1.37M | 12 | 1.595 | 3.63 | 3.60% | - | - | - |
| 6 | Last value | - | 1 | 2.171 | 5.11 | 4.64% | - | - | - |
| 7 | Climatology quantiles | - | 0 | 2.533 | 5.48 | 5.96% | 0.862 | 13.19 | 74.7% |

## PEMS-BAY · Track B: open context (up to 512 steps)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 0.34M | 12 | 1.519 | 3.45 | 3.34% | 0.504 | 7.54 | 79.4% |
| 2 | PWM-Dyn v0.7 (3-seed, CQR) | 0.34M | 312 | 1.533 | 3.47 | 3.40% | 0.509 | 7.60 | 79.1% |
| 3 | STID (CIKM'22, official code) | 0.12M | 12 | 1.561 | 3.60 | 3.54% | - | - | - |
| 4 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 1.569 | 3.57 | 3.48% | - | - | - |
| 5 | STAEformer (CIKM'23, official code) | 1.37M | 12 | 1.595 | 3.63 | 3.60% | - | - | - |
| 6 | TimesFM-3.0 (Google) multivariate (zero-shot, ctx 512) | - | 512 | 1.661 | 3.95 | 3.77% | 0.553 | 8.29 | 81.0% |
| 7 | Last value | - | 1 | 2.171 | 5.11 | 4.64% | - | - | - |
| 8 | Climatology quantiles | - | 0 | 2.533 | 5.48 | 5.96% | 0.862 | 13.19 | 74.7% |
| 9 | Seasonal naive | - | 300 | 3.368 | 7.73 | 7.74% | - | - | - |

## PEMS-BAY · Track R: 30% of sensors dark for the whole test period (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.6 (3-seed, CQR) | 0.34M | 12 | 2.306 | 5.04 | 5.66% | 0.812 | 12.82 | 78.5% |
| 2 | PWM-Dyn v0.7 (3-seed, CQR) | 0.34M | 12 | 2.390 | 5.21 | 5.93% | 0.855 | 13.68 | 77.7% |
| 3 | Climatology quantiles | - | 0 | 2.708 | 6.05 | 6.88% | 0.927 | 14.28 | 74.8% |
| 4 | STID (CIKM'22, official code) | 0.12M | 12 | 42.192 | 45.92 | 68.07% | - | - | - |
| 5 | STAEformer (CIKM'23, official code) | 1.37M | 12 | 44.718 | 46.22 | 71.00% | - | - | - |
| 6 | Graph WaveNet (IJCAI'19, official code) | 0.31M | 12 | 51.758 | 53.17 | 82.76% | - | - | - |

## PEMS-BAY · Track G (new in 1.2): replayed real METR-LA outages on 30% of sensors per window (scored on those sensors)

| # | Model | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PWM-Dyn v0.7 (3-seed, CQR) | 0.34M | 12 | 1.959 | 4.20 | 4.42% | 0.672 | 10.37 | 78.1% |
| 2 | PWM-Dyn v0.6 (3-seed, CQR) | 0.34M | 12 | 2.196 | 4.66 | 5.09% | 0.743 | 11.32 | 78.5% |
| 3 | Climatology quantiles | - | 0 | 2.531 | 5.47 | 5.98% | 0.861 | 13.18 | 74.7% |
| 4 | Last observed value (climatology if none) | - | 12 | 2.662 | 5.96 | 6.05% | - | - | - |
