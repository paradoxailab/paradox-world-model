# Atlas-100M: one compact world model for weather, air quality and traffic (pre-registration)

ParadoxAI Lab · Aditya Kumar, Anupam Singh · written 2026-11-19, **before any GPU run of this model**. The commit
that adds this file is the time stamp. Any later change to a rule is appended to "Deviations" with its date and reason;
nothing above that section is edited after the first run starts.

## 1. Question and what may be claimed

Can **one** set of weights with about 100M parameters, trained only on real public station data, forecast three
different physical systems better than the strongest models that exist for each, under the same paired tests used in
papers 1–5? The domains are weather at 709–5,672 stations worldwide (WEATHER-5K and NOAA after it), PM2.5 at
263 Indian stations, and traffic on six US road networks.

A sentence "Atlas-100M beats X on D" is allowed only for a comparison that is a **WIN** under the rule of section 6.
Every tie and every loss is reported next to the wins. Two claims are **not** made:
- "the best world model in the world": this study has no common test with video or robotics world models (Cosmos,
  Genie and similar) or with global gridded weather models on their own grids;
- beating operational numerical weather prediction "as a whole": section 5H compares only at stations, at 1–24 h.

## 2. Model

- **Atlas-100M** has **98,599,994** parameters (`atlas/m100/multi.py`, counted by code).
- **Shared core:** 94,755,808 parameters. It is the adopted Atlas-5K 24.1M (`models/series/59`, paper 5) grown by the
  exact width map of `atlas/grow.py`: width 392 → 784, heads 8 → 16, 8 encoder and 7 dynamics blocks, hidden width
  5 d, zero-sum perturbation 0.05, seed 700. It contains the encoder blocks, the spatial attention (query, key, value,
  output, norm) and the dynamics blocks, and all three domains use it.
- **Per-domain adapters:** the input layer, the reconstruction head, the forcing embedding, the decoder, the
  geometry → attention-bias MLP and the physical bounds.
  - weather: 779,932 parameters, those of the grown 24.1M model;
  - air quality: 2,983,932 parameters, new;
  - traffic: 80,322 parameters, new.
- A new domain's decoder starts at zero, so its first forecast is its last observation. Checked:
  - the untrained air-quality view equals the harness's "last observed value" baseline exactly;
  - the untrained traffic view has a validation ratio of 1.000 to the last reading.
- Each domain's view is a plain `Atlas` and is scored by that domain's existing, unchanged scorer.

## 3. Data and splits (each domain's published protocol, unchanged)

| Domain | Data | Input → output | Train | Validation | Test |
|---|---|---|---|---|---|
| Weather | WEATHER-5K, 5,672 stations, 5 variables (`run_atlas_5k.py`) | 48 h → 24 h, 32 nearest stations | 2014–2021 | 2022 | 2023; NOAA ISD-Lite 1 Jan 2024 – 24 Aug 2025 ("live") |
| Air quality | CPCB all-India league, 14 networks, 263 stations, 15 variables (`run_atlas_india.py`) | 72 h → 24 h PM2.5 | to 2022-07-31 | 61 days | 2022-10-01 – 2023-03-31, every 6 h; Track S trained stations, Track U never-trained |
| Traffic | ParadoxBench-1.1: PEMS08/04/03/07, METR-LA, PEMS-BAY (`v0.6-conference`) | 12 → 12 steps (5 min) | 60% / 70% | 20% / 10% | official windows |

No test window is read before training has finished. `train.py` reads none at all.

## 4. Training (`atlas/m100/train.py`, defaults = the rule)

- **Batches:** each step draws one domain (weather 0.5, air quality 0.25, traffic 0.25) and one batch with that
  harness's own loss:
  - weather: pinball loss plus reconstruction of 15% hidden inputs, 256 windows;
  - air quality: channel-weighted pinball loss plus reconstruction of up to 40% hidden inputs, 16 windows of one
    network;
  - traffic: pinball loss plus reconstruction, 15% hidden inputs and 10% of sensors dark, one batch of windows of one
    network.
- **Optimiser:** AdamW with weight decay 1e-4. Learning rate 1.5e-4 for the grown 24.1M weights and 1e-3 for the new
  adapters, 3% warm-up, then cosine to 10%.
- **Length:** 100,000 steps at most, gradient clip 1.0, bf16 autocast, seed 700.
- **Selection:** every 2,500 steps each domain's validation metric is computed on fixed windows:
  - weather: E on 300 fixed stations every 6 h, as in paper 5;
  - air quality: pooled PM2.5 MAE at the trained stations;
  - traffic: mean over networks of MAE ÷ last-reading MAE.

  The checkpoint kept has the lowest **S = Σ log(metric)**. Patience is 8 checks.
- **Check G0:** at step 0 the grown model's weather validation E must equal the 24.1M model's within 2e-4, or the run
  stops. CPU checks of every exactness guarantee: `python atlas/m100/test_m100.py` (all passed before this commit).

## 5. Evaluation (`atlas/m100/pipeline.py`)

**W. Weather.**
- **(a) Full test:** all 5,672 stations, every hour of 2023, MAE per variable (`run_atlas_5k.py --eval`), compared
  with the benchmark's published models, as in paper 5.
- **(b) Head-to-head:** 709 stations, the 2023 test every 48 h and the live period every 96 h, against the same ten
  zero-shot opponents whose per-window errors paper 5 saved:
  - persistence;
  - Chronos-Bolt;
  - Chronos-2 (univariate and multivariate);
  - TimesFM 2.5 and 3.0;
  - TTM r2;
  - TiRex;
  - Sundial;
  - Time-MoE 200M.

  Atlas-5K 24.1M is compared as well, on the same windows.
- **(c) Validation:** E on every 4th station every 6 h, against the 24.1M model's 0.27307.

**A. Air quality.**
- Nine zero-shot foundation-model configurations with 512 h of history (`india_opponents.py`): Chronos-Bolt,
  Chronos-2, TimesFM 2.5, TimesFM 3.0 (univariate and multivariate), TTM, TiRex, Sundial, Time-MoE 200M.
- Atlas-India v1.0 (paper 3's released weights, re-forecast with the same code).
- Two baselines: last observed value, same hour yesterday.
- Atlas-F (paper 4) is quoted from paper 4, not paired.

**T. Traffic.**
- Track A:
  - STID, Graph WaveNet and STAEformer, trained with their authors' code and paper 1's wall-clock budgets
    (`run_specialists.py`; on an A100, so more epochs than in paper 1: the difference favours the opponents);
  - PWM-Dyn v0.6r, paper 1's recipe, three fresh seeds.
- Track B: TimesFM 2.5, TimesFM 3.0 (univariate and multivariate), Chronos-2 and Chronos-Bolt, zero-shot with 512 steps.
- The same forecast is entered on both tracks; its context is 12 steps.

**H. Hybrid weather, against the global systems** (`atlas/m100/hybrid.py`).
- **Stations:** 178, every 4th of the 709.
- **Archive:** Open-Meteo Previous Runs, which starts in January 2024. Systems: ECMWF IFS 0.25, ECMWF AIFS, NOAA GFS,
  GraphCast (GFS initial conditions).
- **Hybrid inputs:** each system's day-2 forecast, issued 48 h before the valid hour, so always published before the
  forecast starts, plus a flag, for the centre station.
- **Start:** the widened model starts as the pure model up to float rounding (check H0: maximum difference < 1e-3;
  a logic error would be of order 1).
- **Data split:** fitted on 2024-01-01 – 2024-10-31 at learning rate 5e-5, early stopping on 2024-11-01 – 12-31,
  tested once on 2025-01-01 – 2025-08-24 with forecast starts every 6 h.
- **How opponents are scored:** on the freshest run published before the start, assuming a publication delay of 6 h
  for every system (at or below each one's real delay, so it can only favour them). Each opponent appears three ways:
  - raw;
  - bias-corrected by its own trailing 30-day error at the station;
  - its day-1 run whether or not it was published yet, an advantaged reference reported separately.

## 6. Tests and the WIN rule

- **Weather and hybrid:** station-block bootstrap (10,000) and Diebold–Mariano on daily mean loss differences with
  Newey–West variance (`paired_w5k.py`).
- **Air quality:** the same two tests on station-day sums (`score_aq.py`).
- **Traffic:** Diebold–Mariano and day-block bootstrap (`paradoxbench/significance.py`).
- **Holm correction** over every comparison of a domain family (one family each: weather test, weather live, air
  quality, traffic, hybrid).
- **WIN:** lower MAE, Holm-adjusted p < 0.01, and a 95% interval of the difference that excludes 0. **LOSS:** the
  mirror image. Anything else is a **TIE**.

## 7. Predictions (made now; each is scored HELD or FAILED in the report)

| # | Prediction | Probability |
|---|---|---|
| P1 | G0 holds (grown weather view reproduces the 24.1M) | 0.99 |
| P2 | Weather validation E (every 4th station) ≤ 0.27307, the 24.1M's | 0.55 |
| P3 | Weather validation E ≤ 0.2700 | 0.20 |
| P4 | Weather head-to-head: WIN in all 50 model–variable comparisons with the ten zero-shot opponents, on BOTH the 2023 test and the live period | 0.85 |
| P5 | Weather head-to-head test: lower E than Atlas-5K 24.1M | 0.55 |
| P6 | Full 2023 test: lower MAE than the benchmark's best published model (PhysicsFormer) on at least 4 of 5 variables | 0.75 |
| P7 | Full 2023 test: lower MAE than PhysicsFormer on sea-level pressure | 0.15 |
| P8 | Air quality Track S: WIN against every foundation model | 0.60 |
| P9 | Air quality Track U: WIN against every foundation model | 0.35 |
| P10 | Air quality Track S: WIN against Atlas-India v1.0 | 0.45 |
| P11 | Traffic Track B: WIN against every foundation model on at least 5 of 6 networks | 0.60 |
| P12 | Traffic Track A: WIN against all three trained specialists on at least 4 of 6 networks | 0.25 |
| P13 | Traffic: lower MAE than PWM-Dyn v0.6r on at least 4 of 6 networks | 0.35 |
| P14 | Hybrid: WIN against raw IFS, AIFS, GFS and GraphCast (freshest published run) on temperature and dewpoint | 0.70 |
| P15 | Hybrid: WIN against bias-corrected AIFS on temperature | 0.45 |
| P16 | Hybrid: WIN against raw IFS on sea-level pressure | 0.10 |
| P17 | Pure Atlas-100M LOSES to raw IFS on sea-level pressure on the hybrid test | 0.90 |

Our expectation in one line: weather against foundation models is safe; adding air quality and traffic to the same
weights may cost weather a little; traffic against tuned specialists and pressure against ECMWF are where it can lose.

## 8. Budget and stop rules

- About 50 A100-hours in Colab, split roughly as follows:

  | Stage | A100-hours |
  |---|---|
  | Training | 12 |
  | Weather evaluation | 6 |
  | Air-quality opponents and scoring | 4 |
  | Traffic opponents and scoring | 13 |
  | Hybrid | 3 |
  | Margin | 12 |

- A stage that cannot run inside 60 A100-hours in total is reported as not run, not shortened silently.
- The forecast archive is fetched on CPU and may take several days under Open-Meteo's free daily limit. Until it is
  complete, section H is "pending", not dropped.
- One training seed (700). Seed variance is not measured; the report says so.

## 9. Licences and data terms

- **Evaluation only:** TimesFM 3.0 (non-commercial) and the TiRex community licence.
- **Open-Meteo:** free API for non-commercial use, model data CC-BY 4.0. It is used here only to score forecasts in a
  research study, and none of it is redistributed.
- **Other data sources:** NOAA ISD (public), WEATHER-5K (its licence), CPCB via the public Kaggle copy, Caltrans
  PeMS / METR-LA / PEMS-BAY (as in paper 1).

## Deviations

1. **2026-11-20, air quality: two opponents failed on the first pass and are re-run.** Sundial and Time-MoE 200M
   crashed in `india_opponents.py` (`'DynamicCache' object has no attribute 'seen_tokens'`): Colab's current
   `transformers` is newer than the 4.40.1 their remote code needs (`atlas/delhi/pw/opponents.py` names that version).
   The other seven ran. `aq_score` then scored the seven, and that first score is kept unchanged as
   `atlas100m_aq_results_first7.json`. The two are re-run with `transformers==4.40.1` in a separate package directory
   (nothing else changes: same windows, context, code), and `aq_score` is re-run once over the full pre-registered
   family of nine. If either still fails, it is reported as not run.
2. **2026-11-20, traffic: STAEformer did not start on the first networks.** Its official code imports `torchinfo`,
   which the notebook did not install (`ModuleNotFoundError`). The job failed before training, so no result exists to
   discard; `torchinfo` is installed and the job is retried by the pipeline's own retry pass with the same budget.
3. **2026-11-20, note on P2.** Section 5(c) describes the validation comparison as "every 4th station"; the number it
   names, 0.27307, is the 24.1M model's validation E on **all** 5,672 stations (`run_atlas_5k.py --eval`). P2 is scored
   on that same full protocol (`atlas100m_eval_s600.json`), and the head-to-head validation windows, where both models
   are scored on identical windows, are reported next to it.
4. **2026-11-20, traffic: a second GPU (Kaggle) for ten zero-shot jobs.** Colab gave an L4 instead of an A100, so
   traffic would take about a day. The ten Track B foundation-model jobs for PEMS-BAY and METR-LA run on Kaggle
   (`atlas/m100/kaggle_traffic.py`, notebook `atlas_100m_kaggle_traffic.ipynb`) with the same script, context and
   chunk sizes, and are copied into the pipeline's store under the same job names (`kaggle_bridge.py`). Zero-shot
   models have no training and no time budget, so the GPU cannot change their accuracy; the trained specialists, whose
   budgets are in minutes, all stay on Colab. Traffic is scored only after every job is in. Kaggle's GPU, package
   versions and minutes per job are kept in `logs/kaggle_manifest.json`.
   **Withdrawn the same day, before any Kaggle job ran:** the Kaggle account had no GPU hours left that week, so all
   traffic jobs run on Colab as first planned. The two helper scripts stay in the repository, unused.
5. **2026-11-20, air quality: Time-MoE ran out of GPU memory on its re-run** because it shared the L4 with a TimesFM 3.0
   traffic job. Sundial's re-run finished. Time-MoE is started again, unchanged, once no TimesFM 3.0 job is on the GPU.
