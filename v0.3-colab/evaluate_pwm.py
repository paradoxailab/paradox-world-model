"""Score PWM on the test set: each trained seed, and the seed ensemble (averaged quantiles).

  python evaluate_pwm.py --data PEMS08 --versions v0.3-s0 v0.3-s1 v0.3-s2

Writes results/<data>__PWM-Dyn.json, results/<data>__baselines.json and the ensemble's
test forecasts (models/<data>/ensemble_test_forecasts.npz) for the reasoning layer.
"""
import argparse, json, os, sys
import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pwm.data import load, ROOT
from pwm.evaluation import score, simple_baselines
from train import build, predict, DEV


def load_member(ds, version):
    d = os.path.join(ROOT, "models", ds.name, version)
    cfg = json.load(open(f"{d}/report.json"))["config"]
    m = build(ds, cfg)
    m.load_state_dict(torch.load(f"{d}/weights.pt", map_location="cpu"))
    return m.to(DEV).eval(), cfg


def main(a):
    ds = load(a.data)
    versions = a.versions or sorted(os.listdir(os.path.join(ROOT, "models", ds.name)))
    versions = [v for v in versions if os.path.exists(os.path.join(ROOT, "models", ds.name, v, "weights.pt"))]
    out = {"model": "PWM-Dyn", "provenance": "Paradox-trained from random initialisation",
           "dataset": ds.name, "members": versions, "per_member": {}}
    for split in ("val", "test"):
        idx = ds.indices(split, a.stride)
        qs = []
        for v in versions:
            m, cfg = load_member(ds, v)
            q10, q50, q90, y = predict(m, ds, idx)
            qs.append(np.stack([q10, q50, q90]))
            if split == "test":
                out["per_member"][v] = score(q10, q50, q90, y, ds.valid(y))
        q = np.sort(np.mean(qs, 0), axis=0)
        out[f"ensemble_{split}"] = score(q[0], q[1], q[2], y, ds.valid(y))
        if split == "test":
            np.savez_compressed(os.path.join(ROOT, "models", ds.name, "ensemble_test_forecasts.npz"),
                                idx=idx, q10=q[0], q50=q[1], q90=q[2], y=y)
    out["parameters_per_member"] = sum(p.numel() for p in m.parameters())
    out["setup"] = {"input_steps": ds.in_len, "output_steps": ds.out_len, "stride": a.stride,
                    "units": ds.units, "zero_masked": ds.mask_zero, "meta": ds.meta}
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, "results", f"{ds.name}__PWM-Dyn.json"), "w"), indent=1)
    base = simple_baselines(ds, ds.indices("test", a.stride))
    json.dump(base, open(os.path.join(ROOT, "results", f"{ds.name}__baselines.json"), "w"), indent=1)
    e = out["ensemble_test"]
    print(f"{ds.name} PWM-Dyn ensemble of {len(versions)}: test MAE {e['MAE']:.3f} RMSE {e['RMSE']:.3f} "
          f"cov80 {e['interval_80_coverage']*100:.1f}% | HA {base['historical_average']['MAE']:.3f} "
          f"| last {base['last_value']['MAE']:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--versions", nargs="*")
    ap.add_argument("--stride", type=int, default=1)
    main(ap.parse_args())
