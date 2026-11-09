# PWM-W India v2.0: PWM-F, a 10M-parameter encoder pretrained on all of India

ParadoxAI Lab (Aditya Kumar, Anupam Singh).

v0.9's data-threshold study showed that PWM-W needs about 24 months of a network's own history to stop losing to
TimesFM and Chronos, and about 48 months to beat them on every variable; the Delhi CPCB sensors have 16. v2.0 gives
every network many years of Indian weather by pretraining on every Indian station in NOAA's ISD, then fine-tuning.
Only physical observations are used: no images, video or text.

## What is new

| Part | What it does | Idea it borrows |
|---|---|---|
| All-India corpus (`tools/fetch_india.py`) | Every Indian ISD station, hourly temperature, humidity and wind, 2010 to 2024-12-01 | Pretrain on a large corpus, then specialise |
| PWM-F encoder (`pw/fenc.py`, 10,538,497 parameters) | 21 daily patches of each station's history, per-window normalisation, 5 transformer layers | — |
| Mixture of experts in every layer | 1 always-on shared expert + 8 routed experts, top-2; routing bias nudged towards idle experts instead of a balance loss | Fine-grained MoE with shared experts and auxiliary-loss-free balancing (as in DeepSeek's papers) |
| Pretraining objective (`pretrain_f.py`) | Quantile forecast of the next 24 h + reconstruction of 15% hidden days | Self-supervised generative pretraining |
| Physical rules (`run_weather.py: phys`) | Humidity kept in 0–100 %, wind >= 0, quantiles in order, on every PWM-W forecast | Hard rules the model must obey; calibrated uncertainty |
| Fine-tuning (variants P11, P12) | The pretrained encoder plugged into PWM-W's station graph (P8 base) or PWM-X (P10 base), learning rate x0.1 | — |

About half of PWM-F's parameters are active for each token (shared expert + 2 of 8 routed experts).

## Rules that keep the test clean

* **No leakage:** the corpus ends on 2024-12-01 00 UTC, before every league's validation period (WMO 2024-12-01,
  CPCB 2025-05-03, airports 2025-11-01). Pretraining checkpoints are chosen on the corpus's own last 60 days.
* **Same decision rule:** P11 and P12 replace P0 only if better by more than 2 sigma on validation; v1.0's ensemble and
  self-correction steps still apply; test scores, opponents and significance tests are unchanged.
* **Honest scale:** 10M parameters on tens of millions of station-hours is still data-limited by large-model
  standards; the held-out pretraining loss is reported so overfitting is visible.

## Run (Kaggle, free)

1. Corpus: already built by the `pwm-india-data` notebook (`WX_INDIA.npz`: 187 Indian ISD stations, 2015-01-01 to
   2024-11-30, 16.3M station-hours, 5.9M with a temperature, 66 MB; from branch `delhi-v2.0`'s collector, same leakage
   cutoff). `kaggle_v20_data.sh` (a 2010-start collector) is an alternative.
2. GPU notebook with the corpus attached: `LEAGUES="CPCB" VARIANTS="P10,P11,P12" PRE_HOURS=1.5 bash kaggle_v20.sh`

Branches `delhi-v1.1` (a whole-graph PWM-F with regional pretraining networks) and `delhi-v2.0` (PWM-X pretrained on
the corpus) are earlier drafts of the same step; v2.0 here consolidates them and is the version that is run.

## Results

Pending. They will be reported here exactly as logged, losses included.
