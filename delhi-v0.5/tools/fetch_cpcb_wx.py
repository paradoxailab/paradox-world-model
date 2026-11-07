"""Delhi's CPCB station network as a weather league: each station's own temperature, humidity and wind sensors
(from data/raw/DELHI.npz, built by tools/fetch_delhi.py), plus station coordinates.

The CPCB files carry no coordinates, so each station is located by its name with OpenStreetMap's Nominatim
geocoder (one request per second, as its usage policy asks). Rule: query "<station name>, Delhi, India"; accept
only a result inside the Delhi region (28.35-28.95 N, 76.80-77.45 E); if none, try the name's first part; a
station that still cannot be placed is left out of this league (listed in the output). Locality-level positions
(~1-2 km) are far finer than the global models' grids (9-28 km). The coordinates are written to
results/cpcb_station_coords.csv so they can be checked.

  python tools/fetch_cpcb_wx.py      # -> data/raw/WX_CPCB.npz
"""
import csv, os, re, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
OUT = os.environ.get("PW_OUT", os.path.join(ROOT, "results"))
UA = {"User-Agent": "paradox-world-model-data-builder"}
BOX = (28.35, 28.95, 76.80, 77.45)
KEEP_VARS = ["AT", "RH", "WS", "WD", "SR", "BP", "PM2.5"]


def clean(name):
    n = re.split(r"\s+-\s+", str(name))[0]
    n = re.sub(r",?\s*(New\s+)?Delhi\b.*$", "", n, flags=re.I).strip(" ,")
    return n


def geocode(q):
    import requests
    for k in range(4):
        try:
            r = requests.get("https://nominatim.openstreetmap.org/search", headers=UA, timeout=60,
                             params=dict(q=q, format="json", limit=5, countrycodes="in"))
            r.raise_for_status()
            time.sleep(1.1)
            for h in r.json():
                la, lo = float(h["lat"]), float(h["lon"])
                if BOX[0] <= la <= BOX[1] and BOX[2] <= lo <= BOX[3]:
                    return la, lo, h.get("display_name", "")
            return None
        except Exception as e:
            print(f"    geocoder retry {k + 1}: {str(e)[:120]}", flush=True)
            time.sleep(5 * (k + 1))
    return None


def main():
    z = np.load(os.path.join(RAW, "DELHI.npz"))
    X, names, st = z["X"], [str(v) for v in z["vars"]], [str(s) for s in z["stations"]]
    rows, keep = [], []
    for i, s in enumerate(st):
        base = clean(s)
        tries = [f"{base}, Delhi, India", f"{base.split(',')[0].split('(')[0].strip()}, Delhi, India",
                 f"{' '.join(base.split()[:2])}, Delhi, India"]
        g, used = None, None
        for q in dict.fromkeys(tries):
            g = geocode(q)
            if g:
                used = q
                break
        rows.append([s, used or "", *(g[:2] if g else ("", "")), g[2][:120] if g else "NOT PLACED"])
        print(f"  {s}: {'%.4f, %.4f' % g[:2] if g else 'NOT PLACED'}", flush=True)
        if g:
            keep.append((i, g[0], g[1]))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "cpcb_station_coords.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["station", "query", "lat", "lon", "osm_match"]); w.writerows(rows)
    ix = [k[0] for k in keep]
    Xw = np.stack([X[:, ix, names.index(v)] for v in KEEP_VARS], -1).astype(np.float32)
    for c in range(3):                               # stuck weather sensors: 12+ identical hours in a row -> missing
        for j in range(Xw.shape[1]):
            x = Xw[:, j, c]
            same = np.concatenate([[False], np.diff(x) == 0])
            run = np.zeros(len(x), np.int32)
            for t in range(1, len(x)):
                run[t] = run[t - 1] + 1 if same[t] else 0
            bad = np.zeros(len(x), bool)
            for t in np.where(run >= 11)[0]:
                bad[t - run[t]:t + 1] = True
            x[bad] = np.nan
    if "RH" in KEEP_VARS:
        Xw[..., 1] = np.where(Xw[..., 1] < 1, np.nan, np.minimum(Xw[..., 1], 100))
    np.savez_compressed(os.path.join(RAW, "WX_CPCB.npz"), X=Xw, vars=np.array(KEEP_VARS),
                        stations=np.array([st[i] for i in ix]), ids=np.array([st[i] for i in ix]),
                        lat=np.array([k[1] for k in keep]), lon=np.array([k[2] for k in keep]),
                        elev=np.full(len(ix), 216.0), start=np.array(str(z["start"])[:13].replace(" ", "T")),
                        tz=np.array("Asia/Kolkata"))
    print(f"WX_CPCB: {Xw.shape[0]} hours x {len(ix)} of {len(st)} stations placed; missing % "
          f"{np.round(100 * np.isnan(Xw).mean((0, 1)), 1).tolist()} for {KEEP_VARS}", flush=True)


if __name__ == "__main__":
    main()
