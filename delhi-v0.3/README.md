# PWM-W Delhi v0.3: weather league against the global AI weather models

ParadoxAI Lab. The question for this round is whether a small world model, trained only on Delhi's own station
observations, can forecast the next 24 hours at those stations better than the global AI weather models.

**Status:** METAR and WMO leagues done; the CPCB league and the runs of FourCastNet / GraphCast / GenCast Mini that
we do ourselves are still running.

## Results

All numbers below come from real held-out data. A "BEATS" verdict follows the strict pre-set rule: a significantly
lower MAE than both the global model's latest run and that run after a local bias correction. Significance means
Diebold–Mariano p < 0.05 and a day-block bootstrap 95% interval below zero.

### METAR league

Six airports: Delhi Palam, Jaipur, Amritsar, Lucknow, Udaipur and Bhopal. Test period 2026-02-01 to 2026-10-31,
with 1,089 forecast origins. Values are MAE.

| Entry | Temp °C | RH % | Wind m/s |
|---|---|---|---|
| **PWM-W pure** (observations only) | 1.260 | 6.235 | 1.015 |
| PWM-W pure, 1–6 h | 0.948 | 4.875 | 0.928 |
| PWM-W pure, 13–24 h | 1.411 | 6.880 | 1.053 |
| PWM-W hybrid (global forecasts ≥ 48 h old as inputs) | 1.170 | 5.943 | 0.962 |
| TimesFM 3.0 | 1.341 | 6.523 | 1.032 |
| Chronos-2 | 1.357 | 6.615 | 1.036 |
| TimesFM 2.5 | 1.403 | 6.737 | 1.042 |
| ECMWF AIFS, latest run + bias correction | **0.872** | **5.311** | **0.910** |
| ECMWF AIFS, run 24 h before + bias correction | 1.034 | 6.095 | 0.957 |
| NOAA AIGFS (GraphCast-based), latest run + bias correction | 1.216 | – | 1.025 |
| NOAA GFS, latest run | 2.296 | 19.13 | 1.243 |

**Verdicts, pure model**

| Opponent | Verdict |
|---|---|
| NOAA GFS | **BEATS** on all three variables |
| NOAA AIGFS | Ties on wind; loses on temperature by 3.6% vs bias-corrected |
| ECMWF AIFS, ECMWF IFS, DWD ICON | Loses on all three |

**Verdicts, hybrid:** **BEATS AIGFS** on temperature and wind, and **BEATS GFS** on all three variables.

In the first 6 hours the pure model beats every global model's 24 h-old forecast. Its error then grows with lead
time.

### WMO league

Twenty NOAA ISD stations around Delhi, including Safdarjung and Palam. Test period 2025-03-01 to 2025-08-20, with
689 origins.

**Verdicts, pure model**

| Variable | Verdict |
|---|---|
| Wind speed | **BEATS ECMWF AIFS, ECMWF IFS 9 km, ECMWF IFS 0.25, DWD ICON and NOAA GFS** (16–19% below the bias-corrected ECMWF forecasts) |
| Humidity | **BEATS** IFS 9 km and GFS; ties IFS 0.25; loses to AIFS and ICON |
| Temperature | **BEATS** GFS; loses to AIFS, IFS and ICON |

Removing the station graph clearly worsens validation (0.3948 vs 0.3864).

TimesFM 2.5 ran out of GPU memory in this run, so it is missing here (fixed in v0.4).

### What does not hold

- **Temperature:** ECMWF's models with a local bias correction stay ahead of a station-only model after the first
  hours.
- **The strict rule is generous to the global models.** Their "latest run" is often issued after our forecast start.
  v0.4 also reports a fairer comparison against the newest run published before the start.

## Entries

**Ours**
- **PWM-W (pure):** inductive graph world model over the station network. Its inputs are past observations only;
  nothing from any global model goes in. The model setting is chosen on validation data alone, and the entry is
  the mean of 3 seeds.
- **PWM-W hybrid:** the same model, plus ECMWF IFS (0.25°) and AIFS forecasts issued at least 48 hours earlier as extra
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
