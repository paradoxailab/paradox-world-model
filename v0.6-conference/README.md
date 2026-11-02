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
