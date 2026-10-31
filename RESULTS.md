# Results

Every number below was produced by the code in this repository on real public data, scored by one
shared evaluation function on identical held-out test windows. Nothing is estimated.

## 1. PWM-Dyn v0.3 vs Google TimesFM (Colab + Kaggle, 2026-10-30/31)

MAE / RMSE / 80 % interval coverage. Traffic: vehicles per 5 minutes, zero readings excluded (standard
PeMS protocol). Rainfall: mm/day, dry days included.

| Dataset | Model | MAE | RMSE | 80 % coverage | PWM vs this model |
|---|---|---|---|---|---|
| PEMS08 | **PWM-Dyn v0.3, 3-seed ensemble (0.32 M params)** | **14.18** | 23.31 | 79.7 % | — |
| PEMS08 | TimesFM 2.5 (Google, 200 M), zero-shot, 512-step context | 15.04 | 24.11 | 82.4 % | PWM 5.7 % lower error |
| PEMS08 | TimesFM 3.0 univariate (Google), zero-shot | 14.63 | 23.69 | 81.2 % | PWM 3.1 % lower |
| PEMS08 | TimesFM 3.0 multivariate (Google), zero-shot | 14.55 | 23.59 | 80.7 % | PWM 2.6 % lower |
| PEMS04 | **PWM-Dyn v0.3, 3-seed ensemble (0.33 M)** | **18.50** | 30.41 | 79.8 % | — |
| PEMS04 | TimesFM 2.5 | 19.70 | 31.70 | 82.0 % | PWM 6.1 % lower |
| PEMS04 | TimesFM 3.0 multivariate | 19.14 | 31.02 | 80.7 % | PWM 3.3 % lower |
| IMD central India | **PWM-Dyn v0.3, 3-seed ensemble (0.30 M)** | **2.85** | 10.41 | 54.7 % | — |
| IMD central India | TimesFM 2.5, 365-day context | 2.96 | 10.58 | 84.3 % | PWM 3.9 % lower MAE; TimesFM better calibrated |
| IMD central India | TimesFM 3.0 multivariate | 2.92 | 10.65 | 86.3 % | PWM 2.5 % lower MAE; TimesFM better calibrated |

Published PEMS08 leaderboard (authors' own runs, quoted from the STAEformer paper, not re-run here):
STAEformer 13.46, PDFormer 13.58, **PWM-Dyn v0.3 14.18**, STID 14.21, Graph WaveNet 14.40, MTGNN 15.18,
DCRNN 15.22, GMAN 15.31, AGCRN 15.32, STGCN 16.08.

### Where each number came from

| Run | Hardware | Date | Rows produced |
|---|---|---|---|
| Google Colab, `v0.3-colab/PWM_Colab.ipynb` | Tesla T4 | 2026-10-30 | all PWM-Dyn rows; TimesFM 2.5 and 3.0 multivariate on PEMS08 |
| Kaggle, `v0.3-colab/notebooks/kaggle_opponents_2026-10-31.ipynb` | 2× Tesla T4, background run, 5 h 28 m | 2026-10-31 | TimesFM 3.0 univariate on PEMS08; TimesFM 2.5 and 3.0 multivariate on PEMS04 and IMD |

TimesFM rounds on PEMS04 and IMD used every 2nd test window (stride 2); the remaining rows used every window.

## 2. ParadoxBench-1 (PWM-Dyn v0.4 / v0.5 vs TimesFM, all four tracks)

In progress on Kaggle (2× T4). This section will hold the full leaderboard — MAE, RMSE, MAPE, pinball
loss (QL), interval score (IS80) and coverage — for PEMS08, PEMS04, IMD central India and IMD
Konkan/Western Ghats, on Tracks A (standard), B (open context), R (dead sensors) and Z (zero-shot transfer).

## Limitations

PWM-Dyn wins as a regional specialist trained on each network's own history; TimesFM has never seen
that data. A PWM win is therefore a specialist-vs-zero-shot result, not evidence that PWM is a better
general model. See Section 7 of the paper.
