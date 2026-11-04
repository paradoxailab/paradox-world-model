# Paradox World Model v0.1 (PWM-W): a data-efficient world model for road networks

**Research question.** Can a compact world model learn more predictive information from fewer observations by
combining self-supervision, sparse experts, hierarchical spatial representation, physics constraints and
selective data? And can one such model, pretrained only on public US networks, forecast a network it has never
seen (London's motorways, live 2025-26 data) against Google's and Amazon's time-series foundation models?

This is a research study, not a claim. Every component is tested on its own at equal compute, kept only by
validation rules fixed in `run_world.py` before the run, and the final model is scored once on test with
significance tests.

## Results (Google Colab, one T4 GPU, 187.5 min, run on 2026-11-04)

All numbers come from `results/world_v01_report.md`, which `run_world.py` generated from its results JSON.
Test: London motorways (UK-M25), 2026-04-19 .. 2026-06-30, every 2 h, next 15-60 min, vehicles per 15 minutes.

**PWM-W v0.1** (716,476 parameters, 3 seeds averaged, trained only on 12 months of London data, 1.3 min per seed,
4.3 ms per whole-network forecast) against the time-series foundation models, zero-shot, on the same windows:

| Track S (seen sensors) | MAE | RMSE | MAPE % | QL | IS80 |
|---|---|---|---|---|---|
| TimesFM 3.0 (Google) | **45.22** | 81.64 | **11.06** | 15.03 | 224.9 |
| **PWM-W v0.1** | 45.31 | **80.65** | 11.22 | **14.99** | **223.2** |
| Chronos-2 (Amazon, 120M) | 45.96 | 82.55 | 11.44 | 15.27 | 228.2 |
| TimesFM 2.5 (Google, 200M) | 47.09 | 83.61 | 11.56 | 15.69 | 235.3 |
| Chronos-Bolt (Amazon, 205M) | 48.76 | 86.01 | 11.79 | 16.29 | 244.9 |
| Last observed value | 80.54 | 133.77 | 19.62 | 28.69 | 458.0 |

Significance (PWM-W vs each model; WIN/LOSS only if p < 0.05 and the 95% interval excludes 0):

| | Track S: seen sensors | Track U: locations never trained on |
|---|---|---|
| vs Chronos-Bolt | 5 WIN | 5 WIN |
| vs TimesFM 2.5 | 5 WIN | 5 WIN |
| vs Chronos-2 | 4 WIN, 1 TIE (MAE -1.41%, p = 0.067) | 5 TIE |
| vs TimesFM 3.0 | 1 WIN (RMSE -1.21%), 1 LOSS (MAPE +1.44%), 3 TIE | 5 TIE |

Over 40 comparisons: **25 wins, 14 ties, 1 loss**. A model 170-290x smaller than the three opponents with a
published size, trained on one city's year of data, is statistically level with the strongest foundation model of 2026 and beats the others; it does not beat
TimesFM 3.0, and it loses to it on MAPE. With 30% of sensors dark (Track D) PWM-W's MAE rises to 48.16.

**The five efficiency techniques did not help at this scale** (each at equal compute vs the base model, kept only
if validation MAE improved by more than 2 sigma = 0.74; base 43.35):

| Technique | Validation MAE | Outcome |
|---|---|---|
| Self-supervised masked pretraining phase | 48.13 (14 days of data: 49.69 vs 47.32) | worse |
| Sparse experts (4, top-1, same active size) | 45.17 | worse, 2x slower |
| Physics: flow conservation (151 detector pairs) | 43.16 | no measurable effect |
| Mixed precision vs FP32 | 43.35 vs 43.17 | same accuracy; FP16 34% slower at this size |
| Active window selection vs random (5% budget) | 44.25 vs 43.90 | no gain |
| Hierarchy (region + global tokens) removed | 43.28 | no loss |
| Weather removed | 43.13 | no loss |

**Foundation pretraining** (3.8M parameters, 2.1M active, 6 US networks, 16 min): zero-shot London MAE 50.68,
37% better than the last-value baseline but behind all four foundation models. Fine-tuned it helps only with
very little data and hurts with a full year:

| UK training data | From scratch (MAE, S) | Pretrained + fine-tuned (MAE, S) |
|---|---|---|
| none | - | 50.68 (zero-shot) |
| 7 days | 50.82 | 50.13 |
| 30 days | 48.35 | 48.20 |
| 12 months | 45.77 | 47.33 |

**What this supports**: a compact model with the right structure (scale-free sensor tokens, yesterday / last-week
values at the forecast times, attention over the road graph, outage training, conformal calibration) matches
models at least 170x larger without any pretraining. **What it does not support**: that the five techniques, or our
pretraining, add accuracy here; and data still matters (7 days of data costs 11% MAE versus a year).

**Limits**: one city, one year, horizons up to 60 minutes, a single run of each opponent with a 1,024-step history
(not fine-tuned; TimesFM 3.0 univariate mode only); PWM-W's components were chosen on this network's validation
data, the foundation models' were not.

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
