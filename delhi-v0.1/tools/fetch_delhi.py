"""Build the Delhi world-state dataset from CPCB's public station data (39 continuous ambient air-quality
monitoring stations, published by OpenCity as "Delhi Hourly Air Quality Reports", public domain). Nothing is
re-hosted: run this to rebuild it.

  python tools/fetch_delhi.py            # -> data/raw/DELHI.npz

The dataset has two file series per station. The 2024-25 files are 15-minute measurements of every pollutant
(PM2.5, PM10, NO, NO2, NOx, NH3, SO2, CO, Ozone, BTX) and the meteorology (AT, RH, WS, WD, SR, BP): these are used,
put on an hourly clock (15-minute values averaged when at least 2 of the 4 are present). The 2017-2023 files hold
only the composite hourly AQI index (capped at 500, no concentrations, no weather) and are NOT used.
Clock: the files stamp times "+0000"; the hour of peak solar radiation decides whether that is really UTC (peak near
06-07 h -> shifted to IST) or Indian local time written with a UTC label (peak near 12 h -> kept).

Cleaning rules, fixed before looking at results:
  * values that are not numbers, negative (except temperature), or above a physical ceiling become missing;
  * a pollutant reading repeated unchanged for 24 h or more is a stuck instrument and becomes missing.
Writes X [T, N, C] float32 (NaN = missing), vars [C], stations [N], station_ids [N], start (ISO hour).
"""
import io, json, os, re, sys, time
import concurrent.futures as cf

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
API = "https://data.opencity.in/api/3/action/package_show?id=delhi-hourly-air-quality-reports"
VARS = ["PM2.5", "PM10", "NO2", "Ozone", "CO", "SO2", "NH3", "NO", "AT", "RH", "WS", "WD", "SR", "BP"]
CEIL = {"PM2.5": 1500, "PM10": 2500, "NO2": 1000, "Ozone": 600, "CO": 60, "SO2": 600, "NH3": 1000, "NO": 1500,
        "AT": 55, "RH": 100, "WS": 40, "WD": 360, "SR": 1500, "BP": 1100}
POLLUTANTS = {"PM2.5", "PM10", "NO2", "Ozone", "CO", "SO2", "NH3", "NO"}


def get(url, binary=False, tries=5):
    import requests
    for k in range(tries):
        try:
            r = requests.get(url, timeout=300, headers={"User-Agent": "paradox-world-model-data-builder"})
            r.raise_for_status()
            return r.content if binary else r.json()
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(5 * (k + 1))


def column(cols, name):
    for c in cols:
        base = re.sub(r"\s*\(.*\)\s*$", "", str(c)).strip()
        if base.lower() == name.lower():
            return c
    return None


def parse_time(s):
    import pandas as pd
    best = None
    for dayfirst in (False, True):
        t = pd.to_datetime(s, errors="coerce", dayfirst=dayfirst, format="mixed")
        ok = t.notna().mean()
        d = t.dropna().diff().dt.total_seconds().dropna()
        mono = float((d > 0).mean()) if len(d) else 0.0
        reg = float((d == d.mode().iloc[0]).mean()) if len(d) else 0.0   # the right parse has a regular clock
        score = ok + mono + 2 * reg
        if best is None or score > best[0]:
            best = (score, t, dayfirst, ok, mono)
    return best[1], best[2], best[3], best[4]


def read_station(path):
    import pandas as pd
    df = pd.read_csv(path, low_memory=False)
    tcol = column(df.columns, "Timestamp") or column(df.columns, "From Date") or df.columns[0]
    t, dayfirst, ok, mono = parse_time(df[tcol].astype(str))
    if getattr(t.dt, "tz", None) is not None:
        t = t.dt.tz_localize(None)                       # keep the written clock; checked against the sun below
    src = column(df.columns, "SR")
    shift = 0.0
    if src is not None:
        sr = pd.to_numeric(df[src], errors="coerce")
        prof = sr.groupby(t.dt.hour).mean()
        peak = int(prof.idxmax()) if prof.notna().any() else 12
        if 4 <= peak <= 8:                                # really UTC: move to Indian time
            t = t + pd.Timedelta(hours=5, minutes=30)
            shift = 5.5
    else:
        peak = None
    name = str(df[column(df.columns, "Station Name")].dropna().iloc[0]) if column(df.columns, "Station Name") else \
        os.path.basename(path)
    sid = str(df[column(df.columns, "Station ID")].dropna().iloc[0]) if column(df.columns, "Station ID") else name
    raw_t = t.dropna().sort_values()
    step = float(raw_t.diff().dt.total_seconds().dropna().median() / 60) if len(raw_t) > 2 else 60.0
    out = pd.DataFrame({"t": t.dt.floor("h")})
    for v in VARS:
        c = column(df.columns, v)
        out[v] = pd.to_numeric(df[c], errors="coerce") if c is not None else np.nan
    out = out.dropna(subset=["t"])
    g = out.groupby("t")
    mean, cnt = g.mean(), g.count()
    if step < 60:                                         # 15-minute file: need >= 2 readings in the hour
        mean = mean.where(cnt >= 2)
    return sid, name, mean, {"file": os.path.basename(path), "rows": len(df), "time_col": tcol, "dayfirst": dayfirst,
                             "parsed": round(float(ok), 4), "increasing": round(float(mono), 4),
                             "step_min": float(step), "first": str(mean.index.min()), "last": str(mean.index.max()),
                             "sample_time": str(df[tcol].iloc[0]), "solar_peak_hour": peak, "shift_h": shift}


def stuck(x, run=24):
    """Mask runs of >= run identical consecutive values (stuck instrument) in a 1-D series."""
    eq = np.r_[False, x[1:] == x[:-1]]                  # NaN never equals NaN, so gaps break runs
    rid = np.cumsum(~eq)
    return np.bincount(rid)[rid] >= run


def main():
    import pandas as pd
    out_dir = os.path.join(RAW, "delhi_csv"); os.makedirs(out_dir, exist_ok=True)
    pkg = get(API)["result"]
    allr = [r for r in pkg["resources"] if str(r.get("url", "")).lower().endswith(".csv")]
    res = [r for r in allr if "2024" in str(r.get("name", ""))]
    print(f"OpenCity package '{pkg['title']}': {len(allr)} CSV resources; using the {len(res)} 2024-25 "
          f"measurement files (the others are AQI-only)", flush=True)

    def dl(r):
        f = os.path.join(out_dir, os.path.basename(r["url"]))
        if not os.path.exists(f):
            open(f, "wb").write(get(r["url"], binary=True))
        return f

    with cf.ThreadPoolExecutor(6) as ex:
        files = list(ex.map(dl, res))
    print(f"downloaded {len(files)} files, {sum(os.path.getsize(f) for f in files) / 2**20:.0f} MB", flush=True)
    per, meta = {}, []
    for f in sorted(files):
        try:
            sid, name, m, info = read_station(f)
        except Exception as e:
            print(f"  {os.path.basename(f)}: FAILED {type(e).__name__}: {e}", flush=True)
            continue
        info.update(station=name, station_id=sid)
        meta.append(info)
        key = re.sub(r"[^a-z0-9]", "", name.lower())          # same station across the two file series
        per.setdefault(key, {"name": name, "ids": set(), "parts": []})["parts"].append(m)
        per[key]["ids"].add(sid)
    for i in meta[:6]:
        print("  ", json.dumps(i), flush=True)
    bad = [i for i in meta if i["parsed"] < 0.95 or i["increasing"] < 0.9]
    print(f"files with doubtful timestamps: {len(bad)}", flush=True)
    for i in bad[:10]:
        print("   doubtful:", json.dumps(i), flush=True)
    t0 = min(p.index.min() for s in per.values() for p in s["parts"])
    t1 = max(p.index.max() for s in per.values() for p in s["parts"])
    idx = pd.date_range(t0, t1, freq="h")
    ids = sorted(per, key=lambda k: per[k]["name"])
    X = np.full((len(idx), len(ids), len(VARS)), np.nan, np.float32)
    for j, k in enumerate(ids):
        df = pd.concat(per[k]["parts"]).groupby(level=0).mean().reindex(idx)
        X[:, j] = df[VARS].to_numpy(np.float32)
    for c, v in enumerate(VARS):
        x = X[..., c]
        bad = (x > CEIL[v]) | ((x < 0) & (v != "AT"))
        x[bad] = np.nan
        if v in POLLUTANTS:
            for j in range(x.shape[1]):
                x[stuck(x[:, j]), j] = np.nan
        X[..., c] = x
    np.savez_compressed(os.path.join(RAW, "DELHI.npz"), X=X, vars=np.array(VARS),
                        stations=np.array([per[k]["name"] for k in ids]),
                        station_ids=np.array(["|".join(sorted(per[k]["ids"])) for k in ids]),
                        start=np.array(str(idx[0])))
    json.dump(meta, open(os.path.join(RAW, "DELHI_files.json"), "w"), indent=1)
    print(f"DELHI: {len(idx)} hours ({idx[0]} .. {idx[-1]}) x {len(ids)} stations x {len(VARS)} variables", flush=True)
    for c, v in enumerate(VARS):
        print(f"  {v:6s} observed {100 * np.isfinite(X[..., c]).mean():5.1f}%  "
              f"last 365 days {100 * np.isfinite(X[-8760:, :, c]).mean():5.1f}%", flush=True)
    pm = np.isfinite(X[..., 0])
    for j, k in enumerate(ids):
        print(f"  station {per[k]['name'][:40]:40s} files {len(per[k]['parts'])} PM2.5 observed {100 * pm[:, j].mean():5.1f}% "
              f"(last 365 d {100 * pm[-8760:, j].mean():5.1f}%)", flush=True)


if __name__ == "__main__":
    main()
