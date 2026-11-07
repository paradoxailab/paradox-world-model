# PWM-W Delhi v0.4: learned-correction hybrid and a fair comparison

ParadoxAI Lab. v0.4 builds on v0.3 (the weather league against the global models). The question: can learned local
correction beat the global AI weather models at stations, using only forecasts that exist when our forecast is made?

## What is new in v0.4

1. **Learned-correction hybrid (H2).** The base forecast is the bias-corrected mean of ECMWF IFS 0.25, ECMWF AIFS,
   DWD ICON and NOAA GFS. Each uses its newest run published before the forecast start: the 24 h-old run for hours
   0–16, the 48 h-old run after that. PWM-W then learns the correction from the station network's own
   observations. Validation picked this design over v0.3's inputs-only hybrid (validation 0.348 vs 0.372; the pure
   model scores 0.393).
2. **A fair comparison, reported alongside the strict one.**
   - ISSUED-BEFORE-START scores each global model on its newest run published before our forecast start.
   - STRICT, as in v0.3, scores it on its latest run, which is often issued after our start (generous to it).
   - Both rules require significance against the raw forecast and against the bias-corrected one.
3. **A strong new opponent:** the bias-corrected 4-model ensemble on its own.
4. **Joint training across station networks (P4).** Validation improved from 0.3934 to 0.3920, which is below the
   2-sigma bar, so it was not adopted.
5. **Fixes:** GPU memory is freed before the foundation-model opponents (TimesFM 2.5 had run out of memory in v0.3).

## Results: METAR league

Six airports, including Delhi Palam. Test period 2026-02-01 to 2026-10-31, 1,089 origins. Differences are MAE
(negative means PWM-W is better); every verdict passed significance.

**Hybrid under the ISSUED-BEFORE-START rule** (newest run published before the start, bias-corrected)

| Opponent | Temp | RH | Wind |
|---|---|---|---|
| **ECMWF AIFS** | **BEATS −4.4%** | **BEATS −11.8%** | **BEATS −7.4%** |
| ECMWF IFS 9 km | BEATS −21.0% | BEATS −24.2% | BEATS −13.4% |
| ECMWF IFS 0.25 | BEATS −19.4% | BEATS −22.0% | BEATS −12.7% |
| DWD ICON | BEATS −22.1% | BEATS −23.6% | BEATS −11.0% |
| NOAA AIGFS (GraphCast-based) | BEATS −21.0% | – | BEATS −17.7% |
| NOAA GFS | BEATS −37.2% | BEATS −41.4% | BEATS −29.3% |
| Bias-corrected 4-model ensemble | WIN −6.9% | WIN −11.5% | WIN −3.6% |

**Hybrid under the STRICT rule** (latest run + bias correction)

| Opponent | Verdict |
|---|---|
| Wind | **BEATS** AIFS, IFS 9 km, IFS 0.25, ICON, AIGFS and GFS |
| Humidity | **BEATS** IFS and ICON; **loses** to AIFS (+3.3%) |
| Temperature | **Loses** to AIFS (+15.6%) and IFS 0.25 (+3.3%); ties IFS 9 km and ICON; **BEATS** AIGFS and GFS |

**Pure PWM-W** (station observations only) against the time-series foundation models, each forecasting from a
station's own last 512 hours. PWM-W wins everywhere, p < 0.01.

| Opponent | Temp | RH | Wind |
|---|---|---|---|
| TimesFM 3.0 | −5.8% | −4.3% | −1.5% |
| TimesFM 2.5 | −10.0% | −7.3% | −2.4% |
| Chronos-2 | −6.9% | −5.6% | −1.8% |

**Bottom line:** with the forecasts that actually exist at forecast time, the hybrid beats ECMWF AIFS, IFS, ICON,
AIGFS and GFS at these airports. Against AIFS's freshest run, often issued after our forecast start, it still loses
on temperature and humidity.

The WMO and CPCB leagues are running (`kaggle_v04.sh`).

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
