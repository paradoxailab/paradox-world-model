"""The weather leagues of v0.3 and their fixed rules (written down before any score was computed).

METAR  Airport reports via the Iowa Environmental Mesonet archive, which is current to the present day but holds
       good records only for a few Indian airports (in practice Delhi Palam, VIDP). Times in UTC.
       TRAIN 2021-01-01 .. 2025-10-31, VALIDATION 2025-11-01 .. 2026-01-31, TEST 2026-02-01 .. 2026-10-31.
       The test period lies after every global AI model in the league was operational and archived.
WMO    NOAA's Integrated Surface Database (METAR + SYNOP reports, NOAA quality control): Delhi Safdarjung and
       Palam and the Indian stations within 500 km below 1,000 m (up to 24; 3-hourly SYNOP stations included,
       scored on observed hours only). NOAA's Indian records end on 2025-08-24, so:
       TRAIN 2021-01-01 .. 2024-11-30, VALIDATION 2024-12-01 .. 2025-02-28, TEST 2025-03-01 .. 2025-08-20
       (spring heat, pre-monsoon and monsoon). NOAA AIGFS was not yet archived then.
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
    "WMO": dict(start="2021-01-01", end="2025-08-23", tz="GMT",
                val=("2024-12-01", "2025-02-28"), test=("2025-03-01", "2025-08-20")),
    "CPCB": dict(start="2024-01-01", end="2025-12-31", tz="Asia/Kolkata", test_days=182, val_days=61),
    # v0.9 real-time: the METAR stations from 2021-01-01 up to the latest report (tools/fetch_live_metar.py). The
    # last 3 days are the "test" block (2 observed days + the 24 h being forecast), the 45 days before validation.
    "LIVE": dict(start="2021-01-01", end="", tz="GMT", test_days=3, val_days=45),
}

# v1.1 PWM-F pretraining networks: every Indian NOAA ISD station, grouped into regional networks WX_IN01 .. WX_INnn
# (tools/fetch_india_isd.py). Their data END on 2024-11-30, the day before the earliest validation period of any league
# (WMO, 2024-12-01), so pretraining sees nothing from any league's validation or test weather. The last 90 days are
# The last 7 days are a nominal "test" block (never scored); the 60 days before them only pick the checkpoint.
IN_PRETRAIN = dict(start="2015-01-01", end="2024-11-30", tz="GMT", test_days=7, val_days=60)


class _Leagues(dict):
    def __missing__(self, name):
        if str(name).startswith("IN") and str(name)[2:].isdigit():
            return dict(IN_PRETRAIN)
        raise KeyError(name)


LEAGUES = _Leagues(LEAGUES)

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
# v0.4: the hybrid and the "issued before the forecast start" comparison use, for each forecast hour i (valid time
# o+i), the run made 24 h before the valid time (day1) when it was certainly published before the origin o, else the
# run 48 h before (day2). A day1 run starts at most 30 h before the valid time and ECMWF / DWD / NOAA publish within
# 8 h, so it is out by o whenever i <= 16.
HYBRID_INPUTS = ["ECMWF IFS 0.25 (physics)", "ECMWF AIFS (AI)", "DWD ICON (physics)", "NOAA GFS (physics)"]
HYB_SUFFIXES = ["day1", "day2"]
# v0.5: further predictors from the same runs (model output statistics use more than the target itself)
HYB_EXTRA = ["cloud_cover", "shortwave_radiation", "dew_point_2m", "pressure_msl", "wind_direction_10m"]
DAY1_MAX_I = 16


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
