"""The weather leagues of v0.3 and their fixed rules (written down before any score was computed).

METAR  World Meteorological Organization-grade airport observations (hourly METAR reports via the Iowa
       Environmental Mesonet archive). The two Delhi airports (Palam VIDP, Safdarjung VIDD) and the nearest
       north-Indian airports below 1,000 m (a network of up to 16). Times in UTC.
       TRAIN 2021-01-01 .. 2025-10-31, VALIDATION 2025-11-01 .. 2026-01-31, TEST 2026-02-01 .. 2026-10-31.
       The test period lies after every global AI model in the league was operational and archived.
WMO    Same periods and targets as METAR, from NOAA's Integrated Surface Database (METAR + SYNOP reports,
       NOAA quality control): Delhi Safdarjung and Palam and the Indian stations within 500 km below 1,000 m
       (up to 24; 3-hourly SYNOP stations included, scored on observed hours only). The main league, because the
       IEM archive holds only Palam among the Delhi stations with good coverage.
CPCB   Delhi's CPCB / DPCC / IMD air-quality stations' own weather sensors (temperature, humidity, wind speed),
       2024-01-01 .. 2025-12-31, Indian time; same split as the air-quality league (last 182 days TEST, 61 days
       before VALIDATION). These sensors are not WMO-sited (roof tops, obstructed wind), so every global model is
       also scored after a trailing local bias correction.

Targets: AT = 2 m air temperature (deg C), RH = relative humidity (%), WS = 10 m wind speed (m/s).
Forecast: from origin o (observations up to o-1), the 24 hours o .. o+23. Scored origins: every 6 hours.
"""
import numpy as np

TARGETS = ["AT", "RH", "WS"]
NWP_VARS = {"AT": "temperature_2m", "RH": "relative_humidity_2m", "WS": "wind_speed_10m"}

LEAGUES = {
    "METAR": dict(start="2021-01-01", end="2026-11-05", tz="GMT",
                  val=("2025-11-01", "2026-01-31"), test=("2026-02-01", "2026-10-31")),
    "WMO": dict(start="2021-01-01", end="2026-11-05", tz="GMT",
                val=("2025-11-01", "2026-01-31"), test=("2026-02-01", "2026-10-31")),
    "CPCB": dict(start="2024-01-01", end="2025-12-31", tz="Asia/Kolkata", test_days=182, val_days=61),
}

# Global forecast systems scored from Open-Meteo's archive of their real operational runs (Previous Runs API).
# Several identifiers are tried for each, because Open-Meteo's naming is not documented for every model; the
# one that answered is recorded in the results.
NWP_MODELS = {
    "ECMWF AIFS (AI)": ["ecmwf_aifs025_single", "ecmwf_aifs025"],
    "NOAA AIGFS (AI, GraphCast-based)": ["ncep_aigfs025", "gfs_aigfs025", "ncep_aigfs", "aigfs025"],
    "DWD AICON (AI)": ["dwd_aicon", "dwd_aicon_global", "icon_aicon", "aicon_global", "dwd_ai_icon", "aicon",
                       "icon_ai", "dwd_aicon_seamless"],
    "ECMWF IFS 9 km (physics)": ["ecmwf_ifs", "ecmwf_ifs_hres"],
    "ECMWF IFS 0.25 (physics)": ["ecmwf_ifs025"],
    "NOAA GFS (physics)": ["ncep_gfs_seamless", "gfs_seamless", "ncep_gfs025", "gfs_global"],
    "DWD ICON (physics)": ["dwd_icon_seamless", "icon_seamless", "dwd_icon_global", "icon_global"],
}
# day0 = latest run (lead 0-6 h, often issued after the origin: generous to the global models)
# day1 = the value forecast 24 h before the valid time;  day2 = 48 h before (always available at the origin)
SUFFIXES = {"day0": "", "day1": "_previous_day1", "day2": "_previous_day2"}
HYBRID_INPUTS = ["ECMWF IFS 9 km (physics)", "ECMWF AIFS (AI)"]      # day2 only: strictly available at the origin


def hours(start, end):
    return int((np.datetime64(end) - np.datetime64(start)).astype("timedelta64[h]").astype(int)) + 24


def bounds(name, T):
    c = LEAGUES[name]
    s = np.datetime64(c["start"]).astype("datetime64[h]")
    if "val" in c:
        ix = lambda d: int((np.datetime64(d).astype("datetime64[h]") - s).astype(int))
        va, te = (ix(c["val"][0]), ix(c["val"][1]) + 24), (ix(c["test"][0]), min(T, ix(c["test"][1]) + 24))
        return {"train": (0, va[0]), "val": va, "test": te}
    n_te, n_va = c["test_days"] * 24, c["val_days"] * 24
    return {"train": (0, T - n_te - n_va), "val": (T - n_te - n_va, T - n_te), "test": (T - n_te, T)}
