"""Metrics, split-conformal calibration and paired significance tests (identical windows and masks for every model).

Metrics (real units, observed truth only): MAE, RMSE, MAPE (truth >= 20 vehicles / 15 min), QL (mean pinball loss
of the 10/50/90% quantiles), IS80 (interval score of the 80% band), COV80 (share of truth inside the band).
Significance: per window, the summed loss of model a minus model b; Diebold-Mariano with Newey-West variance
(bandwidth one day of windows) and a day-block bootstrap (2,000 resamples) of the relative difference. A
difference counts only if p < 0.05 AND the 95% interval excludes zero.
"""
import math

import numpy as np

MAPE_FLOOR = 20.0
METRICS = ("MAE", "RMSE", "MAPE", "QL", "IS80", "COV80")


def _cell_losses(q, y):
    lo, md, hi = q[..., 0], q[..., 1], q[..., 2]
    yv = np.nan_to_num(y)
    e = yv - md
    pin = sum(np.maximum(t * (yv - q[..., k]), (t - 1) * (yv - q[..., k])) for k, t in enumerate((0.1, 0.5, 0.9))) / 3
    a = 0.2
    isc = (hi - lo) + (2 / a) * np.maximum(lo - yv, 0) + (2 / a) * np.maximum(yv - hi, 0)
    return {"MAE": np.abs(e), "RMSE": e ** 2, "MAPE": np.abs(e) / np.maximum(yv, 1e-6), "QL": pin, "IS80": isc,
            "COV80": ((yv >= lo) & (yv <= hi)).astype(float)}


def _masks(y):
    v = ~np.isnan(y)
    return {m: (v & (np.nan_to_num(y) >= MAPE_FLOOR)) if m == "MAPE" else v for m in METRICS}


def score(q, y, horizons=(0, 1, 3)):
    """q [W, n, H, 3], y [W, n, H]. Returns overall metrics and per-horizon MAE / RMSE / MAPE."""
    c, mk = _cell_losses(q, y), _masks(y)
    out = {}
    for m in METRICS:
        v = c[m][mk[m]].mean() if mk[m].any() else float("nan")
        out[m] = float(math.sqrt(v) if m == "RMSE" else (100 * v if m in ("MAPE", "COV80") else v))
    for h in horizons:
        for m in ("MAE", "RMSE", "MAPE"):
            s, k = c[m][..., h], mk[m][..., h]
            v = s[k].mean() if k.any() else float("nan")
            out[f"{m}@{15 * (h + 1)}min"] = float(math.sqrt(v) if m == "RMSE" else (100 * v if m == "MAPE" else v))
    return out


def fit_cqr(q, y, cover=0.8):
    """Split-conformal CQR per horizon on validation forecasts: widen (or narrow) both ends by delta_h."""
    yv, v = np.nan_to_num(y), ~np.isnan(y)
    d = []
    for h in range(q.shape[2]):
        e = np.maximum(q[:, :, h, 0] - yv[:, :, h], yv[:, :, h] - q[:, :, h, 2])[v[:, :, h]]
        n = len(e)
        d.append(float(np.quantile(e, min(1.0, math.ceil((n + 1) * cover) / n))) if n else 0.0)
    return np.array(d, np.float32)


def apply_cqr(q, d):
    q = q.copy()
    q[..., 0] = np.maximum(q[..., 0] - d, 0)
    q[..., 2] = q[..., 2] + d
    q[..., 1] = np.clip(q[..., 1], q[..., 0], q[..., 2])
    return q


def _newey_west(d, L):
    d = d - d.mean()
    T = len(d)
    v = float(d @ d) / T
    for k in range(1, min(L, T - 1) + 1):
        v += 2 * (1 - k / (L + 1)) * float(d[k:] @ d[:-k]) / T
    return max(v, 1e-12)


def compare(qa, qb, y, per_day, metric="MAE", reps=2000, seed=0):
    """Paired test of model a vs model b on one metric. Negative rel_diff = a is better."""
    if metric == "COV80":
        return None
    ca, cb, mk = _cell_losses(qa, y)[metric], _cell_losses(qb, y)[metric], _masks(y)[metric]
    W = len(y)
    Sa = np.where(mk, ca, 0).reshape(W, -1).sum(1)
    Sb = np.where(mk, cb, 0).reshape(W, -1).sum(1)
    C = mk.reshape(W, -1).sum(1)
    keep = C > 0
    Sa, Sb, C = Sa[keep], Sb[keep], C[keep]
    T = len(C)
    if T < 3:
        return None
    d = (Sa - Sb) / C.mean()
    L = max(int(per_day), 1)
    z = d.mean() / math.sqrt(_newey_west(d, L) / T)
    p = math.erfc(abs(z) / math.sqrt(2))
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(T / L))
    starts = np.arange(0, max(T - L, 0) + 1)
    rel = np.empty(reps)
    for r in range(reps):
        ix = (rng.choice(starts, nb)[:, None] + np.arange(L)[None]).ravel()[:T]
        rel[r] = Sa[ix].sum() / max(Sb[ix].sum(), 1e-12) - 1
    if metric == "RMSE":                                   # tests on squared error; report RMSE ratio
        rel = np.sqrt(np.maximum(rel + 1, 0)) - 1
        rd = math.sqrt(Sa.sum() / Sb.sum()) - 1
    else:
        rd = Sa.sum() / Sb.sum() - 1
    lo, hi = np.percentile(rel, [2.5, 97.5])
    sig = bool(p < 0.05 and (hi < 0 or lo > 0))
    return {"metric": metric, "rel_diff_pct": float(100 * rd), "ci95_pct": [float(100 * lo), float(100 * hi)],
            "p": float(p), "dm": float(z), "windows": int(T), "significant": sig,
            "verdict": ("WIN" if rd < 0 else "LOSS") if sig else "TIE"}
