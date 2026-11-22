# Atlas-AQ: pre-registration of the design (ParadoxAI Lab, 23 November 2026, before any Atlas-AQ data is fetched)

**Goal (Adi, 23 Nov 2026).** Beat the operational air-quality forecasts of the world on PM2.5, NO₂ and O₃ at monitoring
stations in India, the USA and China: CAMS (ECMWF), NASA GEOS-CF, Microsoft Aurora, SAFAR / IITM's Delhi early-warning
system, NOAA's AQM (NAQFC) and CMA's models. The model size may go up or down; it is chosen on validation only. Nothing
here guarantees a win: the rules below decide, and every loss is published.

**Why a hybrid, not a bigger model.** Our weather results: 24.1M → 98.6M gave nothing; reading ECMWF / NOAA forecasts
beat IFS and GFS. Atlas-AQ therefore reads the operational forecasts it competes with (as Atlas-100M-H2 did) and is sized
by validation.

## 1. Opponents and whether a fair comparison is possible

A fair comparison needs the opponent's forecasts **as issued before the forecast start**, at the same stations and hours.

| Opponent | Archive of issued forecasts | Comparison | Notes |
|---|---|---|---|
| CAMS global (ECMWF) | ADS `cams-global-atmospheric-composition-forecasts`, 2015–present, 00/12 UTC, 5 days, 0.4°, CC-BY | **archived test** | ADS account + licence (lab owner) |
| Microsoft Aurora 0.4° air pollution | checkpoint `aurora-0.4-air-pollution.ckpt` (HF `microsoft/aurora`), run by us from CAMS analyses | **archived test**, subset of starts (compute) | 12-hour steps → compared at leads 12 and 24 h |
| NASA GEOS-CF | NCCS portal `fcst` directories; depth of the archive to be checked | archived test **if** the archive covers the test year | else live log |
| NOAA AQM / NAQFC (USA) | AWS `noaa-nws-naqfc-pds`, from 1 Jan 2020, raw and bias-corrected O₃ and PM2.5 | **archived test** (USA, O₃ and PM2.5; no NO₂) | no account |
| SAFAR / IITM Delhi EWS | no public archive found | **live test only** (daily log from 1 Dec 2026) | Indian sites; fetched where reachable |
| CMA operational models (China) | no public archive found | **not comparable**; stated as such | China tested against CAMS, Aurora, GEOS-CF only, and only if station data are available |
| Time-series foundation models (Chronos-2, TimesFM 3.0) and persistence | run by us | archived test | zero-shot |

## 2. Data

Truth: hourly station observations — India: CPCB / DPCC (OpenAQ archive, OpenCity, Kaggle copy); USA: AirNow (OpenAQ
archive); China: national network where a public archive exists (to be checked; none is assumed). Inputs: the stations'
own and neighbours' history, CAMS forecasts (and GEOS-CF if archived), weather forecasts (Open-Meteo Previous Runs:
IFS, AIFS, GFS), NASA FIRMS fire counts (key held by the lab owner).

Split by time (fixed now): train 1 Jan 2021 – 31 Dec 2024; validation 1 Jan – 30 Jun 2025; **test 1 Jul 2025 – 30 Jun
2026** (one full year: summer ozone, monsoon, two smog seasons' edges, the 2025–26 winter). Live test (SAFAR / IITM,
and all others again): 1 Dec 2026 – 28 Feb 2027 in Delhi.

## 3. Model and size selection

Atlas-AQ = the Atlas core with the air-quality adapter, widened (function-preserving, check H0) to read each forecast
system's PM2.5, NO₂ and O₃ plus a flag, from the freshest run published at least 6 h before the forecast start.
Three candidates, nothing else: **1M** (Atlas-India v1.0 lineage, widened), **25M** (grown from Atlas-5K 25M's core),
**100M** (Atlas-100M widened). The candidate with the lowest validation error (mean of PM2.5, NO₂, O₃ MAE, each divided by
its training standard deviation) is the one tested; within 0.5% of each other → the smaller. The test year is scored
once, for that model only.

## 4. Test, statistics, claims

Forecast starts every 6 h; leads 1–24 h hourly (Aurora: 12 and 24 h). Both forecasts in a pair scored on the same hours
(deviation 8 rule). Opponents raw and bias-corrected (30-day trailing, per station, pollutant and lead). Diebold–Mariano
(Newey–West) on daily mean differences + station-block bootstrap 95% interval; Holm within each family (one family per
region × pollutant). WIN / TIE / LOSS as in `m100/PREREG.md`.

**Claim rule.** "Most accurate station-level forecast of <pollutant> in <region> among those tested" only if Atlas-AQ
WINs against every comparable opponent in that region and pollutant, raw and bias-corrected. No claim about CMA. No
"best in the world" claim unless that holds in all three regions for that pollutant.

## 5. Predictions (scored as held / failed)

- **Q1** WIN against raw CAMS on PM2.5, NO₂ and O₃ in India (85%).
- **Q2** WIN against bias-corrected CAMS on PM2.5 in India (60%).
- **Q3** WIN against Aurora on PM2.5 in India at 24 h (55%).
- **Q4** WIN against NOAA's bias-corrected O₃ in the USA (40%).
- **Q5** Not a WIN against bias-corrected CAMS on NO₂ in the USA (50%).
- **Q6** The selected size is 1M or 25M, not 100M (70%).
- **Q7** Live Delhi, 24 h PM2.5: WIN against SAFAR / IITM (50%).

## 6. Before any run (steps, in order; each recorded with its date)

1. Check the GEOS-CF forecast archive depth and the China station archive; update §1 by a dated addendum **before** any
   data is downloaded for training.
2. Lab owner: ADS account + CAMS licence; FIRMS key and OpenAQ key as secrets.
3. Fetch, build stations lists (all CPCB/DPCC; AirNow; China if available), freeze them by hash.
4. Train the three candidates on 2021–2024; select on validation; score the test year once.

## Addenda (dated; before any Atlas-AQ data is downloaded)

- **23 Nov 2026, 03:45 IST — GEOS-CF archive checked.** NASA's OPeNDAP server lists dated GEOS-CF v2 forecast runs
  (`fcst/aqc_tavg_1hr_glo_L1440x721_slv.<YYYYMMDD>_09z`, 463 entries) starting **5 August 2025**. GEOS-CF is therefore
  compared on the archived test year from 5 Aug 2025 (the July 2025 starts have no GEOS-CF forecast and are scored without
  it), using the 09 UTC run issued before each forecast start.

## Deviations

None yet.
