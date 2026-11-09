"""India-wide pretraining corpus for PWM-India (v2.0) from NOAA's Integrated Surface Database (ISD "Global Hourly":
METAR and SYNOP reports, quality-controlled by NOAA NCEI; free and public, no account). Nothing is re-hosted.

Station rule (fixed before looking at any values):
  * every ISD station with country code IN whose record overlaps 2024 (BEGIN <= 2023-12-31, END >= 2024-06-01);
  * years 2015 .. 2024, hourly value = the report nearest the top of the hour within +-15 minutes, NOAA's
    suspect/erroneous quality flags dropped (the same parser as the WMO league, tools/fetch_isd.py);
  * kept if at least 10% of hours from 2015-01-01 to 2024-11-30 have a temperature; at most 400 stations.

Leakage rule: the corpus ENDS on 2024-11-30, before the earliest validation period of any league (WMO, 2024-12-01).
It therefore contains nothing from any league's validation or test period, for any station.

  python tools/fetch_india.py      # -> data/raw/WX_INDIA.npz
"""
import os, sys, time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fetch_isd as F                                                    # same download, parser and quality rules

RAW = F.RAW
START, END = "2015-01-01", "2024-11-30"
MIN_COV, MAX_N, WORKERS = 0.10, 400, 8
LIM = {"AT": (-30, 52), "RH": (1, 100.5), "WS": (0, 40), "WD": (0, 360), "DP": (-50, 40), "P": (900, 1100),
       "VIS": (0, 4)}


def stations():
    import io
    import pandas as pd
    h = pd.read_csv(io.StringIO(F.get(F.HIST)), dtype=str)
    h = h.rename(columns={"STATION NAME": "NAME", "ELEV(M)": "ELEV"})
    h = h[h["CTRY"] == "IN"].copy()
    for c in ("LAT", "LON", "ELEV"):
        h[c] = pd.to_numeric(h[c], errors="coerce")
    h = h.dropna(subset=["LAT", "LON"])
    h = h[(h["BEGIN"].fillna("99999999") <= "20231231") & (h["END"].fillna("0") >= "20240601")]
    out = [dict(sid=f"{r.USAF}{r.WBAN}", name=str(r.NAME).title(), icao=str(r.ICAO) if isinstance(r.ICAO, str) else "",
                lat=float(r.LAT), lon=float(r.LON), elev=float(r.ELEV) if np.isfinite(r.ELEV) else np.nan)
           for r in h.itertuples()]
    print(f"ISD: {len(out)} Indian stations with records overlapping 2024", flush=True)
    return out


def one(s, T):
    X = np.full((T, len(F.VARS)), np.nan, np.float32)
    for y in range(int(END[:4]), int(START[:4]) - 1, -1):                 # latest year first
        txt = F.get(F.DATA.format(y=y, sid=s["sid"]), tries=4)
        if not txt or "DATE" not in txt[:400]:
            continue
        Xy = F.parse(txt, START, T)
        if Xy is not None:
            X = np.where(np.isfinite(X), X, Xy)
    for ci, v in enumerate(F.VARS):
        lo, hi = LIM[v]
        X[(X[:, ci] < lo) | (X[:, ci] > hi), ci] = np.nan
    X[:, 1] = np.minimum(X[:, 1], 100)
    return X


def main():
    T = int((np.datetime64(END) - np.datetime64(START)).astype(int)) * 24 + 24
    cand = stations()
    keep, Xs, t0 = [], [], time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        for i, (s, X) in enumerate(zip(cand, ex.map(lambda s: one(s, T), cand))):
            cov = float(np.isfinite(X[:, 0]).mean())
            ok = cov >= MIN_COV and len(keep) < MAX_N
            print(f"  [{i + 1}/{len(cand)}] {s['sid']} {s['icao']:4s} {s['name'][:28]:28s} {s['lat']:6.2f} {s['lon']:6.2f} "
                  f"{s['elev']:6.0f} m: hourly AT {100 * cov:3.0f}% -> {'kept' if ok else 'dropped'} "
                  f"({time.time() - t0:.0f}s)", flush=True)
            if ok:
                keep.append(s); Xs.append(X)
    X = np.stack(Xs, 1)
    np.savez_compressed(os.path.join(RAW, "WX_INDIA.npz"), X=X, vars=np.array(F.VARS),
                        stations=np.array([f"{s['icao'] or s['sid']} {s['name']}" for s in keep]),
                        ids=np.array([s["sid"] for s in keep]), lat=np.array([s["lat"] for s in keep]),
                        lon=np.array([s["lon"] for s in keep]), elev=np.array([s["elev"] for s in keep]),
                        start=np.array(START + "T00"), tz=np.array("GMT"))
    n_obs = int(np.isfinite(X[..., 0]).sum())
    print(f"WX_INDIA: {T} hours {START}..{END} x {len(keep)} stations = {T * len(keep):,} station-hours "
          f"({n_obs:,} with a temperature); missing % {np.round(100 * np.isnan(X).mean((0, 1)), 1).tolist()} "
          f"for {F.VARS}; file {os.path.getsize(os.path.join(RAW, 'WX_INDIA.npz')) / 1e6:.0f} MB", flush=True)


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    main()
