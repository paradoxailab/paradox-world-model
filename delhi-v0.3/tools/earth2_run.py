"""Run NVIDIA's open global AI weather models ourselves (NVIDIA Earth2Studio, Apache-2.0) and read their
forecasts at the league's stations: FourCastNet 3 / FourCastNet SFNO (NVIDIA), and GraphCast Operational
(Google DeepMind) if it fits in the GPU's memory.

Each run starts from the real NOAA GFS analysis at 00 UTC of a TEST day (the same starting state an
operational centre would use, fetched from NOAA's public AWS bucket) and steps 6 hours at a time to +18 h.
We keep 2 m temperature, 2 m humidity (when the model predicts it) and 10 m wind speed at the grid point
nearest each station. Days are processed in a spread-out order (every 8th day first, then the gaps), so a run
stopped by its time budget still covers the whole test period evenly. Results are saved after every day.

  python tools/earth2_run.py --league WMO --models sfno,graphcast,fcn3,graphcast_small,aurora --budget_h 7
(a model that cannot be installed, loaded or fit in memory is reported as not run; its time goes to the others)
  -> data/raw/E2_METAR.npz : <model>_v [days, N, 3 leads (6/12/18 h), 3 targets], <model>_days, meta
"""
import argparse, datetime as dt, json, os, subprocess, sys, time, traceback

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pw.leagues import LEAGUES, bounds

RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
LEADS = (6, 12, 18)
CLS = {"fcn3": "FCN3", "sfno": "SFNO", "graphcast": "GraphCastOperational", "graphcast_small": "GraphCastSmall",
       "aurora": "Aurora"}
NAMES = {"fcn3": "NVIDIA FourCastNet 3 (Earth-2)", "sfno": "NVIDIA FourCastNet SFNO (Earth-2)",
         "graphcast": "Google DeepMind GraphCast Operational (0.25 deg)",
         "graphcast_small": "Google DeepMind GraphCast Small (1 deg, ERA5-trained)",
         "aurora": "Microsoft Aurora (0.25 deg)"}


E2S = "earth2studio @ git+https://github.com/NVIDIA/earth2studio.git"
# the git revisions earth2studio's own pyproject pins ([tool.uv.sources]); pip does not read those, so name them
PSN = "nvidia-physicsnemo @ git+https://github.com/NVIDIA/physicsnemo.git@bf0ad4f43275b84a7beab35127d57a99cd359260"
MAKANI = "makani @ git+https://github.com/NVIDIA/makani.git@b38fcb2799d7dbc146fa60459f3f9823394a8bf1"
THARM = "torch-harmonics @ git+https://github.com/NVIDIA/torch-harmonics.git@a632ca748a12bd9f74dbc1e00653317810991f74"
WNEXT = "weathernext @ git+https://github.com/google-deepmind/weathernext.git@9c034db1ff412d5db6cbe6bb0c5c9afc5a267719"
DEPS = {"sfno": [MAKANI, THARM, "pynvml>=12.0.0", "ruamel-yaml>=0.18.10", "scipy>=1.10.0", "moviepy"],
        "fcn3": [MAKANI, THARM, "ruamel.yaml>=0.18.14", "scipy>=1.10.0", "moviepy"],
        "graphcast": [WNEXT, "dm-haiku>=0.0.14", "jax[cuda12]>=0.4.26", "flax>=0.10.6", "dm-tree>=0.1.9"],
        "graphcast_small": [WNEXT, "dm-haiku>=0.0.14", "jax[cuda12]>=0.4.26", "flax>=0.10.6", "dm-tree>=0.1.9"],
        "aurora": ["microsoft-aurora>=2.0.0"]}


def importable(key):
    r = subprocess.run([sys.executable, "-c", f"import earth2studio.models.px as p; getattr(p, '{CLS[key]}')"],
                       capture_output=True, text=True)
    if r.returncode:
        print(f"    import check failed: {r.stderr.strip().splitlines()[-1][:200] if r.stderr.strip() else '?'}", flush=True)
    return r.returncode == 0


def pip(specs, label):
    t0 = time.time()
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", *specs], capture_output=True, text=True)
    print(f"  pip install {label}: {'ok' if r.returncode == 0 else 'FAILED ' + r.stderr[-400:]} "
          f"({time.time() - t0:.0f}s)", flush=True)
    return r.returncode == 0


def install(key):
    """Install earth2studio (main) with the exact dependency revisions it pins, then check the class imports in a
    fresh interpreter. Each model then runs in its own subprocess, so one model's packages cannot break another."""
    if importable(key):
        return True
    pip([E2S, PSN], "earth2studio (main) + physicsnemo (pinned revision)")
    pip(DEPS[key], f"{key} dependencies (pinned revisions)")
    return importable(key)


def load(key, dev):
    import earth2studio.models.px as px
    M = getattr(px, CLS[key])
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
    from earth2studio.utils.coords import map_coords
    from earth2studio.utils.time import to_time_array
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
            when = to_time_array([days[di]])
            kw = {}
            if hasattr(model, "interp_method"):
                kw = dict(interp_to=ic, interp_method=getattr(model, "interp_method", "nearest"))
            x, coords = fetch_data(source=src, time=when, variable=ic["variable"], lead_time=ic["lead_time"],
                                   device=dev, **kw)
            x, coords = map_coords(x, coords, ic)
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
    ap.add_argument("--models", default="sfno,graphcast,fcn3,graphcast_small,aurora")
    ap.add_argument("--budget_h", type=float, default=7.0)
    ap.add_argument("--one", default="")                 # internal: run a single model in this process
    ap.add_argument("--budget_s", type=float, default=0)
    a = ap.parse_args()
    z = np.load(os.path.join(RAW, f"WX_{a.league}.npz"))
    T = z["X"].shape[0]
    if str(z["tz"]) != "GMT":
        raise SystemExit("earth2_run expects a UTC league (WMO or METAR)")
    start = np.datetime64(str(z["start"])[:10])
    te = bounds(a.league, T)["test"]
    days = [str(start + np.timedelta64(int(k // 24), "D")) + "T00:00" for k in range(te[0], te[1] - 23, 24)]
    path = os.path.join(RAW, f"E2_{a.league}.npz")
    if a.one:
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        n = run_model(a.one, days, z["lat"], z["lon"], a.budget_s, path, dev)
        print(f"E2 ONE {a.one} {n}", flush=True)
        return
    keys = [k for k in a.models.split(",") if k]
    meta = {"days_total": len(days), "models": {}}
    t_all = time.time()
    for k, key in enumerate(keys):
        left = a.budget_h * 3600 - (time.time() - t_all)
        if left < 600:
            break
        print(f"== {NAMES[key]}", flush=True)
        try:
            if not install(key):
                raise RuntimeError("could not install / import")
            r = subprocess.run([sys.executable, os.path.abspath(__file__), "--league", a.league, "--one", key,
                                "--budget_s", str(left / (len(keys) - k))], capture_output=True, text=True)
            print(r.stdout[-6000:], r.stderr[-3000:], flush=True)
            done = [l for l in r.stdout.splitlines() if l.startswith("E2 ONE")]
            n = int(done[-1].split()[-1]) if done else 0
            meta["models"][key] = {"name": NAMES[key], "days": n}
            if not n:
                meta["models"][key]["error"] = (r.stderr.strip().splitlines() or ["no days completed"])[-1][:300]
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
