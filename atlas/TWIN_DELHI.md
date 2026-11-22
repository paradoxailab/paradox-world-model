# Atlas Delhi Twin: plan (ParadoxAI Lab, 22 November 2026)

A living model of Delhi: one Atlas core that keeps the city's weather, air, power demand and movement up to date
every hour and forecasts the next 24 hours, each layer scored against the best forecaster for that layer before we
claim anything. Each layer gets its own pre-registration (weather: `PREREG_DELHI.md`) before its test is scored.

## Layers

| Layer | State on the Delhi graph | Data (historical / live) | Opponent to beat | Status |
|---|---|---|---|---|
| 1 Weather | temperature, humidity, wind, pressure; daily max/min; fog | NOAA ISD, METAR (VIDP, VIDD, VIDX), CPCB/DPCC weather sensors, 13 global models | IMD official forecast, ECMWF IFS/AIFS, every global system | pre-registered; archived test running; live log since 22 Nov |
| 2 Air quality | PM2.5, PM10, NO₂, O₃, CO, SO₂ at 40–46 CAAQMS | CPCB/DPCC (OpenCity, Kaggle copy; OpenAQ / data.gov.in with keys), NASA FIRMS fires, Sentinel-5P | CAMS (logged since 22 Nov), SAFAR / IITM, Chronos-2, TimesFM, Atlas-India v1.0 | CAMS logging; station data needs keys |
| 3 Electricity | 5-minute load: Delhi, BRPL, BYPL, TPDDL (NDPL), NDMC, MES | Delhi SLDC load curves (backfill from 2023 running in the Mac browser; GitHub runners cannot reach the site) | SLDC's own day-ahead forecast, seasonal-naive, Chronos-2 | backfill running |
| 4 Mobility | road-segment speed from bus movement | Delhi Open Transit Data GTFS-RT (key), OpenStreetMap, Delhi Traffic Police network | our traffic specialists (STAEformer, PWM-Dyn), foundation models | needs key |
| 5 Base map | land use, zoning, buildings, elevation | Bhuvan, MPD-2041, building footprints, Copernicus DEM | (context, not forecast) | later |

## Model

The Atlas core already shares one network across weather, air quality and traffic. The twin adds Delhi nodes of
each kind (weather stations, air-quality stations, discom zones, road segments) to one graph, with edges by distance
and by physics (wind carries smoke; heat drives cooling load; traffic emits NO₂), and global forecasts as inputs as
in Atlas-100M-H2. Layers are added one at a time and each must not make the others worse (checked on validation,
as the traffic follow-ups checked weather and air quality byte for byte).

## Accounts (created by the lab owner; keys only in Colab / GitHub secrets)

OpenAQ, data.gov.in (Janparichay login), NASA FIRMS map key, Delhi Open Transit Data, IMD API, Copernicus CDS.

## Order

1. Weather (December 2026: archived result, live test starts).
2. Electricity (SLDC history in hand; test: next-day 5-minute load against SLDC's own forecast).
3. Air quality (needs OpenAQ / data.gov.in; test against CAMS and SAFAR through the winter smog season).
4. Mobility (needs the transit key).
5. The live Delhi map: current state and next 24 h for every layer that has passed its test, with the scoreboard.
