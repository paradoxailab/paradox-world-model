"""v2.1 pretraining corpus: CPCB-type rooftop air-quality stations in six more Indian cities, with their own
meteorological sensors, from OpenCity's public "<city> Hourly Air Quality Reports" (the same source and file format
as the Delhi league, tools/fetch_delhi.py). No account or key is needed.

Cities: Mumbai, Kolkata, Chennai, Pune, Hyderabad, Bengaluru (Delhi is the test league and is NOT included).
Files: the "15 minute AQI Data for 2024-25" series only (measurements of every pollutant plus AT, RH, WS, WD, SR, BP);
the 2017-2023 files hold only the composite AQI and are not used.

Rules fixed in advance (same as the Delhi league):
  * hourly value = mean of the hour's 15-minute readings, needs >= 2 of 4; the clock is checked against the solar
    radiation peak and moved to Indian time if it is really UTC (fetch_delhi.read_station);
  * non-numbers, negatives (except temperature) and values above physical ceilings become missing;
  * runs of identical readings of 12 h or longer in AT, RH, WS (stuck sensors), or 24 h in a pollutant, are missing.
Leakage rule: the corpus ENDS at 2025-05-03 00:00 IST, the start of the Delhi league's validation period, so no hour
the Delhi league uses for model choice or testing (nor any later hour) is in it.
Positions: the city centre (only the sun's position is derived from it; a few km do not change it).

  python tools/fetch_cpcb_india.py      # -> $PW_RAW/WX_CPCBIN.npz
"""
import concurrent.futures as cf
import json, os, re, sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import fetch_delhi as FD

RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
API = "https://data.opencity.in/api/3/action/package_show?id={c}-hourly-air-quality-reports"
CITIES = {"mumbai": (19.076, 72.877), "kolkata": (22.573, 88.364), "chennai": (13.083, 80.271),
          "pune": (18.520, 73.857), "hyderabad": (17.385, 78.487), "bengaluru": (12.972, 77.595)}
START, CUTOFF = "2024-01-01 00:00", "2025-05-03 00:00"          # Indian Standard Time
KEEP = ["AT", "RH", "WS", "WD", "SR", "BP", "PM2.5", "PM10", "NO2", "Ozone", "CO", "SO2"]
MET = {"AT", "RH", "WS"}


def main():
    import pandas as pd
    out_dir = os.path.join(RAW, "cpcbin_csv"); os.makedirs(out_dir, exist_ok=True)
    jobs = []
    for c, (la, lo) in CITIES.items():
        pkg = FD.get(API.format(c=c))["result"]
        res = [r for r in pkg["resources"] if str(r.get("url", "")).lower().endswith(".csv")
               and "2024" in str(r.get("name", ""))]
        print(f"{c}: {len(res)} 2024-25 measurement files", flush=True)
        jobs += [(c, la, lo, r) for r in res]

    def dl(j):
        f = os.path.join(out_dir, os.path.basename(j[3]["url"]))
        if not os.path.exists(f):
            open(f, "wb").write(FD.get(j[3]["url"], binary=True))
        return j, f

    with cf.ThreadPoolExecutor(6) as ex:
        got = list(ex.map(dl, jobs))
    print(f"downloaded {len(got)} files, {sum(os.path.getsize(f) for _, f in got) / 2**20:.0f} MB", flush=True)
    idx = pd.date_range(START, CUTOFF, freq="h", inclusive="left")
    cols, names, cities, lat, lon, ids, meta = [], [], [], [], [], [], []
    for (c, la, lo, r), f in got:
        try:
            sid, name, m, info = FD.read_station(f)
        except Exception as e:
            print(f"  {os.path.basename(f)}: FAILED {type(e).__name__}: {e}", flush=True)
            continue
        df = m.reindex(idx)
        X = np.stack([df[v].to_numpy(np.float32) if v in df else np.full(len(idx), np.nan, np.float32)
                      for v in KEEP], -1)
        for k, v in enumerate(KEEP):
            x = X[:, k]
            x[(x > FD.CEIL.get(v, 1e9)) | ((x < 0) & (v != "AT"))] = np.nan
            if v in MET:
                x[FD.stuck(x, 12)] = np.nan
            elif v in FD.POLLUTANTS:
                x[FD.stuck(x, 24)] = np.nan
        cov = np.isfinite(X[:, 0]).mean()
        info.update(city=c, station=name, at_coverage=round(float(cov), 3))
        meta.append(info)
        print(f"  {c:9s} {name[:45]:45s} shift {info['shift_h']:3.1f} h, AT {100 * cov:5.1f}% "
              f"RH {100 * np.isfinite(X[:, 1]).mean():5.1f}% WS {100 * np.isfinite(X[:, 2]).mean():5.1f}% "
              f"PM2.5 {100 * np.isfinite(X[:, 6]).mean():5.1f}%", flush=True)
        if cov < 0.10:
            continue
        cols.append(X); names.append(name); cities.append(c); lat.append(la); lon.append(lo); ids.append(sid)
    X = np.stack(cols, 1).astype(np.float16)                                     # [T, N, C]
    p = os.path.join(RAW, "WX_CPCBIN.npz")
    np.savez_compressed(p, X=X, vars=np.array(KEEP), stations=np.array(names), cities=np.array(cities),
                        ids=np.array(ids), lat=np.array(lat, np.float32), lon=np.array(lon, np.float32),
                        start=np.array("2024-01-01T00"), cutoff=np.array("2025-05-03T00"), utc_offset_h=np.array(5.5))
    json.dump(meta, open(os.path.join(RAW, "WX_CPCBIN_files.json"), "w"), indent=1)
    obs = int(np.isfinite(X[..., 0].astype(np.float32)).sum())
    print(f"WX_CPCBIN: {len(idx)} hours (IST {START} .. {CUTOFF}) x {len(names)} stations in "
          f"{len(set(cities))} cities; {obs:,} observed temperature station-hours; missing % "
          f"{np.round(100 * np.isnan(X[..., :3].astype(np.float32)).mean((0, 1)), 1).tolist()} (AT, RH, WS); "
          f"{os.path.getsize(p) / 1e6:.0f} MB", flush=True)


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    main()
