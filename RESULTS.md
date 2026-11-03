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

## 2. ParadoxBench-1: PWM-Dyn v0.4 / v0.4.1 vs TimesFM 2.5 / 3.0 (Kaggle, 2026-11-01)

Official test windows (every 2nd). Every PWM-Dyn row is a 3-seed ensemble with split-conformal
calibration fitted on validation. Full per-track tables with MAPE: [results/LEADERBOARD.md](results/LEADERBOARD.md);
machine-readable: [results/paradoxbench1_results.json](results/paradoxbench1_results.json).

### Track B — open context (where the foundation models compete), MAE

| Model | Params | Context | PEMS08 | PEMS04 | IMD-CI | IMD-WC |
|---|---|---|---|---|---|---|
| **PWM-Dyn v0.4.1** | 0.3 M | 300 / 12 steps | **14.15** | **19.02** | — | — |
| PWM-Dyn v0.4 | 0.3–0.4 M | 300 steps / 30 days | 14.38 | 19.17 | **2.84** | **3.41** |
| TimesFM 3.0 multivariate (Google, zero-shot) | not stated | 512 / 365 | 14.55 | 19.13 | 2.92 | 3.62 |
| TimesFM 2.5 (Google, zero-shot) | 200 M | 512 / 365 | 15.04 | 19.70 | 2.96 | 3.67 |
| Climatology quantiles | 0 | — | 22.18 | 25.02 | 2.89 | 3.65 |
| Last value | 0 | 1 | 25.30 | 31.56 | 4.37 | 4.88 |

### Track B — interval score IS80 (80 % coverage)

| Model | PEMS08 | PEMS04 | IMD-CI | IMD-WC |
|---|---|---|---|---|
| **PWM-Dyn v0.4.1** | **67.05** (79.5 %) | **87.90** (79.8 %) | — | — |
| PWM-Dyn v0.4 | 67.91 (79.7 %) | 88.16 (80.0 %) | **18.01** (84.7 %) | **20.27** (82.9 %) |
| TimesFM 3.0 multivariate | 67.84 (80.7 %) | 88.42 (80.7 %) | 19.79 (86.3 %) | 21.85 (87.2 %) |
| TimesFM 2.5 | 70.54 (82.4 %) | 91.61 (82.0 %) | 20.72 (84.3 %) | 23.00 (85.2 %) |

PWM-Dyn has lower MAE, pinball loss and interval score than both TimesFM models on all four tasks.
TimesFM 3.0 keeps a 2.5 % lower RMSE on PEMS04, and PWM's 0.6 % MAE lead there is inside its own seed
spread, so PEMS04 is a tie on point accuracy. Conformal calibration fixed v0.3's rainfall coverage
(54.7 % → 84.7 %).

### Other tracks (MAE · IS80 · coverage)

| Task / track | PWM-Dyn v0.4 | PWM-Dyn v0.4.1 | Best baseline |
|---|---|---|---|
| PEMS08 A (12-step context) | 14.53 · 68.94 · 79.7 % | 14.50 · 68.39 · 79.7 % | climatology 22.18 · 117.83 · 71.4 % |
| PEMS04 A | 19.21 · 88.65 · 79.6 % | 19.02 · 87.90 · 79.8 % | climatology 25.02 · 127.81 · 71.5 % |
| PEMS08 R (30 % sensors dark) | 18.70 · 100.61 · 76.8 % | 18.81 · 99.99 · 76.4 % | climatology 21.78 · 113.41 · 72.4 % |
| PEMS04 R | 24.99 · 129.58 · 78.1 % | 24.69 · 126.27 · 78.0 % | climatology 27.39 · 139.04 · 71.3 % |
| IMD-CI A/R | 2.84 · 18.01 · 84.7 % / 2.84 · 17.99 · 85.5 % | — | climatology 2.89 / 2.88 |
| IMD-WC A/R | 3.41 · 20.27 · 82.9 % / 3.43 · 20.75 · 83.2 % | — | climatology 3.65 / 3.60 |
| PEMS08 Z (trained on PEMS04 only) | 16.36 · 83.47 · 86.7 % | 16.57 · 82.58 · 85.3 % | none admissible |

### Honest notes

- **v0.4.1 exists because of a test-set observation.** v0.4's traffic test MAE came out above v0.3's;
  v0.4 had halved the training steps. v0.4.1 lets PEMS08 *validation* pick the recipe (v0.4: 14.485,
  v0.3: 14.601, v0.3 with 100 epochs: 14.443 → chosen); the architecture is unchanged.
- **v0.5 was stopped.** A validation sweep over 100 epochs, a coarse profile input and width 128 landed
  within 0.6 % of the 40-epoch model on both domains; no v0.5 model is reported.
- **Under the standard 12-step context, v0.4/v0.4.1 do not recover v0.3** (PEMS08 14.50 vs 14.18;
  PEMS04 19.02 vs 18.50). The cause is not yet isolated.
- **PEMS08 Tracks B and R are not fully blind:** development checkpoints were scored on those test windows
  while designing v0.4 (see paper §6.2). Rainfall test windows were never scored during development.
- **Generality still belongs to TimesFM:** zero-shot on PEMS08 it scores 14.55; PWM trained on PEMS04 and
  transferred scores 16.36.

### Where each number came from

| Run | Hardware | Date | Rows |
|---|---|---|---|
| Kaggle `notebook0387a11c3a`, version 364310290 (`v0.4-paradoxbench/notebooks/kaggle_paradoxbench_v04.ipynb`) | 2× T4, 254.6 min | 2026-11-01 | all v0.4 rows, TimesFM 2.5 / 3.0, baselines; provenance PASS |
| Kaggle `notebookab27dd6f3e`, version 364348754 (`v0.4-paradoxbench/notebooks/kaggle_pwm_v041.ipynb`) | 2× T4, 93.1 min | 2026-11-01 | all v0.4.1 rows; provenance PASS |

## 3. ParadoxBench-1.1: PWM-Dyn v0.6 vs published specialists and TimesFM (Kaggle, 2026-11-02/03)

This round answers six reviewer-style concerns: specialists re-run with their authors' code, four new
traffic networks, the v0.4 accuracy gap, seeds and significance tests, PEMS08 test exposure, and the
paper in conference format. Paper: [`paper-conference/named/PWM-Dyn_ParadoxBench_v0.6.pdf`](paper-conference/named/PWM-Dyn_ParadoxBench_v0.6.pdf).

**Protocol.** The v0.6 configuration ("noclim-vs1": no climatology input, batch 32, peak LR 2e-3, a fixed
budget of ~33.5k steps, checkpoint chosen on all validation windows) was frozen from a validation-only
ablation before any test score was computed. The reported models use fresh seeds 100–102, which were never
used in development. PEMS03, PEMS07, METR-LA and PEMS-BAY were never touched during development. STID
(e8b313b), Graph WaveNet (6b162e8) and STAEformer (fc49d39) were trained with their official code and
published hyper-parameters on our exact windows, with one seed and a wall-clock budget on one T4 GPU.
† means the budget stopped the run before its authors' schedule ended.

Track A test MAE (lower is better):

| Network | PWM-Dyn v0.6 (3 seeds) | STID | Graph WaveNet | STAEformer | TimesFM 3.0 (Track B, zero-shot) |
|---|---|---|---|---|---|
| PEMS08 | 14.12 | 14.18 | 14.77 | **13.93**† | 14.55 |
| PEMS04 | **18.46** | 18.49 | 19.37† | 19.21† | 19.13 |
| PEMS03 | 14.34 | 15.50 | 14.70† | 15.45† | **14.15** |
| PEMS07 | **19.56** | 19.62† | 23.39† | out of memory | 20.27 |
| METR-LA | **2.92** | 3.12 | 3.05† | 3.09† | 3.40 |
| PEMS-BAY | **1.52** | 1.56† | 1.57† | 1.60† | 1.66 |

**Significance.** We use a Diebold–Mariano test with Newey–West variance and a one-day bandwidth, plus a
day-block bootstrap with 2,000 resamples. A difference counts as significant only if p < 0.05 and the 95%
bootstrap interval excludes 0.

- PWM-Dyn vs STID is a tie on PEMS08 (p = 0.12) and PEMS04 (p = 0.82).
- STAEformer's lead on PEMS08 is significant.
- On PEMS08 Track B, PWM-Dyn's long-context variant (14.18) vs TimesFM 3.0 (14.55) is not significant (p = 0.064). On PEMS04 it is significant (p = 0.029).

Every test is in
[`v0.6-conference/results/v06_rows_and_tests.txt`](v0.6-conference/results/v06_rows_and_tests.txt).

**What changed and what did not.**
- The v0.4 loss came from the climatology input. Without it, PEMS08 scores 14.12 and PEMS04 18.46, slightly better than v0.3 (14.18 / 18.50).
- Single PWM-Dyn seeds are slightly worse than single STID runs on PEMS08, PEMS04 and PEMS07, so part of the margin comes from ensembling.
- In the dead-sensor setting (Track R, 30% of sensors dark), PWM-Dyn beats per-sensor climatology on 7 of 8 tasks. It loses on PEMS07 (30.95 vs 29.10). Specialists without a missing-data mechanism collapse.
- TimesFM 3.0 zero-shot wins on PEMS03.
- Rainfall entries are still from v0.4.

Full per-track tables: [`results/LEADERBOARD_1.1.md`](results/LEADERBOARD_1.1.md); every row as JSON:
[`results/paradoxbench1.1_results.json`](results/paradoxbench1.1_results.json).

## Limitations

PWM-Dyn wins as a regional specialist trained on each network's own history; TimesFM has never seen
that data. A PWM win is therefore a specialist-vs-zero-shot result, not evidence that PWM is a better
general model. See Section 7 of the paper.
