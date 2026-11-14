"""Atlas v1.4 programme: selection, test and the fused system Atlas-F (rules: atlas/README.md, "Atlas v1.4", written
before any of these runs).

Stage V1 (selection, validation only). Candidates trained on all 14 networks, seed 400, identical to Atlas-India except:
  v14n  attention restricted to each station and its graph neighbours (ATLAS_NBR=1)
  v14g  a learned per-station gate on the attention update (ATLAS_GATE=1)
  v14ng both
The candidate with the lowest pooled validation MAE is chosen if that MAE is at least 1% below Atlas-India seed 400's;
otherwise no v1.4 architecture is adopted. Atlas-P (pre-registered 2026-11-14) is decided by its own rule: it replaces
Atlas-India only if its validation MAE, paired by seed over seeds 400-402, is lower by more than 2 standard errors.

Stage V2 (test, once). The chosen model's three seeds (ensemble, calibrated on each network's validation windows) against
Atlas-India (three seeds) and TimesFM 2.5 on the all-India test windows: pooled, both tracks, Diebold-Mariano with a
day-block bootstrap; and per network, both tracks.

Stage F (Atlas-F). The best Atlas (chosen model if adopted, else Atlas-India) and TimesFM 2.5, both calibrated as above,
are averaged with weights w and 1 - w (w on a 0.05 grid, one per lead block 1-6, 7-12, 13-24 h and network). w is chosen
at the start of every test day from the windows of the previous 30 days whose 24 target hours ended before that day
(validation windows fill the first month), on trained stations only; never-trained stations reuse it. Nothing from a
forecast's future is used. Atlas-F is scored once against each member, pooled and per network, both tracks.

  python score_v14.py --stage select
  python score_v14.py --stage test --tag v14ng      # or --tag indiap, or --tag none (Atlas-F with Atlas-India)
"""
import argparse, json, os, sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import FLOOR, SPD
from pw import evaluate as E
import run_atlas_delhi as R
import run_atlas_india as RI
from score_india import found

H, OUT = R.H, R.OUT
CANDS = {"v14n": "neighbour attention", "v14g": "station gate", "v14ng": "neighbour attention + station gate"}
BLOCKS = [(0, 6), (6, 12), (12, 24)]
GRID = np.round(np.arange(0, 1.0001, 0.05), 2)
TRAIL = 30


def log(*a):
    print(*a, flush=True)


def load(tag):
    """Seed files of one recipe: india_s*.npz for Atlas-India, <tag>_s*.npz otherwise (dict seed -> npz)."""
    pat = "india_s*.npz" if tag == "india" else f"{tag}_s*.npz"
    out = {}
    for f in found(pat):
        b = os.path.basename(f)
        if tag == "india" and not b[len("india_s"):-4].isdigit():
            continue
        z = np.load(f); m = json.loads(str(z["meta"]))
        out[int(m["seed"])] = (z, m)
    return out


def select(a):
    res = {}
    ref = load("india")
    assert 400 in ref, "Atlas-India seed 400 not attached"
    v_ref = ref[400][1]["E"]["val_MAE"]
    rows = {}
    for t, nm in CANDS.items():
        s = load(t)
        if 400 in s:
            rows[t] = s[400][1]["E"]["val_MAE"]
            log(f"V1 {t} ({nm}): pooled validation MAE {rows[t]:.4f} (Atlas-India seed 400: {v_ref:.4f}, {100 * (rows[t] / v_ref - 1):+.2f}%)")
    chosen = None
    if len(rows) == len(CANDS):
        best = min(rows, key=rows.get)
        chosen = best if rows[best] <= 0.99 * v_ref else None
    res["V1"] = dict(reference_val=v_ref, candidates=rows, chosen=chosen, complete=len(rows) == len(CANDS),
                     rule="lowest pooled validation MAE, adopted only if at least 1% below Atlas-India seed 400")
    log("V1-RULE " + json.dumps(res["V1"]))
    p = load("indiap")
    seeds = sorted(set(p) & set(ref))
    if seeds:
        dif = np.array([p[s][1]["E"]["val_MAE"] - ref[s][1]["E"]["val_MAE"] for s in seeds])
        se = float(dif.std(ddof=1) / np.sqrt(len(dif))) if len(dif) > 1 else float("inf")
        adopt = bool(len(seeds) == 3 and -dif.mean() > 2 * se)
        res["AtlasP"] = dict(seeds=seeds, val_P=[p[s][1]["E"]["val_MAE"] for s in seeds], val_India=[ref[s][1]["E"]["val_MAE"] for s in seeds],
                             paired_diff=float(dif.mean()), se=se, adopted=adopt, complete=len(seeds) == 3,
                             rule="Atlas-P replaces Atlas-India only if its validation MAE, paired by seed over 400-402, is lower by more than 2 SE")
        log("ATLASP-RULE " + json.dumps(res["AtlasP"], default=float))
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "v14_select.json"), "w"), indent=1, default=float)


def online_w(qa, qb, y, o_hist, o_te, seen):
    """Per lead block, the weight on member a for every test window, from trailing windows only.
    qa, qb, y: arrays over the history+test windows [W, N, H(, 3)]; o_hist: their origins (hours); o_te: test mask."""
    W = len(o_hist)
    ws = np.zeros((W, len(BLOCKS)))
    day0 = (o_hist // SPD) * SPD                            # start of the day the forecast is issued in
    for b, (h0, h1) in enumerate(BLOCKS):
        ya = qa[..., 1][:, seen, h0:h1]; yb = qb[..., 1][:, seen, h0:h1]; yt = y[:, seen, h0:h1]
        err = np.stack([np.nanmean(np.abs(w * ya + (1 - w) * yb - yt).reshape(W, -1), 1) for w in GRID], 1)  # [W, G]
        ok = np.isfinite(err).all(1)
        for i in np.where(o_te)[0]:
            elig = ok & (o_hist + H <= day0[i]) & (o_hist >= day0[i] - TRAIL * SPD)
            ws[i, b] = GRID[np.argmin(err[elig].mean(0))] if elig.any() else 0.5
    return ws


def fuse(qa, qb, ws):
    q = np.empty_like(qa)
    for b, (h0, h1) in enumerate(BLOCKS):
        w = ws[:, b][:, None, None, None]
        q[:, :, h0:h1] = w * qa[:, :, h0:h1] + (1 - w) * qb[:, :, h0:h1]
    return np.sort(q, -1)


def test(a):
    nets = RI.networks(a.quick)
    O = [RI.origins(D, a.quick) for D in nets]
    ref = load("india")
    ch = load(a.tag) if a.tag != "none" else {}
    opp = {}
    for f in found("india_opp_*.npz"):
        z = np.load(f); opp[str(z["name"])] = z
    tfm = next((k for k in opp if k.startswith("TimesFM 2.5")), None)
    assert tfm and len(ref) == 3, "needs TimesFM 2.5 forecasts and the three Atlas-India seeds"
    names = {"india": "Atlas-India (v1.3 recipe)", a.tag: f"Atlas v1.4 candidate {a.tag}", "tfm": "TimesFM 2.5", "F": "Atlas-F"}
    best = a.tag if ch else "india"
    ens = lambda S, net, nm: np.sort(np.mean([S[s][0][f"{net}|E_{nm}"] for s in sorted(S)], 0), -1)
    P = {k: [] for k in (["india", "tfm", "F"] + ([a.tag] if ch else []))}
    Y, wlog = [], {}
    for D, (tr, va4, te) in zip(nets, O):
        ALL = np.arange(D.N)
        yv, yt = R.truth(D, va4, ALL), R.truth(D, te, ALL)
        Y.append(yt)
        raw = {"india": (ens(ref, D.name, "v4"), ens(ref, D.name, "t")), "tfm": (opp[tfm][f"{D.name}|qv"], opp[tfm][f"{D.name}|qt"])}
        if ch:
            raw[a.tag] = (ens(ch, D.name, "v4"), ens(ch, D.name, "t"))
        cal = {}
        for k, (qv, qt) in raw.items():
            d = E.fit_cqr(np.sort(qv, -1)[:, D.seen], yv[:, D.seen])
            cal[k] = (E.apply_cqr(np.sort(qv, -1), d), E.apply_cqr(np.sort(qt, -1), d))
            P[k].append(cal[k][1])
        qa = np.concatenate([cal[best][0], cal[best][1]]); qb = np.concatenate([cal["tfm"][0], cal["tfm"][1]])
        yy = np.concatenate([yv, yt]); oo = np.concatenate([va4, te]); mte = np.r_[np.zeros(len(va4), bool), np.ones(len(te), bool)]
        ws = online_w(qa, qb, yy, oo, mte, D.seen)
        P["F"].append(fuse(qa, qb, ws)[mte])
        wlog[D.name] = [float(ws[mte, b].mean()) for b in range(len(BLOCKS))]
        log(f"F {D.name}: mean weight on {names[best]} by lead block {[round(x, 2) for x in wlog[D.name]]}")
    cat = lambda arrs, which: np.concatenate([x[:, getattr(D, which)] for x, D in zip(arrs, nets)], 1)
    yS, yU = cat(Y, "seen"), cat(Y, "unseen")
    sc = lambda q, y: E.score(q, y, horizons=R.HZ, floor=FLOOR["PM2.5"], step_min=60)
    res = {"best_atlas": best, "weights": wlog, "pooled": {}, "pairs": {}, "networks": {}}
    PP = {k: (cat(v, "seen"), cat(v, "unseen")) for k, v in P.items()}
    for k, (s, u) in PP.items():
        res["pooled"][names[k]] = {"S": sc(s, yS), "U": sc(u, yU)}
        log(f"TEST {names[k]}: trained {res['pooled'][names[k]]['S']['MAE']:.2f}, unseen {res['pooled'][names[k]]['U']['MAE']:.2f}")
    pairs = [("F", "india"), ("F", "tfm")] + ([(a.tag, "india"), (a.tag, "tfm"), ("F", a.tag)] if ch else [])
    for x, z in pairs:
        r = {t: E.compare(PP[x][i], PP[z][i], y, R.PER_DAY, "MAE", reps=a.reps, floor=FLOOR["PM2.5"]) for i, (t, y) in enumerate((("S", yS), ("U", yU)))}
        v = (r["S"]["verdict"], r["U"]["verdict"])
        verdict = "BEATS" if v == ("WIN", "WIN") else ("LOSES" if "LOSS" in v else "level")
        res["pairs"][f"{names[x]} vs {names[z]}"] = dict(S=dict(rel=r["S"]["rel_diff_pct"], p=r["S"]["p"], v=r["S"]["verdict"]),
                                                         U=dict(rel=r["U"]["rel_diff_pct"], p=r["U"]["p"], v=r["U"]["verdict"]), verdict=verdict)
        log(f"SIG {names[x]} vs {names[z]}: S {r['S']['verdict']} {r['S']['rel_diff_pct']:+.2f}% p={r['S']['p']:.2g}; "
            f"U {r['U']['verdict']} {r['U']['rel_diff_pct']:+.2f}% p={r['U']['p']:.2g} -> {verdict}")
    for k, D in enumerate(nets):
        row = {}
        for key, v in P.items():
            row[names[key]] = [float(np.nanmean(np.abs(v[k][:, idx][..., 1] - Y[k][:, idx]))) if len(idx) else float("nan")
                               for idx in (D.seen, D.unseen)]
        for x, z in ([("F", "tfm"), ("F", "india")] + ([(a.tag, "india")] if ch else [])):
            row[f"{names[x]} vs {names[z]}"] = {t: (lambda c: dict(v=c["verdict"], rel=c["rel_diff_pct"], p=c["p"]) if c else None)(
                E.compare(P[x][k][:, idx], P[z][k][:, idx], Y[k][:, idx], R.PER_DAY, "MAE", reps=a.reps, floor=FLOOR["PM2.5"]))
                for t, idx in (("S", D.seen), ("U", D.unseen)) if len(idx)}
        res["networks"][D.name] = row
        log(f"NET {D.name}: " + json.dumps({n: [round(x, 2) for x in row[n]] for n in row if isinstance(row[n], list)}))
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, f"v14_test_{a.tag}.json"), "w"), indent=1, default=float)
    o = [f"# Atlas v1.4 programme, test stage ({a.tag}; generated)", "", "| Entry | trained MAE | unseen MAE |", "|---|---|---|"]
    o += [f"| {n} | {r['S']['MAE']:.2f} | {r['U']['MAE']:.2f} |" for n, r in res["pooled"].items()]
    o += ["", "| Pair | trained | unseen | verdict |", "|---|---|---|---|"]
    o += [f"| {k} | {v['S']['rel']:+.2f}% (p={v['S']['p']:.2g}) | {v['U']['rel']:+.2f}% (p={v['U']['p']:.2g}) | {v['verdict']} |" for k, v in res["pairs"].items()]
    open(os.path.join(OUT, f"V14_REPORT_{a.tag}.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["select", "test"], required=True)
    ap.add_argument("--tag", default="none")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--reps", type=int, default=2000)
    a = ap.parse_args()
    select(a) if a.stage == "select" else test(a)
