"""Weather for every all-India league station (Atlas v2, data step; written before any model uses it).

Two archives from Open-Meteo, no key (free for non-commercial use; data CC BY 4.0; ERA5 by the Copernicus Climate Change
Service; forecasts from the national weather services):

  ERA5 reanalysis (archive-api, models=era5): the weather that happened, hourly, 0.25 degree. Used as the "future
    weather" input in training (the perfect-prognosis convention) and, labelled as an upper bound, at test.
  Forecasts issued the day before (previous-runs-api, *_previous_day1): what a forecaster actually had. Archived only
    from January 2024, so they exist for Delhi's winter 2024-25 (the operational-comparison window) and nowhere in the
    all-India test period (Oct 2022 - Mar 2023).

Stations are placed at their city (geocoded with Open-Meteo's geocoding API, country India, state checked); cities in the
same 0.25-degree ERA5 cell share one series. Requests are cached one file per cell and year in $WX_CACHE, and a cache
found under /kaggle/input is reused, so a run stopped by the daily allowance resumes where it stopped.

Variables (8, so each request counts once per 14 days): temperature_2m, relative_humidity_2m, precipitation,
boundary_layer_height, wind_speed_10m, wind_direction_10m (stored as u10, v10), surface_pressure, cloud_cover.
Clock: the archive is UTC; station files are Indian time (UTC+5:30); every series is moved to Indian hours by averaging
the two UTC hours on either side (wind through u and v), as in fetch_era5_delhi.py.

Periods: Delhi's cell 2019-01-01 .. 2025-02-28 (training, the long Delhi history and the 2024-25 test); every other
cell 2020-01-01 .. 2023-03-31 (all-India training, validation and test); hours outside a cell's period are NaN and a flag
tells the model. Each request's weight against the free allowance (one call per 14 days) is counted; the run paces itself
under the hourly allowance, stops asking at WX_BUDGET and records complete=False, and the next run resumes from the cache.

Writes INDIA_WX.npz: era5 [hours, cells, 9] float32 (NaN = not served), vars, start (Indian time), cells (lat, lon),
stations, station_cell, city_of_cell; DELHI_FC.npz: day-1 forecasts at Delhi's cell, [hours, 9], with what was served.

  python tools/fetch_weather_india.py            # WX_FROM / WX_TO for ERA5 (default 2019-01-01 .. 2025-02-28)
"""
import glob, json, os, re, shutil, sys, time, urllib.error, urllib.parse, urllib.request

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
CACHE = os.environ.get("WX_CACHE", "/kaggle/working/wx_cache")
FIRST, LAST = os.environ.get("WX_FROM", "2019-01-01"), os.environ.get("WX_TO", "2025-02-28")   # Delhi's cell
IN_FROM, IN_TO = os.environ.get("WX_IN_FROM", "2020-01-01"), os.environ.get("WX_IN_TO", "2023-03-31")   # other cells
FC_FROM, FC_TO = os.environ.get("FC_FROM", "2024-01-01"), os.environ.get("FC_TO", "2025-02-28")
TEST_DAYS, VAL_DAYS, SPD, MIN_NET = 182, 61, 24, 6
ASK = ["temperature_2m", "relative_humidity_2m", "precipitation", "boundary_layer_height", "wind_speed_10m",
       "wind_direction_10m", "surface_pressure", "cloud_cover"]
OUT = ["temperature_2m", "relative_humidity_2m", "precipitation", "boundary_layer_height", "wind_speed_10m",
       "u10", "v10", "surface_pressure", "cloud_cover"]
DELHI = (28.61, 77.21)
PAUSE = float(os.environ.get("WX_PAUSE", "0.9"))    # seconds per weighted call (4,000 an hour, under the 5,000 allowance)
BUDGET = float(os.environ.get("WX_BUDGET", "9000"))  # weighted calls per run (the free allowance is 10,000 a day)
USED = [0.0]
STOP = [False]
# cities the geocoder misses or places in another state (coordinates of the town centre)
OVERRIDE = {("Chikkaballapur", "Karnataka"): (13.435, 77.728), ("Davanagere", "Karnataka"): (14.464, 75.922),
            ("Eloor", "Kerala"): (10.075, 76.300), ("Gummidipoondi", "Tamil Nadu"): (13.407, 80.108),
            ("Mandi Gobindgarh", "Punjab"): (30.668, 76.302), ("Ramanagara", "Karnataka"): (12.722, 77.281)}
# last resort for a state none of whose cities could be placed: its capital
CAPITAL = {"Uttar Pradesh": (26.85, 80.95), "Delhi": (28.61, 77.21), "Haryana": (30.73, 76.78), "Maharashtra": (19.08, 72.88),
           "Karnataka": (12.97, 77.59), "Madhya Pradesh": (23.26, 77.41), "West Bengal": (22.57, 88.36), "Bihar": (25.59, 85.14),
           "Rajasthan": (26.91, 75.79), "Gujarat": (23.02, 72.57), "Tamil Nadu": (13.08, 80.27), "Punjab": (30.73, 76.78),
           "Kerala": (8.52, 76.94), "Andhra Pradesh": (16.51, 80.65), "Telangana": (17.39, 78.49), "Odisha": (20.30, 85.82),
           "Assam": (26.14, 91.74), "Jharkhand": (23.34, 85.31), "Chhattisgarh": (21.25, 81.63), "Uttarakhand": (30.32, 78.03),
           "Himachal Pradesh": (31.10, 77.17), "Jammu and Kashmir": (34.08, 74.80), "Chandigarh": (30.73, 76.78),
           "Puducherry": (11.94, 79.81), "Goa": (15.49, 73.83), "Meghalaya": (25.58, 91.89), "Mizoram": (23.73, 92.72),
           "Manipur": (24.82, 93.94), "Nagaland": (25.67, 94.11), "Tripura": (23.83, 91.29), "Sikkim": (27.33, 88.61),
           "Arunachal Pradesh": (27.08, 93.61)}


def log(*a):
    print(*a, flush=True)


def fetch(url, tries=5):
    body = ""
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=240) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf8", "replace")[:300]
            if e.code == 400:
                return {"error": body}
            if e.code == 429:                          # allowance used up: one wait, then stop asking (resume next run)
                log(f"    429 (allowance): {body[:120]}")
                if k == 0:
                    time.sleep(90); continue
                STOP[0] = True
                return {"error": "429: " + body}
            time.sleep(20 * (k + 1))
        except Exception as e:
            body = f"{type(e).__name__}: {e}"
            time.sleep(20 * (k + 1))
    return {"error": body}


def league_cities():
    z = np.load(os.path.join(RAW, "INDIA_LONG.npz"), allow_pickle=False)
    X, vars_ = z["X"], [str(v) for v in z["vars"]]
    names, city, state = [str(s) for s in z["stations"]], [str(s) for s in z["city"]], [str(s) for s in z["state"]]
    T = len(X); b = T - TEST_DAYS * SPD - VAL_DAYS * SPD
    pm = np.isfinite(X[..., vars_.index("PM2.5")])
    ok = (pm[-TEST_DAYS * SPD:].mean(0) >= 0.5) & (pm[:b].mean(0) >= 0.125)      # the league's rule (run_atlas_india)
    keep = np.where(ok)[0]
    return [(names[j], city[j], state[j]) for j in keep]


def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())


def geocode(city, state):
    if (city, state) in OVERRIDE:
        la, lo = OVERRIDE[(city, state)]
        return dict(lat=la, lon=lo, name=city, admin1=state, state_match=True, how="override")
    q = dict(name=city, count=10, language="en", format="json", countryCode="IN")
    d = fetch("https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(q))
    res = d.get("results") or []
    st = norm(state)
    good = [r for r in res if st and (st in norm(r.get("admin1", "")) or norm(r.get("admin1", "")) in st)]
    time.sleep(0.5)
    if not good:                                       # never accept a place in another state
        return None
    pick = good[0]
    return dict(lat=float(pick["latitude"]), lon=float(pick["longitude"]), name=pick.get("name"), admin1=pick.get("admin1"),
                state_match=True, how="geocoder")


def cell_of(lat, lon):
    return (round(lat * 4) / 4, round(lon * 4) / 4)


def era5_cell(lat, lon, t0, n, first, last):
    """UTC hourly [n, len(ASK)] for one cell, year by year (first .. last), cached; paced by weighted calls."""
    x = np.full((n, len(ASK)), np.nan, np.float32)
    y0, y1 = int(first[:4]), int(last[:4])
    for y in range(y0, y1 + 1):
        a, b = max(first, f"{y}-01-01"), min(last, f"{y}-12-31")
        key = f"era5_{lat:.2f}_{lon:.2f}_{y}.json"
        f = os.path.join(CACHE, key)
        hit = [f] + glob.glob(f"/kaggle/input/**/{key}", recursive=True)
        hit = [h for h in hit if os.path.exists(h)]
        if hit:
            d = json.load(open(hit[0]))
        elif STOP[0] or USED[0] >= BUDGET:
            STOP[0] = True
            continue
        else:
            w = max(1.0, ((np.datetime64(b) - np.datetime64(a)).astype(int) + 1) / 14)
            q = dict(latitude=lat, longitude=lon, start_date=a, end_date=b, hourly=",".join(ASK), timezone="GMT",
                     wind_speed_unit="ms", models="era5")
            d = fetch("https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(q))
            USED[0] += w
            if "hourly" in d:
                json.dump(d, open(f, "w"))
            time.sleep(PAUSE * w)
        if "hourly" not in d:
            log(f"    ERA5 {lat:.2f},{lon:.2f} {y}: not served ({str(d.get('error', ''))[:120]})"); continue
        tt = np.array(d["hourly"]["time"], dtype="datetime64[h]")
        ix = (tt - t0).astype(int); okk = (ix >= 0) & (ix < n)
        for c, v in enumerate(ASK):
            vv = np.array([np.nan if z is None else z for z in d["hourly"].get(v, [None] * len(tt))], np.float32)
            x[ix[okk], c] = vv[okk]
    return x


def to_indian(U):
    """UTC [n, 8 ASK] -> Indian-hour [n-1, 9 OUT] (value at UTC i+0:30 = Indian hour i+6)."""
    wd = np.deg2rad(U[:, ASK.index("wind_direction_10m")]); ws = U[:, ASK.index("wind_speed_10m")]
    cols = {v: U[:, ASK.index(v)] for v in ASK}
    cols["u10"], cols["v10"] = -ws * np.sin(wd), -ws * np.cos(wd)
    V = np.stack([cols[v] for v in OUT], -1)
    return 0.5 * (V[:-1] + V[1:])


def main():
    os.makedirs(CACHE, exist_ok=True)
    st = league_cities()
    cities = sorted({(c, s) for _, c, s in st})
    log(f"league: {len(st)} stations in {len(cities)} cities")
    geo = {}
    for c, s in cities:
        g = geocode(c, s)
        geo[(c, s)] = g
        log(f"  {c}, {s}: " + (f"{g['lat']:.3f}, {g['lon']:.3f} ({g['name']}, {g['admin1']}; {g['how']})" if g else "not found in this state"))
    for (c, s), g in list(geo.items()):                # fallback: the centre of the same state's placed cities
        if g is None:
            pts = [(h["lat"], h["lon"]) for (c2, s2), h in geo.items() if s2 == s and h is not None]
            if pts:
                la, lo = float(np.mean([p[0] for p in pts])), float(np.mean([p[1] for p in pts]))
                geo[(c, s)] = dict(lat=la, lon=lo, name=c, admin1=s, state_match=True, how="state centre")
                log(f"  {c}, {s}: STATE CENTRE {la:.3f}, {lo:.3f} (from {len(pts)} cities)")
            elif s in CAPITAL:
                la, lo = CAPITAL[s]
                geo[(c, s)] = dict(lat=la, lon=lo, name=c, admin1=s, state_match=True, how="state capital")
                log(f"  {c}, {s}: STATE CAPITAL {la:.3f}, {lo:.3f}")
    log("placement: " + json.dumps({k: sum(1 for g in geo.values() if g and g["how"] == k) for k in ("geocoder", "override", "state centre", "state capital")}
                                   | {"unplaced": sum(1 for g in geo.values() if g is None)}))
    dc = cell_of(*DELHI)
    cells = [dc] + sorted({cell_of(g["lat"], g["lon"]) for g in geo.values() if g} - {dc})     # Delhi first
    log(f"{len(cells)} distinct 0.25-degree cells (Delhi's included); {sum(1 for g in geo.values() if g is None)} cities not found")
    t0 = np.datetime64(FIRST + "T00"); t1 = np.datetime64(LAST + "T00") + np.timedelta64(24, "h")
    n = int((t1 - t0).astype(int))
    E = np.full((n - 1, len(cells), len(OUT)), np.nan, np.float32)
    for k, (la, lo) in enumerate(cells):
        a, b = (FIRST, LAST) if (la, lo) == dc else (IN_FROM, IN_TO)
        E[:, k] = to_indian(era5_cell(la, lo, t0, n, a, b))
        r0 = int((np.datetime64(a + "T06") - (t0 + np.timedelta64(6, "h"))).astype(int)); r1 = int((np.datetime64(b + "T23") - (t0 + np.timedelta64(6, "h"))).astype(int))
        log(f"  cell {k + 1}/{len(cells)} {la:.2f},{lo:.2f} ({a}..{b}): served {100 * np.isfinite(E[max(r0, 0):r1, k]).all(1).mean():.1f}% "
            f"of its hours; weighted calls used {USED[0]:.0f}{'; ALLOWANCE REACHED, resume in a later run' if STOP[0] else ''}")
    start = t0 + np.timedelta64(6, "h")
    cix = {c: i for i, c in enumerate(cells)}
    sc = np.array([cix[cell_of(geo[(c, s)]["lat"], geo[(c, s)]["lon"])] if geo[(c, s)] else -1 for _, c, s in st])
    city_of = ["; ".join(sorted({f"{c}" for (c, s), g in geo.items() if g and cell_of(g['lat'], g['lon']) == cl})) for cl in cells]
    os.makedirs(RAW, exist_ok=True)
    np.savez_compressed(os.path.join(RAW, "INDIA_WX.npz"), era5=E, vars=np.array(OUT), start=np.array(str(start)),
                        cells=np.array(cells, np.float32), stations=np.array([x[0] for x in st]), station_cell=sc,
                        city_of_cell=np.array(city_of), delhi_cell=np.array(cix[cell_of(*DELHI)]),
                        complete=np.array(not STOP[0]), periods=np.array([f"Delhi cell {FIRST}..{LAST}", f"others {IN_FROM}..{IN_TO}"]))
    served = {v: round(100 * float(np.isfinite(E[..., j]).mean()), 1) for j, v in enumerate(OUT)}
    log("INDIA_WX " + json.dumps(dict(complete=not STOP[0], weighted_calls=round(USED[0]), hours=int(len(E)), start=str(start), cells=len(cells), stations=len(st),
                                      stations_placed=int((sc >= 0).sum()), served_pct=served)))
    # day-1 forecasts at Delhi's cell (the only archive of real forecasts: from January 2024)
    la, lo = cell_of(*DELHI)
    f0 = np.datetime64(FC_FROM + "T00"); f1 = np.datetime64(FC_TO + "T00") + np.timedelta64(24, "h")
    m = int((f1 - f0).astype(int))
    for model in ("ecmwf_ifs025", "best_match"):
        U = np.full((m, len(ASK)), np.nan, np.float32)
        for c, v in enumerate(ASK):
            q = dict(latitude=la, longitude=lo, start_date=FC_FROM, end_date=FC_TO, hourly=f"{v}_previous_day1",
                     timezone="GMT", wind_speed_unit="ms", models=model)
            d = fetch("https://previous-runs-api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(q))
            time.sleep(2)
            if "hourly" not in d:
                log(f"  forecast {model} {v}: not served ({str(d.get('error', ''))[:120]})"); continue
            tt = np.array(d["hourly"]["time"], dtype="datetime64[h]")
            vv = np.array([np.nan if z is None else z for z in d["hourly"][f"{v}_previous_day1"]], np.float32)
            ix = (tt - f0).astype(int); okk = (ix >= 0) & (ix < m)
            U[ix[okk], c] = vv[okk]
            log(f"  forecast {model} {v}: served {100 * np.isfinite(U[:, c]).mean():.1f}% of hours")
        F = to_indian(U)
        np.savez_compressed(os.path.join(RAW, f"DELHI_FC_{model}.npz"), X=F, vars=np.array(OUT),
                            start=np.array(str(f0 + np.timedelta64(6, "h"))), cell=np.array([la, lo], np.float32))
        log(f"DELHI_FC {model} " + json.dumps({v: round(100 * float(np.isfinite(F[:, j]).mean()), 1) for j, v in enumerate(OUT)}))
    shutil.make_archive("/kaggle/working/wx_cache", "zip", CACHE) if os.path.isdir("/kaggle/working") else None


if __name__ == "__main__":
    main()
