"""WMO-grade airport weather observations for Delhi and north India (METAR reports, via the Iowa Environmental
Mesonet ASOS/METAR archive; free, no key). Nothing is re-hosted.

Station rule (fixed before looking at values): every station of IEM's India network within 600 km of Delhi
(Palam, 28.57 N 77.10 E) and below 1,000 m elevation, nearest first, at most 16; kept only if it has >= 60% of
hourly temperatures in the training period. Hourly value = the report closest to the top of the hour within
+-15 minutes (Indian airports report at :00 and :30). Quality limits: AT -15..52 C, RH 1..100 %, WS 0..40 m/s.

  python tools/fetch_metar.py      # -> data/raw/WX_METAR.npz
"""
import datetime as dt, io, math, os, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pw.leagues import LEAGUES, bounds

RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
IEM = "https://mesonet.agron.iastate.edu"
UA = {"User-Agent": "paradox-world-model-data-builder"}
DELHI = (28.57, 77.10)
MAX_KM, MAX_ELEV, MAX_N = 600.0, 1000.0, 16
VARS = ["AT", "RH", "WS", "WD", "DP", "P", "VIS"]


def get(url, params=None, tries=8, text=True):
    import requests
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=300, headers=UA)
            r.raise_for_status()
            if text and r.text.startswith("ERROR"):
                raise RuntimeError(r.text[:200])
            return r.text if text else r.json()
        except Exception as e:
            print(f"    retry {k + 1}/{tries}: {str(e)[:160]}", flush=True)
            if k == tries - 1:
                raise
            time.sleep(min(60, 5 * (k + 1)))


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def stations():
    j = get(f"{IEM}/geojson/network/IN__ASOS.geojson", text=False)
    out = []
    for f in j["features"]:
        p, (lo, la) = f["properties"], f["geometry"]["coordinates"][:2]
        el = p.get("elevation")
        el = float(el) if el not in (None, "") else float("nan")
        d = km(DELHI, (la, lo))
        if d <= MAX_KM and not (el >= MAX_ELEV):
            out.append(dict(sid=p["sid"], name=p.get("sname", p["sid"]), lat=float(la), lon=float(lo), elev=el, km=d))
    out.sort(key=lambda s: s["km"])
    print(f"IEM India network: {len(j['features'])} stations, {len(out)} within {MAX_KM:.0f} km and below "
          f"{MAX_ELEV:.0f} m: {[s['sid'] for s in out]}", flush=True)
    return out


def fetch(sid, y0, y1):
    import pandas as pd
    frames = []
    for y in range(y0, y1 + 1):
        a, b = dt.date(y, 1, 1), dt.date(y + 1, 1, 1)
        p = [("station", sid)] + [("data", v) for v in ("tmpf", "dwpf", "relh", "sknt", "drct", "alti", "mslp", "vsby")]
        p += [("year1", a.year), ("month1", a.month), ("day1", a.day), ("year2", b.year), ("month2", b.month),
              ("day2", b.day), ("tz", "Etc/UTC"), ("format", "onlycomma"), ("latlon", "no"), ("missing", "M"),
              ("trace", "T"), ("direct", "no"), ("report_type", "3"), ("report_type", "4")]
        txt = get(f"{IEM}/cgi-bin/request/asos.py", p)
        df = pd.read_csv(io.StringIO(txt), na_values=["M", "T", ""], low_memory=False)
        if len(df):
            frames.append(df)
        time.sleep(1)
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def hourly(df, start, T):
    """[T, len(VARS)] from raw reports: the report nearest the top of each hour within +-15 min."""
    import pandas as pd
    t = pd.to_datetime(df["valid"], utc=True, errors="coerce").dt.tz_localize(None)
    s0 = pd.Timestamp(start)
    h = ((t - s0).dt.total_seconds() / 3600.0).to_numpy()
    k = np.round(h).astype("float64")
    off = np.abs(h - k)
    num = lambda c: pd.to_numeric(df[c], errors="coerce").to_numpy(np.float64) if c in df else np.full(len(df), np.nan)
    tf, dp, rh, kt = num("tmpf"), num("dwpf"), num("relh"), num("sknt")
    at, dpc = (tf - 32) * 5 / 9, (dp - 32) * 5 / 9
    rh_calc = 100 * np.exp(17.625 * dpc / (243.04 + dpc)) / np.exp(17.625 * at / (243.04 + at))
    rh = np.where(np.isfinite(rh), rh, rh_calc)
    p = num("mslp")
    p = np.where(np.isfinite(p), p, num("alti") * 33.8639)
    cols = [at, rh, kt * 0.514444, num("drct"), dpc, p, np.log1p(np.clip(num("vsby"), 0, 20))]
    ok = np.isfinite(k) & (off <= 0.25) & (k >= 0) & (k < T)
    X = np.full((T, len(VARS)), np.nan, np.float32)
    best = np.full(T, np.inf)
    order = np.argsort(off)[::-1]                    # write far reports first, nearest last (nearest wins)
    for i in order:
        if ok[i]:
            j = int(k[i])
            row = [c[i] for c in cols]
            if off[i] <= best[j]:
                for c, v in enumerate(row):
                    if np.isfinite(v):
                        X[j, c] = v
                best[j] = off[i]
    lim = {"AT": (-15, 52), "RH": (1, 100.5), "WS": (0, 40), "WD": (0, 360), "DP": (-40, 40), "P": (900, 1100),
           "VIS": (0, 4)}
    for c, v in enumerate(VARS):
        lo, hi = lim[v]
        X[(X[:, c] < lo) | (X[:, c] > hi), c] = np.nan
    X[:, 1] = np.minimum(X[:, 1], 100)
    return X


def main():
    c = LEAGUES["METAR"]
    start = c["start"]
    T = int((np.datetime64(c["end"]) - np.datetime64(start)).astype(int)) * 24 + 24
    b_tr = bounds("METAR", T)["train"][1]
    cand = stations()
    keep, Xs = [], []
    for s in cand:
        if len(keep) >= MAX_N:
            break
        df = fetch(s["sid"], int(start[:4]), int(c["end"][:4]))
        if df is None:
            print(f"  {s['sid']} {s['name']}: no data", flush=True)
            continue
        X = hourly(df, start, T)
        cov = np.isfinite(X[:b_tr, 0]).mean()
        cov_te = np.isfinite(X[b_tr:, 0]).mean()
        print(f"  {s['sid']} {s['name']} ({s['km']:.0f} km, {s['elev']:.0f} m): {len(df)} reports, hourly AT "
              f"coverage train {100 * cov:.0f}%, later {100 * cov_te:.0f}%", flush=True)
        if cov >= 0.6 and cov_te >= 0.6:
            keep.append(s); Xs.append(X)
    X = np.stack(Xs, 1)
    np.savez_compressed(os.path.join(RAW, "WX_METAR.npz"), X=X, vars=np.array(VARS),
                        stations=np.array([f"{s['sid']} {s['name']}" for s in keep]),
                        ids=np.array([s["sid"] for s in keep]), lat=np.array([s["lat"] for s in keep]),
                        lon=np.array([s["lon"] for s in keep]), elev=np.array([s["elev"] for s in keep]),
                        start=np.array(start + "T00"), tz=np.array("GMT"))
    print(f"WX_METAR: {T} hours from {start} x {len(keep)} stations {[s['sid'] for s in keep]}; missing % "
          f"{np.round(100 * np.isnan(X).mean((0, 1)), 1).tolist()} for {VARS}", flush=True)


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    main()
