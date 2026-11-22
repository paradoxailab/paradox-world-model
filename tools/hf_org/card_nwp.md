---
license: cc-by-4.0
pretty_name: Archived global weather forecasts at 178 WEATHER-5K stations
tags:
- weather-forecasting
- ecmwf
- gfs
- nwp
- paradoxailab
size_categories:
- 1M<n<10M
---

# Archived global forecasts at 178 stations (2024-01 – 2025-08)

The forecast archive used to test the Atlas hybrid against the world's global weather systems: hourly forecasts of
**ECMWF IFS (0.25°)**, **ECMWF AIFS** and **NOAA GFS** at 178 WEATHER-5K stations (every 32nd station, worldwide),
for two run ages — the run issued 24 h before the valid hour (`previous_day1`) and 48 h before (`previous_day2`).
Retrieved from the Open-Meteo Previous Runs API. GraphCast is not included yet (archive gaps; being fetched).

`NWP_W5K.npz`:

| Key | Shape / value |
|---|---|
| `F` | float32 `[system, hour, station, variable, run]` = `[4, 14447, 178, 5, 2]`; NaN where a system has no forecast |
| `systems` | IFS, AIFS, GFS, GraphCast (GraphCast all NaN in this file) |
| `ids` | the Open-Meteo model ids used (JSON) |
| `stations` | indices into WEATHER-5K's 5,672 stations |
| `vars` | temperature_2m (°C), dew_point_2m (°C), wind_direction_10m (°), wind_speed_10m (m/s), pressure_msl (hPa) — WEATHER-5K units |
| `offsets` | previous_day1, previous_day2 |
| `start` | 2024-01-01T00 (hour 0, UTC) |

Coverage of hours: IFS 0.93, AIFS 0.60 (its archive starts later), GFS 0.97.

**Attribution.** ECMWF open data (CC-BY-4.0), © ECMWF; NOAA GFS (public domain); delivered by
[Open-Meteo](https://open-meteo.com) (CC-BY-4.0). Station ids follow WEATHER-5K / NOAA ISD. Compiled by ParadoxAI Lab
(`atlas/m100/hybrid.py fetch` in [the repository](https://github.com/paradoxailab/paradox-world-model)); this file is
distributed under CC-BY-4.0 with the attributions above.
