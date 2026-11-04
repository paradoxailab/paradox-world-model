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
from paradoxbench.spec import stride_for, windows_per_day


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


def window_losses(kind, q10, q50, q90, y, valid):
    """v0.8: per-window sums of a metric's loss and value counts, for paired tests on every metric.
    MAE: |e|; RMSE: e^2 (the test is on MSE); MAPE: |e|/y over non-zero truths; QL: mean pinball of q10/q50/q90;
    IS80: interval score of [q10, q90]."""
    y0 = np.nan_to_num(y)
    v = valid.copy()
    if kind == "MAE":
        l = np.abs(q50 - y0)
    elif kind == "RMSE":
        l = (q50 - y0) ** 2
    elif kind == "MAPE":
        v &= y0 > 1e-4
        l = np.abs(q50 - y0) / np.maximum(y0, 1e-4)
    elif kind == "QL":
        l = sum(np.maximum(t * (y0 - q), (t - 1) * (y0 - q)) for t, q in ((0.1, q10), (0.5, q50), (0.9, q90))) / 3
    elif kind == "IS80":
        l = (q90 - q10) + 10 * np.maximum(q10 - y0, 0) + 10 * np.maximum(y0 - q90, 0)
    else:
        raise ValueError(kind)
    l = np.where(v, l, 0.0)
    return l.reshape(len(l), -1).sum(1), v.reshape(len(v), -1).sum(1)


def compare_losses(Sa, Sb, C, windows_per_day, reps=2000, seed=0):
    """Same Diebold-Mariano + day-block bootstrap as compare(), on any per-window loss sums."""
    keep = C > 0
    Sa, Sb, C = Sa[keep], Sb[keep], C[keep]
    T, L = len(C), int(windows_per_day)
    d = (Sa - Sb) / C.mean()
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
    return {"loss_a": float(Sa.sum() / C.sum()), "loss_b": float(Sb.sum() / C.sum()),
            "rel_diff_pct": float(100 * (Sa.sum() / Sb.sum() - 1)), "rel_ci95_pct": [float(100 * lo), float(100 * hi)],
            "dm_stat": float(z), "p_value": float(p), "windows": int(T),
            "significant": bool(p < 0.05 and (hi < 0 or lo > 0))}


def compare_all(sa, sb, y, valid, windows_per_day):
    """sa, sb: dicts with q10/q50/q90 (q10/q90 may be absent). Returns {metric: test} for every shared metric."""
    out = {}
    for k in ("MAE", "RMSE", "MAPE", "QL", "IS80"):
        if k in ("QL", "IS80") and (sa.get("q10") is None or sb.get("q10") is None):
            continue
        La, C = window_losses(k, sa.get("q10"), sa["q50"], sa.get("q90"), y, valid)
        Lb, _ = window_losses(k, sb.get("q10"), sb["q50"], sb.get("q90"), y, valid)
        out[k] = compare_losses(La, Lb, C, windows_per_day)
    return out


def load_q50(path):
    return np.load(path)["q50"]


def test_pair(task, track, path_a, path_b, ds=None):
    ds = ds or task_data(task)
    _, y, valid = truth(task, track, ds)
    return compare(load_q50(path_a), load_q50(path_b), y, valid, windows_per_day(ds))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--track", default="B")
    a = ap.parse_args()
    print(test_pair(a.task, a.track, a.a, a.b))
