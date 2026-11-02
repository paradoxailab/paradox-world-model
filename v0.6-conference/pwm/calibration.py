"""v0.4: split-conformal calibration of PWM's 80% interval (conformalised quantile regression,
Romano et al. 2019), fitted on the VALIDATION split only and applied unchanged to test.

Scores are computed in the model's own target space (log1p for rainfall, identity for traffic),
so the widening is multiplicative on rainfall and additive on traffic. One offset per horizon.
The median (point forecast) is never changed, so MAE/RMSE/MAPE are unaffected.
"""
import numpy as np


def _fwd(ds, v):
    return np.log1p(np.maximum(v, 0)) if ds.transform == "log1p" else v


def _inv(ds, v):
    return np.maximum(np.expm1(v), 0) if ds.transform == "log1p" else v


def fit_cqr(ds, q10, q90, y, valid, level=0.8):
    """Arrays [S, H, N] in real units (validation). Returns delta [H] in target space."""
    lo, hi, yt = _fwd(ds, q10), _fwd(ds, q90), _fwd(ds, np.nan_to_num(y))
    s = np.maximum(lo - yt, yt - hi)
    deltas = []
    for h in range(s.shape[1]):
        sh = s[:, h][valid[:, h]]
        n = len(sh)
        k = min(1.0, level * (1 + 1 / max(n, 1)))
        deltas.append(float(np.quantile(sh, k)) if n else 0.0)
    return np.array(deltas, np.float32)


def apply_cqr(ds, q10, q50, q90, delta):
    d = delta[None, :, None]
    lo = _inv(ds, _fwd(ds, q10) - d)
    hi = _inv(ds, _fwd(ds, q90) + d)
    return np.minimum(lo, q50), q50, np.maximum(hi, q50)
