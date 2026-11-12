"""ATF v2.0 data: four public forecasting benchmarks from outside weather and air quality, converted to the station
format used by curves.py (X [T, N, C], NaN = missing). Downloaded from GitHub; no account or key.

  electricity  321 customers' hourly electricity use, 2012-01-01 .. 2014-12-31 (LSTNet release of UCI
               ElectricityLoadDiagrams; laiguokun/multivariate-time-series-data)
  traffic      862 road sensors' hourly occupancy, 2015-01-01 .. 2016-12-31 (California PeMS; same release)
  solar        137 photovoltaic plants in Alabama, 10-minute output in 2006 averaged to hourly (NREL; same release)
  etth1/etth2  two electricity transformers, hourly oil temperature + 6 load readings, 2016-07-01 .. 2018-06-26
               (zhouhaoyi/ETDataset)
The LSTNet files carry no timestamps; the start dates are the ones documented with them (hour 0 of the first day).

  python fetch_bench.py          # -> $PW_RAW/BENCH_{ELEC,TRAFFIC,SOLAR,ETTH1,ETTH2}.npz
"""
import gzip, io, os, sys, urllib.request

import numpy as np

RAW = os.environ.get("PW_RAW", "data/raw")
LST = "https://raw.githubusercontent.com/laiguokun/multivariate-time-series-data/master/"
ETT = "https://raw.githubusercontent.com/zhouhaoyi/ETDataset/main/ETT-small/"


def get(url):
    for i in range(4):
        try:
            return urllib.request.urlopen(url, timeout=300).read()
        except Exception as e:
            print(f"  retry {i + 1} {url}: {e}", flush=True)
    raise SystemExit(f"could not download {url}")


def save(name, X, vars_, stations, start):
    p = os.path.join(RAW, f"BENCH_{name}.npz")
    np.savez_compressed(p, X=X.astype(np.float32), vars=np.array(vars_), stations=np.array(stations), start=np.array(start))
    print(f"BENCH_{name}: {X.shape[0]} hours from {start} x {X.shape[1]} series x {X.shape[2]} variables {vars_}; "
          f"missing {100 * np.isnan(X).mean():.2f}%; {os.path.getsize(p) / 1e6:.0f} MB", flush=True)


def main():
    os.makedirs(RAW, exist_ok=True)
    for name, path, var, start, agg in (("ELEC", "electricity/electricity.txt.gz", "load", "2012-01-01T00", 1),
                                        ("TRAFFIC", "traffic/traffic.txt.gz", "occupancy", "2015-01-01T00", 1),
                                        ("SOLAR", "solar-energy/solar_AL.txt.gz", "power", "2006-01-01T00", 6)):
        x = np.loadtxt(io.BytesIO(gzip.decompress(get(LST + path))), delimiter=",", dtype=np.float32)
        if agg > 1:                                                     # 10-minute -> hourly mean
            x = x[: len(x) // agg * agg].reshape(-1, agg, x.shape[1]).mean(1)
        save(name, x[:, :, None], [var], [f"{name.lower()}-{i}" for i in range(x.shape[1])], start)
    import pandas as pd
    for name in ("ETTh1", "ETTh2"):
        d = pd.read_csv(io.BytesIO(get(ETT + name + ".csv")), parse_dates=["date"])
        cols = ["OT", "HUFL", "HULL", "MUFL", "MULL", "LUFL", "LULL"]
        save(name.upper(), d[cols].to_numpy(np.float32)[:, None, :], cols, [name], str(d.date.iloc[0])[:13].replace(" ", "T"))


if __name__ == "__main__":
    main()
