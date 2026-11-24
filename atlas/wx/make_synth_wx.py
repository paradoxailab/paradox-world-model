"""Synthetic stand-in for the packed GHCNh data (same files and shapes as fetch_ghcnh_all.py writes), for speed and
correctness tests only. Values are a daily cycle plus noise; 1 in 7 hours missing.
  python make_synth_wx.py --out /content/wx_synth --stations 300
"""
import argparse, json, os
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--stations", type=int, default=300)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
rng = np.random.default_rng(0); N = a.stations
st = [dict(id=f"SYN{i:07d}", lat=float(rng.uniform(-60, 70)), lon=float(rng.uniform(-180, 180)), elev=float(rng.uniform(0, 2000)),
           name="synthetic", ctry="XX") for i in range(N)]
json.dump(st, open(os.path.join(a.out, "stations.json"), "w"))
for y in range(1995, 2026):
    n = int((np.datetime64(f"{y + 1}-01-01T00") - np.datetime64(f"{y}-01-01T00")) / np.timedelta64(1, "h"))
    h = np.arange(n); v = np.empty((N, n, 6), np.float16)
    base = 15 + 10 * np.sin(2 * np.pi * h / 24)
    v[:, :, 0] = base[None] + rng.standard_normal((N, n)).astype(np.float32)
    v[:, :, 1] = v[:, :, 0] - 5; v[:, :, 2] = 180; v[:, :, 3] = 3; v[:, :, 4] = 1013; v[:, :, 5] = 0
    v[:, ::7] = np.nan
    np.savez(os.path.join(a.out, f"wx_{y}.npz"), values=v, start=f"{y}-01-01T00", vars=np.array(["T", "Td", "WD", "WS", "SLP", "P_raw"]))
print("synthetic data written:", N, "stations")
