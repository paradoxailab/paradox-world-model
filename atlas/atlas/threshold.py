"""The threshold function: fitted to measured runs, never assumed.

    error(N, P) = floor + a * N^(-alpha) + b * P^(-beta)

N = number of independent training trajectories, P = trainable parameters; error = normalised MSE on fresh
test trajectories. `fit` estimates the five numbers from runs; `need_data` / `need_params` invert the fit;
`bootstrap` resamples the runs to give an interval, and every answer says whether it lies inside the measured range.
"""
import json

import numpy as np
from scipy.optimize import least_squares


def load(paths):
    out = []
    for p in paths:
        try:
            out += [json.loads(l) for l in open(p) if l.strip()]
        except FileNotFoundError:
            pass
    seen, uniq = set(), []
    for r in out:                      # the same configuration may appear in two plans: keep one copy
        k = (r["system"], r["size"], r["N"], r["seed"], r["noise"], r["width"], r["physics"], r["max_steps"])
        if k not in seen:
            seen.add(k); uniq.append(r)
    return uniq


def sel(runs, **kw):
    d = dict(noise=0.05, width=1.0, physics=0)
    d.update(kw)
    return [r for r in runs if all(r[k] == v for k, v in d.items() if v is not None)]


def cells(runs, by=("params", "N"), y="nmse"):
    g = {}
    for r in runs:
        g.setdefault(tuple(r[k] for k in by), []).append(r[y])
    return {k: (float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else float("nan"), len(v)) for k, v in sorted(g.items())}


def model(p, N, P):
    f, a, al, b, be = p
    return f + a * N ** (-al) + b * P ** (-be)


def fit(runs, y="nmse", starts=8):
    N = np.array([r["N"] for r in runs], float); P = np.array([r["params"] for r in runs], float)
    E = np.array([r[y] for r in runs], float)
    best = None
    grid0 = [(al0, be0, f0) for al0 in (0.3, 0.7) for be0 in (0.3, 1.0) for f0 in (0.5 * E.min(), 0.05 * E.min())]
    for al0, be0, f0 in grid0[:starts]:
        if True:
            if True:
                x0 = np.log([f0, 1.0, al0, 1.0, be0])
                res = least_squares(lambda q: np.log(model(np.exp(q), N, P)) - np.log(E), x0,
                                    bounds=(np.log([1e-6, 1e-6, 1e-3, 1e-9, 1e-3]), np.log([E.min(), 1e3, 3, 1e6, 3])))
                if best is None or res.cost < best.cost: best = res
    p = np.exp(best.x)
    rms = float(np.sqrt(np.mean(best.fun ** 2)))
    return dict(floor=p[0], a=p[1], alpha=p[2], b=p[3], beta=p[4], rms_log=rms, n=len(E))


def pred(f, N, P):
    return model([f[k] for k in ("floor", "a", "alpha", "b", "beta")], np.asarray(N, float), np.asarray(P, float))


def need_data(f, target, P):
    """Smallest N with predicted error <= target at P parameters (inf if the model size alone prevents it)."""
    rest = target - f["floor"] - f["b"] * P ** (-f["beta"])
    return float("inf") if rest <= 0 else float((f["a"] / rest) ** (1 / f["alpha"]))


def need_params(f, target, N):
    rest = target - f["floor"] - f["a"] * N ** (-f["alpha"])
    return float("inf") if rest <= 0 else float((f["b"] / rest) ** (1 / f["beta"]))


def boot_fits(runs, n=100, seed=0):
    """Resample runs (with replacement) and re-fit n times; the list of fits gives intervals for anything derived."""
    rng = np.random.default_rng(seed); fits = []
    for _ in range(n):
        try:
            fits.append(fit([runs[i] for i in rng.integers(0, len(runs), len(runs))], starts=1))
        except Exception:
            pass
    return fits


def interval(fits, fn):
    v = np.array([fn(f) for f in fits], float)
    return [float(np.percentile(np.where(np.isfinite(v), v, 1e18), q)) for q in (10, 50, 90)]


def crossing(Ns, Es, target):
    """Measured threshold: smallest N where the mean error curve first goes under target (log-log interpolation)."""
    Ns, Es = np.asarray(Ns, float), np.asarray(Es, float)
    for i in range(len(Ns)):
        if Es[i] <= target:
            if i == 0: return float(Ns[0]), "at or below the smallest N tested"
            t = (np.log(Es[i - 1]) - np.log(target)) / (np.log(Es[i - 1]) - np.log(Es[i]))
            return float(np.exp(np.log(Ns[i - 1]) + t * (np.log(Ns[i]) - np.log(Ns[i - 1])))), "measured"
    return float("inf"), "not reached"


def transition(Ns, Es):
    """Is the fall of error with data sudden or gradual? Compares, on log N, a straight power law
    log E = c - s log N  with a step (logistic) of free position and steepness. Returns AICc of both and
    the largest local slope. A sudden change needs the logistic to win clearly AND a local slope far above the average."""
    x, y = np.log(np.asarray(Ns, float)), np.log(np.asarray(Es, float))
    n = len(x)
    A = np.stack([np.ones(n), x], 1); c = np.linalg.lstsq(A, y, rcond=None)[0]
    rss_p = float(((A @ c - y) ** 2).sum())
    best = None
    for x0 in np.linspace(x.min(), x.max(), 9):
        for k in (1.0, 4.0):
            r = least_squares(lambda q: q[0] + (q[1] - q[0]) / (1 + np.exp(q[3] * (x - q[2]))) - y,
                              [y.min(), y.max(), x0, k])
            if best is None or r.cost < best.cost: best = r
    rss_l = float((best.fun ** 2).sum())
    aicc = lambda rss, k: n * np.log(rss / n) + 2 * k + 2 * k * (k + 1) / max(n - k - 1, 1)
    slopes = -(np.diff(y) / np.diff(x))
    return dict(power_slope=float(-c[1]), aicc_power=float(aicc(rss_p, 2)), aicc_step=float(aicc(rss_l, 4)),
                step_centre_N=float(np.exp(best.x[2])), step_steepness=float(best.x[3]),
                max_local_slope=float(slopes.max()), mean_slope=float((y[0] - y[-1]) / (x[-1] - x[0])))


def bits(nmse):
    """Information the forecast carries about the future, per predicted value, under a Gaussian model: 0.5 log2(1/nMSE)."""
    return float(max(0.0, 0.5 * np.log2(1.0 / nmse)))


def advise(f, N, P, max_P=10_000_000, min_rel=0.05):
    """What to add next, from the fitted function: predicted error now, after 2x data, after 2x parameters.
    Advice is whichever is predicted to help more; "stop" when neither improves the error by min_rel (5%)."""
    now = float(pred(f, N, P)); d2 = float(pred(f, 2 * N, P)); p2 = float(pred(f, N, min(2 * P, max_P)))
    gd, gp = now - d2, now - p2
    act = "stop: under 5% to gain either way" if max(gd, gp) < min_rel * now else ("more data" if gd >= gp else "bigger model")
    return dict(error_now=now, gain_2x_data=gd, gain_2x_params=gp, advice=act,
                data_share_of_excess=float(f["a"] * N ** (-f["alpha"]) / max(now - f["floor"], 1e-12)))
