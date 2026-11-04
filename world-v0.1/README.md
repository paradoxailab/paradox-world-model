# Paradox World Model v0.1 (PWM-W): a data-efficient world model for road networks

**Research question.** Can a compact world model learn more predictive information from fewer observations by
combining self-supervision, sparse experts, hierarchical spatial representation, physics constraints and
selective data? And can one such model, pretrained only on public US networks, forecast a network it has never
seen (London's motorways, live 2025-26 data) against Google's and Amazon's time-series foundation models?

This is a research study, not a claim. Every component is tested on its own at equal compute, kept only by
validation rules fixed in `run_world.py` before the run, and the final model is scored once on test with
significance tests.

## The model

| Part | What it is | Where |
|---|---|---|
| Inductive sensor tokens | every sensor is a token built from its own history, scaled by its own past-week mean; no per-sensor memory, so it runs on any network | `pw/model.py` |
| Hierarchical spatial representation | attention heads at different graph ranges (self, 1-hop, 2-hop, global), plus region tokens (spectral clusters of the road graph) and a global token | `Block` |
| Sparse world experts | feed-forward layers as 4 experts with top-1 routing per sensor token (same active parameters as dense) | `Experts` |
| Self-supervised learning | masked modelling: 30% of history cells and 15% of whole sensor windows hidden and reconstructed | `pw/train.py: ssl_mask` |
| Physics-informed loss | flow conservation: linked detectors whose train-split flow ratio is nearly constant must keep that ratio in the forecast | `physics_loss` |
| Mixed precision | FP16 autocast + gradient scaling (compared with FP32) | `train` |
| Active learning | training windows chosen by model uncertainty (interval width) vs at random, same budget | `run_world.py` step 5D |
| Uncertainty | 10/50/90% quantiles, split-conformal calibration on validation | `pw/evaluate.py` |
| Real-world robustness | trained with whole-sensor dropout and bursts of missing readings | `augment` |

## Data (all public, nothing re-hosted)

* **Pretraining (foundation)**: the TRAIN split of PEMS03, PEMS04, PEMS07, PEMS08 (flow), METR-LA, PEMS-BAY (speed),
  resampled to 15 minutes.
* **Target (never seen in pretraining)**: UK-M25, National Highways WebTRIS, sites in the London orbital box,
  2025-07-01 to 2026-06-30, 15-minute volumes and speeds with real outages left in, plus Open-Meteo hourly weather
  (used only up to the forecast origin). 20% of UK sensors are held out of all UK training (Track U).

## Tracks and metrics

* **S**: seen sensors, clean input. **U**: unseen locations (never trained on). **D**: seen sensors with 30% dark.
* Next 15/30/45/60 minutes. MAE, RMSE, MAPE (truth >= 20 vehicles), QL, IS80, COV80.
* Significance: Diebold-Mariano (Newey-West, one-day bandwidth) and day-block bootstrap; a result counts only if
  p < 0.05 and the 95% interval excludes zero.

## Opponents (zero-shot, same windows, 1,024-step history each, same conformal calibration)

TimesFM 2.5 (Google, Apache-2.0), TimesFM 3.0 (Google, non-commercial licence: evaluation only), Chronos-Bolt
base and Chronos-2 (Amazon, Apache-2.0). Large language models (ChatGPT, Claude) are not time-series forecasters
and are not in this comparison.

## Run (Google Colab or Kaggle, one T4 GPU, ~3.5 h)

```
!git clone -q -b world-v0.1 https://github.com/paradoxailab/paradox-world-model /content/repo
%cd /content/repo/world-v0.1
!pip install -q timesfm chronos-forecasting
!python tools/fetch_all.py
!python run_world.py 2>&1 | tee results/run.log
```

`python run_world.py --quick --opponents ""` checks the whole pipeline on a CPU in two minutes (numbers
meaningless). Results: `results/world_v01_results.json` and the generated `results/world_v01_report.md`.
