# PWM-Dyn v0.6 and ParadoxBench-1.1 — the conference study

This folder is the code for the study behind the conference version of the paper. It answers the six points
a reviewer would raise about the v0.4 results:

| Reviewer point | What this study does |
|---|---|
| Specialists were quoted, not run | `opponents/run_specialists.py` trains **STID**, **Graph WaveNet** and **STAEformer** with their authors' own model code and published hyper-parameters on each task's training split, and scores them on exactly the ParadoxBench windows |
| Two traffic networks is thin | ParadoxBench-1.1 adds **PEMS03, PEMS07, METR-LA and PEMS-BAY** (`tools/prepare_traffic_data.py`, built from public sources at run time; nothing is re-hosted) |
| v0.4 lost to v0.3 under the 12-step context | `run_v06_pwm.py` stage 1: a validation-only ablation of the three v0.4 changes, then one frozen configuration |
| Are the wins noise? | every PWM-Dyn entry reports each seed's test MAE; `paradoxbench/significance.py` runs Diebold–Mariano tests (Newey–West, one-day bandwidth) and a day-block bootstrap on per-window errors |
| PEMS08 Tracks B/R were not blind | the frozen configuration is trained with **fresh seeds (100–102)** and scored once; the four new networks were never touched during development |
| Format | the anonymous conference paper is built from these results (`paper-conference/` in the repository) |

## Run it (Kaggle, GPU T4 ×2, Internet on)

```bash
git clone --depth 1 -b v0.6 https://github.com/paradoxailab/paradox-world-model && cd paradox-world-model/v0.6-conference
# session 1: PWM-Dyn
python tools/fetch_all.py && python run_v06_pwm.py --budget_hours 7
# session 2: opponents (TimesFM 3.0 needs `pip install timesfm`; STAEformer needs `pip install torchinfo`)
python tools/fetch_all.py --opponents && python run_v06_opponents.py --budget_hours 8
# analysis (CPU): merge both sessions and the v0.4 study's TimesFM forecasts, tables and significance tests
python run_v06_analysis.py --roots <session-1 folder> <session-2 folder> <v0.4 folder>
```

`--quick` on either driver checks the whole pipeline on CPU in a few minutes.

## Rules kept from v0.4

- Test windows are scored once, after every choice has been made on validation.
- PWM-Dyn's code imports no external model library; `check_provenance.py` audits code and checkpoints.
- Opponents run with their own code; nothing of theirs is copied into this folder. The one compatibility change
  (Graph WaveNet's `nn.Conv1d` layers with 2-D kernels, rejected by PyTorch ≥ 1.11, are built as `nn.Conv2d`) is
  stated in `opponents/run_specialists.py`.
- TimesFM 3.0 weights are non-commercial research-only and are used for evaluation only.

## Results (Kaggle, 2026-11-02/03)

Runs: PWM-Dyn session `notebookd0ba070ac4` (278.9 min, provenance PASS), opponents session `notebook3ca2e4ffce`
(387.0 min), analysis `notebook9add0bcba5` (CPU). Every scored row and every paired test, exactly as printed by
`run_v06_analysis.py`: [`results/v06_rows_and_tests.txt`](results/v06_rows_and_tests.txt).

Track A (12-step context, trained on the task), test MAE; † = stopped by its wall-clock budget:

| Network | PWM-Dyn v0.6 | STID | Graph WaveNet | STAEformer | TimesFM 3.0 (Track B, zero-shot) |
|---|---|---|---|---|---|
| PEMS08 | 14.12 | 14.18 | 14.77 | **13.93**† | 14.55 |
| PEMS04 | **18.46** | 18.49 | 19.37† | 19.21† | 19.13 |
| PEMS03 (new) | 14.34 | 15.50 | 14.70† | 15.45† | **14.15** |
| PEMS07 (new) | **19.56** | 19.62† | 23.39† | out of memory | 20.27 |
| METR-LA (new) | **2.92** | 3.12 | 3.05† | 3.09† | 3.40 |
| PEMS-BAY (new) | **1.52** | 1.56† | 1.57† | 1.60† | 1.66 |

- **v0.3 gap:** the climatology input was the cause; the validation-chosen configuration without it scores 14.12 / 18.46
  on PEMS08 / PEMS04 (v0.3: 14.18 / 18.50).
- **Significance:** PWM-Dyn vs STID is a statistical tie on PEMS08 (p = 0.12) and PEMS04 (p = 0.82); significant on
  METR-LA, PEMS-BAY, PEMS03. STAEformer's PEMS08 lead is significant. vs TimesFM 3.0: significant on PEMS04, PEMS07,
  METR-LA, PEMS-BAY; PEMS08 p = 0.06; TimesFM ahead on PEMS03 (not significant).
- **Seeds:** single-seed SD 0.002–0.22 MAE; the ensemble beats every seed on every network.
