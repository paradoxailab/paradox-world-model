"""Atlas-100M on the all-India PM2.5 league (rules: atlas/m100/PREREG.md). Test windows are read once.

Same networks, stations, windows, tracks and truth as papers 3 and 4 (atlas/delhi/run_atlas_india.py, unchanged):
14 networks, 263 stations, test 2022-10-01 .. 2023-03-31 every 6 h, next 24 h of PM2.5. Track S = stations trained on,
Track U = stations never trained on (forecast from the whole network's graph). Point metric: MAE of the median, ug/m3.

Entries: Atlas-100M (aq view), Atlas-India v1.0 (paper 3's released weights, re-forecast with the same code), the two
harness baselines (last observed value, same hour yesterday), and every zero-shot foundation model whose
india_opp_<key>.npz (atlas/delhi/india_opponents.py) is in OUT. Paired tests per track: Diebold-Mariano on the daily
mean loss difference (Newey-West) and a station-block bootstrap (10,000); Holm over the whole family; a WIN needs
p_holm < 0.01 for both tests' maximum and a 95% interval excluding 0.

  python atlas/m100/score_aq.py --view $OUT/atlas100m_aq_view.pt --india-v1 40_atlas_india_v1.0.pt
"""
import argparse, glob, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from m100 import domains as Dm
from atlas.grow import load_any
import paired_w5k as PW                   # dm() and holm(): the same tests as the weather comparisons

SPD = 24


def errors(fc, nets, O, R):
    """Per network: absolute error of the median [W, N, H] on test windows (NaN where truth missing)."""
    out = {}
    for D, (tr, va4, te) in zip(nets, O):
        out[D.name] = np.abs(fc[D.name][..., 1] - R.truth(D, te, np.arange(D.N)))
    return out


def by_station_day(err, nets, O, track):
    """sae, cnt [stations, days] over the chosen track's stations of every network (days = test days)."""
    S, C = [], []
    for D, (tr, va4, te) in zip(nets, O):
        nodes = D.seen if track == "S" else D.unseen
        if len(nodes) == 0:
            continue
        e = err[D.name][:, nodes]                                         # [W, n, H]
        day = (te - te[0]) // SPD
        nd = int(day.max()) + 1
        sae = np.zeros((len(nodes), nd)); cnt = np.zeros((len(nodes), nd))
        ok = np.isfinite(e)
        np.add.at(sae.T, day, np.where(ok, e, 0).sum(2))
        np.add.at(cnt.T, day, ok.sum(2))
        S.append(sae); C.append(cnt)
    nd = max(s.shape[1] for s in S)
    pad = lambda x: np.pad(x, ((0, 0), (0, nd - x.shape[1])))
    return np.concatenate([pad(s) for s in S]), np.concatenate([pad(c) for c in C])


def compare(sa, sb, c, B=10000, seed=0):
    rng = np.random.default_rng(seed)
    A, Bs, ca = sa.sum(1), sb.sum(1), c.sum(1)
    mae_a, mae_b = A.sum() / ca.sum(), Bs.sum() / ca.sum()
    idx = rng.integers(0, len(A), size=(B, len(A)))
    boot = (A[idx].sum(1) - Bs[idx].sum(1)) / ca[idx].sum(1)
    p_boot = min(1.0, 2 * min((boot >= 0).mean(), (boot <= 0).mean()) + 1 / B)
    day = (sa - sb).sum(0) / np.maximum(c.sum(0), 1)
    return dict(ours=round(float(mae_a), 3), theirs=round(float(mae_b), 3), diff_pct=round(float(100 * (mae_a / mae_b - 1)), 2),
                ci95_pct=[round(float(100 * np.quantile(boot, q) / mae_b), 2) for q in (0.025, 0.975)],
                p_bootstrap=float(p_boot), p_dm=float(PW.dm(day[c.sum(0) > 0])), points=int(ca.sum()))


def main(a):
    import run_atlas_delhi as R
    import run_atlas_india as RI
    import score_india as SI
    nets = RI.networks(a.quick)
    O = [RI.origins(D, a.quick) for D in nets]
    entries = {}
    view = load_any(a.view, Dm.DEV).to(Dm.DEV).eval()
    f = RI.forecasts(view, nets, O)
    entries["Atlas-100M"] = {D.name: f[(D.name, "t")] for D in nets}
    del view
    if a.india_v1 and os.path.exists(a.india_v1):
        m = load_any(a.india_v1, Dm.DEV).to(Dm.DEV).eval()
        f = RI.forecasts(m, nets, O)
        entries["Atlas-India v1.0 (paper 3)"] = {D.name: f[(D.name, "t")] for D in nets}
        del m
    for kind, nm in (("last", "last observed value"), ("yesterday", "same hour yesterday")):
        try:
            entries[nm] = {D.name: SI.baseline(D, kind, te, np.arange(D.N)) for D, (tr, va4, te) in zip(nets, O)}
        except Exception as e:                                           # the harness names its baselines itself
            print(f"baseline {kind}: {type(e).__name__}: {e}", flush=True)
    for fo in sorted(glob.glob(os.path.join(a.opp_dir, "india_opp_*.npz"))):
        z = np.load(fo)
        nm = str(z["name"])
        entries[nm] = {D.name: z[f"{D.name}|qt"] for D in nets}
    err = {k: errors(v, nets, O, R) for k, v in entries.items()}
    res = {"entries": {}, "tests": []}
    for k, e in err.items():
        row = {}
        for tr in ("S", "U"):
            s, c = by_station_day(e, nets, O, tr)
            row[f"MAE_{tr}"] = float(s.sum() / c.sum())
        row["per_network_S"] = {D.name: float(np.nanmean(e[D.name][:, D.seen])) for D in nets}
        res["entries"][k] = row
        print(f"{k:<44} trained stations {row['MAE_S']:.2f}  never-trained {row['MAE_U']:.2f}", flush=True)
    ours = err["Atlas-100M"]
    for tr in ("S", "U"):
        sa, c = by_station_day(ours, nets, O, tr)
        for k, e in err.items():
            if k == "Atlas-100M":
                continue
            sb, cb = by_station_day(e, nets, O, tr)
            assert np.array_equal(c, cb), f"{k}: not the same scored cells"
            r = compare(sa, sb, c); r.update(track=tr, opponent=k)
            res["tests"].append(r)
    if res["tests"]:
        p = np.array([max(1.0 if np.isnan(r["p_dm"]) else r["p_dm"], r["p_bootstrap"]) for r in res["tests"]])
        for r, ph in zip(res["tests"], PW.holm(p)):
            r["p_holm"] = float(ph)
            ci_ok = r["ci95_pct"][1] < 0 if r["diff_pct"] < 0 else r["ci95_pct"][0] > 0
            r["verdict"] = ("WIN" if r["diff_pct"] < 0 else "LOSS") if (ph < 0.01 and ci_ok) else "TIE"
            print(f"TEST track {r['track']} vs {r['opponent'][:40]:<40} {r['ours']:.2f} vs {r['theirs']:.2f} {r['diff_pct']:+.2f}% "
                  f"[{r['ci95_pct'][0]:+.2f}, {r['ci95_pct'][1]:+.2f}] p_holm {r['p_holm']:.2g} {r['verdict']}", flush=True)
    os.makedirs(a.out, exist_ok=True)
    json.dump(res, open(os.path.join(a.out, "atlas100m_aq_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--view", required=True)
    ap.add_argument("--india-v1", default="")
    ap.add_argument("--opp-dir", default=os.environ.get("ATLAS_OUT", "out"))
    ap.add_argument("--out", default=os.environ.get("ATLAS_OUT", "out"))
    ap.add_argument("--quick", action="store_true")
    main(ap.parse_args())
