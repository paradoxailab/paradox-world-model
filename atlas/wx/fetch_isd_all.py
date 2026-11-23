"""Atlas-WX (atlas/PREREG_WX.md section 1): every qualifying NOAA ISD-Lite station, hourly, 1995-2025, with the
pre-registered station rule and quality control, packed for training.

Source (public, no account; NOAA Open Data on AWS, the same path Phase 5b used):
  https://noaa-isd-pds.s3.amazonaws.com/isd-history.csv                      station list
  https://noaa-isd-pds.s3.amazonaws.com/isd-lite/data/<Y>/<USAF>-<WBAN>-<Y>.gz  hourly data
ISD-Lite columns: year month day hour temp*10 dew*10 slp*10 wdir wspd*10 sky precip1h*10 precip6h*10; missing -9999,
trace precipitation -1 (stored as 0).

Steps (each resumable; raw files are cached in --raw, a local disk, and never re-downloaded):
  1. candidates from isd-history.csv: BEGIN <= 2019-12-31, END >= 2025-12-01, valid coordinates
  2. download 2024 and 2025, keep stations meeting the 2024/2025 rule
  3. download 1995-2023 for those, keep stations with >= 5 qualifying years in 1995-2023
  4. drop duplicate positions (same lat/lon to 0.01 deg: keep the one with more temperature observations)
  5. quality control (physical bounds, 8 robust SDs per station x calendar month), pack, write the frozen station list
     and its SHA-256
Output in --out: wx_<YYYY>.npz (values [stations, hours, 6] float16: T, Td, WD, WS, SLP, P6; NaN = missing),
stations.json, stations.sha256, summary.json. The data are NOAA's; they are used for research and not redistributed.

  python -u fetch_isd_all.py --raw /content/isd_raw --out /content/drive/MyDrive/PWM-WX/isd
  python -u fetch_isd_all.py ... --limit 200          # a quick trial on the first 200 candidates
"""
import argparse, csv, datetime as dt, gzip, hashlib, io, json, os, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np

BASE = "https://noaa-isd-pds.s3.amazonaws.com"
Y0, Y1 = 1995, 2025                              # inclusive
VARS = ["T", "Td", "WD", "WS", "SLP", "P6"]
BOUNDS = {"T": (-90, 60), "Td": (-100, 60), "WD": (0, 360), "WS": (0, 75), "SLP": (860, 1090), "P6": (0, 500)}
# Station rule (PREREG_WX section 1 as amended by its addendum of 23 Nov 2026): a "qualifying year" has at least
# MIN_OBS temperature observations, i.e. at least 3-hourly reporting on average.
MIN_OBS = 2190


def get(url, path, tries=4):
    if os.path.exists(path):
        return path
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ParadoxAI-Lab research"}),
                                        timeout=60) as r:
                b = r.read()
            tmp = path + ".part"
            open(tmp, "wb").write(b); os.replace(tmp, path)
            return path
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                open(path + ".missing", "w").close()
                return None
            time.sleep(2 + 3 * k)
        except Exception:
            time.sleep(2 + 3 * k)
    return None


def raw_path(raw, u, w, y):
    return os.path.join(raw, str(y), f"{u}-{w}-{y}.gz")


def fetch(raw, u, w, y):
    p = raw_path(raw, u, w, y)
    if os.path.exists(p + ".missing"):
        return None
    os.makedirs(os.path.dirname(p), exist_ok=True)
    f = get(f"{BASE}/isd-lite/data/{y}/{u}-{w}-{y}.gz", p)
    if f and open(f, "rb").read(2) != b"\x1f\x8b":            # not gzip (an error page): treat as missing
        os.remove(f); open(p + ".missing", "w").close(); return None
    return f


def parse_lite(data):
    """bytes of an ISD-Lite file (gz or plain) -> (hours since Y0-01-01T00 [int64], values [n, 6] float32)."""
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    text = data.decode("ascii", "ignore")
    flat = np.array(text.split(), dtype=np.int64) if text.strip() else np.zeros(0, np.int64)
    if flat.size % 12 == 0:                                    # the fixed ISD-Lite layout: 12 fields on every line
        a = flat.reshape(-1, 12)
    else:                                                      # a damaged line somewhere: parse line by line
        rows = [l.split() for l in text.splitlines()]
        a = np.array([[int(x) for x in r[:12]] for r in rows if len(r) >= 12], np.int64).reshape(-1, 12)
    if len(a) == 0:
        return np.zeros(0, np.int64), np.zeros((0, 6), np.float32)
    ym = (a[:, 0] - 1970) * 12 + (a[:, 1] - 1)
    day = ym.astype("datetime64[M]").astype("datetime64[D]") + (a[:, 2] - 1).astype("timedelta64[D]")
    h = ((day - np.datetime64(f"{Y0}-01-01")) / np.timedelta64(1, "D")).astype(np.int64) * 24 + a[:, 3]
    v = np.full((len(a), 6), np.nan, np.float32)
    for j, (col, scale) in enumerate([(4, 10), (5, 10), (7, 1), (8, 10), (6, 10), (11, 10)]):
        x = a[:, col].astype(np.float32)
        miss = a[:, col] == -9999
        if j == 5:
            x[a[:, col] == -1] = 0.0                            # trace precipitation
        x = x / scale
        x[miss] = np.nan
        v[:, j] = x
    return h, v


def n_temp(f):
    if not f:
        return 0
    _, v = parse_lite(open(f, "rb").read())
    return int(np.isfinite(v[:, 0]).sum())


def qc(series, hours):
    """series [T, 6] float32 for one station, hours [T] (since Y0) -> QC'd copy and the number of values dropped."""
    s = series.copy(); dropped = 0
    for j, k in enumerate(VARS):
        lo, hi = BOUNDS[k]
        bad = np.isfinite(s[:, j]) & ((s[:, j] < lo) | (s[:, j] > hi))
        dropped += int(bad.sum()); s[bad, j] = np.nan
    bad = np.isfinite(s[:, 1]) & np.isfinite(s[:, 0]) & (s[:, 1] > s[:, 0] + 0.5)   # dewpoint above temperature
    dropped += int(bad.sum()); s[bad, 1] = np.nan
    month = (np.datetime64(f"{Y0}-01-01T00") + hours.astype("timedelta64[h]")).astype("datetime64[M]").astype(int) % 12
    for j, k in enumerate(VARS):
        if k in ("WD", "P6"):                                  # circular / zero-inflated: bounds only
            continue
        for m in range(12):
            sel = (month == m) & np.isfinite(s[:, j])
            if sel.sum() < 50:
                continue
            x = s[sel, j]; med = np.median(x); mad = 1.4826 * np.median(np.abs(x - med))
            if mad <= 0:
                continue
            bad = np.abs(x - med) > 8 * mad
            if bad.any():
                idx = np.nonzero(sel)[0][bad]; s[idx, j] = np.nan; dropped += int(bad.sum())
    return s, dropped


def main(a):
    os.makedirs(a.raw, exist_ok=True); os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    hist = get(f"{BASE}/isd-history.csv", os.path.join(a.raw, "isd-history.csv"))
    cand = []
    for r in csv.DictReader(open(hist, newline="", encoding="latin-1")):
        try:
            lat, lon = float(r["LAT"]), float(r["LON"]); b, e = int(r["BEGIN"]), int(r["END"])
        except (ValueError, KeyError, TypeError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0):
            continue
        if b <= 20191231 and e >= 20251201 and r["USAF"] != "999999":
            elev = r.get("ELEV(M)") or "nan"
            cand.append(dict(id=f'{r["USAF"]}-{r["WBAN"]}', usaf=r["USAF"], wban=r["WBAN"], name=r["STATION NAME"].strip(),
                             ctry=r["CTRY"].strip(), lat=lat, lon=lon, elev=float(elev) if elev not in ("", "-999", "-999.0", "-999.9") else float("nan")))
    if a.limit:
        cand = cand[:a.limit]
    print(f"step 1: {len(cand)} candidate stations", flush=True)

    def years_obs(stations, years):
        jobs = [(s["usaf"], s["wban"], y) for s in stations for y in years]
        with ThreadPoolExecutor(a.workers) as ex:
            files = list(ex.map(lambda j: fetch(a.raw, *j), jobs))
        with ThreadPoolExecutor(a.workers) as ex:
            counts = list(ex.map(n_temp, files))
        c = np.array(counts).reshape(len(stations), len(years))
        return c

    c = years_obs(cand, [2024, 2025])
    keep = [s for s, row in zip(cand, c) if (row >= MIN_OBS).all()]
    print(f"step 2: {len(keep)} stations meet the 2024/2025 rule ({(time.time() - t0) / 60:.1f} min)", flush=True)
    yrs = list(range(Y0, 2024))
    c = years_obs(keep, yrs)
    nq = (c >= MIN_OBS).sum(1)
    keep = [dict(s, years_qualifying=int(q), n_temp=int(row.sum())) for s, q, row in zip(keep, nq, c) if q >= 5]
    print(f"step 3: {len(keep)} stations have >= 5 qualifying years in {Y0}-2023 ({(time.time() - t0) / 60:.1f} min)",
          flush=True)
    keep.sort(key=lambda s: -s["n_temp"]); seen, uniq = set(), []
    for s in keep:
        key = (round(s["lat"], 2), round(s["lon"], 2))
        if key not in seen:
            seen.add(key); uniq.append(s)
    st = sorted(uniq, key=lambda s: s["id"])
    print(f"step 4: {len(st)} stations after removing duplicate positions", flush=True)

    T = int((np.datetime64(f"{Y1 + 1}-01-01T00") - np.datetime64(f"{Y0}-01-01T00")) / np.timedelta64(1, "h"))
    hours = np.arange(T, dtype=np.int64)
    mm_path = os.path.join(a.raw, "wx_all.f16")
    V = np.lib.format.open_memmap(mm_path, mode="w+", dtype=np.float16, shape=(len(st), T, 6))
    dropped = 0
    for i, s in enumerate(st):
        x = np.full((T, 6), np.nan, np.float32)
        for y in range(Y0, Y1 + 1):
            f = raw_path(a.raw, s["usaf"], s["wban"], y)
            if not os.path.exists(f) and not os.path.exists(f + ".missing"):
                f = fetch(a.raw, s["usaf"], s["wban"], y)
            if f and os.path.exists(f):
                h, v = parse_lite(open(f, "rb").read())
                ok = (h >= 0) & (h < T)
                x[h[ok]] = v[ok]
        x, d = qc(x, hours); dropped += d
        V[i] = x.astype(np.float16)
        if i % 500 == 0:
            print(f"step 5: packed {i}/{len(st)} ({(time.time() - t0) / 60:.1f} min)", flush=True)
    V.flush()
    t = 0
    for y in range(Y0, Y1 + 1):
        n = int((np.datetime64(f"{y + 1}-01-01T00") - np.datetime64(f"{y}-01-01T00")) / np.timedelta64(1, "h"))
        fo = os.path.join(a.out, f"wx_{y}.npz")
        np.savez_compressed(fo, values=np.asarray(V[:, t:t + n]), start=f"{y}-01-01T00", vars=np.array(VARS))
        t += n
    ids = "\n".join(s["id"] for s in st).encode()
    sha = hashlib.sha256(ids).hexdigest()
    json.dump(st, open(os.path.join(a.out, "stations.json"), "w"))
    open(os.path.join(a.out, "stations.sha256"), "w").write(sha + "\n")
    cov = {k: round(float(np.isfinite(np.asarray(V[:, -8760:, j], np.float32)).mean() * 100), 1) for j, k in enumerate(VARS)}
    summ = dict(stations=len(st), sha256=sha, hours=T, start=f"{Y0}-01-01T00", end_exclusive=f"{Y1 + 1}-01-01T00",
                station_days_temp_1995_2023=int(sum(s["n_temp"] for s in st) / 24), qc_dropped=dropped, coverage_2025_pct=cov,
                by_country=dict(sorted({c: sum(s["ctry"] == c for s in st) for c in {s["ctry"] for s in st}}.items(),
                                       key=lambda kv: -kv[1])[:25]),
                min_obs_per_year=MIN_OBS, minutes=round((time.time() - t0) / 60, 1))
    json.dump(summ, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
    print("WX-DATA " + json.dumps(summ), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="/content/isd_raw"); ap.add_argument("--out", default="/content/drive/MyDrive/PWM-WX/isd")
    ap.add_argument("--workers", type=int, default=48); ap.add_argument("--limit", type=int, default=0)
    main(ap.parse_args())
