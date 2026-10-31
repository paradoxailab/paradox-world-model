"""ParadoxBench-1 metrics. One function scores every submission (PWM, TimesFM, baselines).

Point:          MAE, RMSE, MAPE (non-zero truths only) of the median q50.
Probabilistic:  QL  = mean pinball loss over the three quantiles (10/50/90) - a proper score;
                      2*QL is a 3-point approximation of CRPS.
                IS80 = interval (Winkler) score of [q10, q90] at 80%: width + 10*(miss below) + 10*(miss above);
                      rewards intervals that are narrow AND cover. Lower is better.
                COV80 = share of truths inside [q10, q90] (target 80%), WIDTH = mean width.
"""
import numpy as np

TAUS = (0.1, 0.5, 0.9)


def bench_score(q10, q50, q90, y, valid):
    e = (q50 - y)[valid]
    yt = y[valid]
    nz = yt > 1e-4
    out = {"MAE": float(np.abs(e).mean()), "RMSE": float(np.sqrt((e ** 2).mean())),
           "MAPE": float((np.abs(e[nz]) / yt[nz]).mean() * 100) if nz.any() else None,
           "per_horizon_MAE": [float(np.abs((q50[:, h] - y[:, h])[valid[:, h]]).mean())
                               for h in range(y.shape[1])],
           "n_values": int(valid.sum())}
    if q10 is None:
        return out
    lo, hi = q10[valid], q90[valid]
    ql = 0.0
    for tau, q in zip(TAUS, (lo, q50[valid], hi)):
        d = yt - q
        ql += np.maximum(tau * d, (tau - 1) * d).mean()
    a = 0.2
    is80 = (hi - lo) + (2 / a) * np.maximum(lo - yt, 0) + (2 / a) * np.maximum(yt - hi, 0)
    out.update({"QL": float(ql / 3), "IS80": float(is80.mean()),
                "COV80": float(((yt >= lo) & (yt <= hi)).mean()), "WIDTH": float((hi - lo).mean())})
    return out
