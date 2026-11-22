# Atlas-Delhi: pre-registration (ParadoxAI Lab, 22 November 2026)

**Question.** Is there a forecast of Delhi's weather more accurate than ours? We say "the most accurate weather
forecast for Delhi among those tested" only if the rules below give that result, and "best weather model in Delhi"
only if part B also gives it. Everything in this file was committed **before** any Atlas-Delhi forecast and before any
forecast at the Delhi stations for 2025–26 was scored by Atlas-100M. Changes after this commit are dated deviations
at the end; the git history is the record.

**What was already seen** (disclosed so it can be weighed): our earlier Delhi studies scored small PWM-W models on six
airport METAR stations including Palam (test February–October 2026) and on 25 CPCB stations (2024–25)
(`atlas/results/kaggle/pwm-weather-v05-metar/`, `pwm-v20/`). There the PWM-W hybrid beat every global forecast
published before the forecast start, but bias-corrected ECMWF AIFS given its newest run was still more accurate on
temperature (0.87 vs 1.01 °C), and Chronos-2 beat the pure model on CPCB temperature. Those results shaped this plan
(the upper-bound family F2 and the Chronos-2 opponent). No Atlas-100M or Atlas-Delhi forecast for Delhi has been
scored.

## Part A: archived forecasts, 1 January 2025 – 31 October 2026

**A1. Model.** *Atlas-Delhi* is the Atlas-100M weather view (98.6M parameters, `atlas/m100`) widened, without
changing its forecasts at step 0, to read every global system available in the archive, in the H2 form: for each
system, the freshest run published at least 12 h before the forecast start, plus a flag channel per system
(`hybrid.py`, `fresh_mask`). Systems: ECMWF IFS 0.25°, ECMWF AIFS, NOAA GFS, GraphCast, NOAA AIGFS, DWD ICON,
UK Met Office global, Météo-France ARPEGE, JMA GSM, CMA GRAPES, Canada GEM; a system with no archived data is left out.

**A2. Data.** Truth: NOAA ISD-Lite hourly observations (the WEATHER-5K source) at **New Delhi Palam** (WMO 42181,
VIDP) and **New Delhi Safdarjung** (WMO 42182, VIDD), fetched once by `tools/fetch_isd_live.py --end 2026-11-01T00`.
Global systems: the Open-Meteo Previous Runs API (`hybrid.py fetch --systems all`), forecasts issued 24 h and 48 h
before each valid hour. Variables: temperature, dewpoint, wind direction, wind speed, sea-level pressure.

**A3. Training (nothing after 31 December 2024 is used).** Stage 1: the 16 Indian WEATHER-5K stations within 700 km
of Safdarjung (`m100/north_india_stations.json`), train 1 January – 31 October 2024, early stopping on the two Delhi
stations, 1 November – 31 December 2024, same settings as H2. Stage 2: continue on the two Delhi stations only
(learning rate 2·10⁻⁵), same validation; it is kept only where it improves validation, so the scored model is
`atlasdelhi2_best.pt`. No other candidate, seed or setting is tried; anything else is a deviation.

**A4. Test.** Forecast starts every 6 h from 1 January 2025 00 UTC to the last start whose 24 h fit before
1 November 2026; lead 1–24 h. Every forecast is scored on exactly the hours where the truth and both compared
forecasts exist (PREREG deviation 8 rule).

**A5. Opponents.**
- **F1, published before the start** (the realistic comparison): each system raw and bias-corrected (minus its mean
  error at that station, variable and lead over the 30 days before the start), on the freshest run published 6 h
  after issue (as in section H of `m100/PREREG.md`); the mean of all bias-corrected systems; Atlas-100M-H2, the
  registered hybrid and pure Atlas-100M (unchanged checkpoints); Chronos-2 and TimesFM 2.5, zero-shot on each
  station's past 512 h.
- **F2, the upper bound:** each system's day-1 run raw and bias-corrected, *including runs not yet published at the
  forecast start*. Nobody can issue these forecasts in real time; this is the bar the earlier study missed.
- **F3:** the 24-h maximum and minimum temperature of each forecast window (windows with at least 20 observed hours),
  against F1.

**A6. Statistics.** Two stations make a station bootstrap meaningless, so: Diebold–Mariano test (Newey–West) on the
daily mean error difference, and a moving-block bootstrap over days (7-day blocks, 10,000 resamples) for the 95%
interval. Holm within each family. **WIN** = lower MAE, Holm-adjusted p < 0.01 and the interval excluding 0; **LOSS**
the mirror image; else **TIE**. Descriptive: MAE by season (winter DJF, pre-monsoon MAM, monsoon JJAS,
post-monsoon ON).

**A7. Claim rule.** "Most accurate 24-h forecast at Delhi among those tested (archived)" only if Atlas-Delhi has no
LOSS in F1 and F3 and WINs on temperature, dewpoint and wind speed against every opponent in F1.

**A8. Predictions** (scored as held / failed):
- **D1** Atlas-100M-H2, unchanged, WINs against raw IFS on temperature at Delhi.
- **D2** Atlas-Delhi WINs against every raw system on temperature, dewpoint and wind speed.
- **D3** Atlas-Delhi WINs against bias-corrected IFS and bias-corrected AIFS (F1) on temperature.
- **D4** Against bias-corrected IFS on sea-level pressure, Atlas-Delhi does **not** WIN.
- **D5** Atlas-Delhi has lower temperature MAE than Atlas-100M-H2 at Delhi.
- **D6** In F2, Atlas-Delhi does not LOSE to newest-run bias-corrected AIFS on temperature.
- **D7** Atlas-Delhi WINs against Chronos-2 on temperature.
- **D8** For every forecaster, winter (DJF) temperature MAE exceeds its whole-period temperature MAE.

## Part B: live, 1 December 2026 – 28 February 2027 (the fog season)

**B1. Log.** From 22 November 2026, `.github/workflows/delhi-live-log.yml` runs `atlas/delhi_live/log_live.py`
twice a day (08:47 and 17:47 IST) and commits to the branch `delhi-live`: IMD's official city forecasts for
Safdarjung, Palam, Ridge and Lodi Road (7 days of maximum and minimum temperature and weather, including fog) and the
observations IMD prints on the same page; the latest forecast of every global system Open-Meteo serves (hourly,
3 days); METAR from VIDP, VIDD and VIDX. The commit time is the proof of issue.

**B2. Our forecast.** Atlas-Delhi's forecast for the same stations must be committed to `delhi-live` by the same
08:47 IST run (or earlier). A forecast committed later is not scored, and a missing day counts against us (scored as
the latest committed forecast we had, or excluded for **all** forecasters if none of ours existed, reported). If the
live runner is not ready by 1 December, part B starts on the first day it is and ends 90 days later.

**B3. Target and test.** Tomorrow's maximum and minimum temperature at Safdarjung and Palam, using the 08:47 IST log
(IMD's minimum = the 24 h to 08:30 IST, its maximum = the day's; Open-Meteo and our hourly forecasts are reduced to the
same windows). Truth: IMD's observed values printed the next days, METAR as the check. Paired test over days as A6,
Holm over all opponents and both targets. Descriptive: fog days (IMD's fog wording against METAR visibility < 1,000 m).

**B4. Claim rule.** "Best weather forecast for Delhi in this test" only if Atlas-Delhi WINs on both targets against
IMD's official forecast and has no LOSS against any system.

## Data used, and what needs an account

Used now (no account): NOAA ISD-Lite, Open-Meteo (non-commercial terms), IMD city pages, Iowa Environmental Mesonet
METAR archive, OpenCity copies of CPCB Delhi data. With accounts the lab owner creates (keys kept in Colab / GitHub
secrets, never in code): IMD API (AWS observations, forecasts), OpenAQ and data.gov.in (CPCB / DPCC live data),
Copernicus CDS (ERA5). Adding any of these as an *input* to Atlas-Delhi is a dated addendum made before the
affected test is scored.

## Deviations

None yet.
