"""ParadoxBench-1 reference baselines, all fitted on the TRAIN split only.

  last value        point only, Tracks A/B
  seasonal naive    value one season earlier (yesterday same time / same day last year), Track B
  climatology       per-location empirical 10/50/90% quantiles of the training data at the same
                    time of week (traffic, +-1 slot) or day of year (rainfall, +-7 days); Tracks A/B/R
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paradoxbench.spec import TASKS, replay_gaps
from paradoxbench.score import task_data, truth, record


def climatology(ds, idx):
    _, b = ds.bounds["train"]
    traffic = ds.period != 366
    key = (ds.dow * ds.period + ds.period_idx) if traffic else ds.period_idx
    nk, w = (7 * ds.period, 1) if traffic else (366, 7)
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
    seas_lag = ds.period if ds.period != 366 else 365
    seas = np.nan_to_num(ds.raw[idx[:, None] - seas_lag + np.arange(H)[None]])
    c10, c50, c90 = climatology(ds, idx)
    for tr in ("A", "B"):
        record(task, tr, "Last value", None, last, None, {**meta, "context_steps": 1}, ds)
        record(task, tr, "Climatology quantiles", c10, c50, c90, {**meta, "context_steps": 0}, ds)
    record(task, "B", "Seasonal naive", None, seas, None, {**meta, "context_steps": seas_lag + H}, ds)
    record(task, "R", "Climatology quantiles", c10, c50, c90, {**meta, "context_steps": 0}, ds)
    # 1.2 Track G: last OBSERVED reading after the replayed outage (climatology median if none), and climatology
    if ds.period == 366:                     # Track G is defined for the traffic tasks only
        return
    gaps, _ = replay_gaps(ds, idx)
    hist = ds.raw[idx[:, None] + np.arange(-ds.in_len, 0)[None]]          # [W, L, N]
    obs = ~np.isnan(hist) & ~gaps
    if ds.mask_zero:
        obs &= hist > 1e-4
    L = ds.in_len
    last_i = np.where(obs.any(1), L - 1 - np.argmax(obs[:, ::-1], 1), -1)  # [W, N]
    lv = np.take_along_axis(np.nan_to_num(hist), np.clip(last_i, 0, None)[:, None, :], 1)[:, 0]
    locf = np.where(last_i >= 0, lv, c50[:, 0])
    record(task, "G", "Last observed value (climatology if none)", None, np.repeat(locf[:, None], H, 1), None,
           {**meta, "context_steps": ds.in_len}, ds)
    record(task, "G", "Climatology quantiles", c10, c50, c90, {**meta, "context_steps": 0}, ds)


if __name__ == "__main__":
    for t in (sys.argv[1:] or list(TASKS)):
        run(t)
