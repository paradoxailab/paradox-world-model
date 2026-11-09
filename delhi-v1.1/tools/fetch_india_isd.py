"""PWM-F pretraining data: every Indian station in NOAA's Integrated Surface Database (ISD "Global Hourly", METAR and
SYNOP reports, NOAA quality control; free, public, no account), 2015-01-01 .. 2024-11-30.

Why that end date: 2024-11-30 is the day before the earliest validation period of any league (WMO, 2024-12-01), so
pretraining never sees the weather of any league's validation or test period.
Station rule (fixed before looking at values): ISD country code IN, a record overlapping 2015-01-01 .. 2024-11-30, and
at least 10% of hours with a temperature over that span. Same parsing, quality flags and limits as tools/fetch_isd.py.
Stations are grouped by position (k-means) into regional networks of about 30, written as WX_IN01.npz, WX_IN02.npz ...
in the WX_WMO.npz format, plus IN_stations.csv listing every station and its network.

  python tools/fetch_india_isd.py [--workers 6] [--per 30]
"""
import argparse, math, os, sys, time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
from fetch_isd import get, parse, HIST, DATA, ADS, VARS          # noqa: E402

RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
START, END = "2015-01-01", "2024-11-30"
LIM = {"AT": (-30, 52), "RH": (1, 100.5), "WS": (0, 40), "WD": (0, 360), "DP": (-45, 40), "P": (850, 1100),
       "VIS": (0, 4)}


def stations():
    import io
    import pandas as pd
    h = pd.read_csv(io.StringIO(get(HIST)), dtype=str)
    h = h.rename(columns={"STATION NAME": "NAME", "ELEV(M)": "ELEV"})
    h = h[h["CTRY"] == "IN"].copy()
    for c in ("LAT", "LON", "ELEV"):
        h[c] = pd.to_numeric(h[c], errors="coerce")
    h = h.dropna(subset=["LAT", "LON"])
    h = h[(h["LAT"].abs() > 0.1) & (h["LON"].abs() > 0.1)]
    h = h[(h["BEGIN"].fillna("99999999") <= END.replace("-", "")) & (h["END"].fillna("0") >= START.replace("-", ""))]
    out = [dict(sid=f"{r.USAF}{r.WBAN}", name=str(r.NAME).title(), icao=str(r.ICAO) if isinstance(r.ICAO, str) else "",
                lat=float(r.LAT), lon=float(r.LON), elev=float(r.ELEV) if r.ELEV == r.ELEV else float("nan"),
                begin=str(r.BEGIN), end=str(r.END))
           for r in h.itertuples()]
    print(f"ISD: {len(out)} Indian stations with records overlapping {START} .. {END}", flush=True)
    return out


def one(s, T):
    X = np.full((T, len(VARS)), np.nan, np.float32)
    y0, y1 = max(int(START[:4]), int(s["begin"][:4] or START[:4])), min(int(END[:4]), int(s["end"][:4] or END[:4]))
    got = 0
    for y in range(y0, y1 + 1):
        txt = get(DATA.format(y=y, sid=s["sid"]), tries=4)
        if not txt or "DATE" not in txt[:400]:
            txt = get(ADS.format(y=y, sid=s["sid"]), tries=3)
        if not txt or "DATE" not in txt[:400]:
            continue
        Xy = parse(txt, START, T)
        if Xy is not None:
            X = np.where(np.isfinite(X), X, Xy)
            got += 1
    for ci, v in enumerate(VARS):
        lo, hi = LIM[v]
        X[(X[:, ci] < lo) | (X[:, ci] > hi), ci] = np.nan
    X[:, 1] = np.minimum(X[:, 1], 100)
    return X, got


def kmeans(lat, lon, k, seed=0):
    P = np.stack([lat, lon * np.cos(np.deg2rad(lat.mean()))], -1)
    rng = np.random.default_rng(seed)
    C = P[rng.choice(len(P), k, replace=False)]
    for _ in range(100):
        lab = ((P[:, None] - C[None]) ** 2).sum(-1).argmin(1)
        C = np.array([P[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
    return lab


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--per", type=int, default=30, help="about this many stations per regional network")
    ap.add_argument("--limit", type=int, default=0, help="debug: only the first N stations")
    a = ap.parse_args()
    T = int((np.datetime64(END) - np.datetime64(START)).astype(int)) * 24 + 24
    S = stations()
    if a.limit:
        S = S[:a.limit]
    t0 = time.time()
    keep, Xs = [], []
    with ThreadPoolExecutor(a.workers) as ex:
        for i, (s, (X, got)) in enumerate(zip(S, ex.map(lambda s: one(s, T), S))):
            cov = float(np.isfinite(X[:, 0]).mean())
            ok = cov >= 0.10
            print(f"  [{i + 1}/{len(S)}] {s['sid']} {s['icao']:4s} {s['name'][:26]:26s} {s['lat']:6.2f} {s['lon']:6.2f} "
                  f"years {got:2d} hourly AT {100 * cov:4.1f}% -> {'kept' if ok else 'dropped'} "
                  f"({time.time() - t0:.0f}s)", flush=True)
            if ok:
                keep.append(s); Xs.append(X)
    if not keep:
        raise SystemExit("no station kept")
    lat = np.array([s["lat"] for s in keep]); lon = np.array([s["lon"] for s in keep])
    k = max(1, int(round(len(keep) / a.per)))
    lab = kmeans(lat, lon, k)
    rows = ["network,sid,icao,name,lat,lon,elev,at_coverage_pct"]
    nets = 0
    for j in range(k):
        idx = np.where(lab == j)[0]
        if len(idx) < 3:
            continue
        nets += 1
        nm = f"IN{nets:02d}"
        X = np.stack([Xs[i] for i in idx], 1)
        np.savez_compressed(os.path.join(RAW, f"WX_{nm}.npz"), X=X, vars=np.array(VARS),
                            stations=np.array([f"{keep[i]['icao'] or keep[i]['sid']} {keep[i]['name']}" for i in idx]),
                            ids=np.array([keep[i]["sid"] for i in idx]), lat=lat[idx], lon=lon[idx],
                            elev=np.array([keep[i]["elev"] for i in idx]), start=np.array(START + "T00"),
                            tz=np.array("GMT"))
        for i in idx:
            s = keep[i]
            rows.append(f"{nm},{s['sid']},{s['icao']},\"{s['name']}\",{s['lat']:.3f},{s['lon']:.3f},{s['elev']},"
                        f"{100 * np.isfinite(Xs[i][:, 0]).mean():.1f}")
        print(f"WX_{nm}: {len(idx)} stations around {lat[idx].mean():.1f} N {lon[idx].mean():.1f} E; missing % "
              f"{np.round(100 * np.isnan(X).mean((0, 1)), 1).tolist()}", flush=True)
    open(os.path.join(RAW, "IN_stations.csv"), "w").write("\n".join(rows) + "\n")
    sh = sum(int(np.isfinite(x[:, 0]).sum()) for x in Xs)
    print(f"INDIA-PRETRAIN: {len(keep)} stations in {nets} networks, {T} hours each ({START} .. {END}); "
          f"{sh:,} station-hours with a temperature; {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    main()
