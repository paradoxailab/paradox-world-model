"""Paired significance tests between two ParadoxBench submissions on the same task, track and windows.

For each official window t, S_t = sum of absolute errors of the median over the scored values and C_t = their
count; a model's MAE is sum(S) / sum(C). For models a and b, the loss differential d_t = (S_a,t - S_b,t) / mean(C)
has mean equal to MAE_a - MAE_b. Consecutive windows overlap and errors are serially correlated, so:

  Diebold-Mariano test  d-bar / sqrt(LRV / T), long-run variance by Newey-West with a one-day bandwidth;
                        two-sided p-value from the normal distribution (Diebold & Mariano 1995).
  Block bootstrap       moving-block bootstrap of whole days of windows (2,000 resamples), 95% interval for
                        the relative MAE difference (MAE_a / MAE_b - 1).

  python -m paradoxbench.significance --a sub_a.npz --b sub_b.npz --task PEMS08 --track B
"""
import argparse, math, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paradoxbench.score import truth, task_data
from paradoxbench.spec import stride_for


def window_errors(q50, y, valid):
    e = np.where(valid, np.abs(q50 - y), 0.0)
    return e.reshape(len(e), -1).sum(1), valid.reshape(len(valid), -1).sum(1)


def newey_west(d, L):
    d = d - d.mean()
    T = len(d)
    v = float(d @ d) / T
    for k in range(1, min(L, T - 1) + 1):
        v += 2 * (1 - k / (L + 1)) * float(d[k:] @ d[:-k]) / T
    return max(v, 1e-12)


def compare(qa, qb, y, valid, windows_per_day, reps=2000, seed=0):
    Sa, C = window_errors(qa, y, valid)
    Sb, _ = window_errors(qb, y, valid)
    keep = C > 0
    Sa, Sb, C = Sa[keep], Sb[keep], C[keep]
    T = len(C)
    mae_a, mae_b = Sa.sum() / C.sum(), Sb.sum() / C.sum()
    d = (Sa - Sb) / C.mean()
    L = int(windows_per_day)
    z = d.mean() / math.sqrt(newey_west(d, L) / T)
    p = math.erfc(abs(z) / math.sqrt(2))
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(T / L))
    starts = np.arange(0, max(T - L, 0) + 1)
    rel = np.empty(reps)
    for r in range(reps):
        s = rng.choice(starts, nb)
        ix = (s[:, None] + np.arange(L)[None]).ravel()[:T]
        rel[r] = Sa[ix].sum() / Sb[ix].sum() - 1
    lo, hi = np.percentile(rel, [2.5, 97.5])
    return {"MAE_a": float(mae_a), "MAE_b": float(mae_b), "diff": float(mae_a - mae_b),
            "rel_diff_pct": float(100 * (mae_a / mae_b - 1)), "rel_ci95_pct": [float(100 * lo), float(100 * hi)],
            "dm_stat": float(z), "p_value": float(p), "windows": int(T), "block_windows": L}


def load_q50(path):
    return np.load(path)["q50"]


def test_pair(task, track, path_a, path_b, ds=None):
    ds = ds or task_data(task)
    _, y, valid = truth(task, track, ds)
    return compare(load_q50(path_a), load_q50(path_b), y, valid, 288 // stride_for(ds))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--track", default="B")
    a = ap.parse_args()
    print(test_pair(a.task, a.track, a.a, a.b))
