"""Run NVIDIA's open global AI weather models ourselves (NVIDIA Earth2Studio, Apache-2.0) and read their
forecasts at the league's stations: FourCastNet 3 / FourCastNet SFNO (NVIDIA), and GraphCast Operational
(Google DeepMind) if it fits in the GPU's memory.

Each run starts from the real NOAA GFS analysis at 00 UTC of a TEST day (the same starting state an
operational centre would use, fetched from NOAA's public AWS bucket) and steps 6 hours at a time to +18 h.
We keep 2 m temperature, 2 m humidity (when the model predicts it) and 10 m wind speed at the grid point
nearest each station. Days are processed in a spread-out order (every 8th day first, then the gaps), so a run
stopped by its time budget still covers the whole test period evenly. Results are saved after every day.

  python tools/earth2_run.py --league METAR --models fcn3,sfno,graphcast --budget_h 7
  -> data/raw/E2_METAR.npz : <model>_v [days, N, 3 leads (6/12/18 h), 3 targets], <model>_days, meta
"""
import argparse, datetime as dt, json, os, subprocess, sys, time, traceback

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pw.leagues import LEAGUES, bounds

RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
LEADS = (6, 12, 18)
PIP = {"fcn3": "earth2studio[fcn3]", "sfno": "earth2studio[sfno]", "graphcast": "earth2studio[graphcast]"}
NAMES = {"fcn3": "NVIDIA FourCastNet 3 (Earth-2)", "sfno": "NVIDIA FourCastNet SFNO (Earth-2)",
         "graphcast": "Google DeepMind GraphCast Operational"}


def install(key):
    for spec in (PIP[key], "earth2studio"):
        r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", spec], capture_output=True, text=True)
        print(f"  pip install {spec}: {'ok' if r.returncode == 0 else 'FAILED ' + r.stderr[-400:]}", flush=True)
        if r.returncode == 0:
            return True
    return False


def load(key, dev):
    import earth2studio.models.px as px
    cls = {"fcn3": "FCN3", "sfno": "SFNO", "graphcast": "GraphCastOperational"}[key]
    M = getattr(px, cls)
    return M.load_model(M.load_default_package()).to(dev)


def order(n):
    seen, out = set(), []
    for step in (8, 4, 2, 1):
        for i in range(0, n, step):
            if i not in seen:
                seen.add(i); out.append(i)
    return out


def rh_from(t_c, d_c):
    return 100 * np.exp(17.625 * d_c / (243.04 + d_c)) / np.exp(17.625 * t_c / (243.04 + t_c))


def run_model(key, days, lat, lon, budget_s, path, dev):
    import torch
    from earth2studio.data import GFS, fetch_data
    model = load(key, dev)
    ic = model.input_coords()
    vars_out = list(model.output_coords(ic)["variable"])
    glat, glon = np.asarray(ic["lat"]), np.asarray(ic["lon"])
    iy = np.array([np.abs(glat - la).argmin() for la in lat])
    ix = np.array([np.abs(((glon - lo + 180) % 360) - 180).argmin() for lo in lon])
    want = {v: vars_out.index(v) for v in ("t2m", "u10m", "v10m", "d2m", "r2m") if v in vars_out}
    print(f"  {NAMES[key]}: grid {len(glat)}x{len(glon)}, {len(vars_out)} variables, using {list(want)}", flush=True)
    src = GFS()
    V = np.full((len(days), len(lat), len(LEADS), 3), np.nan, np.float32)
    done = np.zeros(len(days), bool)
    t_start = time.time()
    for n, di in enumerate(order(len(days))):
        if time.time() - t_start > budget_s:
            print(f"  time budget reached after {done.sum()} days", flush=True)
            break
        t0 = time.time()
        try:
            when = np.array([np.datetime64(days[di])])
            x, coords = fetch_data(source=src, time=when, variable=ic["variable"], lead_time=ic["lead_time"],
                                   device=dev)
            it = model.create_iterator(x, coords)
            with torch.inference_mode():
                for step, (y, c) in enumerate(it):
                    lead = int(np.asarray(c["lead_time"]).ravel()[-1] / np.timedelta64(1, "h"))
                    if lead in LEADS:
                        dims = list(c.keys())
                        a = y.detach()
                        a = a.index_select(dims.index("variable"), torch.tensor(list(want.values()), device=a.device))
                        a = a.float().cpu().numpy()
                        a = np.moveaxis(a, [dims.index("variable"), dims.index("lat"), dims.index("lon")], [-3, -2, -1])
                        a = a.reshape(-1, *a.shape[-3:])[-1]                       # [vars, lat, lon]
                        pt = a[:, iy, ix]                                          # [vars, N]
                        g = {k: pt[j] for j, k in enumerate(want)}
                        li = LEADS.index(lead)
                        t_c = g["t2m"] - 273.15
                        V[di, :, li, 0] = t_c
                        if "r2m" in g:
                            V[di, :, li, 1] = np.clip(g["r2m"], 0, 100)
                        elif "d2m" in g:
                            V[di, :, li, 1] = np.clip(rh_from(t_c, g["d2m"] - 273.15), 0, 100)
                        V[di, :, li, 2] = np.hypot(g["u10m"], g["v10m"])
                    if lead >= LEADS[-1]:
                        break
            done[di] = True
        except Exception as e:
            print(f"    {days[di]}: FAILED {str(e)[:200]}", flush=True)
            if n < 2:
                traceback.print_exc()
        if n % 10 == 0 or n < 3:
            print(f"    {days[di]} done ({done.sum()}/{len(days)}, {time.time() - t0:.0f}s this day)", flush=True)
        if n % 10 == 0:
            save(path, key, V, days, done)
    save(path, key, V, days, done)
    del model
    torch.cuda.empty_cache()
    return int(done.sum())


def save(path, key, V, days, done):
    z = dict(np.load(path, allow_pickle=False)) if os.path.exists(path) else {}
    z[f"{key}_v"] = V[done]
    z[f"{key}_days"] = np.array(days)[done]
    np.savez_compressed(path, **z)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default="METAR")
    ap.add_argument("--models", default="fcn3,sfno,graphcast")
    ap.add_argument("--budget_h", type=float, default=7.0)
    a = ap.parse_args()
    import torch
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    z = np.load(os.path.join(RAW, f"WX_{a.league}.npz"))
    T = z["X"].shape[0]
    if str(z["tz"]) != "GMT":
        raise SystemExit("earth2_run expects a UTC league (METAR)")
    start = np.datetime64(str(z["start"])[:10])
    te = bounds(a.league, T)["test"]
    days = [str(start + np.timedelta64(int(k // 24), "D")) + "T00:00" for k in range(te[0], te[1] - 23, 24)]
    path = os.path.join(RAW, f"E2_{a.league}.npz")
    keys = [k for k in a.models.split(",") if k]
    meta = {"days_total": len(days), "models": {}}
    per = a.budget_h * 3600 / max(len(keys), 1)
    t_all = time.time()
    for k, key in enumerate(keys):
        left = a.budget_h * 3600 - (time.time() - t_all)
        if left < 600:
            break
        print(f"== {NAMES[key]}", flush=True)
        try:
            if not install(key):
                raise RuntimeError("could not install")
            n = run_model(key, days, z["lat"], z["lon"], min(left, per * (1.5 if k == 0 else 1.0)), path, dev)
            meta["models"][key] = {"name": NAMES[key], "days": n}
        except Exception as e:
            traceback.print_exc()
            meta["models"][key] = {"name": NAMES[key], "days": 0, "error": str(e)[:300]}
            print(f"  {NAMES[key]}: NOT RUN ({str(e)[:200]})", flush=True)
    zz = dict(np.load(path)) if os.path.exists(path) else {}
    zz["meta"] = np.array(json.dumps(meta))
    np.savez_compressed(path, **zz)
    print("E2 RESULT", json.dumps(meta), flush=True)


if __name__ == "__main__":
    main()
