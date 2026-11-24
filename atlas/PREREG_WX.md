# Atlas-WX: pre-registration (ParadoxAI Lab, 23 November 2026, before any Atlas-WX data is downloaded)

**Goal (Adi, 23 Nov 2026).** The most accurate station-level forecast of surface weather worldwide among every system we
can test fairly. Plan and archive checks: `PLAN_WX.md` (including its 23 Nov addendum). This file fixes the data, splits,
model selection, opponents, statistics, claim rule and predictions. Every change after today is a dated deviation, and
every loss is published next to the wins. "Best weather model in the world" is never claimed: global gridded forecasting
(WeatherNext 3, AIFS/IFS, WeatherMesh, Aurora, FuXi) is not tested here.

## 1. Data

- **Truth and history:** NOAA ISD-Lite (AWS `noaa-isd-pds`), hourly, 1 Jan 1995 – 31 Dec 2025. Variables: 2 m temperature
  (T), dewpoint (Td), 10 m wind speed (WS) and direction (WD, input only), sea-level pressure (SLP), 6 h precipitation
  (P6, where reported). GHCNh replaces ISD-Lite for any year ISD-Lite lacks; the swap is recorded.
- **Station set (frozen by SHA-256 of the sorted USAF-WBAN list before training):** every ISD station with, for
  temperature, ≥ 60% of hours reported in each of at least 5 calendar years 1995–2023, **and** ≥ 60% in 2024 and in 2025.
  Duplicate positions (same coordinates to 0.01°) keep the station with more data.
- **Quality control (fixed now):** physical bounds (T −90…60 °C, Td ≤ T + 0.5 and ≥ −100 °C, WS 0…75 m/s, SLP 860…1090
  hPa, P6 0…500 mm); a value more than 8 robust SDs (MAD-based, per station × month) from the station's monthly median
  is dropped; ISD-Lite's own −9999 is missing. QC uses only values from the same station, never a forecast.
- **Operational forecasts at the stations:** Open-Meteo Previous Runs for every system with a complete 2024–2025 archive
  at our stations (checked per system on fetch; the list is frozen before Stage 2 training): candidates ECMWF IFS 0.25°,
  ECMWF AIFS, GFS, ICON, GEM, JMA, UKMO, Météo-France, CMA, AIGFS; plus WeatherNext 2 (ensemble mean and the 10/50/90
  quantiles of its 64 members) only if access is granted before Stage 2 training starts.

## 2. Splits (fixed now)

| Stage | Train | Validation | Purpose |
|---|---|---|---|
| 1 observation core | 1995-01-01 – 2022-12-31, all stations | 2023, every 4th station, every 6th hour | size selection |
| 2 hybrid | 2024-01-01 – 2024-12-31, stations not in the validation set | 2024, every 4th station | early stopping |
| **Test (once)** | — | **2025-01-01 – 2025-12-31, all frozen stations, forecast starts 00 and 12 UTC** | claims |
| Live | — | 90 days from the first day the live runner commits Atlas-WX forecasts before they verify | claims (second condition) |

## 3. Models and selection

- **Stage 1:** Atlas (the WEATHER-5K recipe: L = 48 h input, k = 16 neighbours, H = 24 h) at **10M, 30M and 100M**,
  10M grown function-preserving to 30M and 100M (check G0), each capped at 200,000 optimizer steps with the same batch;
  the checkpoint kept is the validation optimum within the cap. Selected: lowest validation E (mean over T, Td, WD, WS,
  SLP of MAE / benchmark scale); within 0.5% of each other → the smaller. Only the selected core goes to Stage 2.
- **Stage 2 hybrid:** the selected core widened (function-preserving) to read, for every frozen forecast system, its
  value, run age and an availability flag for each variable, from the freshest run issued ≥ 6 h before the forecast
  start; output horizon 1–48 h hourly and 51–168 h three-hourly; heads for the 10/50/90% quantiles (median = point
  forecast); P6 added as an output. One model for all stations and variables.

## 4. Opponents (each raw and bias-corrected: 30-day trailing mean error per station × variable × lead)

1. Every frozen Open-Meteo forecast system, read at the station's coordinates.
2. Open-Meteo `best_match`.
3. **MOS baseline (ours, the strongest simple post-processor):** per station × variable × lead hour, ordinary least
   squares on all frozen systems' forecasts plus the last observation, fit on the Stage 2 training data; falls back to the
   bias-corrected IFS where a station has < 60 days.
4. WeatherNext 2 ensemble mean (if access is granted, §1).
5. RealBench's AI models only if their forecasts can be scored on our stations and hours; otherwise cited as context.
6. Persistence (same hour, previous day) and climatology (station × day-of-year × hour, 1995–2023).

## 5. Statistics, families, WIN / TIE / LOSS

- Scores: MAE for T, Td, WS, SLP; for P6, MAE and CRPS (from the three quantiles, the opponents' as point forecasts).
  Both forecasts in a pair are scored on the same station-hours (deviation-8 rule).
- **Families:** region × variable × lead band. Regions (5): India; Europe; North America; East Asia; rest of world.
  Variables (5): T, Td, WS, SLP, P6. Lead bands (3): day 1 (1–24 h), days 2–3, days 4–7. 75 families; Holm within each
  family over its opponents.
- Diebold–Mariano (Newey–West) on daily mean loss differences + station-block bootstrap (10,000) 95% interval.
  **WIN:** lower error, Holm-adjusted p < 0.01 and the interval excludes 0; **LOSS** the mirror; else **TIE**.

## 6. Claim rule

"Atlas-WX is the most accurate station-level forecast of <variable> at <lead band> in <region> among the systems tested"
only if it WINs against **every** opponent of §4 in that family, raw and bias-corrected, **in the 2025 test and in the
live test**. "Worldwide" for a variable and lead band needs that in all five regions. No other superlative is made. All
75 families are published, wins and losses.

## 7. Predictions (probability that each holds; scored once, after the test)

| | Prediction | P |
|---|---|---|
| W1 | The selected Stage 1 size is 30M or 100M (not 10M) | 0.70 |
| W2 | Stage 1: 100M beats 10M on validation E by ≥ 1% | 0.50 |
| W3 | Day 1, T: WIN against raw ECMWF IFS in all five regions | 0.85 |
| W4 | Day 1, T: WIN against bias-corrected IFS in all five regions | 0.65 |
| W5 | Day 1, T: WIN against the MOS baseline in all five regions | 0.40 |
| W6 | Day 1, SLP: **not** a WIN against bias-corrected IFS in Europe (the known weakness persists) | 0.55 |
| W7 | Days 4–7, T: WIN against bias-corrected IFS worldwide (all five regions) | 0.30 |
| W8 | Day 1, P6 CRPS: WIN against bias-corrected IFS in India | 0.40 |
| W9 | Day 1, T: WIN against the WeatherNext 2 ensemble mean (bias-corrected) worldwide, if tested | 0.45 |
| W10 | Live test agrees with the 2025 test (same verdict) in ≥ 80% of the families it covers | 0.70 |

## 8. Order (each step dated in the README when done)

1. Fetch ISD-Lite 1995–2025, apply QC, freeze the station list (hash recorded here as an addendum).
2. Stage 1: three candidates; select on 2023 validation.
3. Fetch the forecast systems for 2024–2025 at the frozen stations; freeze the system list.
4. Stage 2 hybrid and the MOS baseline, on 2024 only.
5. Score 2025 once; start the live runner; publish.

## Addenda

- **23 Nov 2026, 22:15 IST, before any download — station rule restated in observation counts.** ISD-Lite stores one
  observation per hour at most, and much of the world (India's IMD network among it) reports 3-hourly synoptic
  observations; "≥ 60% of hours" would exclude most of India, Africa and Asia. The rule becomes: a qualifying year has
  **≥ 2,190 temperature observations** (at least 3-hourly on average); a station needs ≥ 5 qualifying years in
  1995–2023 and qualifying 2024 and 2025. Candidates are pre-selected from `isd-history.csv` (BEGIN ≤ 2019-12-31,
  END ≥ 2025-12-01, valid coordinates, USAF ≠ 999999). Code: `atlas/wx/fetch_isd_all.py`.
- **23 Nov 2026, 22:50 IST, before any download — exact Stage 1 sizes.** 10M = `sized(10_000_000)` (9,942,032
  parameters, width 680, 2 + 2 blocks, the grid's 10M). "30M" = the trained 10M grown `--grow 1,7,7` (depth 7 + 7, same
  width): **28,472,032**. "100M" = the trained 10M grown `--grow 2,6,6` (width 1,360, depth 6 + 6): **97,621,300**. Each
  grown model gets its own 200,000-step cap after growth (so it has also seen the 10M's steps; stated with the result).
  Code: `atlas/wx/run_atlas_wx.py` (the Atlas-5K recipe on the ISD data; values held in CPU memory when the GPU has no
  room).
- **24 Nov 2026, 00:10 IST, before any station data is downloaded — source switched to GHCNh for all years.** The first
  trial found that NOAA stopped updating ISD in late August 2025 (`isd-history.csv` ends 2025-08-28; no 2026 ISD-Lite
  files), so ISD-Lite cannot cover the 2025 test year. Rather than mix sources between training and test, every year
  (1995–2025) now comes from GHCNh, ISD's successor (AWS `noaa-ghcnh-pds`, by-year parquet, CC0, updated daily; it also
  serves the live test). Per hour, the observation nearest the top of the hour within 30 minutes, variable by variable.
  A value is kept only if its quality code is empty or 0, 1, 4 or 5; the codes dropped are counted and published. The
  station rule, QC, splits and everything else stand. The sixth channel holds the raw precipitation value of the kept
  observation (its accumulation period varies); the 6 h totals for Stage 2 are derived from it before Stage 2 and the
  derivation is recorded then. Code: `atlas/wx/fetch_ghcnh_all.py`. Only the ISD station list had been downloaded.
- **24 Nov 2026, 01:25 IST — station list frozen (before any model sees the data).** 13,267 GHCNh stations had 2024
  and 2025 files; 9,335 met the 2024/2025 rule; **8,791** remain after the 5-qualifying-years rule and duplicate
  positions. SHA-256 of the sorted ID list: `dd1da8fc8a755c46fb5af043af5d021639293a5809895097f984a83fb7123ab1`.
  Temperature hours 1995–2023: 1,211,343,893 (≈ 50.5M station-days, about **3× WEATHER-5K's training data**, less than
  the 4–8× the plan guessed). Largest countries: US 2,844, CA 706, DE 509, BR 391, JP 252, CN 239, …, IN 112.
  Coverage of 2025 hours: T 84.0%, Td 78.9%, WD 66.6%, WS 78.2%, SLP 42.4%, raw precipitation 26.3%.
  Dropped by quality code (largest): WD code 9 (missing) 137.3M; T code 7 (erroneous) 7.56M; Td code 7 7.50M;
  precipitation "Null" 2.55M; SLP 9 1.65M; WS 3 1.53M; values whose code is the text "Null" (T 0.99M, about 0.08%
  of temperature hours) are dropped as the rule says (not in the passed list). Dropped by our QC: WD out of 0–360
  (the 999 "variable" code) 104.8M; WS 8-SD 0.49M; SLP bounds 0.25M; Td 8-SD 0.24M; Td above T 0.19M; WS bounds
  0.19M; SLP 8-SD 0.07M; T 8-SD 0.04M; others < 0.03M. Full counts: `summary.json` beside the data.
- **24 Nov 2026, 15:55 IST, before any Stage 1 training — a fourth size, 250M (Adi's request).** "250M" = the trained
  10M grown `--grow 3,7,7` (width 2,040, depth 7 + 7): **251,879,368** parameters, learning rate 2 × 10⁻⁴, the same
  200,000-step cap, batch and data; trained last, after 97.6M. The selection rule is unchanged (lowest 2023 validation
  E; within 0.5% → the smaller), so 250M is used only if it beats every smaller candidate by more than 0.5%. Added
  prediction **W11**: 250M is selected (P = 0.25); W1 now reads "30M, 100M or 250M" (P unchanged, 0.70). Expected cost
  of the 250M run: about 40–50 A100-hours (several 10-hour sessions; it resumes from its last checkpoint). If it runs
  out of GPU memory at batch 256, the batch change is recorded as a deviation before the run continues.
- **24 Nov 2026, 15:55 IST — forecast archives for Stage 2, checked.** Open-Meteo's AWS bucket (`openmeteo`) holds each
  model's continuous best-estimate series (`data/<model>/<variable>/chunk_*.om`), not the forecasts as issued at each
  lead, so it cannot serve as a fair Stage 2 input or opponent. The Previous Runs API is limited to 10,000 weighted calls a
  day, far short of 8,791 stations × 2 years. Stage 2 will therefore extract the issued forecasts at the frozen stations
  from the public run archives: ECMWF open data (IFS, AIFS) and NOAA GFS on AWS, 00 and 12 UTC runs, 2024–2025, leads to
  168 h, variables 2 m temperature and dewpoint, 10 m wind, mean sea-level pressure, precipitation. The fetcher and the
  exact archive depth per system are recorded in a further addendum before Stage 2 data are downloaded.
- **24 Nov 2026, 20:20 IST — data reproduced and stored.** A second, independent GHCNh fetch (needed after the first
  runtime ended) reproduced the frozen list exactly: 13,267 → 9,335 → 8,853 → **8,791 stations, SHA-256 `dd1da8fc…`
  (match)**. The packed yearly files, `stations.json` and `summary.json` are on Drive (`PWM-WX/isd`). Stage 1 training
  has not started: Colab reports no GPU available for the lab's account.
- **24 Nov 2026, 22:10 IST — Stage 2 archive depths, checked before the Stage 2 download.** Trial (`fetch_nwp_runs.py`,
  2025-03-01, 00 and 12 UTC, leads 0–48 h, all 8,791 stations): GFS and IFS have temperature at every station and lead
  (share present 1.000); AIFS 0.529, because AIFS open data are 6-hourly (the 3-hourly leads in between do not exist).
  Values at station 0 (ACW00011647, St John's, Antigua), 24 h lead: T 18.0 / 14.8 / 15.5 °C (GFS / IFS / AIFS).
  The trial found one error, now fixed: AIFS precipitation is already in mm, and the fetcher multiplied it by 1,000;
  conversion now follows each GRIB message's own units. Archive depth (index files probed on 2024-01-15, 2024-02-01,
  2024-03-01, 2024-06-01, 2025-01-01, 2025-02-24, 2025-02-26): **GFS** present on every date probed (from 2024-01-15); **IFS 0.25°** absent on
  2024-01-15, present from 2024-03-01, but without 2 m dewpoint on 2024-03-01 (dewpoint present by 2024-06-01);
  2024-02-01 was throttled (HTTP 503) and is settled by the full download; **AIFS** under `aifs/0p25` from 2024-03-01 to
  2025-02-24 and under `aifs-single/0p25` from 2025-02-26 (the fetcher reads both). The full download runs 2024-02-01 →
  2026-01-01 for IFS and GFS first (AIFS after); months, leads or fields an archive lacks stay missing (NaN) and are
  reported with the Stage 2 results, never filled. Comparisons in a period are made only where every compared system
  has a forecast.

- **24 Nov 2026, 23:40 IST, before any Stage 1 training — the 250M candidate built and checked; how batch 256 fits.**
  `atlas/wx/build_250m.py` grows a 10M model built exactly as Stage 1 builds it with `--grow 3,7,7`: **251,879,368
  parameters (the registered count)**, width 2,040, 12 heads, depth 7 + 7; check G0 (same forecasts before and after
  growth, on real-format windows) passes with a maximum difference of 0. This used an untrained 10M and synthetic data:
  it checks the build, not the model; the registered 250M is grown from the *trained* Stage 1 10M. One training step
  needs about 1 GB per window in float32 on top of about 4 GB of weights, gradients and optimiser state, so batch 256
  does not fit in one pass on an A100. Rule, fixed now: each batch of 256 is processed in equal parts (`--micro`; 2 on an
  80 GB A100, 4 on a 40 GB one; for any model, doubled automatically on an out-of-memory error, at most 8), with the same
  256 samples and one optimiser update per step. The loss is averaged over the parts, which weights the parts equally
  rather than by their number of observed values, a negligible difference. This is not a change of batch size, so no
  deviation is recorded for it; the number of parts used is written into each run's result file (`micro`).
- **25 Nov 2026, 00:05 IST, before any Stage 1 training — Stage 1 may run on a Colab TPU.** A v5e-1 TPU (Colab Pro,
  about 3.3 compute units per hour, against about 11 for an A100) runs the Stage 1 trainer through native TorchTPU
  (`torch_tpu` 0.2.0 with PyTorch 2.14), measured on synthetic data with `tpu_smoke.sh`: 10M at batch 256 in one pass,
  0.11 s per step; the grown 97.6M at batch 256 in 4 parts, 0.44 s per step; check G0 holds after growth on the TPU.
  On a TPU the trainer computes in float32 (weights, gradients, optimiser), with matrix products at the TPU's default
  precision (bf16 passes with float32 accumulation); bf16 autocast is off because `torch_tpu` 0.2.0 fails on layer
  normalisation under it. On an A100 the trainer uses float16 autocast as before. Each run's result file records the
  device (`gpu`) and the batch split (`micro`). Data, model, schedule, selection rule and test are unchanged; a model's
  device is not a criterion, so no deviation is recorded for it. The 250M candidate needs about 70 TPU-hours at
  this speed (more than the lab's Colab units), so it waits for an A100 as planned.

## Deviations

None yet.
