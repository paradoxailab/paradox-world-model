"""World benchmark WB1 (README, "World benchmarks"): download WEATHER-5K (Han et al., ICML 2026 benchmark; 5,672 global
weather stations, hourly 2014-2023) from the authors' public OneDrive share and convert it, station by station,
straight out of the zip (nothing is extracted to disk) into compact arrays:

  W5K_X.npy   float16 [N, T, 5]  TMP, DEW, WND_ANGLE, WND_RATE, SLP in the benchmark's units minus OFFSET (SLP is stored
              as SLP - 1000 hPa so float16 keeps about 0.03 hPa; the other offsets are 0), T hours from 2014-01-01T00
  W5K_META.npz  names, lat, lon, elev, start, vars, percentiles [N, 5, 8] (the benchmark's SEDI thresholds)

The variables, order and hour grid are the benchmark's own (data_provider/station_dataset.py: columns DATE, TMP, DEW,
WND_ANGLE, WND_RATE, SLP; train 2014-2021, validation 2022, test 2023). Missing hours stay NaN and are counted.

  python fetch_weather5k.py --out /kaggle/working/out
"""
import argparse, io, json, os, sys, time, zipfile
from multiprocessing import Pool

import numpy as np

SHARE = ("https://hkustconnect-my.sharepoint.com/:u:/g/personal/thanad_connect_ust_hk/"
         "EZGm7DP0qstElZwafr_U2YoBk5Ryt9rv7P31OqnUBZUPAA?e=5r0wEo&download=1")
VARS = ["TMP", "DEW", "WND_ANGLE", "WND_RATE", "SLP"]
START = np.datetime64("2014-01-01T00")
END = np.datetime64("2024-01-01T00")
OFFSET = np.array([0.0, 0.0, 0.0, 0.0, 1000.0], np.float32)
T = int((END - START) / np.timedelta64(1, "h"))           # 87,648 hours


def log(*a):
    print(*a, flush=True)


def download(path):
    import requests
    if os.path.exists(path) and os.path.getsize(path) > 6_000_000_000:
        log(f"already downloaded: {path} ({os.path.getsize(path) / 1e9:.2f} GB)"); return
    t0 = time.time()
    with requests.get(SHARE, stream=True, allow_redirects=True, timeout=120) as r:
        r.raise_for_status()
        n = int(r.headers.get("content-length", 0))
        log(f"downloading {n / 1e9:.2f} GB ({r.headers.get('content-type')})")
        got = 0
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 24):
                f.write(chunk); got += len(chunk)
                if got % (1 << 30) < (1 << 24):
                    log(f"  {got / 1e9:.1f} GB, {got / 1e6 / (time.time() - t0):.0f} MB/s")
    log(f"downloaded {got / 1e9:.2f} GB in {(time.time() - t0) / 60:.1f} min")


def parse(args):
    zpath, member = args
    import pandas as pd
    with zipfile.ZipFile(zpath) as z:
        df = pd.read_csv(io.BytesIO(z.read(member)), usecols=["DATE"] + VARS)
    t = pd.to_datetime(df["DATE"]).values.astype("datetime64[h]")
    ix = ((t - START) / np.timedelta64(1, "h")).astype(np.int64)
    ok = (ix >= 0) & (ix < T)
    out = np.full((T, len(VARS)), np.nan, np.float32)
    out[ix[ok]] = df[VARS].values[ok].astype(np.float32) - OFFSET
    return os.path.basename(member), out.astype(np.float16), int(ok.sum())


def main(a):
    os.makedirs(a.out, exist_ok=True); os.makedirs(a.tmp, exist_ok=True)
    zpath = os.path.join(a.tmp, "WEATHER-5K.zip")
    download(zpath)
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        csvs = sorted(n for n in names if n.endswith(".csv") and "global_weather_stations" in n)
        jm = [n for n in names if n.endswith("meta_info.json")]
        jp = [n for n in names if n.endswith("percentile.json")]
        log(f"zip: {len(names)} members, {len(csvs)} station files; meta {jm}, percentiles {jp}")
        meta = json.loads(z.read(jm[0])) if jm else {}
        pct = json.loads(z.read(jp[0])) if jp else {}
    if a.quick:
        csvs = csvs[:20]
    X = np.lib.format.open_memmap(os.path.join(a.out, "W5K_X.npy"), mode="w+", dtype=np.float16, shape=(len(csvs), T, len(VARS)))
    t0 = time.time(); stn, rows = [], []
    with Pool(a.workers) as p:
        for i, (nm, arr, nrow) in enumerate(p.imap(parse, [(zpath, c) for c in csvs], chunksize=4)):
            X[i] = arr; stn.append(nm); rows.append(nrow)
            if (i + 1) % 500 == 0:
                log(f"  {i + 1}/{len(csvs)} stations, {(time.time() - t0) / 60:.1f} min")
    X.flush()
    key = lambda s: s if s in meta else s.replace(".csv", "")
    lat = np.array([float(meta.get(key(s), {}).get("latitude", np.nan)) for s in stn])
    lon = np.array([float(meta.get(key(s), {}).get("longitude", np.nan)) for s in stn])
    elev = np.array([float(meta.get(key(s), {}).get("ELEVATION", np.nan)) for s in stn])
    P = np.array([np.array(pct.get(s, pct.get(key(s), np.full((5, 8), np.nan))), float) for s in stn])
    np.savez(os.path.join(a.out, "W5K_META.npz"), names=np.array(stn), lat=lat, lon=lon, elev=elev, start=str(START),
             vars=np.array(VARS), offset=OFFSET, percentiles=P, rows=np.array(rows))
    miss = np.array([np.isnan(X[i]).mean(0) for i in range(len(stn))])
    yrs = {y: f"{100 * np.isnan(X[:, (np.datetime64(f'{y}-01-01T00') - START).astype(int):(np.datetime64(f'{y + 1}-01-01T00') - START).astype(int)]).mean():.2f}%"
           for y in (2014, 2021, 2022, 2023)} if a.quick else {}
    log("W5K-DATA " + json.dumps(dict(stations=len(stn), hours=T, vars=VARS, missing_by_var=dict(zip(VARS, (100 * miss.mean(0)).round(3).tolist())),
                                     stations_with_coords=int(np.isfinite(lat).sum()), percentiles_shape=list(P.shape),
                                     percentiles_found=int(np.isfinite(P).all(axis=(1, 2)).sum()), missing_by_year=yrs,
                                     minutes=round((time.time() - t0) / 60, 1),
                                     means=(np.nanmean(X[::50, ::24].astype(np.float32), axis=(0, 1)) + OFFSET).round(2).tolist())))
    if not a.keep:
        os.remove(zpath)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/kaggle/working/out")
    ap.add_argument("--tmp", default="/kaggle/tmp")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--keep", action="store_true")
    main(ap.parse_args())
