# PWM-W Delhi v0.3: weather league against the global AI weather models

ParadoxAI Lab. The question for this round is whether a small world model, trained only on Delhi's own station
observations, can forecast the next 24 hours at those stations better than the global AI weather models.

**Status:** code ready; Kaggle runs pending. Results will be added here when they are in.

## Entries

**Ours**
- **PWM-W (pure):** inductive graph world model over the station network. Its inputs are past observations only;
  nothing from any global model goes in. The model setting is chosen on validation data alone, and the entry is
  the mean of 3 seeds.
- **PWM-W hybrid:** the same model, plus ECMWF IFS and AIFS forecasts issued at least 48 hours earlier as extra
  inputs. It is reported separately and never counted as the pure model.

**Global weather models.** These are the real operational forecasts, archived by the Open-Meteo Previous Runs API:
- ECMWF AIFS (AI)
- NOAA AIGFS (AI, GraphCast-based)
- DWD AICON (AI)
- ECMWF IFS 9 km and 0.25°
- NOAA GFS
- DWD ICON

Each is scored in several versions:
- its latest run (generous to the global model: often issued after our forecast's origin);
- its run from 24 h before the valid time;
- each of the above, after a trailing 30-day local bias correction.

**Models we run ourselves.** NVIDIA Earth2Studio runs FourCastNet 3 / SFNO and, if it fits in the GPU's memory,
GraphCast Operational. Each run starts from the real NOAA GFS analysis at 00 UTC of each test day, and the
forecasts are read at each station at +6, +12 and +18 h.

**Time-series foundation models.** TimesFM 2.5, TimesFM 3.0 (evaluation only, non-commercial licence) and
Chronos-2, each on each station's own last 512 hours.

**Baselines**
- same hour yesterday;
- the last 14 days' daily cycle;
- the daily cycle plus the latest anomaly.

**Not tested:** GenCast and WeatherNext. They have no public forecast archive, and their data needs a Google
Cloud access request.

## Leagues (`pw/leagues.py`)

| League | Stations | Period | Test |
|---|---|---|---|
| METAR | Delhi Palam and Safdarjung airports, plus nearby north-Indian airports below 1,000 m (up to 16; WMO-grade reports, IEM archive) | 2021-01 to 2026-11 (UTC) | 2026-02-01 to 2026-10-31 |
| CPCB | Delhi's CPCB/DPCC/IMD stations' own weather sensors (located by name with OpenStreetMap) | 2024-01 to 2025-12 (IST) | last 182 days |

Targets are 2 m temperature (°C), relative humidity (%) and 10 m wind speed (m/s), forecast for the next 24
hours. Origins are every 6 hours.

## Rule for "beats"

A global model counts as beaten on a variable only if PWM-W's MAE is significantly lower than both:
- its latest run, and
- its bias-corrected latest run.

"Significantly lower" means Diebold–Mariano p < 0.05 and a day-block bootstrap 95% interval below zero. Each
comparison uses only the hours where both forecasts exist. Results are also broken down by lead time
(1–6 h, 7–12 h, 13–24 h).

## Run (Kaggle)

```
pip install -q timesfm chronos-forecasting
python tools/fetch_metar.py                 # WX_METAR.npz
python tools/fetch_nwp.py --league METAR    # NWP_METAR.npz (global models' archived forecasts)
python tools/fetch_delhi.py && python tools/fetch_cpcb_wx.py && python tools/fetch_nwp.py --league CPCB
python tools/earth2_run.py --league METAR --budget_h 7      # GPU: FourCastNet / GraphCast runs
python run_weather.py --league METAR && python run_weather.py --league CPCB
```

## Data licences

- METAR: Iowa Environmental Mesonet archive of public airport reports.
- Global forecasts: Open-Meteo (CC BY 4.0, non-commercial free tier). The underlying models are © ECMWF, NOAA
  and DWD.
- CPCB: OpenCity, public domain.
- Station positions: © OpenStreetMap contributors (ODbL).

No data or weights are stored in this repository.
