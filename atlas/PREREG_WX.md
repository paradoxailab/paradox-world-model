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

## Deviations

None yet.
