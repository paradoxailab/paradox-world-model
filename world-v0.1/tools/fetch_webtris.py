"""Build the present-day ParadoxBench task UK-M25 from National Highways' live WebTRIS API (MIDAS loop sensors on
England's motorways; free, no registration, Open Government Licence v3.0). Nothing is re-hosted: run this to
rebuild the task. 15-minute vehicle counts and mean speeds, real outages left in place.

  python tools/fetch_webtris.py --start 2025-07-01 --end 2026-06-30   # the latest 12 published months (2026-11-04)

Selection, fixed before looking at any data values:
  * sites whose Status is "Active", inside the London orbital box (lat 51.20-51.80, lon -0.65..0.35), which covers
    the M25 and the first junctions of every radial motorway;
  * sorted by site Id, then every k-th site so that at most --max_sites remain (spatial spread, no cherry-picking);
  * after download, a site is kept only if >= 60% of its 15-minute volumes are present in the TRAIN period.
Graph: Gaussian kernel of great-circle distance between sites (sigma = std of all pairwise distances under 10 km),
weights below 0.1 dropped, as for the other ParadoxBench graphs.

Writes data/raw/UK-M25.pb.npz with data [T, N] (Total Volume per 15 min, NaN = missing), speed [T, N] (mph),
tod [T] (15-minute slot, 0-95), dow [T] (0 = Monday), adj [N, N], site_ids [N], lat [N], lon [N], start (ISO date),
desc [N] (WebTRIS site description, e.g. "M25/4321B": road / location code + carriageway letter).
"""
import argparse, concurrent.futures as cf, datetime as dt, json, os, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
API = "https://webtris.nationalhighways.co.uk/api/v1.0"
BOX = (51.20, 51.80, -0.65, 0.35)


def get(url, params=None, tries=5):
    import requests
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=180)
            if r.status_code == 204:
                return None
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if k == tries - 1:
                raise
            time.sleep(3 * (k + 1))


def key(row, *names):
    for n in names:
        for k in row:
            if k.strip().lower() == n:
                return row[k]
    return None


def fetch_site(sid, start, end, cache):
    f = os.path.join(cache, f"{sid}.json")
    if os.path.exists(f):
        return sid, json.load(open(f))
    rows, page = [], 1
    while True:
        j = get(f"{API}/reports/daily", dict(sites=str(sid), start_date=start.strftime("%d%m%Y"),
                                             end_date=end.strftime("%d%m%Y"), page=page, page_size=20000))
        if not j or not j.get("Rows"):
            break
        rows += j["Rows"]
        links = (j.get("Header") or {}).get("links") or []
        if not any(str(l.get("rel", "")).lower() == "nextpage" for l in links):
            break
        page += 1
    out = []
    for r in rows:
        d, t = key(r, "report date"), key(r, "time interval")
        v, s = key(r, "total volume"), key(r, "avg mph")
        if d is None or t is None:
            continue
        out.append([str(d)[:10], int(t), None if v in (None, "") else float(v), None if s in (None, "") else float(s)])
    json.dump(out, open(f, "w"))
    return sid, out


def haversine(lat, lon):
    la, lo = np.deg2rad(lat), np.deg2rad(lon)
    d = (np.sin((la[:, None] - la[None]) / 2) ** 2 +
         np.cos(la[:, None]) * np.cos(la[None]) * np.sin((lo[:, None] - lo[None]) / 2) ** 2)
    return 2 * 6371.0 * np.arcsin(np.sqrt(d))


def main(a):
    start, end = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    sites = get(f"{API}/sites")["sites"]
    act = [s for s in sites if str(s.get("Status", "")).lower() == "active" and s.get("Latitude") and s.get("Longitude")
           and BOX[0] <= float(s["Latitude"]) <= BOX[1] and BOX[2] <= float(s["Longitude"]) <= BOX[3]]
    act.sort(key=lambda s: int(s["Id"]))
    step = max(1, -(-len(act) // a.max_sites))
    pick = act[::step][:a.max_sites]
    print(f"WebTRIS: {len(sites)} sites, {len(act)} active in the box, {len(pick)} selected (every {step})", flush=True)
    cache = os.path.join(RAW, "webtris_cache"); os.makedirs(cache, exist_ok=True)
    days = (end - start).days + 1
    T = days * 96
    vol = np.full((T, len(pick)), np.nan, np.float32); spd = np.full((T, len(pick)), np.nan, np.float32)
    col = {int(s["Id"]): i for i, s in enumerate(pick)}
    done = 0
    with cf.ThreadPoolExecutor(a.threads) as ex:
        for sid, rows in ex.map(lambda s: fetch_site(int(s["Id"]), start, end, cache), pick):
            i = col[sid]
            for d, t, v, s in rows:
                k = (dt.date.fromisoformat(d) - start).days * 96 + t
                if 0 <= k < T and 0 <= t < 96:
                    if v is not None and v >= 0:
                        vol[k, i] = v
                    if s is not None and s > 0:
                        spd[k, i] = s
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{len(pick)} sites downloaded", flush=True)
    n_tr = int(round(T * 0.7))
    cov = (~np.isnan(vol[:n_tr])).mean(0)
    keep = np.where(cov >= 0.6)[0]
    print(f"coverage in train period: median {np.median(cov):.2f}; kept {len(keep)} of {len(pick)} sites (>= 60%)", flush=True)
    vol, spd = vol[:, keep], spd[:, keep]
    lat = np.array([float(pick[i]["Latitude"]) for i in keep]); lon = np.array([float(pick[i]["Longitude"]) for i in keep])
    km = haversine(lat, lon)
    near = (km < 10) & (km > 0)
    sigma = km[near].std() if near.any() else 1.0
    A = np.where(near, np.exp(-(km / sigma) ** 2), 0.0)
    A[A < 0.1] = 0.0
    t = np.arange(T)
    dow = (start.weekday() + t // 96) % 7
    np.savez_compressed(os.path.join(RAW, "UK-M25.pb.npz"), data=vol, speed=spd, tod=t % 96, dow=dow,
                        adj=A.astype(np.float32), site_ids=np.array([int(pick[i]["Id"]) for i in keep]),
                        lat=lat, lon=lon, start=np.array(a.start),
                        desc=np.array([str(pick[i].get("Description") or pick[i].get("Name") or "") for i in keep]))
    miss = np.isnan(vol).mean()
    print(f"UK-M25: {T} steps x {len(keep)} sensors ({a.start} .. {a.end}), {int((A > 0).sum())} directed links, "
          f"missing {100 * miss:.1f}% -> {RAW}/UK-M25.pb.npz", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-07-01")
    ap.add_argument("--end", default="2026-06-30")
    ap.add_argument("--max_sites", type=int, default=300)
    ap.add_argument("--threads", type=int, default=6)
    main(ap.parse_args())
