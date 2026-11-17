"""Fresh observations for the WEATHER-5K stations after the benchmark ends: 1 January 2024 to the latest hour NOAA has
published, from NOAA NCEI's ISD-Lite (hourly, the observation nearest the top of each hour; public).
https://noaa-isd-pds.s3.amazonaws.com/isd-lite/data/<year>/<USAF>-<WBAN>-<year>.gz (NOAA Open Data on AWS)

Writes, in the layout run_atlas_5k.load() reads (values minus the benchmark's offset, float16, stations in WEATHER-5K's
order), to --out:
  W5K_OBS.npy   what was observed (NaN where nothing was reported): the truth that forecasts are scored against
  W5K_X.npy     model input: the same series with gaps filled by carrying the last observation forward (causal: no value
                after an hour is ever used to fill it), so every model sees the same past and nothing of the future
  W5K_META.npz  the WEATHER-5K metadata with start = 2024-01-01T00 and the live end
The data are NOAA's; they are used here to score forecasts and are not redistributed.

  python fetch_isd_live.py --meta /content/raw/W5K_META.npz --out /content/live --years 2024,2025,2026
"""
import argparse, gzip, io, json, os, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np

URL = "https://noaa-isd-pds.s3.amazonaws.com/isd-lite/data/{y}/{u}-{w}-{y}.gz"   # NOAA's open-data copy (NCEI's old path now serves a web page)
START = np.datetime64("2024-01-01T00")
OFFSET = np.array([0.0, 0.0, 0.0, 0.0, 1000.0], np.float32)


def ids(name):
    s = os.path.basename(str(name)).replace(".csv", "")
    if "-" in s:
        u, w = s.split("-")[:2]
    else:
        u, w = s[:6], s[6:11]
    return u, w


def get(args):
    u, w, y, tmp = args
    f = os.path.join(tmp, f"{u}-{w}-{y}.gz")
    if os.path.exists(f):
        return f
    for k in range(4):
        try:
            with urllib.request.urlopen(URL.format(y=y, u=u, w=w), timeout=60) as r:
                b = r.read()
            if b[:2] != b"\x1f\x8b":                           # not a gzip file: treat as missing, never parse a web page
                return None
            open(f, "wb").write(b)
            return f
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            time.sleep(2 + 3 * k)
        except Exception:
            time.sleep(2 + 3 * k)
    return None


def parse(f, T):
    """ISD-Lite columns: year month day hour temp*10 dew*10 slp*10 wdir wspd*10 sky p1 p6; missing -9999."""
    out = np.full((T, 5), np.nan, np.float32)
    if not f:
        return out
    a = np.loadtxt(io.BytesIO(gzip.open(f).read()), dtype=np.int64, ndmin=2)
    if a.size == 0:
        return out
    yr = (a[:, 0] - 1970).astype("datetime64[Y]")
    day = (yr.astype("datetime64[M]") + (a[:, 1] - 1).astype("timedelta64[M]")).astype("datetime64[D]") + (a[:, 2] - 1).astype("timedelta64[D]")
    dt = day.astype("datetime64[h]") + a[:, 3].astype("timedelta64[h]")
    h = ((dt - START) / np.timedelta64(1, "h")).astype(np.int64)
    ok = (h >= 0) & (h < T)
    v = a[ok][:, [4, 5, 8, 6]].astype(np.float32)          # temp, dew, wspd, slp (scaled by 10)
    d = a[ok][:, 7].astype(np.float32)                      # wind direction, degrees
    v[v == -9999] = np.nan; d[d == -9999] = np.nan
    vals = np.stack([v[:, 0] / 10, v[:, 1] / 10, d, v[:, 2] / 10, v[:, 3] / 10], 1)   # TMP, DEW, WND_ANGLE, WND_RATE, SLP
    out[h[ok]] = vals
    return out


def main(a):
    os.makedirs(a.out, exist_ok=True); tmp = os.path.join(a.out, "isd"); os.makedirs(tmp, exist_ok=True)
    M = dict(np.load(a.meta, allow_pickle=True))
    names = M["names"]; N = len(names)
    years = [int(y) for y in a.years.split(",")]
    now = np.datetime64(time.strftime("%Y-%m-%dT%H", time.gmtime()))
    T = int((now - START) / np.timedelta64(1, "h")) + 1
    jobs = [(*ids(n), y, tmp) for n in names for y in years]
    t0 = time.time()
    with ThreadPoolExecutor(a.workers) as ex:
        files = list(ex.map(get, jobs))
    got = sum(f is not None for f in files)
    print(f"downloaded {got}/{len(jobs)} station-years in {(time.time() - t0) / 60:.1f} min", flush=True)
    obs = np.full((N, T, 5), np.nan, np.float32)
    for i in range(N):
        for k, y in enumerate(years):
            arr = parse(files[i * len(years) + k], T)
            m = np.isfinite(arr)
            obs[i][m] = arr[m]
    # the live end: the last hour at which at least half of the stations that report at all have a temperature
    rep = np.isfinite(obs[:, :, 0])
    active = rep.any(1)
    share = rep[active].mean(0)
    end = int(np.max(np.nonzero(share >= 0.5)[0])) + 1
    obs = obs[:, :end]
    # causal fill for inputs: carry the last observation forward
    x = obs.copy()
    for i in range(N):
        for v in range(5):
            s = x[i, :, v]; ok = np.isfinite(s)
            if ok.any():
                idx = np.where(ok, np.arange(end), 0); np.maximum.accumulate(idx, out=idx)
                f = s[idx]; f[:np.argmax(ok)] = np.nan; x[i, :, v] = f
    np.save(os.path.join(a.out, "W5K_OBS.npy"), (obs - OFFSET).astype(np.float16))
    np.save(os.path.join(a.out, "W5K_X.npy"), (x - OFFSET).astype(np.float16))
    M.update(start=str(START), live_end=str(START + np.timedelta64(end, "h")), offset=OFFSET, source="NOAA NCEI ISD-Lite")
    np.savez(os.path.join(a.out, "W5K_META.npz"), **M)
    cov = {v: round(float(np.isfinite(obs[active][:, :, k]).mean() * 100), 1) for k, v in enumerate(["TMP", "DEW", "WND_ANGLE", "WND_RATE", "SLP"])}
    print("LIVE-DATA " + json.dumps(dict(stations=N, stations_reporting=int(active.sum()), start=str(START),
                                         end=str(START + np.timedelta64(end, "h")), hours=end, observed_pct_of_hours=cov,
                                         minutes=round((time.time() - t0) / 60, 1))), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", required=True); ap.add_argument("--out", default="/content/live")
    ap.add_argument("--years", default="2024,2025,2026"); ap.add_argument("--workers", type=int, default=32)
    main(ap.parse_args())
