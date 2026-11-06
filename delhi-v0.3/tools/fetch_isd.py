"""WMO weather-station observations for Delhi and north India from NOAA's Integrated Surface Database (ISD,
"Global Hourly": METAR and SYNOP reports, quality-controlled by NOAA NCEI; free, public). Nothing is re-hosted.

Station rule (fixed before looking at any values): every Indian ISD station within 500 km of Delhi (Safdarjung,
28.58 N 77.21 E), below 1,000 m, whose ISD record spans 2021-01-01 .. 2025-08-01 (NOAA's Indian records end on 2025-08-24); nearest first; kept if at least
10% of hours have a temperature in both the training and the test period (3-hourly SYNOP stations qualify; scoring
uses observed hours only); at most 24 stations.
Hourly value = the report nearest the top of the hour within +-15 minutes; NOAA's suspect/erroneous quality
flags (2, 3, 6, 7) are dropped. Limits: AT -15..52 C, RH 1..100 %, WS 0..40 m/s.

  python tools/fetch_isd.py      # -> data/raw/WX_WMO.npz
"""
import io, math, os, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pw.leagues import LEAGUES, bounds

RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
HIST = "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv"
DATA = "https://www.ncei.noaa.gov/data/global-hourly/access/{y}/{sid}.csv"
ADS = ("https://www.ncei.noaa.gov/access/services/data/v1?dataset=global-hourly&stations={sid}"
       "&startDate={y}-01-01&endDate={y}-12-31&format=csv")
UA = {"User-Agent": "paradox-world-model-data-builder"}
DELHI = (28.58, 77.21)
MAX_KM, MAX_ELEV, MAX_N, MIN_COV = 500.0, 1000.0, 24, 0.10
VARS = ["AT", "RH", "WS", "WD", "DP", "P", "VIS"]
BAD_Q = set("2367")


def get(url, tries=8):
    import requests
    for k in range(tries):
        try:
            r = requests.get(url, timeout=600, headers=UA, allow_redirects=True)
            if r.status_code == 404:
                print(f"    404 {url} (final {r.url})", flush=True)
                return None
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"    retry {k + 1}/{tries}: {str(e)[:160]}", flush=True)
            if k == tries - 1:
                return None
            time.sleep(min(60, 5 * (k + 1)))


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def stations(start, end):
    import pandas as pd
    h = pd.read_csv(io.StringIO(get(HIST)), dtype=str)
    h = h.rename(columns={"STATION NAME": "NAME", "ELEV(M)": "ELEV"})
    print(f"ISD history: {len(h)} stations, {int((h['CTRY'] == 'IN').sum())} in India", flush=True)
    h = h[(h["CTRY"] == "IN")].copy()
    for c in ("LAT", "LON", "ELEV"):
        h[c] = pd.to_numeric(h[c], errors="coerce")
    h = h.dropna(subset=["LAT", "LON"])
    h["km"] = [km(DELHI, (a, b)) for a, b in zip(h["LAT"], h["LON"])]
    near = h[h["km"] <= MAX_KM].sort_values("km")
    print("nearest Indian ISD stations (id, name, km, elev, begin, end):", flush=True)
    for r in near.head(40).itertuples():
        print(f"    {r.USAF}{r.WBAN} {str(r.NAME)[:26]:26s} {r.km:5.0f} {r.ELEV} {r.BEGIN} {r.END}", flush=True)
    h = h[(h["BEGIN"].fillna("99999999") <= start.replace("-", "")) & (h["END"].fillna("0") >= end.replace("-", ""))]
    h = h[(h["km"] <= MAX_KM) & ~(h["ELEV"] >= MAX_ELEV)].sort_values("km")
    out = [dict(sid=f"{r.USAF}{r.WBAN}", name=str(r.NAME).title(), icao=str(r.ICAO) if isinstance(r.ICAO, str) else "",
                lat=float(r.LAT), lon=float(r.LON), elev=float(r.ELEV), km=r.km)
           for r in h.itertuples()]
    print(f"ISD: {len(out)} Indian stations within {MAX_KM:.0f} km, below {MAX_ELEV:.0f} m, spanning {start}..{end}: "
          f"{[(s['sid'], s['name'][:18]) for s in out]}", flush=True)
    return out


def field(s, scale, missing, val_idx=0, q_idx=1):
    import pandas as pd
    parts = s.fillna("").str.split(",", expand=True)
    v = parts[val_idx].fillna("").str.replace("+", "", regex=False)
    x = pd.to_numeric(v.where(~v.isin(missing)), errors="coerce").to_numpy(np.float64) / scale
    if parts.shape[1] > q_idx:
        x[np.isin(parts[q_idx].fillna("9").to_numpy(), list(BAD_Q))] = np.nan
    return x


def parse(txt, start, T):
    import pandas as pd
    df = pd.read_csv(io.StringIO(txt), usecols=lambda c: c in ("DATE", "TMP", "DEW", "WND", "SLP", "VIS"),
                     dtype=str, low_memory=False)
    if not len(df):
        return None
    t = pd.to_datetime(df["DATE"], errors="coerce")
    h = ((t - pd.Timestamp(start)).dt.total_seconds() / 3600.0).to_numpy()
    k = np.round(h)
    off = np.abs(h - k)
    nan = np.full(len(df), np.nan)
    at = field(df["TMP"], 10, ["9999"]) if "TMP" in df else nan
    dp = field(df["DEW"], 10, ["9999"]) if "DEW" in df else nan
    if "WND" in df:
        w = df["WND"].fillna(",,,,").str.split(",", expand=True)
        wd = pd.to_numeric(w[0].where(w[0] != "999"), errors="coerce").to_numpy(np.float64)
        ws = pd.to_numeric(w[3].where(w[3] != "9999"), errors="coerce").to_numpy(np.float64) / 10
        ws[np.isin(w[4].fillna("9").to_numpy(), list(BAD_Q))] = np.nan
        ws[(w[2] == "C").to_numpy()] = 0.0
    else:
        wd = ws = nan
    p = field(df["SLP"], 10, ["99999"]) if "SLP" in df else nan
    vis = field(df["VIS"], 1000, ["999999"]) if "VIS" in df else nan
    rh = 100 * np.exp(17.625 * dp / (243.04 + dp)) / np.exp(17.625 * at / (243.04 + at))
    cols = [at, rh, ws, wd, dp, p, np.log1p(np.clip(vis, 0, 20))]
    ok = np.isfinite(k) & (off <= 0.25) & (k >= 0) & (k < T)
    X = np.full((T, len(VARS)), np.nan, np.float32)
    best = np.full(T, np.inf)
    for i in np.where(ok)[0][np.argsort(-off[ok])]:
        j = int(k[i])
        if off[i] <= best[j]:
            for c in range(len(VARS)):
                if np.isfinite(cols[c][i]):
                    X[j, c] = cols[c][i]
            best[j] = off[i]
    return X


def main():
    c = LEAGUES["WMO"]
    start = c["start"]
    T = int((np.datetime64(c["end"]) - np.datetime64(start)).astype(int)) * 24 + 24
    B = bounds("WMO", T)
    lim = {"AT": (-15, 52), "RH": (1, 100.5), "WS": (0, 40), "WD": (0, 360), "DP": (-40, 40), "P": (900, 1100),
           "VIS": (0, 4)}
    keep, Xs = [], []
    for s in stations(start, "2025-08-01"):
        if len(keep) >= MAX_N:
            break
        X = np.full((T, len(VARS)), np.nan, np.float32)
        for y in range(int(c["end"][:4]), int(start[:4]) - 1, -1):          # latest year first
            txt = get(DATA.format(y=y, sid=s["sid"]))
            if not txt or "DATE" not in txt[:400]:
                txt = get(ADS.format(y=y, sid=s["sid"]))
            if not txt or "DATE" not in txt[:400]:
                print(f"    {s['sid']} {y}: no data ({(txt or '')[:120]!r})", flush=True)
                continue
            Xy = parse(txt, start, T)
            if Xy is not None:
                X = np.where(np.isfinite(X), X, Xy)
            if y == int(c["end"][:4]) and np.isfinite(X[B["test"][0]:B["test"][1], 0]).mean() < MIN_COV:
                break                                                          # not enough in the test period
        for ci, v in enumerate(VARS):
            lo, hi = lim[v]
            X[(X[:, ci] < lo) | (X[:, ci] > hi), ci] = np.nan
        X[:, 1] = np.minimum(X[:, 1], 100)
        ctr = np.isfinite(X[B["train"][0]:B["train"][1], 0]).mean()
        cte = np.isfinite(X[B["test"][0]:B["test"][1], 0]).mean()
        ok = ctr >= MIN_COV and cte >= MIN_COV
        print(f"  {s['sid']} {s['icao']:4s} {s['name'][:28]:28s} {s['km']:4.0f} km {s['elev']:5.0f} m: hourly AT "
              f"train {100 * ctr:3.0f}% test {100 * cte:3.0f}% -> {'kept' if ok else 'dropped'}", flush=True)
        if ok:
            keep.append(s); Xs.append(X)
    X = np.stack(Xs, 1)
    np.savez_compressed(os.path.join(RAW, "WX_WMO.npz"), X=X, vars=np.array(VARS),
                        stations=np.array([f"{s['icao'] or s['sid']} {s['name']}" for s in keep]),
                        ids=np.array([s["sid"] for s in keep]), lat=np.array([s["lat"] for s in keep]),
                        lon=np.array([s["lon"] for s in keep]), elev=np.array([s["elev"] for s in keep]),
                        start=np.array(start + "T00"), tz=np.array("GMT"))
    print(f"WX_WMO: {T} hours from {start} x {len(keep)} stations; missing % "
          f"{np.round(100 * np.isnan(X).mean((0, 1)), 1).tolist()} for {VARS}", flush=True)


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    main()
