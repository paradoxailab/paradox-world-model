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

```
python tools/fetch_delhi.py && python tools/fetch_wxfc.py && python tools/fetch_cams.py && python tools/backbone.py   # GPU for the backbone
python run_delhi.py
```
