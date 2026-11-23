# Atlas-WX: plan to build the most accurate station weather forecast we can, and test it fairly (ParadoxAI Lab, 23 Nov 2026)

Status: **plan, not a pre-registration.** The pre-registration (`PREREG_WX.md`) is written from this plan and committed
before any Atlas-WX training data is downloaded. Nothing here is a result.

## 1. Which "best" is winnable, and which is not

| Arena | Who leads (Nov 2026) | What it takes | Our position |
|---|---|---|---|
| Global gridded fields (ERA5 / analysis verification, 0.25° and finer, 15 days, ensembles) | Google DeepMind WeatherNext 3 (launched 31 Aug 2026; tops Brightband's Operational WeatherBench on 2 m temperature on 26 of 30 August days, by Brightband's report), ECMWF AIFS / IFS, WindBorne WeatherMesh 6 (company claim), Aurora, FuXi, GraphCast/GenCast | petabytes of ERA5, hundreds of accelerators for weeks, live satellite and analysis feeds | **not winnable with our compute**; we do not compete here and never claim to |
| Station (point) forecasts: what a person at a place gets, verified against that station's observation | operational NWP + statistical post-processing (ECMWF point products, NOAA NBM/MOS), and AI global models read at the nearest grid point (RealBench scores AIFS, Aurora, GraphCast, Pangu, FuXi, FengWu, Stormer at 10,000+ GHCNh stations in 2025) | station archives (free), archived NWP at the stations (free for 2022+), modest GPUs | **winnable**: Atlas-100M-H2 already has 11–34% lower error than raw and bias-corrected IFS and GFS on temperature, dewpoint and wind at 178 stations in 2025; it loses on sea-level pressure |

The goal is therefore: **the most accurate station-level forecast of surface weather, worldwide, among every system we can
test fairly.** The claim rule (§6) says when we may say so. "Best weather model in the world" is never claimed.

## 2. What the evidence says to change

1. **Data first, then size.** The WEATHER-5K grid (23 Nov): with ≤ 1/4 of the data, 3M and 10M are no better than 1M;
   with all of it, 1M 0.2929 → 3M 0.2874 → 10M 0.2824 (seed noise 0.08–0.15%). Size pays only once data is there, and
   no fitted law passed the pre-registered test, so the next size must be measured, not extrapolated.
2. **Read the operational forecasts.** The hybrid that reads ECMWF/NOAA runs beat IFS and GFS; growing the
   observation-only model from 24M to 99M gave nothing. The best station forecast is a learned combination of all
   forecasts plus local observations.
3. **Pressure is where we lose.** NWP sea-level pressure is already close to the observation; a residual on the
   freshest NWP run, not a forecast from scratch, is the fix to test.

## 3. Data

- **Stations (truth and history):** NOAA GHCNh / ISD global hourly, all stations with ≥ 5 years of data, 1995–2026
  (expected 10,000–15,000 stations, roughly 10–20× WEATHER-5K's station-days). Variables: 2 m temperature, dewpoint,
  10 m wind (speed, direction), sea-level pressure, precipitation (6 h, where reported). Stations frozen by hash.
- **Operational forecasts at the stations (inputs and opponents):** Open-Meteo Previous Runs (IFS, AIFS, GFS, ICON, GEM,
  JMA, UKMO, ARPEGE, CMA, AIGFS where archived) from 2022; ECMWF open data; NOAA NBM (USA) from AWS.
- **AI global models at the stations (opponents):** RealBench's 2025 station scores (AIFS, Aurora, GraphCast, Pangu,
  FuXi, FengWu, Stormer, at WEATHER-10K stations), recomputed on our station set where their forecasts are released;
  WeatherNext 2/3 only if an archive of issued forecasts is accessible (to be checked; not assumed).

## 4. Model and training

- **Stage 1, observation core:** Atlas grown from 10M (function-preserving) on 1995–2021 station data, all stations;
  candidates 10M, 30M, 100M, each trained to the same token budget; chosen on validation 2022 (within 0.5% → the smaller).
- **Stage 2, hybrid:** the chosen core widened to read every archived forecast system (value + run age + flag), the
  freshest run issued ≥ 6 h before the start; trained 2022-01 → 2024-12; output = residual on the forecast-system
  ensemble mean, per variable.
- **Horizon and uncertainty:** leads 1 h – 10 days (hourly to 48 h, 3-hourly to 10 days); quantile head (10/50/90) scored
  by CRPS as well as MAE; precipitation added (6 h totals).

## 5. Tests

- **Archived test, once:** 1 Jan – 31 Dec 2025, all frozen stations, against raw and 30-day bias-corrected IFS HRES,
  IFS ENS mean, AIFS, GFS, ICON, NBM (USA), the RealBench AI models, Open-Meteo "best match", persistence and
  climatology. Same hours for every pair (deviation 8 rule).
- **Live test:** 90 days from the first day the live runner commits forecasts before verification time (Delhi live test
  from 1 Dec 2026 is the pilot).
- **Statistics:** as `m100/PREREG.md`: Diebold–Mariano (Newey–West) on daily mean differences, station-block bootstrap
  95% interval, Holm within each family (region × variable × lead band); WIN / TIE / LOSS.

## 6. Claim rule (to be fixed in PREREG_WX.md)

"Most accurate station-level forecast of <variable> at <lead band> in <region> among the systems tested" only for a WIN
against every comparable opponent there, raw and bias-corrected, archived **and** live. A worldwide claim for a variable
needs that in every region. Losses are published with the wins.

## 7. Cost (rough; checked on the first runs)

- Station data: ~30–60 GB raw, one Colab session to fetch and pack.
- 10M on WEATHER-5K, all data: 81 min on an L4. Stage 1 with 10–20× the data at 10M / 30M / 100M: roughly 25–40 A100
  hours in total; Stage 2 hybrid: ~10 A100 hours; scoring: ~2 hours.

## Addendum, 23 Nov 2026 21:45 IST: archives checked (step 1; before any download)

- **Open-Meteo Previous Runs:** "most models are archived from January 2024"; GFS 2 m temperature from March 2021, JMA
  from 2018; offsets `previous_day0` … `previous_day7`. → The hybrid trains on **2024** only, and leads stop at **7 days**
  (not 10). The 2025 test is unaffected.
- **WeatherNext 2 (Google DeepMind):** Earth Engine / GCS archive from **1 Jan 2022**, 0.25°, 6-hourly steps to 15 days,
  64 members, 2 m temperature, 10 m wind, MSLP, 6 h precipitation (no dewpoint); historic data CC BY 4.0, access by
  Google's WeatherNext Data Request form. → An opponent (and possible input) **only if the lab owner requests access**;
  the form and its terms are his to accept.
- **RealBench (arXiv 2605.24945, May 2026):** scores AIFS, Aurora, GraphCast, Pangu, FuXi, FengWu, Stormer at 10,000+
  GHCNh stations in 2025; code at github.com/lixruize-del/NWP-Benchmark; release of the forecasts themselves not stated.
  → Their models enter as opponents only if their forecasts can be scored on our stations and hours; otherwise their
  published numbers are cited as context and never compared as if paired.
- **Station truth:** NOAA ISD-Lite on AWS (`noaa-isd-pds/isd-lite/data/<year>/<USAF>-<WBAN>-<year>.gz`, the path our
  Phase 5b live data already used; hourly temperature, dewpoint, SLP, wind direction and speed, 1 h and 6 h precipitation)
  with the station list `isd-history.csv`; GHCNh (`noaa-ghcnh-pds`, CC0) as the fallback if ISD-Lite stops updating.
  Expected data: roughly 4–8× WEATHER-5K's station-days (counted on fetch, not assumed).
- **NOAA NBM (USA):** archive depth at stations to be checked when the US opponents are fetched; until then not listed.

## 8. Order of work

1. Check archives (NWP depth per system at stations, RealBench forecast release, WeatherNext archive, NBM); dated addendum.
2. Write and commit `PREREG_WX.md` (claim rule, predictions with probabilities, splits, opponents).
3. Fetch and freeze stations (GHCNh/ISD); build the packed dataset.
4. Stage 1 candidates → select on validation.
5. Stage 2 hybrid → validation only.
6. Score 2025 once; start the live runner; publish everything.
