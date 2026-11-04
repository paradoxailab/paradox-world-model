"""Build road-sensor networks from National Highways' live WebTRIS API (MIDAS loop sensors on England's motorways
and major A-roads; free, no registration, Open Government Licence v3.0). Nothing is re-hosted.

Target cities (test tasks, never used in pretraining), 2025-07-01 .. 2026-06-30:
  python tools/fetch_webtris.py city --name UK-M25 --box 51.20 51.80 -0.65 0.35
  python tools/fetch_webtris.py city --name UK-MAN --box 53.30 53.65 -2.60 -1.95
Pretraining networks (rest of England, both target boxes excluded, ending before any test period):
  python tools/fetch_webtris.py england --start 2024-07-01 --end 2026-03-31 --max_sites 1000 --regions 6

Selection rules, fixed before looking at any data values:
  * sites whose Status is "Active" inside the box (city) or outside every excluded box (england);
  * sorted by site Id, then every k-th site so that at most --max_sites remain (no cherry-picking);
  * a site is kept only if >= 60% of its 15-minute volumes are present in the first 70% of the period;
  * england: kept sites are grouped into --regions regional networks by k-means on latitude / longitude.
Graph: Gaussian kernel of great-circle distance (sigma = std of pairwise distances under 10 km), weights < 0.1 dropped.
Writes data/raw/<NAME>.pb.npz: data [T, N] volume per 15 min (NaN = missing), speed [T, N] mph, tod, dow, adj,
site_ids, lat, lon, desc, start.
"""
import argparse, concurrent.futures as cf, datetime as dt, os, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
API = "https://webtris.nationalhighways.co.uk/api/v1.0"
BOXES = {"UK-M25": (51.20, 51.80, -0.65, 0.35), "UK-MAN": (53.30, 53.65, -2.60, -1.95)}
EXCLUDE_MARGIN = 0.15                    # degrees: pretraining sites must also stay clear of the target boxes' edges


def get(url, params=None, tries=6):
    import requests
    for k in range(tries):
        try:
            r = requests.get(url, params=params, timeout=180)
            if r.status_code == 204:
                return None
            r.raise_for_status()
            return r.json()
        except Exception:
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
    """[days*96] volume and speed for one site (NaN = missing), cached as a small .npz."""
    f = os.path.join(cache, f"{sid}_{start}_{end}.npz")
    T = ((end - start).days + 1) * 96
    if os.path.exists(f):
        z = np.load(f)
        return sid, z["v"], z["s"]
    vol, spd = np.full(T, np.nan, np.float32), np.full(T, np.nan, np.float32)
    page = 1
    while True:
        j = get(f"{API}/reports/daily", dict(sites=str(sid), start_date=start.strftime("%d%m%Y"),
                                             end_date=end.strftime("%d%m%Y"), page=page, page_size=20000))
        if not j or not j.get("Rows"):
            break
        for r in j["Rows"]:
            d, t = key(r, "report date"), key(r, "time interval")
            if d is None or t is None:
                continue
            k = (dt.date.fromisoformat(str(d)[:10]) - start).days * 96 + int(t)
            if not (0 <= k < T and 0 <= int(t) < 96):
                continue
            v, s = key(r, "total volume"), key(r, "avg mph")
            if v not in (None, "") and float(v) >= 0:
                vol[k] = float(v)
            if s not in (None, "") and float(s) > 0:
                spd[k] = float(s)
        links = (j.get("Header") or {}).get("links") or []
        if not any(str(l.get("rel", "")).lower() == "nextpage" for l in links):
            break
        page += 1
    np.savez_compressed(f, v=vol, s=spd)
    return sid, vol, spd


def haversine(lat, lon):
    la, lo = np.deg2rad(lat), np.deg2rad(lon)
    d = (np.sin((la[:, None] - la[None]) / 2) ** 2 +
         np.cos(la[:, None]) * np.cos(la[None]) * np.sin((lo[:, None] - lo[None]) / 2) ** 2)
    return 2 * 6371.0 * np.arcsin(np.sqrt(d))


def graph(lat, lon):
    km = haversine(lat, lon)
    near = (km < 10) & (km > 0)
    sigma = km[near].std() if near.any() else 1.0
    A = np.where(near, np.exp(-(km / sigma) ** 2), 0.0)
    A[A < 0.1] = 0.0
    return A.astype(np.float32)


def active_sites():
    sites = get(f"{API}/sites")["sites"]
    out = [s for s in sites if str(s.get("Status", "")).lower() == "active" and s.get("Latitude") and s.get("Longitude")]
    out.sort(key=lambda s: int(s["Id"]))
    return len(sites), out


def thin(sites, k):
    step = max(1, -(-len(sites) // k))
    return sites[::step][:k], step


def download(pick, start, end, threads, label):
    cache = os.path.join(RAW, "webtris_cache"); os.makedirs(cache, exist_ok=True)
    T = ((end - start).days + 1) * 96
    vol = np.full((T, len(pick)), np.nan, np.float32); spd = np.full((T, len(pick)), np.nan, np.float32)
    col = {int(s["Id"]): i for i, s in enumerate(pick)}
    done, t0 = 0, time.time()
    with cf.ThreadPoolExecutor(threads) as ex:
        for sid, v, s in ex.map(lambda s: fetch_site(int(s["Id"]), start, end, cache), pick):
            vol[:, col[sid]], spd[:, col[sid]] = v, s
            done += 1
            if done % 50 == 0:
                print(f"  {label}: {done}/{len(pick)} sites ({(time.time() - t0) / 60:.1f} min)", flush=True)
    return vol, spd


def save(name, vol, spd, sites, keep, start):
    vol, spd = vol[:, keep], spd[:, keep]
    lat = np.array([float(sites[i]["Latitude"]) for i in keep]); lon = np.array([float(sites[i]["Longitude"]) for i in keep])
    A = graph(lat, lon)
    T = len(vol)
    t = np.arange(T)
    np.savez_compressed(os.path.join(RAW, f"{name}.pb.npz"), data=vol, speed=spd, tod=t % 96,
                        dow=(start.weekday() + t // 96) % 7, adj=A,
                        site_ids=np.array([int(sites[i]["Id"]) for i in keep]), lat=lat, lon=lon,
                        desc=np.array([str(sites[i].get("Description") or sites[i].get("Name") or "") for i in keep]),
                        start=np.array(start.isoformat()))
    print(f"{name}: {T} steps x {len(keep)} sensors ({start} ..), {int((A > 0).sum())} directed links, "
          f"missing {100 * np.isnan(vol).mean():.1f}%", flush=True)


def coverage_keep(vol, frac=0.7, need=0.6):
    n = int(round(len(vol) * frac))
    cov = (~np.isnan(vol[:n])).mean(0)
    return np.where(cov >= need)[0], cov


def inside(s, b, m=0.0):
    la, lo = float(s["Latitude"]), float(s["Longitude"])
    return b[0] - m <= la <= b[1] + m and b[2] - m <= lo <= b[3] + m


def city(a):
    start, end = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    box = tuple(a.box) if a.box else BOXES[a.name]
    n_all, act = active_sites()
    act = [s for s in act if inside(s, box)]
    pick, step = thin(act, a.max_sites)
    print(f"{a.name}: {n_all} sites, {len(act)} active in the box, {len(pick)} selected (every {step})", flush=True)
    vol, spd = download(pick, start, end, a.threads, a.name)
    keep, cov = coverage_keep(vol)
    print(f"  coverage median {np.median(cov):.2f}; kept {len(keep)} of {len(pick)} (>= 60%)", flush=True)
    save(a.name, vol, spd, pick, keep, start)


def england(a):
    start, end = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    n_all, act = active_sites()
    act = [s for s in act if not any(inside(s, b, EXCLUDE_MARGIN) for b in BOXES.values())]
    pick, step = thin(act, a.max_sites)
    print(f"England pretraining: {n_all} sites, {len(act)} active outside the target cities, {len(pick)} selected "
          f"(every {step})", flush=True)
    vol, spd = download(pick, start, end, a.threads, "England")
    keep, cov = coverage_keep(vol)
    print(f"  coverage median {np.median(cov):.2f}; kept {len(keep)} of {len(pick)} (>= 60%)", flush=True)
    X = np.array([[float(pick[i]["Latitude"]), float(pick[i]["Longitude"]) * 0.62] for i in keep])
    rng = np.random.default_rng(0)
    C = X[rng.choice(len(X), a.regions, replace=False)]
    for _ in range(100):
        lab = ((X[:, None] - C[None]) ** 2).sum(-1).argmin(1)
        C = np.array([X[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(a.regions)])
    for j in range(a.regions):
        idx = keep[lab == j]
        if len(idx) >= 20:
            save(f"ENG-R{j}", vol, spd, pick, idx, start)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("city")
    c.add_argument("--name", required=True); c.add_argument("--box", type=float, nargs=4)
    c.add_argument("--start", default="2025-07-01"); c.add_argument("--end", default="2026-06-30")
    c.add_argument("--max_sites", type=int, default=300); c.add_argument("--threads", type=int, default=8)
    e = sub.add_parser("england")
    e.add_argument("--start", default="2024-07-01"); e.add_argument("--end", default="2026-03-31")
    e.add_argument("--max_sites", type=int, default=1000); e.add_argument("--regions", type=int, default=6)
    e.add_argument("--threads", type=int, default=8)
    a = ap.parse_args()
    city(a) if a.cmd == "city" else england(a)
