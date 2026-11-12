"""Atlas on Delhi, stage 8: (A) does a longer PM2.5 history close the gap to the foundation models, and
(B) the data and model-size threshold on real data.

Same data, splits, test windows and scoring as run_atlas_delhi.py (whose functions are reused). Plain Atlas only:
identification was not chosen on Delhi's validation data.

A  Context. The foundation models read 512 h of PM2.5; Atlas read 72 h. Variant "long": the same 72-h window of 15
   variables plus PM2.5 alone for the 264 h before it (336 h in all). Both recipes: 1M parameters, 3 seeds each,
   all training data. Rule (fixed here): the long variant is adopted only if its mean validation MAE is lower by
   more than 2 standard errors of the difference (from the two sets of 3 seeds). The adopted recipe's 3 seeds are
   ensembled, CQR on validation, and scored once on test against the cached foundation-model forecasts.
B  Threshold. Base recipe (72 h), sizes x last-k-months of training data x 2 seeds; every run reports validation
   MAE and test MAE (trained stations, single model, median forecast). The threshold function
   error = floor + a*N^-alpha + b*P^-beta is fitted to the runs (N = training windows, P = parameters), checked on
   held-out cells (the largest data amount), and inverted for the data needed to reach each foundation model's MAE.
   Caveat written in advance: "more months" also means other seasons, so N is not a count of identical samples.

  python run_atlas_threshold.py            # --quick: pipeline check, numbers meaningless
"""
import argparse, json, os, time

import numpy as np

import run_atlas_delhi as R
from run_atlas_delhi import Delhi, TARGETS, E, FLOOR, SPD, DM, H, HZ, PER_DAY, TH, log

RES = {"A": {}, "B": {"runs": []}, "tracks": {}, "significance": {}, "skipped": []}
T0 = time.time()


def save():
    os.makedirs(R.OUT, exist_ok=True)
    json.dump(RES, open(os.path.join(R.OUT, "atlas_threshold_results.json"), "w"), indent=1, default=float)


def main(a):
    q = a.quick
    D = Delhi(targets=TARGETS, backbone=False, wxfc=False)
    log(D.describe())
    tr, va, te = D.origins("train", R.TRAIN_STRIDE), D.origins("val", R.VAL_STRIDE), D.origins("test", R.TEST_STRIDE)
    lo = max(DM * SPD, 7 * SPD) + R.L + (0 if q else a.long)       # same training windows for both context lengths
    tr = tr[tr >= lo]
    va_fast = va[::2]
    if q:
        va, va_fast, te = va[:30], va[:30:2], te[:40]
    steps = 60 if q else a.steps
    upos = np.arange(D.N)[D.unseen]
    yv, yS, yU = R.truth(D, va, D.seen), R.truth(D, te, D.seen), R.truth(D, te, D.unseen)
    sc = lambda qq, yy: E.score(qq, yy, horizons=HZ, floor=FLOOR["PM2.5"], step_min=60)
    left = lambda: a.hours * 3600 - (time.time() - T0)
    preds = {"S": {}, "U": {}}

    def record(name, qS, qU, extra=None):
        RES["tracks"][name] = {"S": sc(qS, yS), "U": sc(qU, yU), **(extra or {})}
        preds["S"][name], preds["U"][name] = qS, qU
        log(f"TEST {name}: Track S MAE {RES['tracks'][name]['S']['MAE']:.2f}, Track U MAE {RES['tracks'][name]['U']['MAE']:.2f}")
        save()

    # ------------------------------------------------------------------ A: context length
    size = a.size if not q else 150000
    seeds = (200, 201, 202) if not q else (200, 201)
    groups = {}
    for nm, long in (("base 72 h", 0), ("long 336 h", a.long if not q else 48)):
        R.LONG = long
        ms = [R.train(D, size, 0, tr, va_fast, s, steps, f"A-{nm}-s{s}") for s in seeds]
        vals = [i["val_MAE"] for _, i in ms]
        groups[nm] = dict(long=long, models=[m for m, _ in ms], vals=vals)
        RES["A"][nm] = dict(val_MAE=vals, mean=float(np.mean(vals)), sd=float(np.std(vals, ddof=1)),
                            params=ms[0][1]["params"], minutes=[i["minutes"] for _, i in ms])
        log("CONTEXT " + nm + " " + json.dumps(RES["A"][nm], default=float)); save()
    b, l = RES["A"]["base 72 h"], RES["A"]["long 336 h"]
    se = float(np.sqrt(b["sd"] ** 2 / len(seeds) + l["sd"] ** 2 / len(seeds)))
    adopt = (b["mean"] - l["mean"]) > 2 * se
    pick = "long 336 h" if adopt else "base 72 h"
    RES["A"]["decision"] = dict(diff=b["mean"] - l["mean"], se=se, adopted=pick,
                                rule="long adopted only if mean validation MAE is lower by more than 2 standard errors")
    log("DECISION " + json.dumps(RES["A"]["decision"], default=float)); save()
    for nm, g in groups.items():                                   # both are scored so the test effect is visible
        R.LONG = g["long"]
        ens = lambda org, nodes: np.sort(np.mean([R.predict(m, D, org, nodes) for m in g["models"]], 0), -1)
        d = E.fit_cqr(ens(va, D.seen), yv)
        record(f"Atlas {nm} (3 seeds)" + (" [adopted]" if nm == pick else ""), E.apply_cqr(ens(te, D.seen), d),
               E.apply_cqr(ens(te, np.arange(D.N))[:, upos], d))
    FINAL = f"Atlas {pick} (3 seeds) [adopted]"
    R.LONG = 0
    del groups

    # cached foundation-model forecasts (from the atlas-delhi run's output, attached as input)
    od = os.path.join(R.OUT, "opponents")
    for f in sorted(os.listdir(od)) if os.path.isdir(od) else []:
        try:
            zz = np.load(os.path.join(od, f)); meta = json.loads(str(zz["meta"]))
            if zz["qt"].shape[0] != len(te):
                raise ValueError(f"cached forecasts cover {zz['qt'].shape[0]} windows, test has {len(te)}")
            d = E.fit_cqr(zz["qv"][:, D.seen], R.truth(D, va[::4], D.seen))
            record(meta["name"] + " zero-shot", E.apply_cqr(zz["qt"][:, D.seen], d), E.apply_cqr(zz["qt"][:, D.unseen], d))
        except Exception as e:
            log(f"  cached opponent {f} unusable: {type(e).__name__}: {e}"); RES["skipped"].append(f"opponent {f}: {e}")
    for t, yt in (("S", yS), ("U", yU)):
        RES["significance"][t] = {}
        for other, qo in preds[t].items():
            if other == FINAL:
                continue
            r = E.compare(preds[t][FINAL], qo, yt, PER_DAY, "MAE", reps=200 if q else 2000, floor=FLOOR["PM2.5"])
            if r:
                RES["significance"][t][other] = r
                log(f"SIG track {t} vs {other}: {r['verdict']} {r['rel_diff_pct']:+.2f}% p={r['p']:.2g}")
    save()

    # ------------------------------------------------------------------ B: threshold grid
    span = D.bounds["train"][1]
    sizes = [int(x) for x in a.sizes.split(",")] if not q else [60000, 150000]
    months = [0.5, 1, 2, 4, 8, 99] if not q else [0.5, 99]
    plan = [(s, mo, sd) for sd in (0, 1) for mo in months for s in sizes]            # seed 0 of everything first
    plan += [(int(x), mo, 0) for x in (a.big.split(",") if a.big and not q else []) for mo in (2, 99)]
    for size, mo, seed in plan:
        if left() < 1500:
            RES["skipped"].append(f"B size {size} months {mo} seed {seed}: time budget"); continue
        sub = tr if mo == 99 else tr[tr >= span - int(mo * 30.4 * SPD)]
        if mo != 99 and len(sub) >= len(tr):
            continue
        m, info = R.train(D, size, 0, sub, va_fast, seed, steps, f"B-{size}-{mo}mo-s{seed}")
        mae = float(np.nanmean(np.abs(R.predict(m, D, te, D.seen)[..., 1] - yS)))
        RES["B"]["runs"].append(dict(size=size, params=info["params"], months=round(len(sub) * R.TRAIN_STRIDE / (30.4 * SPD), 2),
                                     N=len(sub), seed=seed, val_MAE=info["val_MAE"], test_MAE=mae, steps=info["steps"],
                                     minutes=info["minutes"], hit_time_cap=info["hit_time_cap"]))
        log("THRESHOLD " + json.dumps(RES["B"]["runs"][-1], default=float)); save()
        del m
    fit_threshold(); save(); report()
    log(f"done in {(time.time() - T0) / 60:.1f} min")


def fit_threshold():
    runs = RES["B"]["runs"]
    if len(runs) < 10:
        return
    out = {}
    targets = {n: v["S"]["MAE"] for n, v in RES["tracks"].items() if "zero-shot" in n}
    for y in ("test_MAE", "val_MAE"):
        f = TH.fit(runs, y=y)
        o = dict(fit=f)
        nmax = max(r["N"] for r in runs)
        small, held = [r for r in runs if r["N"] < nmax], [r for r in runs if r["N"] == nmax]
        if len(small) >= 8 and held:
            fs = TH.fit(small, y=y)
            e = np.array([np.log(float(TH.pred(fs, r["N"], r["params"])) / r[y]) for r in held])
            o["holdout"] = dict(n_fit=len(small), n_held=len(held), rms_log=float(np.sqrt((e ** 2).mean())), bias_log=float(e.mean()))
        if y == "test_MAE":
            rng = np.random.default_rng(0); BF = []           # bootstrap: resample runs, refit
            for _ in range(100):
                try:
                    BF.append(TH.fit([runs[i] for i in rng.integers(0, len(runs), len(runs))], y=y, starts=1))
                except Exception:
                    pass
            pmax = max(r["params"] for r in runs)
            o["floor_interval"] = TH.interval(BF, lambda g: g["floor"])
            o["need"] = {}
            for n, tgt in targets.items():
                o["need"][n] = dict(target=tgt, P=pmax, N=TH.need_data(f, tgt, pmax),
                                    interval=TH.interval(BF, lambda g: TH.need_data(g, tgt, pmax)),
                                    N_any_size=TH.need_data(f, tgt, 1e12), measured_max_N=nmax)
        out[y] = o
    RES["B"]["threshold"] = out
    log("THRESHOLD-FIT " + json.dumps(out, default=float))


def report():
    o = ["# Atlas on Delhi, stage 8: context length and the data threshold (generated)", ""]
    A = RES["A"]
    if "decision" in A:
        o += ["## A. Context length (1M parameters, 3 seeds each)", "", "| recipe | validation MAE per seed | mean | spread |", "|---|---|---|---|"]
        o += [f"| {k} | {', '.join(f'{x:.2f}' for x in v['val_MAE'])} | {v['mean']:.3f} | {v['sd']:.3f} |" for k, v in A.items() if k != "decision"]
        d = A["decision"]
        o += ["", f"Difference {d['diff']:+.3f} µg/m3, standard error {d['se']:.3f}: adopted = {d['adopted']}.", ""]
    for t, title in (("S", "trained stations"), ("U", "unseen stations")):
        o += [f"## Test, {title} (PM2.5 MAE, µg/m3)", "", "| Model | MAE | MAE@1h | MAE@6h | MAE@12h | MAE@24h | adopted Atlas against it |", "|---|---|---|---|---|---|---|"]
        for n, v in sorted(RES["tracks"].items(), key=lambda kv: kv[1][t]["MAE"]):
            s = v[t]; g = RES["significance"].get(t, {}).get(n)
            cmp = "–" if not g else f"{'WINS' if g['verdict'] == 'WIN' else ('LOSES' if g['verdict'] == 'LOSS' else 'tie')} {g['rel_diff_pct']:+.1f}% (p={g['p']:.2g})"
            o.append(f"| {n} | {s['MAE']:.2f} | {s['MAE@1h']:.2f} | {s['MAE@6h']:.2f} | {s['MAE@12h']:.2f} | {s['MAE@24h']:.2f} | {cmp} |")
        o.append("")
    runs = RES["B"]["runs"]
    if runs:
        ps = sorted({r["params"] for r in runs}); ns = sorted({(r["N"], r["months"]) for r in runs})
        for y, title in (("test_MAE", "test MAE, trained stations"), ("val_MAE", "validation MAE")):
            o += [f"## B. Threshold grid: {title} (mean over seeds)", "", "| parameters | " + " | ".join(f"{mo} mo ({n:,} windows)" for n, mo in ns) + " |", "|---" * (len(ns) + 1) + "|"]
            for p in ps:
                cs = []
                for n, _ in ns:
                    v = [r[y] for r in runs if r["params"] == p and r["N"] == n]
                    cs.append("–" if not v else f"{np.mean(v):.2f}" + (f" ±{np.std(v, ddof=1):.2f}" if len(v) > 1 else ""))
                o.append(f"| {p:,} | " + " | ".join(cs) + " |")
            o.append("")
    th = RES["B"].get("threshold")
    if th:
        f = th["test_MAE"]["fit"]
        o += ["## Threshold function on real data (fitted to test MAE)", "",
              f"floor {f['floor']:.2f} µg/m3 (10–90% interval {th['test_MAE']['floor_interval'][0]:.2f}–{th['test_MAE']['floor_interval'][2]:.2f}), "
              f"alpha {f['alpha']:.3f}, beta {f['beta']:.3f}, typical misfit x{np.exp(f['rms_log']):.3f}."]
        h = th["test_MAE"].get("holdout")
        if h:
            o += [f"Held-out check: fitted without the largest data amount ({h['n_fit']} runs), it predicts those {h['n_held']} runs within x{np.exp(h['rms_log']):.3f} (bias x{np.exp(h['bias_log']):.3f})."]
        o += ["", "| to reach | its MAE | training windows needed at the largest size (10–90% interval) | measured up to |", "|---|---|---|---|"]
        g = lambda x: "not reachable (below the fitted floor)" if not np.isfinite(x) or x > 1e15 else f"{x:,.0f}"
        o += [f"| {n} | {v['target']:.2f} | {g(v['N'])} ({g(v['interval'][0])} – {g(v['interval'][2])}) | {v['measured_max_N']:,} |" for n, v in th["test_MAE"]["need"].items()] + [""]
    if RES["skipped"]:
        o += ["## Skipped", ""] + [f"- {x}" for x in RES["skipped"]] + [""]
    os.makedirs(R.OUT, exist_ok=True)
    open(os.path.join(R.OUT, "ATLAS_THRESHOLD_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--size", type=int, default=1_000_000)
    ap.add_argument("--long", type=int, default=264)
    ap.add_argument("--sizes", default="60000,250000,1000000")
    ap.add_argument("--big", default="4000000", help="extra sizes run at 2 months and all data, 1 seed, if time allows")
    ap.add_argument("--hours", type=float, default=10.5)
    main(ap.parse_args())
