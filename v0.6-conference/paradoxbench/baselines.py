"""ParadoxBench-1 reference baselines, all fitted on the TRAIN split only.

  last value        point only, Tracks A/B
  seasonal naive    value one season earlier (yesterday same time / same day last year), Track B
  climatology       per-location empirical 10/50/90% quantiles of the training data at the same
                    time of week (traffic, +-1 slot) or day of year (rainfall, +-7 days); Tracks A/B/R
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paradoxbench.spec import TASKS
from paradoxbench.score import task_data, truth, record


def climatology(ds, idx):
    _, b = ds.bounds["train"]
    traffic = ds.period == 288
    key = (ds.dow * 288 + ds.period_idx) if traffic else ds.period_idx
    nk, w = (7 * 288, 1) if traffic else (366, 7)
    tr = ds.raw[:b]
    tbl = np.zeros((3, nk, ds.N), np.float32)
    for k in range(nk):
        near = [(k + j) % nk for j in range(-w, w + 1)]
        rows = tr[np.isin(key[:b], near)]
        if ds.mask_zero:
            rows = np.where(rows > 1e-4, rows, np.nan)
        tbl[:, k] = np.nan_to_num(np.nanquantile(rows, (0.1, 0.5, 0.9), axis=0)) if len(rows) else 0
    fo = idx[:, None] + np.arange(ds.out_len)[None]
    q = tbl[:, key[fo]]
    return q[0], q[1], q[2]


def run(task):
    ds = task_data(task)
    idx, y, _ = truth(task, "A", ds)
    H = ds.out_len
    meta = {"type": "baseline", "params": 0, "trained_on": f"{task} train split"}
    last = np.repeat(np.nan_to_num(ds.raw[idx - 1])[:, None], H, 1)
    seas_lag = 288 if ds.period == 288 else 365
    seas = np.nan_to_num(ds.raw[idx[:, None] - seas_lag + np.arange(H)[None]])
    c10, c50, c90 = climatology(ds, idx)
    for tr in ("A", "B"):
        record(task, tr, "Last value", None, last, None, {**meta, "context_steps": 1}, ds)
        record(task, tr, "Climatology quantiles", c10, c50, c90, {**meta, "context_steps": 0}, ds)
    record(task, "B", "Seasonal naive", None, seas, None, {**meta, "context_steps": seas_lag + H}, ds)
    record(task, "R", "Climatology quantiles", c10, c50, c90, {**meta, "context_steps": 0}, ds)


if __name__ == "__main__":
    for t in (sys.argv[1:] or list(TASKS)):
        run(t)
