"""Paired comparison of two models scored by score_tsfm_w5k.py on the same WEATHER-5K windows.

For each variable: MAE of both on the windows both scored, the difference, a station-block bootstrap (stations resampled
with replacement; neighbouring hours of one station are not independent) and a Diebold-Mariano test on the daily mean
loss difference with a Newey-West variance. Holm's correction over every (opponent, variable) pair reported together.

  python paired_w5k.py --year val --ours atlas10m --vs tfm25,tfm3,chronos2,chronos-bolt
"""
import argparse, json, math, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
NAMES = ["Temperature", "Dewpoint", "Wind direction", "Wind speed", "Sea-level pressure"]
OUT = os.environ.get("ATLAS_OUT", "/kaggle/working/out")


def norm_sf(z):
    return 0.5 * math.erfc(z / math.sqrt(2))


def dm(d):
    """Diebold-Mariano on a series of loss differences d [T] (two-sided p), Newey-West lags = T^(1/3)."""
    d = d[np.isfinite(d)]; T = len(d)
    if T < 10:
        return float("nan")
    u = d - d.mean(); lag = int(round(T ** (1 / 3)))
    v = (u @ u) / T + 2 * sum((1 - k / (lag + 1)) * (u[k:] @ u[:-k]) / T for k in range(1, lag + 1))
    return 2 * norm_sf(abs(d.mean()) / math.sqrt(max(v, 1e-30) / T))


def compare(a, b, B=10000, seed=0):
    """a, b: dicts with sae [S, O, 5], cnt [S, O, 5]. Returns per-variable rows."""
    rng = np.random.default_rng(seed)
    both = (a["cnt"] > 0) & (b["cnt"] > 0)
    rows = []
    S = a["sae"].shape[0]
    idx = rng.integers(0, S, size=(B, S))
    for v, n in enumerate(NAMES):
        m = both[..., v]
        c = np.where(m, a["cnt"][..., v], 0).astype(np.float64)
        sa, sb = np.where(m, a["sae"][..., v], 0).astype(np.float64), np.where(m, b["sae"][..., v], 0).astype(np.float64)
        ca = c.sum(1); A = sa.sum(1); Bs = sb.sum(1)                        # per station
        mae_a, mae_b = A.sum() / ca.sum(), Bs.sum() / ca.sum()
        boot = (A[idx].sum(1) - Bs[idx].sum(1)) / ca[idx].sum(1)          # MAE_a - MAE_b, resampled stations
        p_boot = min(1.0, 2 * min((boot >= 0).mean(), (boot <= 0).mean()) + 1 / B)
        day = (sa - sb).sum(0) / np.maximum(c.sum(0), 1)                   # daily mean difference over stations
        rows.append(dict(variable=n, ours=round(mae_a, 4), theirs=round(mae_b, 4), diff_pct=round(100 * (mae_a / mae_b - 1), 2),
                         ci95_pct=[round(100 * np.quantile(boot, 0.025) / mae_b, 2), round(100 * np.quantile(boot, 0.975) / mae_b, 2)],
                         p_bootstrap=float(p_boot), p_dm=float(dm(day[c.sum(0) > 0])), points=int(ca.sum())))
    return rows


def holm(ps):
    order = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (m - r) * ps[i])); adj[i] = run
    return adj


def main(a):
    d = os.path.join(OUT, a.h2h_dir)
    load = lambda k: dict(np.load(os.path.join(d, f"{k}_{a.year}.npz")))
    ours = load(a.ours); res = {}
    allrows = []
    for k in a.vs.split(","):
        rows = compare(ours, load(k), a.B)
        res[k] = rows; allrows += [(k, r) for r in rows]
    adj = holm(np.array([max(r["p_bootstrap"], r["p_dm"] if np.isfinite(r["p_dm"]) else 1) for _, r in allrows]))
    for (k, r), p in zip(allrows, adj):
        r["p_holm"] = float(p)
        r["verdict"] = ("WIN" if r["diff_pct"] < 0 else "LOSS") if p < a.alpha else "TIE"
    for k in res:
        wins = sum(r["verdict"] == "WIN" for r in res[k])
        print(f"\n{a.ours} vs {k} ({a.year}; Holm over {len(allrows)} pairs): {wins}/5 significant wins" + ("  -> FULLY BEATS" if wins == 5 else ""))
        for r in res[k]:
            print(f"  {r['variable']:<19} ours {r['ours']:>8} theirs {r['theirs']:>8}  {r['diff_pct']:+6.2f}% "
                  f"[{r['ci95_pct'][0]:+.2f}, {r['ci95_pct'][1]:+.2f}]  p_holm {r['p_holm']:.2g}  {r['verdict']}")
    json.dump(res, open(os.path.join(d, f"paired_{a.ours}_{a.year}{a.suffix}.json"), "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", default="val"); ap.add_argument("--ours", default="atlas10m")
    ap.add_argument("--vs", default="tfm25,tfm3,chronos2,chronos-bolt")
    ap.add_argument("--B", type=int, default=10000); ap.add_argument("--alpha", type=float, default=0.01)
    ap.add_argument("--suffix", default="", help="added to the output name (a new comparison family keeps earlier files)")
    ap.add_argument("--h2h-dir", dest="h2h_dir", default="h2h")
    main(ap.parse_args())
