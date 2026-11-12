"""ATF v1.2, part 2: decide before training, and combine (rules fixed in the README before results).

Needs: curves.py outputs (truth + Atlas forecasts per data amount) and fm.py outputs, in $ATF_OUT.
(a) Decision: from the 2-month pilot's VALIDATION error and the pooled ATF law (fitted on the other networks'
    validation curves), predict Atlas's validation error with all data; predict "Atlas beats the best foundation
    model" if that is lower than the best foundation model's validation error. Checked against test.
(b) Combination: for each network-target, weight w in {0, .25, .5, .75, 1} on Atlas (all data, seeds averaged) and
    1 - w on the foundation model with the lowest validation MAE, chosen on validation; scored once on test.
    Paired tests (Diebold-Mariano on per-window errors + day-block bootstrap) against every foundation model and Atlas.

  python blend.py                 # -> BLEND_REPORT.md, blend_results.json
"""
import glob, json, math, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), "delhi"))
import atf as A
from pw import evaluate as E

OUT = os.environ.get("ATF_OUT", "out_atf")
W = [0.0, 0.25, 0.5, 0.75, 1.0]


def load_atlas(net, amount_tag):
    fs = sorted(glob.glob(os.path.join(OUT, "curves", f"{net}__{amount_tag}__s*.npz")))
    if not fs: return None, None
    z = [np.load(f) for f in fs]
    return (np.sort(np.mean([x["qt"].astype(np.float32) for x in z], 0), -1),
            np.sort(np.mean([x["qv"].astype(np.float32) for x in z], 0), -1))


def mae(q, y):
    return float(np.nanmean(np.abs(q[..., 1] - y)))


def main():
    logs = glob.glob(os.path.join(OUT, "**", "log_s*.txt"), recursive=True) + glob.glob(os.path.join(OUT, "*.txt"))
    curves_raw, _ = A.read(logs)
    cv_val = A.build(curves_raw, "val")
    res = {"decision": [], "blend": [], "skipped": []}
    for tf in sorted(glob.glob(os.path.join(OUT, "curves", "*__truth.npz"))):
        net = os.path.basename(tf).split("__")[0]
        z = np.load(tf)
        yt, yv, targets = z["yt"].astype(np.float32), z["yv"].astype(np.float32), [str(t) for t in z["targets"]]
        qa_t, qa_v = load_atlas(net, "allmo")
        fms = {}
        for f in sorted(glob.glob(os.path.join(OUT, "fm", f"{net}__*.npz"))):
            x = np.load(f); fms[json.loads(str(x["meta"]))["name"]] = (x["qt"].astype(np.float32), x["qv"].astype(np.float32))
        if qa_t is None or not fms:
            res["skipped"].append(f"{net}: Atlas all-data forecasts {'missing' if qa_t is None else 'ok'}, {len(fms)} foundation models"); continue
        train = [c for k, c in cv_val.items() if k[0] != net]
        alpha, phi = A.pool_fit(train)
        for k, v in enumerate(targets):
            best = min(fms, key=lambda n: mae(fms[n][1][..., k, :], yv[..., k]))
            fq_t, fq_v = fms[best][0][..., k, :], fms[best][1][..., k, :]
            # (a) decision from the pilot's validation error
            c = cv_val.get((net, v))
            if c:
                pred_val = A.e2(c) * A.g(max(c["N"]) / A.P_N, phi, alpha)
                res["decision"].append(dict(network=net, var=v, predicted_atlas_val=pred_val, fm_val=mae(fq_v, yv[..., k]),
                                            predict_beats=bool(pred_val < mae(fq_v, yv[..., k])),
                                            atlas_test=mae(qa_t[..., k, :], yt[..., k]), fm_test=mae(fq_t, yt[..., k]),
                                            actually_beats=bool(mae(qa_t[..., k, :], yt[..., k]) < mae(fq_t, yt[..., k])), best_fm=best))
            # (b) combination chosen on validation
            vals = [mae(w * qa_v[..., k, :] + (1 - w) * fq_v, yv[..., k]) for w in W]
            w = W[int(np.argmin(vals))]
            qb = np.sort(w * qa_t[..., k, :] + (1 - w) * fq_t, -1)
            row = dict(network=net, var=v, weight_on_atlas=w, best_fm_on_val=best, blend_test=mae(qb, yt[..., k]),
                       atlas_test=mae(qa_t[..., k, :], yt[..., k]), vs={})
            for name, q in [("Atlas", qa_t[..., k, :])] + [(n, fms[n][0][..., k, :]) for n in fms]:
                r = E.compare(qb, q, yt[..., k], 2, "MAE", reps=1000, floor=0.0)
                row["vs"][name] = dict(test=mae(q, yt[..., k]), **({"rel_diff_pct": r["rel_diff_pct"], "p": r["p"], "verdict": r["verdict"]} if r else {}))
            res["blend"].append(row)
    report(res)


def report(res):
    o = ["# ATF v1.2: deciding before training, and combining (generated)", ""]
    d = res["decision"]
    if d:
        acc = np.mean([x["predict_beats"] == x["actually_beats"] for x in d])
        yes, no = np.mean([x["actually_beats"] for x in d]), 1 - np.mean([x["actually_beats"] for x in d])
        o += [f"## (a) Will Atlas with all data beat the best foundation model? ({len(d)} network-targets)", "",
              f"ATF decision accuracy {100 * acc:.0f}% (always-yes {100 * yes:.0f}%, always-no {100 * no:.0f}%).", "",
              "| network | target | predicted Atlas (val) | best FM (val) | predicted | Atlas test | FM test | actual |", "|---|---|---|---|---|---|---|---|"]
        o += [f"| {x['network']} | {x['var']} | {x['predicted_atlas_val']:.3f} | {x['fm_val']:.3f} | {'beats' if x['predict_beats'] else 'loses'} | {x['atlas_test']:.3f} | {x['fm_test']:.3f} | {'beats' if x['actually_beats'] else 'loses'} |" for x in d]
        o.append("")
    b = res["blend"]
    if b:
        names = sorted({n for x in b for n in x["vs"]})
        o += [f"## (b) Combination chosen on validation ({len(b)} network-targets)", "", "| network | target | w (Atlas) | combination | " + " | ".join(names) + " |", "|---" * (len(names) + 4) + "|"]
        for x in b:
            cells = []
            for n in names:
                r = x["vs"].get(n)
                cells.append("–" if not r else f"{r['test']:.3f}" + (f" ({'W' if r.get('verdict') == 'WIN' else ('L' if r.get('verdict') == 'LOSS' else 't')} {r['rel_diff_pct']:+.1f}%)" if "verdict" in r else ""))
            o.append(f"| {x['network']} | {x['var']} | {x['weight_on_atlas']} | {x['blend_test']:.3f} | " + " | ".join(cells) + " |")
        o += ["", "W = combination significantly better (p < 0.05 and bootstrap interval excludes 0), L = significantly worse, t = tie.", ""]
        summ = {}
        for n in names:
            v = [x["vs"][n].get("verdict") for x in b if n in x["vs"]]
            summ[n] = dict(wins=v.count("WIN"), ties=v.count("TIE"), losses=v.count("LOSS"), n=len(v))
            o.append(f"- against {n}: {summ[n]['wins']} wins, {summ[n]['ties']} ties, {summ[n]['losses']} losses of {summ[n]['n']}")
        fm_names = [n for n in names if n != "Atlas"]
        claim = all(summ[n]["wins"] > summ[n]["n"] / 2 for n in fm_names) if fm_names else False
        o += ["", f"**Pre-registered claim (beats every foundation model on a majority of network-targets): {'MET' if claim else 'NOT MET'}**", ""]
        res["summary"] = summ; res["claim_met"] = claim
    if res["skipped"]:
        o += ["Skipped: " + "; ".join(res["skipped"]), ""]
    open(os.path.join(OUT, "BLEND_REPORT.md"), "w").write("\n".join(o) + "\n")
    json.dump(res, open(os.path.join(OUT, "blend_results.json"), "w"), indent=1, default=float)
    print("\n".join(o))


if __name__ == "__main__":
    main()
