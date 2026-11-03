# ParadoxBench-1 — Paradox Physical-Dynamics Benchmark, version 1

ParadoxBench-1 measures how well a model forecasts physical quantities that evolve and spread over real
networks — highway traffic in the US and monsoon rainfall in India — and whether its uncertainty
is honest. It scores task-trained specialists and zero-shot foundation models with one scorer, on
one frozen set of test windows.

## Tasks

| Task | Data | Locations | Step | Forecast | Standard context | Open context | Split |
|---|---|---|---|---|---|---|---|
| PEMS08 | Caltrans PeMS District 8 flow | 170 sensors | 5 min | 12 steps (1 h) | 12 | 512 | chronological 60/20/20 |
| PEMS04 | Caltrans PeMS District 4 flow | 307 sensors | 5 min | 12 steps (1 h) | 12 | 512 | chronological 60/20/20 |
| IMD-CI | IMD 0.25° gridded rainfall, central India (21–26.75 N, 74–82.75 E) | land cells with > 90 % coverage | 1 day | 7 days | 30 | 365 | 2000–2018 train, 2019–2021 val, 2022–2024 test |
| IMD-WC | IMD 0.25° gridded rainfall, Konkan / Western Ghats (14–20.75 N, 72.5–76.25 E) | land cells with > 90 % coverage | 1 day | 7 days | 30 | 365 | as IMD-CI |

Traffic metrics exclude zero readings (sensor outages), the standard PeMS protocol. Rainfall keeps
zeros: a dry day is a real observation.

## Tracks

- **A — Standard.** Look-back ≤ the standard context. Training on the task's train split only.
- **B — Open context.** Look-back ≤ 512 steps / 365 days. Pretrained foundation models compete here zero-shot.
- **R — Robustness.** 30 % of locations (fixed: `numpy.random.default_rng(2026).permutation(N)[:round(0.3 N)]`)
  have no observations during the test period. Models must still forecast them; scored on those locations only.
- **Z — Zero-shot transfer.** Forecast PEMS08 with a model that has seen no PEMS08 data at all — not its
  training split, not its normalisation statistics, not its validation split for calibration.

## Official windows

Every 2nd test window (`STRIDE = 2`), all models, all tracks. Submissions are `.npz` files with
`q10`, `q50`, `q90` arrays of shape `[windows, horizon, locations]` in real units.

## Metrics (one scorer: `paradoxbench/metrics.py`)

| Metric | Meaning | Better |
|---|---|---|
| MAE, RMSE | error of the median forecast q50 | lower |
| MAPE | MAE relative to the truth, non-zero truths only | lower |
| QL | mean pinball loss over the 10/50/90 % quantiles (proper scoring rule; 2·QL ≈ CRPS) | lower |
| IS80 | interval (Winkler) score of [q10, q90]: width + 10 × miss below + 10 × miss above | lower |
| COV80 | share of truths inside [q10, q90] | close to 80 % |

MAE is the headline point metric; IS80 is the headline uncertainty metric. A model that only gives a
point forecast is ranked on MAE/RMSE and shows "–" for the rest.

## Rules

1. No test-period data in training, model selection, early stopping or calibration.
2. Validation-period data may be used for selection and calibration (except Track Z, which may use only
   the source task).
3. Report parameters, look-back actually used, and what the model was trained on.
4. Submissions are scored by `python -m paradoxbench.score`; the `.npz` and its SHA-256 are kept with the result.

## ParadoxBench-1.1 (2026-11-03)

Version 1.1 adds four traffic tasks. Nothing about the four ParadoxBench-1 tasks changes, so their results stay valid.

| Task | Data | Locations | Split | Official windows |
|---|---|---|---|---|
| PEMS03 | Caltrans District 3 flow, 5-min, Sep–Nov 2018 | 358 sensors | chronological 60/20/20 | every 6th test window |
| PEMS07 | Caltrans District 7 flow, 5-min, May–Aug 2017 | 883 sensors | chronological 60/20/20 | every 6th |
| METR-LA | Los Angeles loop-detector speed (mph), 5-min, Mar–Jun 2012 | 207 sensors | chronological 70/10/20 | every 6th |
| PEMS-BAY | Bay Area loop-detector speed (mph), 5-min, Jan–May 2017 | 325 sensors | chronological 70/10/20 | every 6th |

All four use 12 → 12 steps, a standard context of 12 steps and an open context of 512. Values and time features
come from the STAEformer repository's copies of the published datasets; road graphs come from the ASTGNN
distance files (PEMS03/07) and the DCRNN adjacency (METR-LA/PEMS-BAY). `tools/prepare_traffic_data.py` builds
them at run time, so nothing is re-hosted. Targets of exactly 0 are excluded from every metric, as in the
literature. The new tasks use every 6th test window (every 30 minutes) so that zero-shot foundation models can be
run on all of them on one free GPU; every model on a task is scored on that task's same windows.

## ParadoxBench-1.2 (2026-11-04): Track G, real-outage replay

All 1.1 tasks, windows, tracks and metrics are unchanged. Track G (traffic tasks): in each official test window,
30% of locations (re-drawn per window, `GAP_SEED = 2027`) have their 12-step input replaced by a real outage
pattern, drawn uniformly from all 12-step METR-LA detector windows of METR-LA's training split that contain at
least one missing reading (513,184 patterns; 53% fully dark, 69% include the latest step). Readings missing in the
original data stay missing. Scored on the affected locations only, with the same metrics. Model selection may use
the validation counterpart (`VAL_SEED = 7`), never the test draws.
