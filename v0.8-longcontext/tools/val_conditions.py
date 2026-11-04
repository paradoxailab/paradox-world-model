"""v0.7 model selection under real conditions, on VALIDATION data only.

For one trained model, writes models/<data>/<version>/val_conditions.json with the validation MAE on the official
validation windows under three conditions:
  clean   every reading as recorded
  dark    a validation-only 30% of locations (spec.VAL_SEED, not the Track R set) with no readings; scored there
  gaps    Track G's real-outage replay with validation-only draws (spec.VAL_SEED); scored on affected locations

  python tools/val_conditions.py --data PEMS08 --version ab-robust-s0
"""
import argparse, json, os, sys

import numpy as np
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from pwm.data import load
from paradoxbench.spec import validation_windows, hidden_sensors_val, replay_gaps, VAL_SEED
from paradoxbench.metrics import bench_score
from train import build, predict, DEV


def main(a):
    d = os.path.join(ROOT, "models", a.data, a.version)
    rep = json.load(open(os.path.join(d, "report.json")))
    ds = load(a.data, lc=bool(rep["config"].get("lc")))
    m = build(ds, rep["config"])
    m.load_state_dict(torch.load(os.path.join(d, "weights.pt"), map_location="cpu"))
    m = m.to(DEV).eval()
    idx = validation_windows(load(a.data))
    out = {}
    q10, q50, q90, y = predict(m, ds, idx)
    out["clean"] = bench_score(None, q50, None, y, ds.valid(y))["MAE"]
    hid = hidden_sensors_val(ds.N)
    _, q50, _, y = predict(m, ds, idx, drop_nodes=hid)
    keep = np.zeros(ds.N, bool); keep[hid] = True
    out["dark"] = bench_score(None, q50, None, y, ds.valid(y) & keep[None, None, :])["MAE"]
    gaps, aff = replay_gaps(ds, idx, seed=VAL_SEED)
    _, q50, _, y = predict(m, ds, idx, gaps=gaps)
    out["gaps"] = bench_score(None, q50, None, y, ds.valid(y) & aff[:, None, :])["MAE"]
    json.dump(out, open(os.path.join(d, "val_conditions.json"), "w"), indent=1)
    print(f"ParadoxBench-valcond {a.data} {a.version}: clean {out['clean']:.3f} dark {out['dark']:.3f} "
          f"gaps {out['gaps']:.3f}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--version", required=True)
    main(ap.parse_args())
