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

## Results (Kaggle run pwm-v20, 2026-11-09, CPCB)

**Pretraining** (187 Indian ISD stations, 2015-01 to 2024-11): stopped by its 1.5 h cap at step 31,188 of 40,000.
Held-out pinball loss fell from 0.1487 (step 1,000) to **0.1305**; held-out MAE 0.862 °C, 4.80 %, 0.578 m/s. Expert
load stayed balanced (each of the 8 routed experts took 10–14% of tokens throughout).

**Validation on CPCB** (MAE / spread; 2σ = 0.0077):

| P0 | P10 (PWM-X, v0.9) | P11 (PWM-F in the station graph) | P12 (PWM-F + PWM-X) |
|---|---|---|---|
| 0.4922 ± 0.0038 | **0.4597 (chosen)** | 0.4620 | 0.4617 |

Both PWM-F variants pass the 2σ bar against P0 but are slightly worse than P10, so the rule keeps P10. The v1.0
ensemble step (P10 + P11) improved validation from 0.4561 to 0.4509, by 0.0052, which is below 2σ: not adopted.
Self-correction again made validation worse (0.4686): not adopted.

**Test:** because P10 was chosen, the CPCB test verdicts are identical to v0.9/v1.0: against TimesFM 2.5 and 3.0 and
Chronos-2, ties on 5 comparisons and losses on 4 (wind against all three, +2.9 to +3.8%; temperature against
Chronos-2, +3.4%). **PWM-F closed none of the four losses.**

**Hybrid:** not run. The attached global-forecast file chosen by the script lacked a usable hybrid block and the
loader skipped the hybrid silently. Fixed for later runs: the script now picks, per league, the attached file with a
usable hybrid block, and the loader prints a warning when it skips one.

**What this says.** Pretraining on 187 airport and synoptic stations did not transfer to Delhi's rooftop CPCB sensors,
whose readings (sheltered wind, siting) differ from the stations it learned from. The next lever is data of the same
kind as the target: nationwide CPCB sensors (needs a free data.gov.in API key that only the owner can create) or
longer pretraining (the held-out loss was still falling slowly at the cap).

## v2.1: pretraining on CPCB rooftop stations in six more cities

The v2.0 corpus (airport and synoptic stations) did not transfer to Delhi's rooftop CPCB sensors. v2.1 adds data of
the same kind as the target: CPCB/state-board stations in Mumbai, Kolkata, Chennai, Pune, Hyderabad and Bengaluru, with
their own temperature, humidity and wind sensors (and PM2.5 and other pollutants, kept for pollution forecasting
later), from OpenCity's public "<city> Hourly Air Quality Reports" — the same source and file format as the Delhi league,
no account or key (`tools/fetch_cpcb_india.py`). The corpus ends at 2025-05-03 00:00 IST, the start of the Delhi
league's validation period. Pretraining samples it 50/50 with the ISD corpus (`--mix`).

(The data.gov.in "Real time Air Quality Index" resource was considered and rejected: it publishes only current
readings of pollutants, with no history, no weather variables and no API.)

    bash kaggle_v21_data.sh                                                # CPU: the six-city corpus
    LEAGUES="CPCB" VARIANTS="P10,P11,P12" PRE_HOURS=1.0 bash kaggle_v20.sh   # GPU, with both corpora attached

### v2.1 results so far

**Corpus (Kaggle notebook pwm-v21-data, 2026-11-10):** 84 station files read, 58 stations kept (AT coverage >= 10%),
11,712 hours (2024-01-01 to 2025-05-03 IST), 554,432 observed temperature station-hours; missing 18.4% AT, 20.2% RH,
27.7% WS; 12 MB. Several Chennai and Pune stations have no temperature sensor and were dropped.

**Pretraining (Kaggle run pwm-v21, 2026-11-10, GPU T4, pretrain only):** ISD corpus (187 stations, 5.9M temperature
hours) and the six-city CPCB corpus, sampled 50/50; PWM-F 10,538,497 parameters; stopped by its 1.25 h cap at step
27,592 of 40,000.

| Step | 1,000 | 2,000 | 3,000 | 5,000 | 10,000 | 15,000 | 20,000 | 25,000 | 27,000 |
|---|---|---|---|---|---|---|---|---|---|
| Training loss | 0.2082 | 0.1969 | 0.1827 | 0.1750 | 0.1685 | 0.1491 | 0.1445 | 0.1517 | 0.1426 |
| Held-out pinball (both corpora) | 0.1499 | 0.1430 | **0.1415** | 0.1416 | 0.1443 | 0.1471 | 0.1488 | 0.1504 | 0.1507 |

Best held-out pinball **0.1415 at step 3,000** (MAE 0.897 °C, 5.92 %, 0.445 m/s); that checkpoint is the one saved and
used for fine-tuning. Expert load stayed balanced (each routed expert 11–15% of tokens throughout).

**What this says.** After step 3,000 the training loss kept falling while the held-out loss rose: the model
**overfits**. The likely cause is the small CPCB corpus: it supplies half of every batch but holds about 1/10 as many
temperature hours as the ISD corpus, so its windows are seen many times over. The held-out score mixes both corpora and is not
comparable with v2.0's ISD-only 0.1305; the log does not report the two corpora separately. Whether the step-3,000
encoder helps Delhi is decided only by the fine-tune and CPCB scoring (`notebooks/pwm_v21_finetune.ipynb`, with the
pwm-v21 output attached, `REUSE_FENC=1`), which waits for the weekly GPU quota reset. Options if it does not help:
a lower CPCB weight (`--mix 0.8,0.2`), more dropout, or starting from the v2.0 encoder and adding CPCB briefly.
