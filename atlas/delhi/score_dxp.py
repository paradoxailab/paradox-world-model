"""Atlas v3, the data x size threshold function (rules: atlas/README.md, "Atlas v3", written before any of these runs).

Reads the run files of the D x P grid (seed 400, weather forcing, all 14 networks): W1 (1M, all data), W10 (10M, all
data) and dxp_<size>_f<share>_s400.npz, and uses validation MAE only (pooled trained stations, checkpoint E). For each
size P and data share f: E(f, P). The size gap g_P(f) = E(f, P) / E(f, 1M) - 1. The data-size interaction:
D_P = g_P(1/8) - g_P(1). The trend: g_P(n) = g0 + s * log2(n / n_all) by least squares over the four shares (n =
valid training windows), and the crossover n_x = n_all * 2^(-g_P(all) / s) where the trend reaches zero (only if
s < 0). Seed noise: sigma = relative standard deviation of validation MAE over W1 seeds 400-402; a parametric bootstrap
(each E perturbed by sigma, 10,000 draws) gives intervals for s and n_x / n_all.

  python score_dxp.py
"""
import json, os, sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
import run_atlas_delhi as R
from score_india import found

OUT = R.OUT
SIZES = {"1m": 1_000_000, "3m": 3_000_000, "10m": 9_990_000}


def log(*a):
    print(*a, flush=True)


def meta(f):
    return json.loads(str(np.load(f)["meta"]))


def main():
    runs = {}                                                  # (size key, share) -> meta
    for key, tag in (("1m", "w1"), ("10m", "w10")):
        for f in found(f"{tag}_s400.npz"):
            runs[(key, 1.0)] = meta(f)
    for f in found("dxp_*_s400.npz"):
        m = meta(f); b = os.path.basename(f)
        key = b.split("_")[1]
        runs[(key, float(m.get("frac") or 1.0))] = m
    w1 = {int(meta(f)["seed"]): meta(f)["E"]["val_MAE"] for f in found("w1_s40[0-2].npz")}
    assert len(w1) == 3, f"needs W1 seeds 400-402 for the seed noise (found {sorted(w1)})"
    v = np.array(list(w1.values()))
    sigma = float(v.std(ddof=1) / v.mean())
    shares = sorted({f for (_, f) in runs})
    res = {"sigma_rel": sigma, "W1_seeds": w1, "E": {}, "windows": {}, "gap": {}, "trend": {}, "rule": {}}
    for (k, f), m in sorted(runs.items()):
        res["E"][f"{k}@{f:g}"] = m["E"]["val_MAE"]
        res["windows"][f"{f:g}"] = int(sum(m["train_windows"]))
        log(f"E {k:>3} share {f:<6g} params {m['params']:>9,} windows {sum(m['train_windows']):>7,} val MAE {m['E']['val_MAE']:.3f} "
            f"(best at step {m['E']['steps']})")
    n_all = res["windows"]["1"]
    rng = np.random.default_rng(0)
    for k in ("3m", "10m"):
        fs = [f for f in shares if (k, f) in runs and ("1m", f) in runs]
        if len(fs) < 2:
            continue
        E1 = np.array([runs[("1m", f)]["E"]["val_MAE"] for f in fs]); EP = np.array([runs[(k, f)]["E"]["val_MAE"] for f in fs])
        x = np.log2(np.array([res["windows"][f"{f:g}"] for f in fs]) / n_all)
        g = EP / E1 - 1
        res["gap"][k] = {f"{f:g}": float(gi) for f, gi in zip(fs, g)}

        def fit(gg):
            s, g0 = np.polyfit(x, gg, 1)
            gall = gg[fs.index(1.0)] if 1.0 in fs else g0
            nx = 2 ** (-gall / s) if s < 0 else np.inf
            return s, nx
        s, nx = fit(g)
        B = []
        for _ in range(10000):
            gg = (EP * (1 + sigma * rng.standard_normal(len(fs)))) / (E1 * (1 + sigma * rng.standard_normal(len(fs)))) - 1
            B.append(fit(gg))
        B = np.array(B)
        fin = np.isfinite(B[:, 1])
        res["trend"][k] = dict(slope_per_doubling=float(s), slope_ci90=[float(x_) for x_ in np.percentile(B[:, 0], [5, 95])],
                               crossover_x_current=float(nx), crossover_ci90=([float(x_) for x_ in np.percentile(B[fin, 1], [5, 95])]
                                                                             if fin.mean() > 0.9 else None),
                               share_draws_with_crossover=float(fin.mean()))
        if 0.125 in fs and 1.0 in fs:
            D = float(g[fs.index(0.125)] - g[fs.index(1.0)])
            res["rule"][f"interaction {k}"] = dict(D=D, bar=4 * sigma, verdict="CONFIRMED" if D > 4 * sigma else "not confirmed")
        log(f"GAP {k} vs 1M by share: " + ", ".join(f"{f:g}: {100 * gi:+.2f}%" for f, gi in zip(fs, g)))
        t = res["trend"][k]
        log(f"TREND {k}: {100 * s:+.2f} points per doubling of data (90% {100 * t['slope_ci90'][0]:+.2f} .. {100 * t['slope_ci90'][1]:+.2f}); "
            f"crossover at {nx:.3g} x current data" + (f" (90% {t['crossover_ci90'][0]:.3g} .. {t['crossover_ci90'][1]:.3g})" if t["crossover_ci90"] else
                                                       f" (finite in {100 * t['share_draws_with_crossover']:.0f}% of draws)"))
    log(f"seed noise: relative sd of W1 validation MAE {100 * sigma:.2f}% (seeds {sorted(w1)})")
    log("DXP-RULE " + json.dumps(res["rule"], default=float))
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "dxp_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
