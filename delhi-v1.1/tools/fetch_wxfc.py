"""Real 1-day-ahead weather FORECASTS for Delhi (Open-Meteo Previous Runs API, best-match model, free for
non-commercial use, no key). For every hour t we take the value that was forecast for t at least 24 hours before t
("_previous_day1"), so a forecast made at origin o for hours o .. o+23 only uses weather forecasts that existed
before o. Archived from January 2024, which covers the whole CPCB 2024-25 period.

  python tools/fetch_wxfc.py        # -> data/raw/DELHI_wxfc.npz  (hourly, Indian time, 3-point city mean)
"""
import datetime as dt, os, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
API = "https://previous-runs-api.open-meteo.com/v1/forecast"
VARS = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "wind_direction_10m", "precipitation",
        "cloud_cover", "shortwave_radiation", "surface_pressure"]
POINTS = [(28.74, 77.12), (28.61, 77.21), (28.53, 77.27)]          # north-west, centre, south-east Delhi


def get(params, tries=6):
    import requests
    for k in range(tries):
        try:
            r = requests.get(API, params=params, timeout=180, headers={"User-Agent": "paradox-world-model-data-builder"})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if k == tries - 1:
                raise
            time.sleep(10 * (k + 1))


def main(start="2024-01-01", end="2026-01-02"):
    s0, s1 = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    T = ((s1 - s0).days + 1) * 24
    F = np.full((T, len(POINTS), len(VARS)), np.nan, np.float32)
    names = [v + "_previous_day1" for v in VARS]
    a = s0
    while a <= s1:                                                 # quarter by quarter
        b = min(s1, (dt.date(a.year + (a.month + 2) // 12, (a.month + 2) % 12 + 1, 1) - dt.timedelta(days=1)))
        for p, (la, lo) in enumerate(POINTS):
            j = get(dict(latitude=la, longitude=lo, hourly=",".join(names), start_date=a.isoformat(),
                         end_date=b.isoformat(), timezone="Asia/Kolkata"))
            h = j["hourly"]
            for i, ts in enumerate(h["time"]):
                t = dt.datetime.fromisoformat(ts)
                k = (t.date() - s0).days * 24 + t.hour
                if 0 <= k < T:
                    for v, nm in enumerate(names):
                        x = h.get(nm, [None] * len(h["time"]))[i]
                        if x is not None:
                            F[k, p, v] = x
        print(f"  weather forecasts {a} .. {b}: done", flush=True)
        a = b + dt.timedelta(days=1)
    wd = np.deg2rad(F[..., VARS.index("wind_direction_10m")])
    u = -F[..., VARS.index("wind_speed_10m")] * np.sin(wd)          # wind as vectors before averaging points
    v = -F[..., VARS.index("wind_speed_10m")] * np.cos(wd)
    with np.errstate(all="ignore"):
        city = np.nanmean(F, 1)
        uu, vv = np.nanmean(u, 1), np.nanmean(v, 1)
    keep = [VARS.index(x) for x in ("temperature_2m", "relative_humidity_2m", "wind_speed_10m", "precipitation",
                                    "cloud_cover", "shortwave_radiation", "surface_pressure")]
    X = np.concatenate([city[:, keep], uu[:, None], vv[:, None]], 1).astype(np.float32)
    names_out = [VARS[i] for i in keep] + ["wind_u", "wind_v"]
    np.savez_compressed(os.path.join(RAW, "DELHI_wxfc.npz"), X=X, vars=np.array(names_out), start=np.array(start + " 00:00:00"))
    miss = 100 * np.isnan(X).mean(0)
    print(f"DELHI_wxfc: {T} hours from {start}, variables {names_out}, missing % {np.round(miss, 2).tolist()}", flush=True)


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    main()
