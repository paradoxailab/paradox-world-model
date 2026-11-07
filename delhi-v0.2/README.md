# Paradox World Model: Delhi v0.2 (hybrid)

Delhi v0.1 (branch `delhi-v0.1`) beat every simple baseline by 19-29% but lost to Google TimesFM 3.0 / 2.5 and was
level with Amazon Chronos on PM2.5. v0.2 targets the reasons:

| v0.1 weakness | v0.2 change |
|---|---|
| 24 h of input vs 512 h for the foundation models | long context: 72 h hourly + 14 daily means |
| no knowledge of tomorrow's weather (wind, humidity, rain drive Delhi's smog) | real 1-day-ahead weather forecasts (Open-Meteo Previous Runs API: for each hour, the forecast issued >= 24 h earlier; archived from Jan 2024) |
| learning everything from 16 months of one city | **hybrid**: Chronos-2 and TimesFM 2.5 (Apache-2.0) forecast first; PWM-W corrects their median with the station graph, the other pollutants, meteorology and the weather forecast |
| four targets hurt PM2.5 on validation | PM2.5 only |

Variants (all trained on the same origins, every 3 h): A0 v0.1-style (seeds 0-2 give the noise floor), A1 long
context, A2 + weather forecasts, A3 long + hybrid, A4 long + weather + hybrid. The one with the lowest validation
PM2.5 MAE is kept only if it beats A0 by more than 2 sigma; 3 fresh seeds, CQR, test once.
Opponents: TimesFM 3.0 (univariate and multivariate; evaluation only, non-commercial licence), TimesFM 2.5,
Chronos-2, Chronos-Bolt, zero-shot, same windows, significance tests. TimesFM 3.0 is never used as a backbone.

## Results (Kaggle T4, 2026-11-07)

**Validation choice:** A4, which uses long context, weather forecasts and the hybrid. It scored 20.17 µg/m³ MAE,
against A0's 21.75 ± 0.22. Note that A4 is a hybrid: its backbone is Chronos-2 and TimesFM 2.5's own forecast, which
PWM-W corrects.

**Test results, PM2.5:**
- Track S is the seen stations, track U the unseen stations.
- MAE in µg/m³; differences are against PWM-W Delhi v0.2. Significance uses DM plus a day-block bootstrap.

| Opponent | Track S MAE | vs v0.2 | Track U MAE | vs v0.2 |
|---|---|---|---|---|
| **PWM-W Delhi v0.2** | **31.28** | – | **27.59** | – |
| CAMS global (ECMWF Copernicus), latest | 62.86 | **WIN −49.8%** | 53.53 | **WIN −47.5%** |
| CAMS + local bias correction | 41.87 | **WIN −24.6%** | 39.81 | **WIN −29.4%** |
| Chronos-2 | 31.17 | tie (+0.4%) | 27.41 | tie (+0.7%) |
| Chronos-Bolt | 31.35 | tie (−0.2%) | 27.94 | tie (−1.2%) |
| TimesFM 2.5 | 30.83 | tie (+1.5%) | 27.10 | tie (+1.8%) |
| TimesFM 3.0 | 30.31 | tie (+3.2%) | 26.84 | tie (+2.8%) |
| TimesFM 3.0 multivariate | 29.95 | tie (+4.5%, p=0.08) | 26.16 | **LOSS +5.5%** |
| v0.1-style PWM-W | 35.50 | **WIN −11.9%** | – | – |

**Plain reading:**
- PWM-W beats ECMWF's CAMS global air-quality forecast by about half, and still by a quarter after bias correction.
- It is level with the foundation models on MAE. On unseen stations it loses to multivariate TimesFM 3.0.
- Because A4 corrects Chronos-2 and TimesFM 2.5's own forecasts, these ties are not an independent model matching
  them.

```
python tools/fetch_delhi.py && python tools/fetch_wxfc.py && python tools/fetch_cams.py && python tools/backbone.py   # GPU for the backbone
python run_delhi.py
```
