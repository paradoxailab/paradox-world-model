"""Post-hoc analyses of Atlas-F for the follow-up paper. NOT pre-registered: nothing here changes a recorded verdict
(README, "F results"); every number is reported as an analysis of the already-scored system.

On the same inputs and windows as score_v14.py --stage test --tag none (Atlas-India three seeds, TimesFM 2.5, all-India
test windows, every entry calibrated on each network's validation windows):

  A. Combination ablations. The fused forecast w*Atlas + (1-w)*TimesFM with w chosen by
       equal       w = 0.5 everywhere (the "forecast combination puzzle" baseline)
       static-1    one w for all networks and lead blocks, chosen on validation windows (trained stations)
       static-NB   one w per network and lead block, chosen on validation windows
       online-1B   online as Atlas-F (trailing 30 days) but one block for all 24 lead hours
       online-7/14/60  online as Atlas-F with a 7-, 14- or 60-day trailing window
       oracle-NB   one w per network and lead block chosen on the TEST windows (an upper bound, not a forecast)
     Pooled MAE/RMSE/QL/IS80/COV80 on both tracks; each against Atlas-F by Diebold-Mariano + day-block bootstrap.
  B. Lead-time curves: pooled MAE per lead hour (1-24) for Atlas-India, TimesFM 2.5 and Atlas-F, both tracks.
  C. Probabilistic quality of the three entries (QL, IS80, COV80 from pw/evaluate.score).
  D. Seed spread: each Atlas-India seed alone (calibrated the same way), pooled MAE both tracks.
  E. Weight paths: Atlas-F's daily weight per lead block for every network (for a figure).

  python analyze_f.py [--quick] [--reps 2000]
"""
import argparse, json, os, sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import FLOOR, SPD
from pw import evaluate as E
import run_atlas_delhi as R
import run_atlas_india as RI
import score_v14 as S

H, OUT = R.H, R.OUT
GRID = S.GRID
B3 = [(0, 6), (6, 12), (12, 24)]
B1 = [(0, 24)]


def log(*a):
    print(*a, flush=True)


def grid_err(qa, qb, y, idx, h0, h1):
    """Per window, MAE of the fused median for every grid weight: [W, G] (NaN where no truth)."""
    ya, yb, yt = qa[..., 1][:, idx, h0:h1], qb[..., 1][:, idx, h0:h1], y[:, idx, h0:h1]
    W = len(ya)
    return np.stack([np.nanmean(np.abs(w * ya + (1 - w) * yb - yt).reshape(W, -1), 1) for w in GRID], 1)


def grid_sum(qa, qb, y, idx, h0, h1):
    """Summed absolute error and cell count for every grid weight (for weights pooled across networks)."""
    ya, yb, yt = qa[..., 1][:, idx, h0:h1], qb[..., 1][:, idx, h0:h1], y[:, idx, h0:h1]
    m = np.isfinite(yt)
    return np.array([np.abs(w * ya + (1 - w) * yb - yt)[m].sum() for w in GRID]), int(m.sum())


def online(qa, qb, y, o, mte, seen, trail, blocks):
    W = len(o)
    ws = np.zeros((W, len(blocks)))
    day0 = (o // SPD) * SPD
    for b, (h0, h1) in enumerate(blocks):
        err = grid_err(qa, qb, y, seen, h0, h1)
        ok = np.isfinite(err).all(1)
        for i in np.where(mte)[0]:
            elig = ok & (o + H <= day0[i]) & (o >= day0[i] - trail * SPD)
            ws[i, b] = GRID[np.argmin(err[elig].mean(0))] if elig.any() else 0.5
    return ws


def fuse(qa, qb, ws, blocks):
    q = np.empty_like(qa)
    for b, (h0, h1) in enumerate(blocks):
        w = ws[:, b][:, None, None, None]
        q[:, :, h0:h1] = w * qa[:, :, h0:h1] + (1 - w) * qb[:, :, h0:h1]
    return np.sort(q, -1)


def lead_mae(q, y):
    e = np.abs(q[..., 1] - y)
    return [float(np.nanmean(e[:, :, h])) for h in range(y.shape[-1])]


def main(a):
    nets = RI.networks(a.quick)
    O = [RI.origins(D, a.quick) for D in nets]
    ref = S.load("india")
    opp = {}
    for f in S.found("india_opp_*.npz"):
        z = np.load(f); opp[str(z["name"])] = z
    tfm = next((k for k in opp if k.startswith("TimesFM 2.5")), None)
    assert tfm and len(ref) == 3, "needs TimesFM 2.5 forecasts and the three Atlas-India seeds"
    seeds = sorted(ref)
    ens = lambda net, nm: np.sort(np.mean([ref[s][0][f"{net}|E_{nm}"] for s in seeds], 0), -1)
    # per network: calibrated members on validation and test, and the pieces every variant needs
    NV = []
    for D, (tr, va4, te) in zip(nets, O):
        ALL = np.arange(D.N)
        yv, yt = R.truth(D, va4, ALL), R.truth(D, te, ALL)
        raw = {"india": (ens(D.name, "v4"), ens(D.name, "t")), "tfm": (opp[tfm][f"{D.name}|qv"], opp[tfm][f"{D.name}|qt"])}
        for s in seeds:
            raw[f"seed{s}"] = (np.sort(ref[s][0][f"{D.name}|E_v4"], -1), np.sort(ref[s][0][f"{D.name}|E_t"], -1))
        cal = {}
        for k, (qv, qt) in raw.items():
            d = E.fit_cqr(np.sort(qv, -1)[:, D.seen], yv[:, D.seen])
            cal[k] = (E.apply_cqr(np.sort(qv, -1), d), E.apply_cqr(np.sort(qt, -1), d))
        qa = np.concatenate([cal["india"][0], cal["india"][1]]); qb = np.concatenate([cal["tfm"][0], cal["tfm"][1]])
        yy = np.concatenate([yv, yt]); oo = np.concatenate([va4, te])
        mte = np.r_[np.zeros(len(va4), bool), np.ones(len(te), bool)]
        NV.append(dict(D=D, cal=cal, qa=qa, qb=qb, y=yy, o=oo, mte=mte, yt=yt, nv=len(va4)))
        log(f"loaded {D.name}: {len(va4)} validation and {len(te)} test windows, {D.N} stations")
    # weights shared across networks (static-1): pooled validation error per grid weight
    tot, cnt = np.zeros(len(GRID)), 0
    for n in NV:
        s_, c_ = grid_sum(n["qa"][~n["mte"]], n["qb"][~n["mte"]], n["y"][~n["mte"]], n["D"].seen, 0, H)
        tot += s_; cnt += c_
    w_glob = float(GRID[np.argmin(tot / max(cnt, 1))])
    log(f"static-1: one weight for all networks and lead blocks, chosen on validation: w = {w_glob}")
    variants = ["Atlas-F", "equal", "static-1", "static-NB", "online-1B", "online-7", "online-14", "online-60", "oracle-NB"]
    P = {k: [] for k in ["india", "tfm"] + [f"seed{s}" for s in seeds] + variants}
    Y, paths, wsum = [], {}, {k: {} for k in variants}
    for n in NV:
        D, qa, qb, y, o, mte = n["D"], n["qa"], n["qb"], n["y"], n["o"], n["mte"]
        Y.append(n["yt"])
        for k in ["india", "tfm"] + [f"seed{s}" for s in seeds]:
            P[k].append(n["cal"][k][1])
        W = len(o)
        WS = {}
        WS["Atlas-F"] = (online(qa, qb, y, o, mte, D.seen, 30, B3), B3)
        WS["equal"] = (np.full((W, 3), 0.5), B3)
        WS["static-1"] = (np.full((W, 3), w_glob), B3)
        st = [float(GRID[np.nanargmin(np.nanmean(grid_err(qa[~mte], qb[~mte], y[~mte], D.seen, h0, h1), 0))]) for h0, h1 in B3]
        WS["static-NB"] = (np.tile(st, (W, 1)), B3)
        WS["online-1B"] = (online(qa, qb, y, o, mte, D.seen, 30, B1), B1)
        for t in (7, 14, 60):
            WS[f"online-{t}"] = (online(qa, qb, y, o, mte, D.seen, t, B3), B3)
        orc = [float(GRID[np.nanargmin(np.nanmean(grid_err(qa[mte], qb[mte], y[mte], D.seen, h0, h1), 0))]) for h0, h1 in B3]
        WS["oracle-NB"] = (np.tile(orc, (W, 1)), B3)
        for k, (ws, bl) in WS.items():
            P[k].append(fuse(qa, qb, ws, bl)[mte])
            wsum[k][D.name] = [float(x) for x in ws[mte].mean(0)]
        wf = WS["Atlas-F"][0][mte]
        day = (o[mte] // SPD)
        paths[D.name] = {"day_hours": [int(d * SPD) for d in np.unique(day)],
                         "w": [[float(x) for x in wf[day == d][0]] for d in np.unique(day)]}
        log(f"weights {D.name}: " + json.dumps({k: [round(x, 2) for x in v[D.name]] for k, v in wsum.items()}))
    cat = lambda arrs, which: np.concatenate([x[:, getattr(D, which)] for x, D in zip(arrs, nets)], 1)
    yS, yU = cat(Y, "seen"), cat(Y, "unseen")
    sc = lambda q, y: E.score(q, y, horizons=R.HZ, floor=FLOOR["PM2.5"], step_min=60)
    PP = {k: (cat(v, "seen"), cat(v, "unseen")) for k, v in P.items()}
    res = {"note": "post-hoc analyses, not pre-registered", "static_1_weight": w_glob, "pooled": {}, "vs_AtlasF": {},
           "lead_MAE": {}, "weights_mean": wsum, "weight_paths": paths, "seeds": seeds}
    for k, (s, u) in PP.items():
        res["pooled"][k] = {"S": sc(s, yS), "U": sc(u, yU)}
        r = res["pooled"][k]
        log(f"POOLED {k}: S MAE {r['S']['MAE']:.3f} RMSE {r['S']['RMSE']:.2f} QL {r['S']['QL']:.3f} IS80 {r['S']['IS80']:.2f} "
            f"COV80 {r['S']['COV80']:.1f} | U MAE {r['U']['MAE']:.3f} RMSE {r['U']['RMSE']:.2f} QL {r['U']['QL']:.3f} "
            f"IS80 {r['U']['IS80']:.2f} COV80 {r['U']['COV80']:.1f}")
    for k in variants[1:] + ["india", "tfm"]:
        r = {t: E.compare(PP["Atlas-F"][i], PP[k][i], yy, R.PER_DAY, "MAE", reps=a.reps, floor=FLOOR["PM2.5"])
             for i, (t, yy) in enumerate((("S", yS), ("U", yU)))}
        res["vs_AtlasF"][k] = {t: dict(rel=r[t]["rel_diff_pct"], ci=r[t]["ci95_pct"], p=r[t]["p"], v=r[t]["verdict"]) for t in r}
        log(f"SIG Atlas-F vs {k}: S {r['S']['rel_diff_pct']:+.2f}% p={r['S']['p']:.2g} {r['S']['verdict']}; "
            f"U {r['U']['rel_diff_pct']:+.2f}% p={r['U']['p']:.2g} {r['U']['verdict']}")
    for k in ("india", "tfm", "Atlas-F", "equal"):
        res["lead_MAE"][k] = {"S": lead_mae(PP[k][0], yS), "U": lead_mae(PP[k][1], yU)}
        log(f"LEAD {k}: S " + " ".join(f"{x:.2f}" for x in res["lead_MAE"][k]["S"]) +
            " | U " + " ".join(f"{x:.2f}" for x in res["lead_MAE"][k]["U"]))
    sm = np.array([[res["pooled"][f"seed{s}"][t]["MAE"] for t in ("S", "U")] for s in seeds])
    res["seed_spread"] = {"mean": sm.mean(0).tolist(), "std": sm.std(0, ddof=1).tolist(), "per_seed": sm.tolist()}
    log(f"SEEDS Atlas-India single seeds {seeds}: S {sm[:, 0].round(3).tolist()} U {sm[:, 1].round(3).tolist()}; "
        f"mean {sm.mean(0).round(3).tolist()} sd {sm.std(0, ddof=1).round(3).tolist()}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "analysis_f.json"), "w"), indent=1, default=float)
    log("ANALYSIS-DONE")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--reps", type=int, default=2000)
    main(ap.parse_args())
