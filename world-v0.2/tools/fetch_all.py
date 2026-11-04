"""Fetch every public input of the Paradox World Model v0.1 study. Nothing is redistributed with this kit.

  python tools/fetch_all.py            # 6 US networks (pretraining) + UK-M25 (live WebTRIS) + London weather

Sources
  PEMS04, PEMS08          ASTGNN repository (Caltrans PeMS flow, 5 min)
  PEMS03, PEMS07,         STAEformer repository data.npz (values, time) + ASTGNN distance CSV / DCRNN adjacency
  METR-LA, PEMS-BAY       (graphs); built by tools/prepare_traffic_data.py
  UK-M25, UK-MAN          National Highways WebTRIS API, 2025-07-01 .. 2026-06-30 (London, Greater Manchester;
                          test cities, never in pretraining)
  ENG-R*                  WebTRIS, rest of England, 2024-07-01 .. 2026-03-31 (pretraining; ends before any test)
  weather                 Open-Meteo historical archive (ERA5-based), hourly, 3 x 3 grid over each test city
"""
import datetime as dt, json, os, subprocess, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PW_RAW", os.path.join(ROOT, "data", "raw"))
EXT = os.path.join(ROOT, "ext")
ASTGNN = "https://raw.githubusercontent.com/guoshnBJTU/ASTGNN/main/data"
DCRNN = "https://raw.githubusercontent.com/liyaguang/DCRNN/master/data/sensor_graph"
STAE = "https://github.com/XDZhelheim/STAEformer"
WEATHER_VARS = ("temperature_2m", "precipitation", "wind_speed_10m")


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def curl(url, dst):
    if not os.path.exists(dst):
        run(["curl", "-sSfL", "--retry", "3", "-o", dst, url])


def us_networks():
    os.makedirs(os.path.join(EXT, "astgnn"), exist_ok=True)
    os.makedirs(os.path.join(EXT, "dcrnn"), exist_ok=True)
    for d in ("PEMS08", "PEMS04"):
        for e in ("npz", "csv"):
            curl(f"{ASTGNN}/{d}/{d}.{e}", f"{RAW}/{d}.{e}")
    if all(os.path.exists(f"{RAW}/{n}.pb.npz") for n in ("PEMS03", "PEMS07", "METR-LA", "PEMS-BAY")):
        return
    for f in ("PEMS03/PEMS03.csv", "PEMS03/PEMS03.txt", "PEMS07/PEMS07.csv"):
        curl(f"{ASTGNN}/{f}", os.path.join(EXT, "astgnn", os.path.basename(f)))
    for f in ("adj_mx.pkl", "adj_mx_bay.pkl"):
        curl(f"{DCRNN}/{f}", os.path.join(EXT, "dcrnn", f))
    dst = os.path.join(EXT, "STAEformer")
    if not os.path.exists(dst):
        run(["git", "clone", "-q", "--depth", "1", STAE, dst])
    run([sys.executable, os.path.join(ROOT, "tools", "prepare_traffic_data.py"), "--staeformer", dst,
         "--astgnn", os.path.join(EXT, "astgnn"), "--dcrnn", os.path.join(EXT, "dcrnn")])


def weather(name, box, start, end):
    """Hourly weather on a 3 x 3 grid over the city (local clock time, Europe/London), saved as [days*24, 9, 3]."""
    out = f"{RAW}/{name}.weather.npz"
    if os.path.exists(out):
        return
    import requests
    lats = list(np.linspace(box[0] + 0.1, box[1] - 0.1, 3))
    lons = list(np.linspace(box[2] + 0.15, box[3] - 0.15, 3))
    pts = [(a, b) for a in lats for b in lons]
    days = (dt.date.fromisoformat(end) - dt.date.fromisoformat(start)).days + 1
    W = np.full((days * 24, len(pts), len(WEATHER_VARS)), np.nan, np.float32)
    for g, (la, lo) in enumerate(pts):
        for k in range(5):
            try:
                r = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=120, params=dict(
                    latitude=la, longitude=lo, start_date=start, end_date=end, hourly=",".join(WEATHER_VARS),
                    timezone="Europe/London"))
                r.raise_for_status()
                h = r.json()["hourly"]
                break
            except Exception as e:
                if k == 4:
                    raise
                time.sleep(5 * (k + 1))
        s0 = dt.datetime.fromisoformat(start + "T00:00")
        for i, ts in enumerate(h["time"]):                      # local clock hours; DST duplicates overwrite
            t = dt.datetime.fromisoformat(ts)
            j = (t.date() - s0.date()).days * 24 + t.hour
            if 0 <= j < len(W):
                for v, name in enumerate(WEATHER_VARS):
                    x = h[name][i]
                    if x is not None:
                        W[j, g, v] = x
    np.savez_compressed(out, weather=W, lat=np.array([p[0] for p in pts]), lon=np.array([p[1] for p in pts]),
                        vars=np.array(WEATHER_VARS), start=np.array(start))
    print(f"weather {name}: {W.shape} hourly, missing {100 * np.isnan(W).mean():.2f}% -> {out}", flush=True)


def main():
    os.makedirs(RAW, exist_ok=True)
    us_networks()
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from fetch_webtris import BOXES
    for name in ("UK-M25", "UK-MAN"):
        if not os.path.exists(f"{RAW}/{name}.pb.npz"):
            run([sys.executable, os.path.join(ROOT, "tools", "fetch_webtris.py"), "city", "--name", name])
        weather(name, BOXES[name], "2025-07-01", "2026-06-30")
    if not any(f.startswith("ENG-R") for f in os.listdir(RAW)):
        run([sys.executable, os.path.join(ROOT, "tools", "fetch_webtris.py"), "england",
             "--max_sites", os.environ.get("PW_ENG_SITES", "800"), "--regions", "5"])
    print("data ready:", sorted(os.listdir(RAW)), flush=True)


if __name__ == "__main__":
    main()
