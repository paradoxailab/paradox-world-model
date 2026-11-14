"""ICML programme, T1: the transfer threshold function (rules: atlas/README.md, written before any score).

For each of the four leave-one-network-out networks X and each data budget B (the most recent B months of X's
training data), two arms were run (kaggle_threshold.sh): Atlas pre-trained on the other 13 networks then adapted on
the budget ("pre"; B = 0 is the pre-trained model as it is), and Atlas trained on the budget alone from random weights
("scratch"). Every single model is calibrated on X's validation windows (CQR, as in the league) and scored on X's
test windows; TimesFM 2.5's forecasts of the same windows (atlas-india-opp-gpu v2) are calibrated the same way.

Measured:
  r = MAE / TimesFM 2.5's MAE (trained stations, Track S; unseen stations, Track U, reported), mean over seeds;
  n* = the smallest budget with r <= 1 (TimesFM 2.5's level), per network and arm;
  the scratch law, r = c_X + a * n^-alpha (n = valid training windows; floor c_X per network, a and alpha shared);
  the effective data transferred by pre-training, D_T(n) = n_eq - n, where the scratch law reaches the pre-trained
  arm's r at n_eq windows, and the transfer law D_T = k * n^gamma fitted to it.
The rule (T1) is applied at the end.

  python score_threshold.py
"""
import argparse, json, os, re, sys

import numpy as np
from scipy.optimize import least_squares

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import FLOOR
from pw import evaluate as E
import run_atlas_delhi as R
import run_atlas_india as RI
from score_india import found

TARGETS = ["Uttar Pradesh", "Haryana", "Maharashtra", "Karnataka"]
ARMS = ("pre", "scratch")
slug = lambda k: re.sub(r"[^a-z0-9]+", "_", k.lower())
bkey = lambda b: float("inf") if b == "all" else float(b)


def log(*a):
    print(*a, flush=True)


def scratch_law(rows):
    """r = c_X + a n^-alpha, fitted in log space; c_X per network, a and alpha shared."""
    nets = sorted({r["net"] for r in rows})
    n = np.array([r["n"] for r in rows], float); y = np.array([r["rS"] for r in rows], float)
    ix = np.array([nets.index(r["net"]) for r in rows])

    def f(q):
        c = np.exp(q[:len(nets)]); a, al = np.exp(q[len(nets)]), np.exp(q[len(nets) + 1])
        return c[ix] + a * n ** (-al)
    best = None
    for al0 in (0.1, 0.3, 0.7):
        for c0 in (0.6, 0.9):
            x0 = np.log([c0] * len(nets) + [1.0, al0])
            res = least_squares(lambda q: np.log(f(q)) - np.log(y), x0,
                                bounds=(np.log([1e-3] * len(nets) + [1e-6, 1e-3]), np.log([5] * len(nets) + [1e4, 3])))
            if best is None or res.cost < best.cost:
                best = res
    q = best.x
    return dict(c={k: float(np.exp(q[i])) for i, k in enumerate(nets)}, a=float(np.exp(q[len(nets)])),
                alpha=float(np.exp(q[len(nets) + 1])), rms_log=float(np.sqrt(np.mean(best.fun ** 2))), n=len(y))


def n_equiv(law, net, r):
    c = law["c"].get(net)
    if c is None:
        return float("nan")
    return float("inf") if r <= c else float((law["a"] / (r - c)) ** (1 / law["alpha"]))


def main(a):
    global TARGETS
    if a.targets:
        TARGETS = [t.strip() for t in a.targets.split(",")]
    nets = {D.name: D for D in RI.networks(a.quick)}
    opp = {}
    for f in found("india_opp_*.npz"):
        z = np.load(f); opp[str(z["name"])] = z
    tfm = next((k for k in opp if k.startswith("TimesFM 2.5")), None)
    assert tfm, f"TimesFM 2.5 forecasts not attached (found {list(opp)})"
    sc = lambda q, y, idx: E.score(q[:, idx], y[:, idx], horizons=R.HZ, floor=FLOOR["PM2.5"], step_min=60)
    rows, table, sig = [], {}, {}
    for X in TARGETS:
        if X not in nets:
            continue
        D = nets[X]; tr, va4, te = RI.origins(D, a.quick)
        ALL = np.arange(D.N)
        yv, yt = R.truth(D, va4, ALL), R.truth(D, te, ALL)
        cal = lambda qv, qt: E.apply_cqr(np.sort(qt, -1), E.fit_cqr(np.sort(qv, -1)[:, D.seen], yv[:, D.seen]))
        T = cal(opp[tfm][f"{X}|qv"], opp[tfm][f"{X}|qt"])
        base = {t: sc(T, yt, idx)["MAE"] for t, idx in (("S", D.seen), ("U", D.unseen))}
        table[X] = {"TimesFM 2.5": base, "pre": {}, "scratch": {}}
        sig[X] = {"pre": {}, "scratch": {}}
        for arm in ARMS:
            budgets = {}
            for f in found(f"thr_{slug(X)}_{arm}_b*_s*.npz"):
                b = re.search(r"_b([0-9.]+|all)_s\d+\.npz$", f).group(1)
                budgets.setdefault(b, []).append(f)
            for b in sorted(budgets, key=bkey):
                Z = [np.load(f) for f in budgets[b]]
                metas = [json.loads(str(z["meta"])) for z in Z]
                P = [cal(z[f"{X}|E_v4"], z[f"{X}|E_t"]) for z in Z]
                mS = float(np.mean([sc(p, yt, D.seen)["MAE"] for p in P]))
                mU = float(np.mean([sc(p, yt, D.unseen)["MAE"] for p in P]))
                n = int(metas[0]["train_windows"][0])
                row = dict(net=X, arm=arm, budget=b, n=n, seeds=[m["seed"] for m in metas], MAE_S=mS, MAE_U=mU,
                           rS=mS / base["S"], rU=mU / base["U"], steps=[m["E"]["steps"] for m in metas],
                           since=metas[0].get("avail_from"))
                ens = cal(np.mean([z[f"{X}|E_v4"] for z in Z], 0), np.mean([z[f"{X}|E_t"] for z in Z], 0))
                c = {t: E.compare(ens[:, idx], T[:, idx], yt[:, idx], R.PER_DAY, "MAE", reps=a.reps, floor=FLOOR["PM2.5"])
                     for t, idx in (("S", D.seen), ("U", D.unseen))}
                row["vs_tfm_ensemble"] = {t: dict(verdict=c[t]["verdict"], rel=c[t]["rel_diff_pct"], p=c[t]["p"]) for t in c}
                rows.append(row); table[X][arm][b] = row
                log(f"T1 {X} {arm} B={b}: {n} windows, MAE {mS:.2f} / {mU:.2f} (TimesFM 2.5 {base['S']:.2f} / {base['U']:.2f}), "
                    f"r = {row['rS']:.3f} / {row['rU']:.3f}; {len(Z)}-seed ensemble vs TimesFM 2.5: S {c['S']['verdict']} "
                    f"{c['S']['rel_diff_pct']:+.1f}%, U {c['U']['verdict']} {c['U']['rel_diff_pct']:+.1f}%")
    # n*: the smallest budget at TimesFM 2.5's level (r <= 1, Track S)
    nstar = {}
    for X in table:
        nstar[X] = {}
        for arm in ARMS:
            hit = [b for b in sorted(table[X][arm], key=bkey) if table[X][arm][b]["rS"] <= 1.0]
            nstar[X][arm] = hit[0] if hit else None
    # the scratch law and the effective data transferred
    srows = [r for r in rows if r["arm"] == "scratch" and r["n"] > 0]
    law = scratch_law(srows) if len({r["net"] for r in srows}) >= 2 and len(srows) >= 6 else None
    trans, tlaw = [], None
    if law:
        for r in rows:
            if r["arm"] == "pre":
                ne = n_equiv(law, r["net"], r["rS"])
                trans.append(dict(net=r["net"], budget=r["budget"], n=r["n"], n_eq=ne, D_T=ne - r["n"]))
        ok = [t for t in trans if t["n"] > 0 and np.isfinite(t["D_T"]) and t["D_T"] > 0]
        if len(ok) >= 4:
            g, k = np.polyfit(np.log([t["n"] for t in ok]), np.log([t["D_T"] for t in ok]), 1)
            tlaw = dict(k=float(np.exp(k)), gamma=float(g), points=len(ok),
                        infinite=sum(1 for t in trans if not np.isfinite(t["D_T"])))
    # rule T1
    support = [X for X in nstar if nstar[X]["pre"] is not None and
               (nstar[X]["scratch"] is None or bkey(nstar[X]["pre"]) < bkey(nstar[X]["scratch"]))]
    done = [X for X in nstar if table[X]["pre"] and table[X]["scratch"]]
    rule = None
    if len(done) == len(TARGETS):
        rule = "CONFIRMED" if len(support) >= 3 else "NOT CONFIRMED"
    out = dict(table=table, nstar=nstar, scratch_law=law, transfer=trans, transfer_law=tlaw, support=support,
               scored=done, rule=rule, rule_text="confirmed if pre-training lowers n* (the smallest budget at TimesFM "
               "2.5's level on trained stations) on at least 3 of the 4 networks; a network where neither arm reaches it "
               "does not count as support")
    log("T1-NSTAR " + json.dumps(nstar))
    log("T1-SCRATCH-LAW " + json.dumps(law))
    log("T1-TRANSFER-LAW " + json.dumps(tlaw))
    log("T1-RULE " + json.dumps({"support": support, "scored": done, "rule": rule}))
    os.makedirs(R.OUT, exist_ok=True)
    json.dump(out, open(os.path.join(R.OUT, "threshold_t1_results.json"), "w"), indent=1, default=float)
    o = ["# ICML T1: the transfer threshold function (generated)", "",
         "r = calibrated test MAE / TimesFM 2.5's, trained stations (unseen in brackets); mean over seeds.", ""]
    bs = sorted({r["budget"] for r in rows}, key=bkey)
    o += ["| Network | arm | " + " | ".join(f"{b} mo" if b != "all" else "all" for b in bs) + " | n* |",
          "|---|---|" + "---|" * (len(bs) + 1)]
    for X in table:
        for arm in ARMS:
            cells = [f"{table[X][arm][b]['rS']:.3f} ({table[X][arm][b]['rU']:.3f})" if b in table[X][arm] else "–" for b in bs]
            o.append(f"| {X} | {arm} | " + " | ".join(cells) + f" | {nstar[X][arm] or 'not reached'} |")
    if law:
        o += ["", f"Scratch law: r = c_X + {law['a']:.3g} n^-{law['alpha']:.3f} (misfit x{np.exp(law['rms_log']):.3f}); "
              + ", ".join(f"c[{k}] = {v:.3f}" for k, v in law["c"].items())]
    if tlaw:
        o += [f"Transfer law: D_T = {tlaw['k']:.3g} n^{tlaw['gamma']:.3f} ({tlaw['points']} points; "
              f"{tlaw['infinite']} pre-trained runs below every scratch floor)"]
    o += ["", f"Rule: {out['rule_text']}. Support: {support}. Result: {rule or 'incomplete'}"]
    open(os.path.join(R.OUT, "THRESHOLD_T1_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--targets", default="", help="pipeline checks only (the rule's networks are fixed above)")
    main(ap.parse_args())
