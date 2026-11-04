# Paradox World Model v0.2 (PWM-W): scaled pretraining, two unseen cities

v0.1 (branch `world-v0.1`) showed that a 0.7M-parameter road-network model trained on one year of London data is
statistically level with TimesFM 3.0 and beats TimesFM 2.5, Chronos-Bolt and (mostly) Chronos-2, but that its own
foundation pretraining and the five efficiency techniques did not help. v0.2 attacks every limitation listed there.

| v0.1 limitation | v0.2 change |
|---|---|
| one test city | London (UK-M25, identical task) **and Greater Manchester (UK-MAN)**, live 2025-26 WebTRIS data, both never in pretraining |
| small pretraining set (6 US networks, 2016-18) | + 5 regional networks from the rest of England, 2024-07 .. 2026-03 (ends before any test window; both cities excluded with a 0.15 degree margin): ~7x more observed values |
| lost to TimesFM 3.0 / Chronos-2 at 60 min and on MAPE | long context (forecast times on each of the last 7 days, yesterday's lead-in, last 24 h hourly) and a relative-error loss, each kept only by a validation rule |
| techniques only tested at small scale | two foundation pretrainings at **equal wall-clock compute**: F-tech (sparse experts, masked self-supervision, physics, hierarchy) vs F-plain (none), chosen on held-out time of the England regions |
| fine-tuning hurt with a full year | gentler fine-tuning (lr 2e-4), final model chosen on validation among scratch / fine-tuned / mixed 3+3 ensembles |
| TimesFM 3.0 univariate only | TimesFM 3.0 univariate **and multivariate** (all sensors of a city together), Chronos-2 |

TimesFM 2.5 and Chronos-Bolt are not re-run: v0.1 beat both significantly on every metric and track.

## Run (Colab or Kaggle, one T4; ~40 min data + ~4.5 h study)

```
!git clone -q -b world-v0.2 https://github.com/paradoxailab/paradox-world-model /content/repo2
%cd /content/repo2/world-v0.2
!pip install -q timesfm chronos-forecasting
!python tools/fetch_all.py
!python run_world.py 2>&1 | tee results/run.log
```

`python run_world.py --quick --opponents ""` checks the pipeline on a CPU in two minutes. Results:
`results/world_v02_results.json` and the generated `results/world_v02_report.md` (written after every stage).
