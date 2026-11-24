"""Atlas-WX Stage 2 (atlas/PREREG_WX.md, addendum of 24 Nov 2026): operational forecasts *as issued*, read at every
frozen station, from the public run archives on AWS. These are both Stage 2 inputs and opponents.

Systems and sources (public; no account):
  ifs   ECMWF IFS HRES 0.25 deg   s3://ecmwf-forecasts/<YYYYMMDD>/<HH>z/ifs/0p25/oper/<YYYYMMDDHH>0000-<step>h-oper-fc.grib2
  aifs  ECMWF AIFS 0.25 deg       .../<HH>z/aifs-single/0p25/oper/... (2024 runs under .../aifs/0p25/oper/)
  gfs   NOAA GFS 0.25 deg         s3://noaa-gfs-bdp-pds/gfs.<YYYYMMDD>/<HH>/atmos/gfs.t<HH>z.pgrb2.0p25.f<FFF>
Each GRIB file has a byte index (.index JSON lines for ECMWF, .idx text for GFS), so only the needed fields are
downloaded with HTTP range requests: 2 m temperature, 2 m dewpoint, 10 m u and v wind, mean sea-level pressure, total
precipitation. Fields are interpolated bilinearly to the stations of stations.json (the frozen GHCNh list).

Output, one file per system and month: <out>/<system>/<system>_<YYYYMM>.npz with
  values [runs, steps, stations, 6] float16 (T C, Td C, WS m/s, WD deg, SLP hPa, P mm accumulated since the run start),
  runs (ISO times), steps (hours). Missing fields are NaN. Resumable: finished months are skipped.

  pip install eccodes
  python -u fetch_nwp_runs.py --stations /content/wx_out/stations.json --out /content/nwp --system ifs \\
         --start 2024-02-01 --end 2026-01-01
"""
import argparse, datetime as dt, json, os, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np

VARS = ["T", "Td", "WS", "WD", "SLP", "P"]
STEPS = list(range(0, 145, 3)) + list(range(150, 169, 6))          # leads to 168 h (ECMWF open data: 3-hourly to 144)
ECMWF = {"2t": "t2", "2d": "d2", "10u": "u10", "10v": "v10", "msl": "msl", "tp": "tp"}
GFS = {"TMP:2 m above ground": "t2", "DPT:2 m above ground": "d2", "UGRD:10 m above ground": "u10",
       "VGRD:10 m above ground": "v10", "PRMSL:mean sea level": "msl", "APCP:surface": "tp"}


def http(url, rng=None, tries=6):
    for k in range(tries):
        try:
            h = {"User-Agent": "ParadoxAI-Lab research"}
            if rng:
                h["Range"] = f"bytes={rng[0]}-{rng[1]}"
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(2 * (k + 1) + (5 if e.code in (429, 503) else 0))     # S3 "SlowDown": back off
        except Exception:
            time.sleep(2 * (k + 1))
    return None


def urls(system, run, step):
    d, hh = run.strftime("%Y%m%d"), run.strftime("%H")
    if system == "gfs":
        u = f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{d}/{hh}/atmos/gfs.t{hh}z.pgrb2.0p25.f{step:03d}"
        return [(u, u + ".idx")]
    base = f"https://ecmwf-forecasts.s3.amazonaws.com/{d}/{hh}z"
    f = f"{d}{hh}0000-{step}h-oper-fc"
    dirs = ["ifs/0p25/oper"] if system == "ifs" else ["aifs-single/0p25/oper", "aifs/0p25/oper"]
    return [(f"{base}/{x}/{f}.grib2", f"{base}/{x}/{f}.index") for x in dirs]


def ranges(system, idx_bytes):
    """-> {short name: (start, end)} byte ranges of the wanted fields in the GRIB file."""
    out = {}
    if system == "gfs":
        lines = idx_bytes.decode().strip().splitlines()
        offs = [int(l.split(":")[1]) for l in lines]
        for i, l in enumerate(lines):
            p = l.split(":")
            key = f"{p[3]}:{p[4]}"
            if key in GFS and GFS[key] not in out:
                if key.startswith("APCP") and "acc fcst" not in p[5]:           # keep run-start accumulation only
                    continue
                if key.startswith("APCP") and not p[5].startswith("0-"):
                    continue
                out[GFS[key]] = (offs[i], offs[i + 1] - 1 if i + 1 < len(offs) else None)
        return out
    for l in idx_bytes.decode().strip().splitlines():
        j = json.loads(l)
        if j.get("param") in ECMWF and j.get("levtype", "sfc") == "sfc":
            out[ECMWF[j["param"]]] = (int(j["_offset"]), int(j["_offset"]) + int(j["_length"]) - 1)
    return out


class Interp:
    """Bilinear weights from a regular lat-lon grid (as decoded) to the stations, built from the first field."""
    def __init__(self, lat, lon):
        self.lat, self.lon = np.asarray(lat, np.float64), np.mod(np.asarray(lon, np.float64), 360)
        self.key = None

    def build(self, nx, ny, lat0, lon0, dlat, dlon):
        y = (self.lat - lat0) / dlat; x = np.mod(self.lon - lon0, 360) / dlon
        y0 = np.clip(np.floor(y).astype(int), 0, ny - 2); x0 = np.floor(x).astype(int) % nx
        self.i = (y0, x0, (x0 + 1) % nx); self.w = (y - y0, x - np.floor(x)); self.key = (nx, ny, lat0, lon0, dlat, dlon)

    def __call__(self, g):
        (y0, x0, x1), (wy, wx) = self.i, self.w
        a = g[y0, x0] * (1 - wx) + g[y0, x1] * wx
        b = g[y0 + 1, x0] * (1 - wx) + g[y0 + 1, x1] * wx
        return a * (1 - wy) + b * wy


def decode(buf, interp):
    import eccodes
    h = eccodes.codes_new_from_message(buf)
    try:
        nx, ny = eccodes.codes_get(h, "Ni"), eccodes.codes_get(h, "Nj")
        la0, lo0 = eccodes.codes_get(h, "latitudeOfFirstGridPointInDegrees"), eccodes.codes_get(h, "longitudeOfFirstGridPointInDegrees")
        la1 = eccodes.codes_get(h, "latitudeOfLastGridPointInDegrees")
        dlat = (la1 - la0) / (ny - 1); dlon = 360.0 / nx
        if interp.key != (nx, ny, la0, lo0, dlat, dlon):
            interp.build(nx, ny, la0, lo0, dlat, dlon)
        v = eccodes.codes_get_values(h).reshape(ny, nx)
        return interp(v)
    finally:
        eccodes.codes_release(h)


def one(system, run, step, interp):
    """-> [stations, 6] float32 for one run and lead, NaN where a field is missing."""
    out = np.full((len(interp.lat), 6), np.nan, np.float32)
    for gurl, iurl in urls(system, run, step):
        ib = http(iurl)
        if not ib:
            continue
        f = {}
        for name, (a, b) in ranges(system, ib).items():
            buf = http(gurl, (a, b if b is not None else ""))
            if buf:
                try:
                    f[name] = decode(buf, interp)
                except Exception:
                    pass
        if not f:
            continue
        if "t2" in f: out[:, 0] = f["t2"] - 273.15
        if "d2" in f: out[:, 1] = f["d2"] - 273.15
        if "u10" in f and "v10" in f:
            out[:, 2] = np.hypot(f["u10"], f["v10"])
            out[:, 3] = np.mod(np.degrees(np.arctan2(-f["u10"], -f["v10"])), 360)   # direction the wind blows from
        if "msl" in f: out[:, 4] = f["msl"] / 100.0
        if "tp" in f: out[:, 5] = f["tp"] * (1000.0 if system != "gfs" else 1.0)      # ECMWF m -> mm; GFS kg/m2 = mm
        return out
    return out


def main(a):
    st = json.load(open(a.stations))
    interp = Interp([s["lat"] for s in st], [s["lon"] for s in st])
    od = os.path.join(a.out, a.system); os.makedirs(od, exist_ok=True)
    s, e = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    steps = [x for x in STEPS if x <= a.max_lead]
    m = dt.date(s.year, s.month, 1)
    while m < e:
        nm = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
        fo = os.path.join(od, f"{a.system}_{m:%Y%m}.npz")
        if not os.path.exists(fo):
            t0 = time.time()
            runs = [dt.datetime(d.year, d.month, d.day, h) for d in (m + dt.timedelta(k) for k in range((nm - m).days))
                    if s <= d < e for h in (0, 12)]
            V = np.full((len(runs), len(steps), len(st), 6), np.nan, np.float16)
            jobs = [(i, j) for i in range(len(runs)) for j in range(len(steps))]
            with ThreadPoolExecutor(a.workers) as ex:
                for (i, j), x in zip(jobs, ex.map(lambda ij: one(a.system, runs[ij[0]], steps[ij[1]], interp), jobs)):
                    V[i, j] = x
            np.savez_compressed(fo, values=V, runs=np.array([r.isoformat() for r in runs]), steps=np.array(steps),
                                vars=np.array(VARS), system=a.system)
            have = np.isfinite(V[..., 0].astype(np.float32)).mean()
            print(f"{a.system} {m:%Y-%m}: {len(runs)} runs x {len(steps)} leads, T present {have:.3f}, "
                  f"{(time.time() - t0) / 60:.1f} min", flush=True)
        m = nm


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stations", required=True); ap.add_argument("--out", default="/content/nwp")
    ap.add_argument("--system", choices=["ifs", "aifs", "gfs"], required=True)
    ap.add_argument("--start", default="2024-02-01"); ap.add_argument("--end", default="2026-01-01")
    ap.add_argument("--max-lead", type=int, default=168); ap.add_argument("--workers", type=int, default=16)
    main(ap.parse_args())
