"""v2.0 pretraining corpus: every Indian station in NOAA's Integrated Surface Database (ISD, free and public), hourly
temperature, relative humidity and wind speed from 2010 up to the CUTOFF.

Leakage rule (fixed in advance): the corpus ends on 2024-12-01 00 UTC, before the earliest validation period of any
league (WMO validation starts 2024-12-01; CPCB 2025-05-03; airports 2025-11-01). So no hour that any league uses for
model choice or testing is in the pretraining corpus. A station is kept if at least 5% of its hours have a
temperature. Hourly value = report nearest the top of the hour within +-15 min; NOAA suspect flags dropped (as in
tools/fetch_isd.py, whose parser is reused).

  python tools/fetch_india.py --workers 6      # -> $PW_RAW/PRE_INDIA.npz
"""
import argparse, io, os, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fetch_isd as FI

RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
START, CUTOFF = "2010-01-01", "2024-12-01"
MIN_COV = 0.05
LIM = {"AT": (-30, 52), "RH": (1, 100.5), "WS": (0, 40)}


def all_india():
    import pandas as pd
    h = pd.read_csv(io.StringIO(FI.get(FI.HIST)), dtype=str)
    h = h.rename(columns={"STATION NAME": "NAME", "ELEV(M)": "ELEV"})
    h = h[h["CTRY"] == "IN"].copy()
    for c in ("LAT", "LON", "ELEV"):
        h[c] = pd.to_numeric(h[c], errors="coerce")
    h = h.dropna(subset=["LAT", "LON"])
    h = h[(h["END"].fillna("0") >= "20120101") & (h["BEGIN"].fillna("99999999") <= "20240601")]
    h = h[(h["LAT"] > 5) & (h["LAT"] < 38) & (h["LON"] > 67) & (h["LON"] < 98)]
    out = [dict(sid=f"{r.USAF}{r.WBAN}", name=str(r.NAME).title(), lat=float(r.LAT), lon=float(r.LON),
                elev=float(r.ELEV) if r.ELEV == r.ELEV else 0.0, begin=str(r.BEGIN), end=str(r.END))
           for r in h.itertuples()]
    out = list({s["sid"]: s for s in out}.values())
    print(f"ISD: {len(out)} Indian stations with records overlapping 2012..2024", flush=True)
    return out


def one(s, T):
    X = np.full((T, 3), np.nan, np.float32)
    y0 = max(int(START[:4]), int(s["begin"][:4]) if s["begin"][:4].isdigit() else 2010)
    y1 = min(int(CUTOFF[:4]), int(s["end"][:4]) if s["end"][:4].isdigit() else 2024)
    got = 0
    for y in range(y0, y1 + 1):
        txt = FI.get(FI.DATA.format(y=y, sid=s["sid"]), tries=4)
        if not txt or "DATE" not in txt[:400]:
            continue
        Xy = FI.parse(txt, START, T)
        if Xy is None:
            continue
        got += 1
        X = np.where(np.isfinite(X), X, Xy[:, :3])
    for ci, v in enumerate(("AT", "RH", "WS")):
        lo, hi = LIM[v]
        X[(X[:, ci] < lo) | (X[:, ci] > hi), ci] = np.nan
    X[:, 1] = np.minimum(X[:, 1], 100)
    return s, X, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--max_stations", type=int, default=0)
    a = ap.parse_args()
    T = int((np.datetime64(CUTOFF) - np.datetime64(START)).astype(int)) * 24
    sts = all_india()
    if a.max_stations:
        sts = sts[:a.max_stations]
    keep, Xs, t0 = [], [], time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        futs = [ex.submit(one, s, T) for s in sts]
        for i, f in enumerate(as_completed(futs)):
            try:
                s, X, got = f.result()
            except Exception as e:
                print(f"  failed: {str(e)[:120]}", flush=True)
                continue
            cov = np.isfinite(X[:, 0]).mean()
            ok = cov >= MIN_COV
            print(f"  [{i + 1}/{len(sts)} {time.time() - t0:5.0f}s] {s['sid']} {s['name'][:24]:24s} {s['lat']:6.2f} "
                  f"{s['lon']:6.2f} {s['elev']:6.0f} m: {got} years, AT coverage {100 * cov:4.1f}% -> "
                  f"{'kept' if ok else 'dropped'}", flush=True)
            if ok:
                keep.append(s); Xs.append(X.astype(np.float16))
    order = np.argsort([s["sid"] for s in keep])
    keep = [keep[i] for i in order]
    X = np.stack([Xs[i] for i in order], 1)                                  # [T, N, 3] float16
    np.savez_compressed(os.path.join(RAW, "PRE_INDIA.npz"), X=X, vars=np.array(["AT", "RH", "WS"]),
                        ids=np.array([s["sid"] for s in keep]), names=np.array([s["name"] for s in keep]),
                        lat=np.array([s["lat"] for s in keep], np.float32),
                        lon=np.array([s["lon"] for s in keep], np.float32),
                        elev=np.array([s["elev"] for s in keep], np.float32),
                        start=np.array(START + "T00"), cutoff=np.array(CUTOFF + "T00"))
    obs = int(np.isfinite(X[..., 0].astype(np.float32)).sum())
    print(f"PRE_INDIA: {T} hours x {len(keep)} stations; {obs:,} observed station-hours of temperature; missing % "
          f"{np.round(100 * np.isnan(X.astype(np.float32)).mean((0, 1)), 1).tolist()}; "
          f"{os.path.getsize(os.path.join(RAW, 'PRE_INDIA.npz')) / 1e6:.0f} MB", flush=True)


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    main()
