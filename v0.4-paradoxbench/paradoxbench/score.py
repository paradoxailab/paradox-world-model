"""Score a ParadoxBench-1 submission and record it on the leaderboard.

A submission is an .npz with arrays q10, q50, q90 of shape [W, H, N] (official test windows x
horizon x locations, real units), plus a JSON-able meta dict. Anyone can submit:

  python -m paradoxbench.score --task PEMS08 --track B --sub my_model.npz --model "My model" \
      --type foundation --params 200e6 --context 512 --trained-on "pretraining corpus X"
"""
import argparse, hashlib, json, os, re, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from pwm.data import load, ROOT
from paradoxbench.spec import TASKS, VERSION, STRIDE, official_windows, hidden_sensors
from paradoxbench.metrics import bench_score

RES = os.path.join(ROOT, "results", "paradoxbench")
SUB = os.path.join(ROOT, "submissions")


def task_data(task):
    return load(TASKS[task][0])


def truth(task, track, ds=None):
    ds = ds or task_data(task)
    idx = official_windows(ds)
    y = ds.raw[idx[:, None] + np.arange(ds.out_len)[None]]
    valid = ds.valid(y)
    if track == "R":
        keep = np.zeros(ds.N, bool)
        keep[hidden_sensors(ds.N)] = True
        valid &= keep[None, None, :]
    return idx, y, valid


def slug(s):
    return re.sub(r"[^A-Za-z0-9.+-]+", "_", s).strip("_")


def record(task, track, model, q10, q50, q90, meta, ds=None, save_submission=True):
    idx, y, valid = truth(task, track, ds)
    for name, q in (("q50", q50), ("q10", q10), ("q90", q90)):
        if q is not None and q.shape != y.shape:
            raise ValueError(f"{name} has shape {q.shape}; ParadoxBench-1 {task} expects {y.shape}")
    m = bench_score(q10, q50, q90, y, valid)
    os.makedirs(RES, exist_ok=True)
    out = {"benchmark": VERSION, "task": task, "track": track, "model": model,
           "windows": {"split": "test", "stride": STRIDE, "count": int(len(idx))},
           "metrics": m, **meta}
    if save_submission and q10 is not None:
        os.makedirs(SUB, exist_ok=True)
        p = os.path.join(SUB, f"{task}__{track}__{slug(model)}.npz")
        np.savez_compressed(p, q10=q10.astype(np.float32), q50=q50.astype(np.float32),
                            q90=q90.astype(np.float32))
        out["submission_sha256"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    json.dump(out, open(os.path.join(RES, f"{task}__{track}__{slug(model)}.json"), "w"), indent=1)
    cov = f"COV80 {m['COV80']*100:.1f}% IS80 {m['IS80']:.2f} QL {m['QL']:.3f}" if "IS80" in m else "point only"
    print(f"ParadoxBench {task}/{track} {model}: MAE {m['MAE']:.3f} RMSE {m['RMSE']:.3f} {cov}", flush=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=list(TASKS))
    ap.add_argument("--track", required=True, choices=list("ABRZ"))
    ap.add_argument("--sub", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--type", default="submitted")
    ap.add_argument("--params", type=float, default=None)
    ap.add_argument("--context", type=int, default=None)
    ap.add_argument("--trained-on", default="")
    a = ap.parse_args()
    z = np.load(a.sub)
    record(a.task, a.track, a.model, z["q10"], z["q50"], z["q90"],
           {"type": a.type, "params": a.params, "context_steps": a.context, "trained_on": a.trained_on})
