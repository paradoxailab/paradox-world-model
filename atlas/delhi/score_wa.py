"""Atlas v2-W, T-A (rules: atlas/README.md, "Atlas v2-W", written before any of these runs): the all-India test with
the weather that happened (ERA5 forcing; the fourth use of the October 2022 - March 2023 test period). Every verdict is
labelled "with perfect weather": a real forecaster would have had forecasts, not the reanalysis.

Entries, each calibrated on its own network's validation windows as in the all-India league:
  W1         the adopted weather model (1M parameters + eight ERA5 series), seeds 400-402 ensembled (w1_s*.npz)
  Atlas-India  the reference, seeds 400-402 (india_s*.npz, forecasts with the 2026-11-13 input fix)
  TimesFM 2.5  zero-shot (india_opp_*.npz)
  Atlas-F      Atlas-India + TimesFM 2.5 by the frozen online rule (score_v14.online_w)
  Atlas-F2     W1 + TimesFM 2.5 by the same frozen rule
Criteria, each reported pass or fail:
  B1  W1 beats Atlas-India (significant win on at least one track, loss on neither)
  B2  W1 loses to TimesFM 2.5 in none of the 28 network-tracks and beats it pooled on both tracks
  B3  W1 is level with or better than Atlas-F on both tracks
  B4  Atlas-F2 beats Atlas-F on both tracks

  python score_wa.py
"""
import argparse, json, os, sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import FLOOR
from pw import evaluate as E
import run_atlas_delhi as R
import run_atlas_india as RI
from score_india import found
from score_v14 import load, online_w, fuse, BLOCKS

H, OUT = R.H, R.OUT
NAMES = {"w1": "W1 (1M + weather)", "india": "Atlas-India", "tfm": "TimesFM 2.5", "F": "Atlas-F", "F2": "Atlas-F2 (W1 + TimesFM 2.5)"}


def log(*a):
    print(*a, flush=True)


def main(a):
    nets = RI.networks(a.quick)
    O = [RI.origins(D, a.quick) for D in nets]
    ref, w1 = load("india"), load(a.tag)
    opp = {}
    for f in found("india_opp_*.npz"):
        z = np.load(f); opp[str(z["name"])] = z
    tfm = next((k for k in opp if k.startswith("TimesFM 2.5")), None)
    assert tfm and sorted(ref) == [400, 401, 402], "needs TimesFM 2.5 forecasts and Atlas-India seeds 400-402"
    assert sorted(w1) == [400, 401, 402] or a.quick, f"needs {a.tag} seeds 400-402 (found {sorted(w1)})"
    for s, (z, m) in sorted(w1.items()):
        log(f"{a.tag} seed {s}: {m['params']:,} parameters, validation {m['E']['val_MAE']:.3f} at step {m['E']['steps']}")
    ens = lambda S, net, nm: np.sort(np.mean([S[s][0][f"{net}|E_{nm}"] for s in sorted(S)], 0), -1)
    P = {k: [] for k in NAMES}
    Y, wlog = [], {}
    for D, (tr, va4, te) in zip(nets, O):
        ALL = np.arange(D.N)
        yv, yt = R.truth(D, va4, ALL), R.truth(D, te, ALL)
        Y.append(yt)
        raw = {"w1": (ens(w1, D.name, "v4"), ens(w1, D.name, "t")), "india": (ens(ref, D.name, "v4"), ens(ref, D.name, "t")),
               "tfm": (opp[tfm][f"{D.name}|qv"], opp[tfm][f"{D.name}|qt"])}
        cal = {}
        for k, (qv, qt) in raw.items():
            d = E.fit_cqr(np.sort(qv, -1)[:, D.seen], yv[:, D.seen])
            cal[k] = (E.apply_cqr(np.sort(qv, -1), d), E.apply_cqr(np.sort(qt, -1), d))
            P[k].append(cal[k][1])
        yy = np.concatenate([yv, yt]); oo = np.concatenate([va4, te]); mte = np.r_[np.zeros(len(va4), bool), np.ones(len(te), bool)]
        qb = np.concatenate(cal["tfm"])
        for key, mem in (("F", "india"), ("F2", "w1")):
            qa = np.concatenate(cal[mem])
            ws = online_w(qa, qb, yy, oo, mte, D.seen)
            P[key].append(fuse(qa, qb, ws)[mte])
            wlog.setdefault(key, {})[D.name] = [float(ws[mte, b].mean()) for b in range(len(BLOCKS))]
        log(f"WEIGHTS {D.name}: on Atlas-India in Atlas-F {[round(x, 2) for x in wlog['F'][D.name]]}, "
            f"on W1 in Atlas-F2 {[round(x, 2) for x in wlog['F2'][D.name]]} (lead blocks 1-6, 7-12, 13-24 h)")
    cat = lambda arrs, which: np.concatenate([x[:, getattr(D, which)] for x, D in zip(arrs, nets)], 1)
    yS, yU = cat(Y, "seen"), cat(Y, "unseen")
    sc = lambda q, y: E.score(q, y, horizons=R.HZ, floor=FLOOR["PM2.5"], step_min=60)
    PP = {k: (cat(v, "seen"), cat(v, "unseen")) for k, v in P.items()}
    res = {"label": "with perfect weather (ERA5 forcing)", "weights": wlog, "pooled": {}, "pairs": {}, "networks": {}, "criteria": {}}
    for k, (s, u) in PP.items():
        res["pooled"][NAMES[k]] = {"S": sc(s, yS), "U": sc(u, yU)}
        r = res["pooled"][NAMES[k]]
        log(f"TEST {NAMES[k]}: MAE trained {r['S']['MAE']:.2f}, unseen {r['U']['MAE']:.2f}")

    def pair(x, z):
        r = {t: E.compare(PP[x][i], PP[z][i], y, R.PER_DAY, "MAE", reps=a.reps, floor=FLOOR["PM2.5"])
             for i, (t, y) in enumerate((("S", yS), ("U", yU)))}
        v = (r["S"]["verdict"], r["U"]["verdict"])
        verdict = "BEATS" if v == ("WIN", "WIN") else ("LOSES" if "LOSS" in v else "level")
        out = dict(S=dict(rel=r["S"]["rel_diff_pct"], p=r["S"]["p"], v=r["S"]["verdict"]),
                   U=dict(rel=r["U"]["rel_diff_pct"], p=r["U"]["p"], v=r["U"]["verdict"]), verdict=verdict)
        res["pairs"][f"{NAMES[x]} vs {NAMES[z]}"] = out
        log(f"SIG {NAMES[x]} vs {NAMES[z]}: S {v[0]} {out['S']['rel']:+.2f}% p={out['S']['p']:.2g}; "
            f"U {v[1]} {out['U']['rel']:+.2f}% p={out['U']['p']:.2g} -> {verdict}")
        return out

    pW_I, pW_T, pW_F, pF2_F, pF2_I, pF2_T = (pair("w1", "india"), pair("w1", "tfm"), pair("w1", "F"), pair("F2", "F"),
                                             pair("F2", "india"), pair("F2", "tfm"))
    lost = []
    for k, D in enumerate(nets):
        row = {NAMES[key]: [float(np.nanmean(np.abs(v[k][:, idx][..., 1] - Y[k][:, idx]))) if len(idx) else float("nan")
                            for idx in (D.seen, D.unseen)] for key, v in P.items()}
        for x, z in (("w1", "tfm"), ("w1", "india"), ("F2", "tfm"), ("F2", "F")):
            c = {t: E.compare(P[x][k][:, idx], P[z][k][:, idx], Y[k][:, idx], R.PER_DAY, "MAE", reps=a.reps, floor=FLOOR["PM2.5"])
                 for t, idx in (("S", D.seen), ("U", D.unseen)) if len(idx)}
            row[f"{NAMES[x]} vs {NAMES[z]}"] = {t: (dict(v=cc["verdict"], rel=cc["rel_diff_pct"], p=cc["p"]) if cc else None) for t, cc in c.items()}
            if (x, z) == ("w1", "tfm"):
                lost += [f"{D.name} {t}" for t, cc in c.items() if cc and cc["verdict"] == "LOSS"]
        res["networks"][D.name] = row
        log(f"NET {D.name}: " + json.dumps({n: [round(x, 2) for x in row[n]] for n in row if isinstance(row[n], list)}))
    win1 = "WIN" in (pW_I["S"]["v"], pW_I["U"]["v"]) and "LOSS" not in (pW_I["S"]["v"], pW_I["U"]["v"])
    res["criteria"] = {
        "B1 W1 beats Atlas-India": "PASS" if win1 else "FAIL",
        "B2 W1 never loses to TimesFM 2.5 (28 network-tracks) and beats it pooled": "PASS" if (not lost and pW_T["verdict"] == "BEATS") else "FAIL",
        "B3 W1 level with or better than Atlas-F": "PASS" if pW_F["verdict"] != "LOSES" else "FAIL",
        "B4 Atlas-F2 beats Atlas-F": "PASS" if pF2_F["verdict"] == "BEATS" else "FAIL",
        "network-tracks W1 loses to TimesFM 2.5": lost}
    log("TA-CRITERIA (with perfect weather) " + json.dumps(res["criteria"]))
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "wa_test.json"), "w"), indent=1, default=float)
    o = ["# Atlas v2-W, T-A: all-India test with perfect weather (generated)", "", "| Entry | trained MAE | unseen MAE |", "|---|---|---|"]
    o += [f"| {n} | {r['S']['MAE']:.2f} | {r['U']['MAE']:.2f} |" for n, r in res["pooled"].items()]
    o += ["", "| Pair | trained | unseen | verdict |", "|---|---|---|---|"]
    o += [f"| {k} | {v['S']['rel']:+.2f}% (p={v['S']['p']:.2g}) | {v['U']['rel']:+.2f}% (p={v['U']['p']:.2g}) | {v['verdict']} |" for k, v in res["pairs"].items()]
    o += ["", "| Criterion (with perfect weather) | result |", "|---|---|"] + [f"| {k} | {v} |" for k, v in res["criteria"].items()]
    open(os.path.join(OUT, "WA_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="w1")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--reps", type=int, default=2000)
    main(ap.parse_args())
