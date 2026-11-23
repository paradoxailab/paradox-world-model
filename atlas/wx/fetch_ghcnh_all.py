"""Atlas-WX (atlas/PREREG_WX.md section 1 and its addenda): every qualifying NOAA GHCNh station, hourly, 1995-2025,
with the pre-registered station rule and quality control, packed for training.

Why GHCNh and not ISD-Lite: NOAA stopped updating ISD in late August 2025 (isd-history.csv ends 2025-08-28; no 2026
files), so ISD-Lite cannot cover the 2025 test year. GHCNh is ISD's successor, updated daily, and covers 1995-2026 from
one source (PREREG_WX addendum of 24 Nov 2026).

Source (public, CC0, no account; NOAA Open Data on AWS):
  https://noaa-ghcnh-pds.s3.amazonaws.com/hourly/access/by-year/<Y>/parquet/GHCNh_<ID>_<Y>.parquet
  station list: https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh-station-list.txt
Each file holds every observation of one station in one year (several per hour at some stations). Per hour we keep the
observation nearest the top of the hour (within 30 minutes). A value is kept only if its quality code is empty or one
of 0, 1, 4, 5 (passed); the codes dropped are counted in summary.json.

Steps (each resumable; raw files are cached in --raw, a local disk):
  1. candidates: stations with a 2024 and a 2025 file (S3 listing)
  2. keep stations with >= 2,190 temperature observations (hours) in 2024 and in 2025
  3. keep stations with >= 5 qualifying years in 1995-2023
  4. drop duplicate positions (same lat/lon to 0.01 deg: keep the one with more temperature hours)
  5. quality control (physical bounds, dewpoint <= temperature + 0.5, 8 robust SDs per station x calendar month), pack,
     frozen station list + SHA-256
Output in --out: wx_<YYYY>.npz (values [stations, hours, 6] float16: T, Td, WD, WS, SLP, P_raw; NaN = missing; P_raw =
the precipitation value of the kept observation, whose accumulation period varies, for Stage 2 to derive 6 h totals),
stations.json, stations.sha256, summary.json.

  python -u fetch_ghcnh_all.py --raw /content/gh_raw --out /content/wx_out --limit 200     # trial
  python -u fetch_ghcnh_all.py --raw /content/gh_raw --out /content/wx_out                 # all
"""
import argparse, hashlib, json, os, re, time, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import numpy as np

BASE = "https://noaa-ghcnh-pds.s3.amazonaws.com"
LIST_URL = "https://www.ncei.noaa.gov/oa/global-historical-climatology-network/hourly/doc/ghcnh-station-list.txt"
Y0, Y1 = 1995, 2025
VARS = ["T", "Td", "WD", "WS", "SLP", "P_raw"]
COLS = ["temperature", "dew_point_temperature", "wind_direction", "wind_speed", "sea_level_pressure", "precipitation"]
BOUNDS = {"T": (-90, 60), "Td": (-100, 60), "WD": (0, 360), "WS": (0, 75), "SLP": (860, 1090), "P_raw": (0, 500)}
OK_CODES = {"", "0", "1", "4", "5"}
MIN_OBS = 2190


def http(url, tries=4, timeout=60):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ParadoxAI-Lab research"}),
                                        timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            time.sleep(2 + 3 * k)
        except Exception:
            time.sleep(2 + 3 * k)
    return None


def list_year(y, cache):
    """{station_id: size} of the year's parquet files (S3 ListObjectsV2, cached as JSON)."""
    f = os.path.join(cache, f"list_{y}.json")
    if os.path.exists(f):
        return json.load(open(f))
    out, tok = {}, None
    while True:
        u = f"{BASE}/?list-type=2&max-keys=1000&prefix=hourly/access/by-year/{y}/parquet/"
        if tok:
            u += "&continuation-token=" + urllib.request.quote(tok, safe="")
        x = http(u).decode()
        for key, size in re.findall(r"<Key>[^<]*/GHCNh_([^<]+)_\d{4}\.parquet</Key>.*?<Size>(\d+)</Size>", x):
            out[key] = int(size)
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", x)
        if not m:
            break
        tok = m.group(1)
    json.dump(out, open(f, "w"))
    return out


def raw_path(raw, sid, y):
    return os.path.join(raw, str(y), f"{sid}.parquet")


def fetch(raw, sid, y):
    p = raw_path(raw, sid, y)
    if os.path.exists(p):
        return p
    os.makedirs(os.path.dirname(p), exist_ok=True)
    b = http(f"{BASE}/hourly/access/by-year/{y}/parquet/GHCNh_{sid}_{y}.parquet")
    if b is None:
        return None
    open(p + ".part", "wb").write(b); os.replace(p + ".part", p)
    return p


def hourly(path, y):
    """-> (hour index within the year [n], values [n, 6] float32, Counter of dropped quality codes)."""
    import pandas as pd
    want = ["DATE"] + COLS + [c + "_Quality_Code" for c in COLS]
    try:
        import pyarrow.parquet as pq
        have = set(pq.read_schema(path).names)
        d = pd.read_parquet(path, columns=[c for c in want if c in have])
    except Exception:
        return np.zeros(0, np.int64), np.zeros((0, 6), np.float32), Counter()
    if d.empty or "DATE" not in d:
        return np.zeros(0, np.int64), np.zeros((0, 6), np.float32), Counter()
    t = pd.to_datetime(d["DATE"], errors="coerce")
    ok = t.notna().values
    d, t = d[ok], t[ok]
    t0 = np.datetime64(f"{y}-01-01T00:00")
    mins = ((t.values.astype("datetime64[m]") - t0) / np.timedelta64(1, "m")).astype(np.int64)
    h = np.floor((mins + 30) / 60).astype(np.int64)                 # nearest hour
    off = np.abs(mins - h * 60)
    n = int((np.datetime64(f"{y + 1}-01-01T00") - np.datetime64(f"{y}-01-01T00")) / np.timedelta64(1, "h"))
    keep = (h >= 0) & (h < n)
    dropped = Counter()
    V = np.full((len(d), 6), np.nan, np.float32)
    for j, c in enumerate(COLS):
        if c not in d:
            continue
        x = pd.to_numeric(d[c], errors="coerce").values.astype(np.float32)
        qc = d.get(c + "_Quality_Code")
        if qc is not None:
            q = qc.fillna("").astype(str).str.strip().values
            bad = ~np.isin(q, list(OK_CODES)) & np.isfinite(x)
            for code, k in Counter(q[bad]).items():
                dropped[f"{VARS[j]}:{code}"] += k
            x[bad] = np.nan
        V[:, j] = x
    h, off, V = h[keep], off[keep], V[keep]
    # per hour the observation nearest the top of the hour, variable by variable (a missing value does not win)
    out_h = np.unique(h)
    out = np.full((len(out_h), 6), np.nan, np.float32)
    pos = np.searchsorted(out_h, h)
    for j in range(6):
        f = np.isfinite(V[:, j])
        if not f.any():
            continue
        o = np.lexsort((off[f], pos[f]))                             # by hour, then nearest first
        p, v = pos[f][o], V[f, j][o]
        first = np.r_[True, p[1:] != p[:-1]]
        out[p[first], j] = v[first]
    return out_h, out, dropped


def n_temp(args):
    path, y = args
    if not path:
        return 0
    h, v, _ = hourly(path, y)
    return int(np.isfinite(v[:, 0]).sum())


def qc(series, hours):
    """-> QC'd copy and a Counter of values dropped per (variable, check)."""
    s = series.copy(); dropped = Counter()
    for j, k in enumerate(VARS):
        lo, hi = BOUNDS[k]
        bad = np.isfinite(s[:, j]) & ((s[:, j] < lo) | (s[:, j] > hi))
        dropped[f"{k}:bounds"] += int(bad.sum()); s[bad, j] = np.nan
    bad = np.isfinite(s[:, 1]) & np.isfinite(s[:, 0]) & (s[:, 1] > s[:, 0] + 0.5)
    dropped["Td:above_T"] += int(bad.sum()); s[bad, 1] = np.nan
    month = (np.datetime64(f"{Y0}-01-01T00") + hours.astype("timedelta64[h]")).astype("datetime64[M]").astype(int) % 12
    for j, k in enumerate(VARS):
        if k in ("WD", "P_raw"):
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
                idx = np.nonzero(sel)[0][bad]; s[idx, j] = np.nan; dropped[f"{k}:8sd"] += int(bad.sum())
    return s, +dropped


def build_station(args):
    """All years of one station -> (float16 [T, 6], QC drops, dropped quality codes)."""
    raw, sid, T = args
    x = np.full((T, 6), np.nan, np.float32); codes = Counter(); t = 0
    for y in range(Y0, Y1 + 1):
        n = int((np.datetime64(f"{y + 1}-01-01T00") - np.datetime64(f"{y}-01-01T00")) / np.timedelta64(1, "h"))
        p = raw_path(raw, sid, y)
        if os.path.exists(p):
            h, v, c = hourly(p, y); codes.update(c)
            x[t + h] = v
        t += n
    x, d = qc(x, np.arange(T))
    return x.astype(np.float16), d, codes


def main(a):
    os.makedirs(a.raw, exist_ok=True); os.makedirs(a.out, exist_ok=True)
    t0 = time.time()
    lf = os.path.join(a.raw, "ghcnh-station-list.txt")
    if not os.path.exists(lf):
        open(lf, "wb").write(http(LIST_URL, timeout=120))
    meta = {}
    for line in open(lf, encoding="latin-1"):
        p = line.split()
        if len(p) < 4:
            continue
        try:
            lat, lon, elev = float(p[1]), float(p[2]), float(p[3])
        except ValueError:
            continue
        ctry = p[-1] if len(p[-1]) == 2 and p[-1].isalpha() and p[-1].isupper() else p[0][:2]
        meta[p[0]] = dict(id=p[0], lat=lat, lon=lon, elev=elev if elev > -999 else float("nan"),
                          name=" ".join(p[4:-1] if ctry == p[-1] else p[4:]).strip(), ctry=ctry)
    L = {y: list_year(y, a.raw) for y in range(Y0, Y1 + 1)}
    cand = sorted(s for s in L[2024] if s in L[2025] and s in meta
                  and -90 <= meta[s]["lat"] <= 90 and -180 <= meta[s]["lon"] <= 180
                  and not (meta[s]["lat"] == 0 and meta[s]["lon"] == 0))
    if a.limit:
        cand = cand[:a.limit]
    print(f"step 1: {len(meta)} listed stations; {len(L[2024])} files in 2024, {len(L[2025])} in 2025; "
          f"{len(cand)} candidates with both", flush=True)

    def counts(stations, years):
        jobs = [(s, y) for s in stations for y in years if s in L[y]]
        with ThreadPoolExecutor(a.workers) as ex:
            paths = list(ex.map(lambda j: fetch(a.raw, *j), jobs))
        with ProcessPoolExecutor(a.procs) as ex:
            n = list(ex.map(n_temp, [(p, y) for p, (s, y) in zip(paths, jobs)], chunksize=16))
        c = {s: {} for s in stations}
        for (s, y), k in zip(jobs, n):
            c[s][y] = k
        return c

    c = counts(cand, [2024, 2025])
    keep = [s for s in cand if c[s].get(2024, 0) >= MIN_OBS and c[s].get(2025, 0) >= MIN_OBS]
    print(f"step 2: {len(keep)} stations meet the 2024/2025 rule ({(time.time() - t0) / 60:.1f} min)", flush=True)
    c = counts(keep, list(range(Y0, 2024)))
    st = []
    for s in keep:
        q = sum(v >= MIN_OBS for v in c[s].values())
        if q >= 5:
            st.append(dict(meta[s], years_qualifying=int(q), n_temp=int(sum(c[s].values()))))
    print(f"step 3: {len(st)} stations have >= 5 qualifying years in {Y0}-2023 ({(time.time() - t0) / 60:.1f} min)", flush=True)
    st.sort(key=lambda s: -s["n_temp"]); seen, uniq = set(), []
    for s in st:
        key = (round(s["lat"], 2), round(s["lon"], 2))
        if key not in seen:
            seen.add(key); uniq.append(s)
    st = sorted(uniq, key=lambda s: s["id"])
    print(f"step 4: {len(st)} stations after removing duplicate positions", flush=True)

    T = int((np.datetime64(f"{Y1 + 1}-01-01T00") - np.datetime64(f"{Y0}-01-01T00")) / np.timedelta64(1, "h"))
    V = np.lib.format.open_memmap(os.path.join(a.raw, "wx_all.f16"), mode="w+", dtype=np.float16, shape=(len(st), T, 6))
    dropped, codes = Counter(), Counter()
    with ProcessPoolExecutor(a.procs) as ex:
        for i, (x, d, cd) in enumerate(ex.map(build_station, [(a.raw, s["id"], T) for s in st], chunksize=4)):
            V[i] = x; dropped.update(d); codes.update(cd)
            if i % 500 == 0:
                print(f"step 5: packed {i}/{len(st)} ({(time.time() - t0) / 60:.1f} min)", flush=True)
    V.flush()
    t = 0
    for y in range(Y0, Y1 + 1):
        n = int((np.datetime64(f"{y + 1}-01-01T00") - np.datetime64(f"{y}-01-01T00")) / np.timedelta64(1, "h"))
        np.savez_compressed(os.path.join(a.out, f"wx_{y}.npz"), values=np.asarray(V[:, t:t + n]), start=f"{y}-01-01T00",
                            vars=np.array(VARS))
        t += n
    sha = hashlib.sha256("\n".join(s["id"] for s in st).encode()).hexdigest()
    json.dump(st, open(os.path.join(a.out, "stations.json"), "w"))
    open(os.path.join(a.out, "stations.sha256"), "w").write(sha + "\n")
    last = np.asarray(V[:, -8760:], np.float32) if len(st) else np.zeros((0, 8760, 6), np.float32)
    summ = dict(source="GHCNh by-year parquet (noaa-ghcnh-pds)", stations=len(st), sha256=sha, hours=T,
                start=f"{Y0}-01-01T00", end_exclusive=f"{Y1 + 1}-01-01T00",
                station_hours_temp_1995_2023=int(sum(s["n_temp"] for s in st)),
                qc_dropped=dict(dropped.most_common()), quality_codes_dropped=dict(codes.most_common(30)),
                coverage_2025_pct={k: (round(float(np.isfinite(last[:, :, j]).mean() * 100), 1) if len(st) else None)
                                   for j, k in enumerate(VARS)},
                by_country=dict(Counter(s["ctry"] for s in st).most_common(25)),
                min_obs_per_year=MIN_OBS, minutes=round((time.time() - t0) / 60, 1))
    json.dump(summ, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
    print("WX-DATA " + json.dumps(summ), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="/content/gh_raw"); ap.add_argument("--out", default="/content/wx_out")
    ap.add_argument("--workers", type=int, default=64); ap.add_argument("--procs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--limit", type=int, default=0)
    main(ap.parse_args())
