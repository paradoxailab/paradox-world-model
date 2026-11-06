# Paradox World Model: Delhi v0.1

A working world-state model of Delhi's air, built on real public data: CPCB's continuous monitoring stations
(39 stations, published by OpenCity as "Delhi Hourly Air Quality Reports", public domain), hourly 2017-2023 and
15-minute 2024-25, every station measuring PM2.5, PM10, NO2, ozone, CO, SO2, NH3, NO and the meteorology
(temperature, humidity, wind speed and direction, solar radiation, pressure).

## Results (Kaggle CPU, 9.2 h, run on 2026-11-05/06; notebook output `delhi_v01_report.md`)

Data: 39 stations, 2024-01-01 .. 2025-12-31 hourly (17,544 h), 0 files with doubtful timestamps; solar radiation
peaks at 12:00 in every file, so the clock is Indian time. Train 2024-01 .. 2025-05-02, validation to 2025-07-02,
**test 2025-07-03 .. 2025-12-31** (monsoon to winter smog). 8 stations held out entirely (Track U).

PM2.5, next 24 h, Track S (training stations), ug/m3:

| Model | MAE | RMSE | MAPE % | IS80 | MAE@6h | MAE@24h |
|---|---|---|---|---|---|---|
| TimesFM 3.0 multivariate (Google), zero-shot | **29.95** | **54.09** | **30.5** | **145.9** | **27.61** | 35.09 |
| TimesFM 3.0 (Google), zero-shot | 30.31 | 54.30 | 31.0 | 147.2 | 28.89 | **34.68** |
| TimesFM 2.5 (Google, 200M), zero-shot | 30.83 | 55.52 | 30.8 | 150.3 | 29.17 | 35.34 |
| Chronos-2 (Amazon, 120M), zero-shot | 31.17 | 55.81 | 32.1 | 150.9 | 29.29 | 35.99 |
| Chronos-Bolt (Amazon, 205M), zero-shot | 31.35 | 56.00 | 32.0 | 150.9 | 29.33 | 36.26 |
| **PWM-W Delhi v0.1** (0.88M params, 3 seeds) | 32.63 | 57.76 | 33.5 | 163.7 | 28.39 | 38.30 |
| Same hour yesterday | 40.30 | 70.24 | 44.5 | 257.0 | 39.94 | 40.35 |
| Last observed value | 46.01 | 81.07 | 47.7 | 311.8 | 47.16 | 38.94 |

* PWM-W beats every baseline by 19-29% MAE (significant), works at stations it never trained on (Track U MAE 28.26)
  and barely degrades with 30% of stations dark (Track D MAE 32.77).
* **It does not beat the foundation models on Delhi PM2.5**: significantly worse than TimesFM 3.0 (+7.7% MAE),
  TimesFM 3.0 multivariate (+9.0%) and TimesFM 2.5 (+5.9%); level with Chronos on MAE (+4%, not significant) but
  worse on MAPE and interval scores. It is competitive at 1-6 h and falls behind at 12-24 h.
* Does the "world" help? The station graph does (without it MAE is 9.4% worse, significant). Meteorology and the
  other pollutants did not pass the validation rule (MAE 4% better on test, other metrics not significant).
  Forecasting four pollutants together was worse on validation than PM2.5 alone (by 6 sigma), so the final model
  forecasts PM2.5 only.
* Likely causes, to test next: a 24-hour input window plus 3 lag days against 512 hours of history for the
  foundation models; 16 months of training with a single full winter; and no future weather (wind and mixing height
  drive Delhi's smog). Next: long context, the 2017-23 AQI history as pretraining signal, weather forecasts as inputs,
  and fire counts (NASA FIRMS) for the stubble-burning season.

The latest forecast (`delhi_forecast.json`) covers 2026-01-01 00:00-23:00 IST for all 39 stations: the first day
after the data ends. Live use needs a current CPCB feed.

**What it forecasts**: the next 24 hours of four pollutants together (PM2.5, PM10, NO2, ozone) at every station,
with calibrated 80% bands, from everything every station measured in the last day plus the same hours on earlier
days, mixed across the station network (PWM-W graph attention; stations linked by how their PM2.5 moves together).

**How it is tested** (`run_delhi.py`, rules fixed before the run, test scored once):
* last 182 days = test, the 61 days before = validation, everything earlier = training;
* Track S (training stations), Track U (20% of stations never used in training), Track D (30% of stations dark);
* "does the world help?": the model without meteorology/other pollutants, without the station graph, and with one
  target instead of four, each kept or dropped by a validation rule;
* Google TimesFM 2.5 / 3.0 (univariate and multivariate) and Amazon Chronos-Bolt / Chronos-2, zero-shot on PM2.5
  with 512 hours of history, on the same windows; Diebold-Mariano and day-block bootstrap significance tests;
* finally, a real forecast: the next 24 h after the last hour in the data, for every station
  (`results/delhi_forecast.json`, ready for Atlas).

Traffic: there is no open Delhi traffic-sensor network comparable to England's WebTRIS; NO2, NO and CO here are
dominated by vehicle exhaust, so the model already carries a traffic signal. A live traffic feed (e.g. TomTom
Traffic Flow, free developer key) is the next data source to add.

```
python tools/fetch_delhi.py        # ~10 min, writes data/raw/DELHI.npz
python run_delhi.py                # CPU or GPU; resumable (PW_CACHE)
python run_delhi.py --quick --opponents ""   # 1-minute pipeline check
```
