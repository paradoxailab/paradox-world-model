"""Shared scoring: every model (PWM or an opponent) is scored by this one function on
exactly the same windows, so comparisons are like-for-like."""
import numpy as np


def score(q10, q50, q90, y, valid):
    """All arrays [S, H, N] in real units. valid = which truths count."""
    e = (q50 - y)[valid]
    yt = y[valid]
    nz = yt > 1e-4
    out = {
        "MAE": float(np.abs(e).mean()),
        "RMSE": float(np.sqrt((e ** 2).mean())),
        "MAPE": float((np.abs(e[nz]) / yt[nz]).mean() * 100),
        "per_horizon_MAE": [float(np.abs((q50[:, h] - y[:, h])[valid[:, h]]).mean())
                            for h in range(y.shape[1])],
        "n_values_scored": int(valid.sum()),
    }
    if q10 is not None:
        inside = (y >= q10) & (y <= q90)
        out["interval_80_coverage"] = float(inside[valid].mean())
        out["interval_80_mean_width"] = float((q90 - q10)[valid].mean())
    return out


def simple_baselines(ds, idx):
    """Last value and seasonal historical average (from TRAIN data only)."""
    fo = idx[:, None] + np.arange(ds.out_len)[None]
    y = ds.raw[fo]
    valid = ds.valid(y)
    last = np.repeat(np.nan_to_num(ds.raw[idx - 1])[:, None], ds.out_len, 1)
    _, b = ds.bounds["train"]
    key = ds.dow[:b] * ds.period + ds.period_idx[:b]
    table = np.full((7 * ds.period, ds.N), np.nan, np.float32)
    for k in np.unique(key):
        table[k] = np.nanmean(ds.raw[:b][key == k], 0)
    table = np.where(np.isnan(table), np.nanmean(ds.raw[:b], 0), table)
    ha = table[ds.dow[fo] * ds.period + ds.period_idx[fo]]
    return {"last_value": score(None, last, None, y, valid),
            "historical_average": score(None, ha, None, y, valid)}
