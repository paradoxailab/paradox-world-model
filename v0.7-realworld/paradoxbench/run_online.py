"""PWM-Dyn v0.7 online error correction: a Track B entry (open context) for real streaming use.

In deployment a forecast made at origin s for step s+h can be checked as soon as step s+h has been observed. At
origin t, for every location n and horizon h, the median (and both interval ends) are shifted by

    c[t, h, n] = beta * sum_j w_j r[t-1-h-j, h, n] / (lambda + sum_j w_j v[t-1-h-j, h, n]),   w_j = exp(-j / tau),

the exponentially weighted mean of the most recent resolved errors r = y - q50 of the same horizon and location,
over at most K = 288 past origins (v = 1 where the truth was a valid reading). Only readings observed before t
are used; with the 12-step input of each past forecast the total look-back is at most 312 steps, inside Track B's
512-step budget. beta and tau are chosen on the VALIDATION stream (beta = 0, no correction, is one option), the
conformal offsets are refitted on the corrected validation forecasts, and test is touched once.

  python paradoxbench/run_online.py --task PEMS08 --tag v0.7 --versions v07-s200 v07-s201 v07-s202
"""
import argparse, json, os, sys

import numpy as np
import torch
from scipy.signal import fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from pwm.data import load, ROOT
from pwm.calibration import fit_cqr, apply_cqr
from paradoxbench.spec import TASKS, official_windows, validation_windows
from paradoxbench.metrics import bench_score
from paradoxbench.score import record, truth
from paradoxbench.run_pwm import members
from train import build, predict, DEV

K, LAM = 288, 1.0
# Negative beta is allowed: on noisy 5-minute counts the errors of consecutive forecasts are negatively
# correlated (a model that follows a noisy last reading over-shoots, and the next error has the opposite sign).
BETAS, TAUS = (-0.5, -0.25, 0.0, 0.25, 0.5, 1.0), (1.0, 3.0, 12.0, 48.0)


def stream(ds, mem, origins, chunk=2048):
    """Ensemble quantiles for every origin (stride 1), accumulated member by member to bound memory."""
    acc = None
    for v, rep in mem:
        m = build(ds, rep["config"])
        m.load_state_dict(torch.load(os.path.join(ROOT, "models", ds.name, v, "weights.pt"), map_location="cpu"))
        m = m.to(DEV).eval()
        parts, ys = [], []
        for s in range(0, len(origins), chunk):
            q10, q50, q90, y = predict(m, ds, origins[s:s + chunk])
            parts.append(np.stack([q10, q50, q90]).astype(np.float32)); ys.append(y.astype(np.float32))
        q = np.concatenate(parts, 1)
        acc = q if acc is None else acc + q
        y = np.concatenate(ys)
    return np.sort(acc / len(mem), axis=0), y


def corrections(p50, y, valid, tau):
    S, H, N = p50.shape
    r = np.where(valid, y - p50, 0.0).astype(np.float32)
    v = valid.astype(np.float32)
    k = np.exp(-np.arange(K) / tau)[:, None].astype(np.float32)
    c = np.zeros_like(p50)
    for h in range(H):
        num = fftconvolve(r[:, h], k, axes=0)[:S]
        den = fftconvolve(v[:, h], k, axes=0)[:S]
        lag = 1 + h                                   # origin t may use errors of origins <= t-1-h
        c[lag:, h] = num[:S - lag] / (LAM + np.maximum(den[:S - lag], 0))
    return c


def main(a):
    loader = TASKS[a.task][0]
    ds = load(loader)
    mem = members(loader, a.versions)
    test_idx, val_idx = official_windows(ds), validation_windows(ds)
    o0, o1 = ds.bounds["val"][0] + ds.in_len, ds.bounds["test"][1] - ds.out_len
    origins = np.arange(o0, o1 + 1)
    q, y = stream(ds, mem, origins)
    valid = ds.valid(y)
    pos_v, pos_t = val_idx - o0, test_idx - o0
    base_val = bench_score(None, q[1][pos_v], None, y[pos_v], valid[pos_v])["MAE"]
    grid = {}
    for tau in TAUS:
        c = corrections(q[1], y, valid, tau)
        for beta in BETAS:
            grid[(beta, tau)] = bench_score(None, (q[1] + beta * c)[pos_v], None, y[pos_v], valid[pos_v])["MAE"]
    beta, tau = min(grid, key=grid.get)
    print(f"ParadoxBench-online {a.task}: validation MAE without correction {base_val:.3f}; best beta {beta} tau {tau} "
          f"-> {grid[(beta, tau)]:.3f} ({100 * (grid[(beta, tau)] / base_val - 1):+.2f}%)", flush=True)
    if beta == 0.0:   # no correction: Track B gets the plain ensemble (as in v0.6 for the standard-context model)
        print(f"ParadoxBench-online {a.task}: correction not selected on validation; Track B = Track A model", flush=True)
    c = beta * corrections(q[1], y, valid, tau) if beta else np.zeros_like(q[1])
    qc = q + c[None]
    delta = fit_cqr(ds, qc[0][pos_v], qc[2][pos_v], y[pos_v], valid[pos_v])
    c10, c50, c90 = apply_cqr(ds, np.maximum(qc[0][pos_t], 0), np.maximum(qc[1][pos_t], 0),
                              np.maximum(qc[2][pos_t], 0), delta)
    idx, yt, vt = truth(a.task, "B", ds)
    assert np.array_equal(idx, test_idx)
    name = f"PWM-Dyn {a.tag} online ({len(mem)}-seed, CQR)" if beta else f"PWM-Dyn {a.tag} ({len(mem)}-seed, CQR)"
    record(a.task, "B", name, c10, c50, c90,
           {"type": "specialist (Paradox, trained from scratch) + online error correction",
            "params": sum(p.numel() for p in build(ds, mem[0][1]["config"]).parameters()),
            "context_steps": K + ds.out_len + ds.in_len, "members": [v for v, _ in mem],
            "trained_on": f"{a.task} train split only",
            "online": {"beta": beta, "tau": tau, "K": K, "lambda": LAM, "val_MAE_uncorrected": base_val,
                       "val_grid": {f"{b}|{t}": m for (b, t), m in grid.items()}},
            "calibration": {"method": "split-conformal CQR on corrected validation", "delta_per_horizon": delta.tolist()}},
           ds)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=list(TASKS))
    ap.add_argument("--versions", nargs="+", required=True)
    ap.add_argument("--tag", default="v0.7")
    main(ap.parse_args())
