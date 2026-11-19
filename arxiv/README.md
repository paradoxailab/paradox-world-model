# arXiv submission kit (ParadoxAI Lab)

Five papers in series order (the order the work was done), each by **Aditya Kumar and Anupam Singh**, ParadoxAI Lab,
info@paradoxailab.com. Each has a tested source package (`*_arxiv_source.tar.gz`; compiles with pdflatex alone, as arXiv
builds it, bibliography included as `main.bbl`) and the PDF arXiv will produce. Audit of every reference and number:
[`AUDIT.md`](AUDIT.md). Prepared 2026-11-19.

## Before submitting (arXiv rules in force in 2026)

1. **Both authors read every paper in full.** arXiv holds every author responsible for all content however it was
   produced, and bans authors for a year for unchecked AI-generated text. All five declare the AI assistance used.
2. **Endorsement.** A first-time submitter needs an endorsement from an existing arXiv author in the category. All five
   use primary category **cs.LG**, so one cs.LG endorsement covers them.
3. **Rate limit.** At most **2 submissions per calendar month per submitter**, at most 3 in moderation at once. If
   Anupam also registers and is endorsed, he can submit two more per month.
4. **Conference policy.** If a paper is also under review at a venue, check that venue's preprint rules first.

## Order

| # | Paper | When |
|---|---|---|
| 1 | Trained Small, Scored Fairly: A Sub-Million-Parameter Graph Model Against Published Specialists and Zero-Shot Foundation Models on Physical Network Forecasting | November 2026 |
| 2 | A Small Station-Graph World Model for 0-24 h Weather in North India: A Version-by-Version Record Against Global AI Weather Models and Time-Series Foundation Models | November 2026 |
| 3 | When Does a Small Sensor-Only Model Beat Time-Series Foundation Models? A Pre-Registered Evaluation on Indian Air Quality | December 2026 |
| 4 | Atlas-F: Pre-Registered PM2.5 Forecasting Across India by Online Fusion of a Small Station-Graph Model and a Foundation Model | December 2026, after #3 is announced: first replace the atlas1 citation with #3's arXiv number |
| 5 | Grow, Don't Restart: Compact Station World Models, Grown from 1M to 24M Parameters, Beat TimesFM and Chronos on WEATHER-5K | January 2027 (earlier if Anupam also submits) |

Not for arXiv: `paper/` (PWM-Dyn v0.4, superseded by #1) and `atlas/paper3/` (Atlas-5K 10M only, superseded by #5).

## Metadata for each submission

Authors: **Aditya Kumar; Anupam Singh** (ParadoxAI Lab). Licence: **CC BY 4.0**.

### 1. Trained Small, Scored Fairly: A Sub-Million-Parameter Graph Model Against Published Specialists and Zero-Shot Foundation Models on Physical Network Forecasting

* Upload: `1_PWM-Dyn_ParadoxBench_arxiv_source.tar.gz` · check against `1_PWM-Dyn_ParadoxBench.pdf`
* Primary category: **cs.LG** · cross-list: stat.ML
* Comments: 7 pages, 1 figure, 7 tables. Code, rules, logs and weights: https://github.com/paradoxailab/paradox-world-model
* Abstract (1842 characters; arXiv limit 1,920):

> Time-series foundation models now forecast any series zero-shot, while graph specialists are still trained per network, and the two are rarely compared under one protocol. We compare them on physical sensor networks with a fixed, open benchmark: six traffic networks (PEMS03/04/07/08, METR-LA, PEMS-BAY) and two monsoon rainfall regions, four tracks (standard context, open context, 30% dead sensors, zero-shot transfer), one scorer for point error, pinball loss and interval score, saved forecasts and paired Diebold-Mariano and block-bootstrap tests. We introduce PWM-Dyn, a 0.3-0.4M-parameter graph-diffusion model with explicit missing-data inputs, quantile outputs and split-conformal calibration, and compare it with STID, Graph WaveNet and STAEformer trained with their official code on identical windows under a fixed compute budget, and with zero-shot TimesFM 2.5 and 3.0. Configurations were chosen on validation and the reported models use fresh seeds; four networks were never used during development. Under a 12-step context a three-seed PWM-Dyn ensemble has the lowest MAE on five of six traffic networks (0.3-4.2% below the best trained opponent on the four new ones), is not significantly different from STID on three (PEMS08, PEMS04, PEMS07), and trails a budget-capped STAEformer on PEMS08. Against TimesFM 3.0 it has lower MAE and interval score on seven of eight tasks (five of six traffic networks; the MAE difference is significant on four; rainfall entries from the previous model version) and loses on PEMS03. With 30% of sensors dark it beats per-sensor climatology on seven of eight tasks, where specialists without a missing-data mechanism fail. An ablation traces most of an earlier accuracy loss on PEMS04 to a climatology input. Code, benchmark and forecasts: https://github.com/paradoxailab/paradox-world-model.

### 2. A Small Station-Graph World Model for 0-24 h Weather in North India: A Version-by-Version Record Against Global AI Weather Models and Time-Series Foundation Models

* Upload: `2_PWM-W_North_India_weather_arxiv_source.tar.gz` · check against `2_PWM-W_North_India_weather.pdf`
* Primary category: **cs.LG** · cross-list: physics.ao-ph
* Comments: 8 pages, 10 tables. Code, rules, logs and weights: https://github.com/paradoxailab/paradox-world-model
* Abstract (1906 characters; arXiv limit 1,920):

> Global AI weather models and zero-shot time-series foundation models are not built for what many users in India need: the next 24 hours of temperature, humidity and wind at a specific station. We study whether a small model trained only on a station network's own history can do better. PWM-W is a graph world model of about one million parameters. A pure form uses observations only; a hybrid also reads global forecasts published before the forecast starts. We test it in three north-Indian leagues: six airports (METAR), 20 NOAA stations around Delhi (WMO) and 25 Delhi air-quality stations' weather sensors (CPCB). The opponents are real archived operational forecasts of AIFS, IFS, ICON, GFS and NOAA's GraphCast-based AIGFS, raw and locally bias-corrected, together with TimesFM 2.5 and 3.0 and Chronos-2. Each change from version 0.3 to 0.9 was adopted only if it beat the default on validation by more than two seed standard deviations; several failed. At the airports, the hybrid beats every global model on every variable it forecasts when each is scored on its newest run published before the forecast starts (AIFS by 4.4%, 11.8% and 7.4%). Against AIFS's freshest run it still loses on temperature and humidity. The pure model beats all three foundation models on every variable at the airport and WMO stations. On the noisier CPCB sensors, cross-network training, a 14-day encoder and weight averaging turned four of its losses into ties, but it still trails Chronos-2 on temperature and all three foundation models on wind. Bias-corrected FourCastNet and GenCast Mini beat the pure model on airport temperature. We report every result, including the losses, and the test-reuse risk of a version-by-version study. A data-threshold study shows that PWM-W needs 12-24 months of a network's own history to stop losing to the foundation models and 24-48 months to beat all three on every variable.

### 3. When Does a Small Sensor-Only Model Beat Time-Series Foundation Models? A Pre-Registered Evaluation on Indian Air Quality

* Upload: `3_Atlas_India_air_quality_arxiv_source.tar.gz` · check against `3_Atlas_India_air_quality.pdf`
* Primary category: **cs.LG** · cross-list: physics.ao-ph; stat.ML
* Comments: 15 pages, 4 figures, 13 tables. Code, rules, logs and weights: https://github.com/paradoxailab/paradox-world-model
* Abstract (1835 characters; arXiv limit 1,920):

> Time-series foundation models (TSFMs) forecast unseen series zero-shot and lead public benchmarks. We ask whether a small model trained only on Indian monitoring-station data can beat them at the task those stations exist for: forecasting PM2.5 for the next 24 hours. We present Atlas, a 0.97M-parameter spatio-temporal forecaster with graph-biased attention across stations and latent dynamics driven by known future inputs, and evaluate it under a protocol in which every rule was committed to a public repository before the score it governs, and every comparison is a Diebold-Mariano test, run separately on stations used in training and on stations never used. On an all-India test that no model choice ever touched (14 networks, 263 stations, winter 2022-23), one set of Atlas weights beats TimesFM 2.5 by 6.1% at trained and 4.8% at never-trained stations (p<10^-10). On Delhi it beats six zero-shot TSFMs (Moirai 2.0, TiRex, TimesFM 2.5, Chronos-2, Chronos-Bolt, Granite TTM) by 5.2-8.6% at trained stations and the ECMWF CAMS forecast by 29-54%. The decisive ingredient is related data, not scale: pre-training on 13 other Indian networks makes Atlas level with TimesFM 2.5 on Delhi before it has seen any Delhi data. A pre-registered confirmation that repeats this recipe with each of four networks left out of pre-training succeeds on Uttar Pradesh but fails on Maharashtra and Karnataka, where the station graph hurts never-trained stations: transfer wins where the target resembles the networks it learned from. A 14K-parameter variant whose forecast is an explicit relaxation-exchange update is more data-efficient than Atlas at every data budget, and removing the update costs it 5.6-6.5%. We also report three pre-registered failures: a lockdown counterfactual, a cross-domain data-scaling law and continuous retraining.

### 4. Atlas-F: Pre-Registered PM2.5 Forecasting Across India by Online Fusion of a Small Station-Graph Model and a Foundation Model

* Upload: `4_AtlasF_India_arxiv_source.tar.gz` · check against `4_AtlasF_India.pdf`
* Primary category: **cs.LG** · cross-list: physics.ao-ph; stat.AP
* Comments: 15 pages, 7 figures, 8 tables. Code, rules, logs and weights: https://github.com/paradoxailab/paradox-world-model
* Abstract (1886 characters; arXiv limit 1,920):

> Small models trained on a country's own monitoring stations and large time-series foundation models (TSFMs) are both proposed for air-quality forecasting, but they are rarely compared under a protocol that fixes the claims before the scores are seen, and almost never against the forecasts a government actually issues. We report a pre-registered study of 24-hour PM2.5 forecasting at 263 Indian stations in 14 networks. A confirmation test of Atlas, a 0.97M-parameter station-graph model previously reported to beat TSFMs, fails its pre-registered rule: with each of four networks held out of pre-training it beats TimesFM 2.5 in Uttar Pradesh but loses in Maharashtra and Karnataka, and the losses trace to never-trained stations in geographically spread networks, where attention over all stations mixes unrelated sites. We propose Atlas-F, which combines Atlas and TimesFM 2.5 with weights re-chosen each day from the previous 30 days of verified forecasts. On the all-India test Atlas-F beats both members on trained and never-trained stations (-1.2%/-2.0% against Atlas, -7.2%/-6.8% against TimesFM 2.5; Diebold-Mariano p<10^-13) and has lower error than TimesFM 2.5 in all 28 network-track cells, meeting a dominance rule fixed in advance; ablations show that the gain comes from network-specific weights: equal weights are significantly worse (+0.9%/+0.8%), a static per-network rule fitted on validation is equivalent, and Atlas-F is within 0.2% of an oracle. Finally, an Atlas trained only on data up to 30 September 2024 has an hourly Delhi-average error of RMSE 54.2 and MAE 31.3 µg/m³ in winter 2024-25 (95% CI for MAE 26.7-36.4), below the published Day-1 errors of the operational WRF-Chem (92.5, 58.8) and SILAM (108.0, 71.7) systems; we show why this by-number comparison, which persistence also passes, measures a different skill from what those systems are built for.

### 5. Grow, Don't Restart: Compact Station World Models, Grown from 1M to 24M Parameters, Beat TimesFM and Chronos on WEATHER-5K

* Upload: `5_Atlas5K_10M_25M_arxiv_source.tar.gz` · check against `5_Atlas5K_10M_25M.pdf`
* Primary category: **cs.LG** · cross-list: physics.ao-ph
* Comments: 16 pages, 3 figures, 12 tables. Code, rules, logs and weights: https://github.com/paradoxailab/paradox-world-model
* Abstract (1855 characters; arXiv limit 1,920):

> Time-series foundation models with up to 205M parameters are increasingly used zero-shot for weather-station forecasting. We test whether a compact, task-trained world model that is grown rather than restarted can beat them under paired statistical tests. Atlas-5K is a station-graph model: each station reads its last 48 hours together with its 31 nearest neighbours, the model encodes them into a latent state, and one shared transition with geometry-biased attention rolls the state forward. We grow an adopted 0.97M-parameter Atlas twice with exact, function-preserving maps: to 9.64M, then to 24.1M (hidden layers widened 2.5x, one block added). Every rule and numeric prediction was committed to a public repository before the run it governs. On WEATHER-5K at 24 hours we compare both grown models, on identical windows at 709 stations, with nine foundation-model configurations (TimesFM 2.5 and 3.0, Chronos-2 univariate and multivariate, Chronos-Bolt, TiRex, Sundial, Time-MoE and TTM) and persistence. Both models win all 50 model-variable comparisons (station-block bootstrap and Diebold-Mariano, Holm-corrected, α=0.01) on the 2023 test year and on 19 months of NOAA observations from 2024-25 that Atlas never saw. The 24.1M model's standardised error is 17.0% below the best foundation model, TimesFM 3.0, and its per-variable error is 9-48% below every foundation model. On the full 2023 test it has lower error than the benchmark's best published model, PhysicsFormer (19.3M), on four of five variables, but higher error on sea-level pressure, where ECMWF's operational forecast remains far ahead. Size bought little: 10x the parameters gave -1.95% validation error and a further 2.5x gave -1.03%, with no significant gain on pressure. We report every prediction, including the two that failed, and release the code, rules, logs and weights.

The arXiv abstracts of #2 and #5 are shortened from the papers' own abstracts by removing descriptive detail only;
every result and every loss stated in the paper's abstract is kept.
