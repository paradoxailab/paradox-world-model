# Paradox World Model: Delhi v0.1

A working world-state model of Delhi's air, built on real public data: CPCB's continuous monitoring stations
(39 stations, published by OpenCity as "Delhi Hourly Air Quality Reports", public domain), hourly 2017-2023 and
15-minute 2024-25, every station measuring PM2.5, PM10, NO2, ozone, CO, SO2, NH3, NO and the meteorology
(temperature, humidity, wind speed and direction, solar radiation, pressure).

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
