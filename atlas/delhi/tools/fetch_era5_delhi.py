"""Reanalysis weather for Delhi (what-if test 1b, data step).

ERA5 hourly values at Delhi's centre (28.61 N, 77.21 E; one 0.25-degree cell, about 25 km) from Open-Meteo's
historical archive. No key is needed. Terms: Open-Meteo's free API is for non-commercial use and its data is
CC BY 4.0; ERA5 is produced by the Copernicus Climate Change Service. Used here for a research test only.

Variables asked for, one request per variable and year so that one the archive does not serve cannot stop the
others: precipitation, boundary-layer height, wind speed and direction at 100 m, cloud cover, top-layer soil
moisture. The archive's clock is UTC; the station files are on Indian time (UTC+5:30), so every series is moved to
Indian hours by averaging the two UTC hours on either side (wind direction through its east and north components).

Writes DELHI_ERA5.npz: X [hours, variables] float32 (NaN = not served), vars, start (Indian time). Prints what was
served and monthly rain totals, so the test's rules can be fixed before any model is run.

  python tools/fetch_era5_delhi.py
"""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
LAT, LON = 28.61, 77.21
FIRST, LAST = os.environ.get("ERA_FROM", "2017-12-20"), os.environ.get("ERA_TO", "2020-06-02")
ASK = ["precipitation", "boundary_layer_height", "wind_speed_100m", "wind_direction_100m", "cloud_cover", "soil_moisture_0_to_7cm"]
OUT_VARS = ["precipitation", "boundary_layer_height", "wind_speed_100m", "u100", "v100", "cloud_cover", "soil_moisture_0_to_7cm"]


def get(var, a, b):
    q = dict(latitude=LAT, longitude=LON, start_date=a, end_date=b, hourly=var, timezone="GMT", wind_speed_unit="ms")
    url = "https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(q)
    for k in range(4):
        try:
            with urllib.request.urlopen(url, timeout=180) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf8", "replace")[:200]
            if e.code == 400:
                return {"error": body}
            time.sleep(20 * (k + 1))
        except Exception as e:
            body = f"{type(e).__name__}: {e}"
            time.sleep(20 * (k + 1))
    return {"error": body}


def main():
    t0 = np.datetime64(FIRST + "T00"); t1 = np.datetime64(LAST + "T00") + np.timedelta64(24, "h")
    hours = t0 + np.arange(int((t1 - t0).astype(int)))                           # UTC hours
    raw = {}
    y0, y1 = int(FIRST[:4]), int(LAST[:4])
    for v in ASK:
        x = np.full(len(hours), np.nan, np.float32)
        for y in range(y0, y1 + 1):
            a, b = max(FIRST, f"{y}-01-01"), min(LAST, f"{y}-12-31")
            d = get(v, a, b)
            if "error" in d or "hourly" not in d:
                print(f"  {v} {y}: not served ({str(d.get('error', d))[:160]})", flush=True); continue
            tt = np.array(d["hourly"]["time"], dtype="datetime64[h]")
            vv = np.array([np.nan if z is None else z for z in d["hourly"][v]], np.float32)
            ix = (tt - t0).astype(int); ok = (ix >= 0) & (ix < len(x))
            x[ix[ok]] = vv[ok]
            time.sleep(1.0)
        raw[v] = x
        print(f"  {v}: served on {100 * np.isfinite(x).mean():.1f}% of hours; median {np.nanmedian(x) if np.isfinite(x).any() else float('nan'):.2f}", flush=True)
    wd = np.deg2rad(raw["wind_direction_100m"])
    raw["u100"], raw["v100"] = -raw["wind_speed_100m"] * np.sin(wd), -raw["wind_speed_100m"] * np.cos(wd)
    # to Indian hours: hour h (Indian) covers UTC h-5:30 .. h-4:30; average the UTC hours h-6 and h-5
    U = np.stack([raw[v] for v in OUT_VARS], -1)
    X = 0.5 * (U[:-1] + U[1:])                                                   # value at UTC hour i + 0:30 = Indian hour i + 6
    start = t0 + np.timedelta64(6, "h")
    os.makedirs(RAW, exist_ok=True)
    np.savez_compressed(os.path.join(RAW, "DELHI_ERA5.npz"), X=X.astype(np.float32), vars=np.array(OUT_VARS), start=np.array(str(start)))
    print(f"DELHI_ERA5: {len(X)} hours from {start} (Indian time) x {len(OUT_VARS)} variables", flush=True)
    t = start + np.arange(len(X))
    p = X[:, 0]
    mon = t.astype("datetime64[M]")
    print("rain by month, mm (India Meteorological Department, Safdarjung: March 2020 109.6 mm, normal 15.9 mm):", flush=True)
    for m in ("2018-03", "2019-03", "2020-01", "2020-02", "2020-03", "2020-04", "2020-05", "2019-04", "2019-05"):
        s = mon == np.datetime64(m)
        print(f"  {m}: {np.nansum(p[s]):6.1f} mm, hours with rain {int((p[s] > 0.1).sum())}", flush=True)
    served = [v for j, v in enumerate(OUT_VARS) if np.isfinite(X[:, j]).mean() > 0.99]
    print("ERA5 " + json.dumps(dict(hours=int(len(X)), start=str(start), served=served,
                                    not_served=[v for v in OUT_VARS if v not in served])), flush=True)


if __name__ == "__main__":
    main()
