"""ICML programme, L1: leave one network out (rules: atlas/README.md, written before any score).

For each network X with a run of kaggle_lono.sh attached (lono_<x>_ad_s*.npz: Atlas pre-trained without X, then adapted
to X), the adapted model (checkpoint E) and the pre-trained weights before adaptation (P) are calibrated on X's validation
windows and scored once on X's all-India test windows against TimesFM 2.5 (india_opp_*.npz) and, for reference,
Atlas-India (india_s*.npz, trained on all 14 networks including X). The rule is applied at the end.

  python score_lono.py
"""
import argparse, json, os, re, sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import FLOOR
from pw import evaluate as E
import run_atlas_delhi as R
import run_atlas_india as RI
from score_india import found

TARGETS = ["Uttar Pradesh", "Haryana", "Maharashtra", "Karnataka"]
slug = lambda k: re.sub(r"[^a-z0-9]+", "_", k.lower())


def log(*a):
    print(*a, flush=True)


def main(a):
    nets = {D.name: D for D in RI.networks(a.quick)}
    opp = {}
    for f in found("india_opp_*.npz"):
        z = np.load(f); opp[str(z["name"])] = z
    tfm = next((k for k in opp if k.startswith("TimesFM 2.5")), None)
    assert tfm, f"TimesFM 2.5 forecasts not attached (found {list(opp)})"
    india = [np.load(f) for f in found("india_s*.npz")]
    res, wins, losses, done = {}, 0, 0, []
    for X in TARGETS:
        files = found(f"lono_{slug(X)}_ad_s*.npz")
        if not files or X not in nets:
            log(f"{X}: no run attached"); continue
        D = nets[X]; tr, va4, te = RI.origins(D, a.quick)
        Z = [np.load(f) for f in files]
        metas = [json.loads(str(z["meta"])) for z in Z]
        ALL = np.arange(D.N)
        yv, yt = R.truth(D, va4, ALL), R.truth(D, te, ALL)
        ens = lambda k, nm: np.sort(np.mean([z[f"{X}|{k}_{nm}"] for z in Z], 0), -1)
        cand = {"Atlas, X left out, then adapted (E)": (ens("E", "v4"), ens("E", "t")),
                "Atlas, X left out, not adapted (P)": (ens("P", "v4"), ens("P", "t")),
                tfm: (opp[tfm][f"{X}|qv"], opp[tfm][f"{X}|qt"])}
        if india:
            for k in ("E",):
                cand["Atlas-India (all 14 networks, reference)"] = (np.sort(np.mean([z[f"{X}|{k}_v4"] for z in india], 0), -1),
                                                                   np.sort(np.mean([z[f"{X}|{k}_t"] for z in india], 0), -1))
        P = {}
        for nm, (qv, qt) in cand.items():
            P[nm] = E.apply_cqr(qt, E.fit_cqr(qv[:, D.seen], yv[:, D.seen]))
        sc = lambda q, idx: E.score(q[:, idx], yt[:, idx], horizons=R.HZ, floor=FLOOR["PM2.5"], step_min=60)
        row = {"stations": D.N, "unseen": int(len(D.unseen)), "seeds": [m["seed"] for m in metas],
               "adapt_steps": [m["E"]["steps"] for m in metas], "adapt_val_MAE": [m["E"]["val_MAE"] for m in metas],
               "pretrain_networks": None, "scores": {}, "vs_tfm": {}}
        for nm, q in P.items():
            row["scores"][nm] = {"S": sc(q, D.seen), "U": sc(q, D.unseen)}
        for nm in ("Atlas, X left out, then adapted (E)", "Atlas, X left out, not adapted (P)"):
            row["vs_tfm"][nm] = {t: E.compare(P[nm][:, idx], P[tfm][:, idx], yt[:, idx], R.PER_DAY, "MAE", reps=a.reps,
                                                floor=FLOOR["PM2.5"]) for t, idx in (("S", D.seen), ("U", D.unseen))}
        v = row["vs_tfm"]["Atlas, X left out, then adapted (E)"]
        verdict = "BEATS" if (v["S"]["verdict"], v["U"]["verdict"]) == ("WIN", "WIN") else (
            "LOSES" if "LOSS" in (v["S"]["verdict"], v["U"]["verdict"]) else "level")
        row["verdict"] = verdict
        wins += verdict == "BEATS"; losses += verdict == "LOSES"; done.append(X)
        res[X] = row
        log(f"LONO {X}: " + json.dumps({nm: [round(s['S']['MAE'], 2), round(s['U']['MAE'], 2)] for nm, s in row['scores'].items()})
            + f" | adapted vs TimesFM 2.5: S {v['S']['verdict']} {v['S']['rel_diff_pct']:+.2f}% p={v['S']['p']:.2g}; "
              f"U {v['U']['verdict']} {v['U']['rel_diff_pct']:+.2f}% p={v['U']['p']:.2g} -> {verdict}")
    rule = None
    if len(done) == len(TARGETS):
        rule = "CONFIRMED" if (wins >= 3 and losses == 0) else "NOT CONFIRMED"
    out = dict(networks=res, wins=wins, losses=losses, scored=done, rule=rule,
               rule_text="confirmed if the adapted model beats TimesFM 2.5 on at least 3 of the 4 networks and loses on none")
    log("LONO-RULE " + json.dumps({k: out[k] for k in ("wins", "losses", "scored", "rule")}))
    os.makedirs(R.OUT, exist_ok=True)
    json.dump(out, open(os.path.join(R.OUT, "lono_results.json"), "w"), indent=1, default=float)
    o = ["# ICML L1: leave one network out (generated)", "",
         "| Network | adapted (S / U) | not adapted, P (S / U) | TimesFM 2.5 (S / U) | Atlas-India, all 14 (S / U) | adapted vs TimesFM 2.5 (S / U) | verdict |",
         "|---|---|---|---|---|---|---|"]
    for X, r in res.items():
        g = lambda nm: " / ".join(f"{r['scores'][nm][t]['MAE']:.2f}" for t in ("S", "U")) if nm in r["scores"] else "–"
        v = r["vs_tfm"]["Atlas, X left out, then adapted (E)"]
        o.append(f"| {X} | {g('Atlas, X left out, then adapted (E)')} | {g('Atlas, X left out, not adapted (P)')} | {g(tfm)} | "
                 f"{g('Atlas-India (all 14 networks, reference)')} | {v['S']['rel_diff_pct']:+.1f}% (p={v['S']['p']:.2g}) / "
                 f"{v['U']['rel_diff_pct']:+.1f}% (p={v['U']['p']:.2g}) | {r['verdict']} |")
    o += ["", f"Rule: {out['rule_text']}. Result: {rule or 'incomplete (' + str(len(done)) + ' of 4 scored)'}"]
    open(os.path.join(R.OUT, "LONO_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--reps", type=int, default=2000)
    main(ap.parse_args())
