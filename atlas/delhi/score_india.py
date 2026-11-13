"""Atlas-India v1.0: scoring of the all-India league (rules in atlas/README.md, written before any score).

Reads the forecasts saved by run_atlas_india.py (one file per seed), decides E against F on pooled validation
(paired by seed), averages the seeds of the chosen recipe, calibrates the 80% band on each network's validation
windows, and scores once on the test windows: all networks pooled (Track S = trained stations, Track U = stations
never trained on) and each network on its own. Baselines: same hour yesterday, last observed value. Foundation-model
forecasts made on the same windows (india_opp_<key>.npz, GPU) are scored too when attached.

  python score_india.py
"""
import argparse, glob, json, os, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import SPD, FLOOR
from pw import evaluate as E
import run_atlas_delhi as R
import run_atlas_india as RI

H, OUT = R.H, R.OUT
RES = {"pooled": {}, "networks": {}, "significance": {}, "claims": {}}


def log(*a):
    print(*a, flush=True)


def found(pattern):
    """Files matching the pattern in OUT and in the attached Kaggle inputs; a file copied into OUT (e.g. to be
    re-forecast) replaces the input file of the same name."""
    mine = sorted(glob.glob(os.path.join(OUT, "**", pattern), recursive=True))
    names = {os.path.basename(f) for f in mine}
    return mine + sorted(f for f in glob.glob(os.path.join("/kaggle/input", "**", pattern), recursive=True)
                         if os.path.basename(f) not in names and not f.startswith(os.path.abspath(OUT)))


def baseline(D, kind, org, nodes):
    fo = org[:, None] + np.arange(H)[None]
    yd = D.Y[fo - SPD][:, :, nodes, 0]
    if kind == "last":
        hi = D.Y[org[:, None] + np.arange(-24, 0)[None]][:, :, nodes, 0]
        li = np.where(~np.isnan(hi), np.arange(24)[None, :, None], -1).max(1)
        v = np.take_along_axis(hi, np.maximum(li, 0)[:, None], 1)[:, 0]
        p = np.repeat(np.where(li >= 0, v, yd[:, 0])[:, None], H, 1)
    else:
        p = yd
    p = np.nan_to_num(np.where(np.isnan(p), yd, p))
    return np.repeat(p.transpose(0, 2, 1)[..., None], 3, -1).astype(np.float32)


def main(a):
    t0 = time.time()
    nets = RI.networks(a.quick)
    O = [RI.origins(D, a.quick) for D in nets]
    files = found("india_s*.npz")
    Z = [np.load(f) for f in files]
    metas = [json.loads(str(z["meta"])) for z in Z]
    old = [m["seed"] for m in metas if "input_fix" not in m and "loader" not in m]
    assert not old, f"seeds {old} were forecast before the input fix: run run_atlas_india.py --reforecast first"
    if any("input_fix" in m for m in metas):
        RES["input_fix"] = [dict(m["input_fix"], seed=m["seed"]) for m in metas if "input_fix" in m]
        RES["fixed_from_start"] = [m["seed"] for m in metas if "input_fix" not in m]
    assert Z, "no india_s*.npz found"
    for m in metas:
        assert m["networks"][:len(nets)] == [D.name for D in nets], "networks differ from the training runs'"
    val = {k: [m[k]["val_MAE"] for m in metas] for k in ("E", "F")}
    dif = np.array(val["E"]) - np.array(val["F"])
    se = float(dif.std(ddof=1) / np.sqrt(len(dif))) if len(dif) > 1 else float("inf")
    fam = "F" if dif.mean() > 2 * se else "E"
    oth = "E" if fam == "F" else "F"
    RES["decision"] = dict(seeds=[m["seed"] for m in metas], val_MAE=val, steps={k: [m[k]["steps"] for m in metas] for k in ("E", "F")},
                           paired_diff=float(dif.mean()), se=se, recipe=fam, time_capped=[bool(m["hit_time_cap"]) for m in metas],
                           single_model_test={k: [[m[k]["test_S"], m[k]["test_U"]] for m in metas] for k in ("E", "F")},
                           rule="F (last step of the whole schedule) replaces E (early stopping) only if its pooled validation MAE "
                                "is lower by more than 2 standard errors, paired by seed")
    log("DECISION " + json.dumps(RES["decision"], default=float))

    ens = lambda net, k, nm: np.sort(np.mean([z[f"{net}|{k}_{nm}"] for z in Z], 0), -1)
    opp = {}
    for f in found("india_opp_*.npz"):
        zz = np.load(f)
        opp[str(zz["name"])] = zz
    entries = {}                                              # name -> per network (test quantiles [W, N, H, 3])
    YT = []
    for D, (tr, va4, te) in zip(nets, O):
        ALL = np.arange(D.N)
        yv, yt = R.truth(D, va4, ALL), R.truth(D, te, ALL)
        YT.append(yt)
        cand = {"Atlas-India": (ens(D.name, fam, "v4"), ens(D.name, fam, "t")),
                f"Atlas-India, recipe {oth} (not chosen)": (ens(D.name, oth, "v4"), ens(D.name, oth, "t")),
                "Same hour yesterday": (baseline(D, "yday", va4, ALL), baseline(D, "yday", te, ALL)),
                "Last observed value": (baseline(D, "last", va4, ALL), baseline(D, "last", te, ALL))}
        for nm, zz in opp.items():
            if f"{D.name}|qt" in zz.files and zz[f"{D.name}|qt"].shape[:2] == (len(te), D.N):
                cand[nm] = (zz[f"{D.name}|qv"], zz[f"{D.name}|qt"])
        for nm, (qv, qt) in cand.items():
            d = E.fit_cqr(qv[:, D.seen], yv[:, D.seen])       # calibrated on this network's validation windows
            entries.setdefault(nm, []).append(E.apply_cqr(qt, d))
    full = [nm for nm, v in entries.items() if len(v) == len(nets)]
    sc = lambda q, y: E.score(q, y, horizons=R.HZ, floor=FLOOR["PM2.5"], step_min=60)
    cat = lambda arrs, which: np.concatenate([x[:, getattr(D, which)] for x, D in zip(arrs, nets)], 1)
    yS, yU = cat(YT, "seen"), cat(YT, "unseen")
    P = {}
    for nm in full:
        P[nm] = (cat(entries[nm], "seen"), cat(entries[nm], "unseen"))
        RES["pooled"][nm] = {"S": sc(P[nm][0], yS), "U": sc(P[nm][1], yU)}
        log(f"TEST {nm}: all India, trained stations MAE {RES['pooled'][nm]['S']['MAE']:.2f}, unseen stations {RES['pooled'][nm]['U']['MAE']:.2f}")
    A = "Atlas-India"
    for other in full:
        if other == A:
            continue
        r = {t: {mm: E.compare(P[A][i], P[other][i], y, R.PER_DAY, mm, reps=a.reps, floor=FLOOR["PM2.5"]) for mm in ("MAE", "QL")}
             for i, (t, y) in enumerate((("S", yS), ("U", yU)))}
        RES["significance"][other] = r
        log(f"SIG Atlas-India vs {other}: trained stations {r['S']['MAE']['verdict']} {r['S']['MAE']['rel_diff_pct']:+.2f}% p={r['S']['MAE']['p']:.2g}; "
            f"unseen stations {r['U']['MAE']['verdict']} {r['U']['MAE']['rel_diff_pct']:+.2f}% p={r['U']['MAE']['p']:.2g}")
        vS, vU = r["S"]["MAE"]["verdict"], r["U"]["MAE"]["verdict"]
        RES["claims"][other] = "BEATS" if (vS, vU) == ("WIN", "WIN") else ("LOSES" if "LOSS" in (vS, vU) else "level")
    for k, (D, (tr, va4, te)) in enumerate(zip(nets, O)):     # each network on its own
        row = {"stations": D.N, "unseen": int(len(D.unseen)), "mean_PM25_test": float(np.nanmean(YT[k]))}
        for nm in full:
            q = entries[nm][k]
            row[nm] = {"S": float(np.nanmean(np.abs(q[:, D.seen][..., 1] - YT[k][:, D.seen]))),
                       "U": float(np.nanmean(np.abs(q[:, D.unseen][..., 1] - YT[k][:, D.unseen]))) if len(D.unseen) else float("nan")}
            if nm != A:
                c = E.compare(entries[A][k][:, D.seen], q[:, D.seen], YT[k][:, D.seen], R.PER_DAY, "MAE", reps=a.reps, floor=FLOOR["PM2.5"])
                row[nm]["atlas_vs"] = dict(verdict=c["verdict"], rel=c["rel_diff_pct"], p=c["p"]) if c else None
        RES["networks"][D.name] = row
    RES["minutes"] = round((time.time() - t0) / 60, 1)
    os.makedirs(OUT, exist_ok=True)
    json.dump(RES, open(os.path.join(OUT, "india_results.json"), "w"), indent=1, default=float)
    np.savez_compressed(os.path.join(OUT, "india_preds.npz"), qS=P[A][0], qU=P[A][1], yS=yS, yU=yU,
                        networks=np.array([D.name for D in nets]), n_seen=np.array([len(D.seen) for D in nets]),
                        n_unseen=np.array([len(D.unseen) for D in nets]))
    report(full, A)


def report(full, A):
    d = RES["decision"]
    o = ["# Atlas-India v1.0: all-India league results (generated from india_results.json)", "",
         f"Recipe decision on pooled validation: E {[round(x, 3) for x in d['val_MAE']['E']]} after {d['steps']['E']} steps; "
         f"F {[round(x, 3) for x in d['val_MAE']['F']]} after {d['steps']['F']} steps; paired difference E - F {d['paired_diff']:+.3f}, "
         f"standard error {d['se']:.3f}: recipe {d['recipe']}. Single models on test (trained / unseen): "
         f"E {[[round(v, 2) for v in x] for x in d['single_model_test']['E']]}, F {[[round(v, 2) for v in x] for x in d['single_model_test']['F']]}.", "",
         "## All networks pooled (PM2.5, ug/m3, next 24 h)", "",
         "| Entry | Trained: MAE | RMSE | QL | COV80 % | MAE@1h | MAE@6h | MAE@12h | MAE@24h | Unseen: MAE | QL | COV80 % | Atlas-India against it (trained / unseen) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for nm in sorted(full, key=lambda n: RES["pooled"][n]["S"]["MAE"]):
        s, u = RES["pooled"][nm]["S"], RES["pooled"][nm]["U"]
        g = RES["significance"].get(nm)
        cmp = "–" if not g else " / ".join(f"{g[t]['MAE']['verdict']} {g[t]['MAE']['rel_diff_pct']:+.1f}% (p={g[t]['MAE']['p']:.2g})" for t in ("S", "U"))
        o.append(f"| {nm} | {s['MAE']:.2f} | {s['RMSE']:.2f} | {s['QL']:.2f} | {s['COV80']:.0f} | {s['MAE@1h']:.2f} | {s['MAE@6h']:.2f} | "
                 f"{s['MAE@12h']:.2f} | {s['MAE@24h']:.2f} | {u['MAE']:.2f} | {u['QL']:.2f} | {u['COV80']:.0f} | {cmp} |")
    others = [n for n in full if n != A]
    fx = RES.get("input_fix")
    if fx:                                                   # correction of 2026-11-13 (run_atlas_india.py --reforecast)
        o += ["", f"Input fix applied (weights unchanged) to seeds {[f['seed'] for f in fx]} by re-forecasting: variables that no trained "
              f"station of a network reports are no longer inputs there: {json.dumps(fx[0]['dropped'])}. Their single models on test as "
              f"first run (trained / unseen): E {[[round(v, 2) for v in f['as_run']['E']] for f in fx]}, F {[[round(v, 2) for v in f['as_run']['F']] for f in fx]}. "
              f"Largest change of any trained-station forecast: {max(max(f['trained_station_max_change'].values()) for f in fx):.4f} ug/m3."
              + (f" Seeds {RES['fixed_from_start']} were forecast with the fixed loader from the start." if RES.get("fixed_from_start") else "")]
    o += ["", "## Each network (MAE on trained stations; Atlas-India against the entry in brackets)", "",
          "| Network | stations (unseen) | mean PM2.5 in test | Atlas-India: trained / unseen | " + " | ".join(others) + " |",
          "|---|---|---|---|" + "---|" * len(others)]
    for k, r in RES["networks"].items():
        cells = []
        for n in others:
            c = r[n].get("atlas_vs")
            cells.append(f"{r[n]['S']:.2f}" + (f" ({c['verdict']} {c['rel']:+.1f}%)" if c else ""))
        o.append(f"| {k} | {r['stations']} ({r['unseen']}) | {r['mean_PM25_test']:.0f} | {r[A]['S']:.2f} / {r[A]['U']:.2f} | " + " | ".join(cells) + " |")
    tally = {n: [sum(1 for r in RES["networks"].values() if (r[n].get("atlas_vs") or {}).get("verdict") == v) for v in ("WIN", "TIE", "LOSS")] for n in others}
    o += ["", "Networks where Atlas-India wins / ties / loses (trained stations): " + "; ".join(f"{n}: {t[0]} / {t[1]} / {t[2]}" for n, t in tally.items()), "",
          "## Verdicts under the rules written before the run", ""] + [f"- {n}: {c}" for n, c in RES["claims"].items()] + [""]
    RES["tally"] = tally
    json.dump(RES, open(os.path.join(OUT, "india_results.json"), "w"), indent=1, default=float)
    open(os.path.join(OUT, "INDIA_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o))
    log(f"done in {RES['minutes']} min")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--quick", action="store_true")
    main(ap.parse_args())
