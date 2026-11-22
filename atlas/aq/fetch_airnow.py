"""Atlas-AQ (atlas/PREREG_AQ.md) — USA station truth: AirNow hourly files, every US site, PM2.5 / NO2 / O3.

AirNow publishes one pipe-delimited file per hour with every site's readings:
  https://files.airnowtech.org/airnow/YYYY/YYYYMMDD/HourlyData_YYYYMMDDHH.dat
  columns: date | time | AQSID | site name | GMT offset | parameter | units | value | data source
and the site list (Monitoring_Site_Locations_V2.dat, same folder). Public, no account. Run where the internet is
reachable (Colab):
  python -u fetch_airnow.py --start 2021-01-01 --end 2026-07-01 --out /content/drive/MyDrive/PWM-AQ/airnow
Output: one compressed .npz per month: values [hours, sites, 3] (PM2.5 µg/m³, NO2 ppb, O3 ppb; NaN = missing),
the AQSID list and the hour axis; plus sites.json (AQSID -> lat, lon, name). Resumable: finished months are skipped.
"""
import argparse, concurrent.futures as cf, datetime as dt, io, json, os, time, urllib.request

import numpy as np

BASE = "https://files.airnowtech.org/airnow"
PARAMS = {"PM2.5": 0, "NO2": 1, "OZONE": 2}


def get(url, tries=4):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ParadoxAI-Lab research"}), timeout=60) as r:
                return r.read().decode("latin-1")
        except Exception as e:
            if getattr(e, "code", None) == 404:
                return None
            time.sleep(3 * (k + 1))
    return None


def parse_hourly(text):
    """-> list of (aqsid, param_index, value); skips malformed lines and the -999 missing code."""
    out = []
    for line in (text or "").splitlines():
        f = line.split("|")
        if len(f) < 8:
            continue
        p = PARAMS.get(f[5].strip().upper())
        if p is None:
            continue
        try:
            v = float(f[7])
        except ValueError:
            continue
        if v <= -999:                                    # AirNow's missing code
            continue
        out.append((f[2].strip(), p, v))
    return out


def parse_sites(text):
    sites = {}
    rows = [l.split("|") for l in (text or "").splitlines() if l.strip()]
    if not rows:
        return sites
    head = [h.strip().lower() for h in rows[0]]
    has_head = "aqsid" in head or "stationid" in head
    for r in rows[1:] if has_head else rows:
        if has_head:
            d = dict(zip(head, r))
            sid = (d.get("aqsid") or d.get("stationid") or "").strip()
            lat, lon, name = d.get("latitude"), d.get("longitude"), d.get("sitename") or d.get("site name")
        else:                                              # legacy layout: AQSID|param|...|name|...|lat|lon|...
            sid, name = r[0].strip(), r[3] if len(r) > 3 else ""
            lat, lon = (r[8], r[9]) if len(r) > 9 else (None, None)
        try:
            sites[sid] = dict(lat=float(lat), lon=float(lon), name=(name or "").strip())
        except (TypeError, ValueError):
            continue
    return sites


def month_hours(y, m):
    a = dt.datetime(y, m, 1)
    b = dt.datetime(y + (m == 12), m % 12 + 1, 1)
    return [a + dt.timedelta(hours=h) for h in range(int((b - a).total_seconds() // 3600))]


def main(a):
    os.makedirs(a.out, exist_ok=True)
    s = dt.date.fromisoformat(a.start); e = dt.date.fromisoformat(a.end)
    sites_f = os.path.join(a.out, "sites.json")
    sites = json.load(open(sites_f)) if os.path.exists(sites_f) else {}
    y, m = s.year, s.month
    while dt.date(y, m, 1) < e:
        fo = os.path.join(a.out, f"airnow_{y}{m:02d}.npz")
        if not os.path.exists(fo):
            hrs = month_hours(y, m)
            urls = [f"{BASE}/{t:%Y}/{t:%Y%m%d}/HourlyData_{t:%Y%m%d%H}.dat" for t in hrs]
            with cf.ThreadPoolExecutor(a.workers) as ex:
                texts = list(ex.map(get, urls))
            st = get(f"{BASE}/{y}/{y}{m:02d}15/Monitoring_Site_Locations_V2.dat")
            sites.update(parse_sites(st)); json.dump(sites, open(sites_f, "w"))
            recs = [parse_hourly(t) for t in texts]
            ids = sorted({r[0] for rr in recs for r in rr})
            ix = {k: i for i, k in enumerate(ids)}
            V = np.full((len(hrs), len(ids), 3), np.nan, np.float32)
            for h, rr in enumerate(recs):
                for sid, p, v in rr:
                    V[h, ix[sid], p] = v
            np.savez_compressed(fo, values=V, aqsid=np.array(ids), hours=np.array([t.isoformat() for t in hrs]),
                                missing_files=np.array(sum(t is None for t in texts)))
            print(f"{y}-{m:02d}: {len(ids)} sites, {sum(t is None for t in texts)} of {len(hrs)} hourly files missing, "
                  f"coverage {np.isfinite(V).mean():.3f}", flush=True)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-01-01"); ap.add_argument("--end", default="2026-07-01")
    ap.add_argument("--out", default="/content/drive/MyDrive/PWM-AQ/airnow"); ap.add_argument("--workers", type=int, default=16)
    main(ap.parse_args())
