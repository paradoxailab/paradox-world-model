"""Atlas-W air core v0 on Delhi (rules: atlas/README.md, "Atlas-W", written before any score).

Same data file, windows, loss, optimiser and scoring as Atlas stage 8 (run_atlas_threshold.py); the model is
atlas/atlas/atlasw.py. Part 1: the data-threshold grid (last k months x width x 2 seeds), compared with Atlas's
stage-8B numbers on the same windows. Part 2: all 16 months, 3 seeds of the validation-chosen width, ensembled,
calibrated, scored once and tested against the cached foundation-model forecasts.

  python run_atlasw.py            # --quick: pipeline check, numbers meaningless
"""
import argparse, glob, json, math, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
import run_atlas_delhi as R
import run_atlas_long as RL
from run_atlas_delhi import Delhi, TARGETS, E, FLOOR, SPD, DM, H, HZ, PER_DAY, TH, log
from atlas.atlasw import AtlasW

MONTHS = [0.5, 1, 2, 4, 8, 99]
ATLAS_8B = {50232: [47.3, 48.3, 50.6, 43.1, 38.0, 35.1], 231312: [43.5, 47.1, 51.9, 43.6, 36.9, 34.9],
            967632: [42.7, 42.8, 44.2, 40.0, 35.4, 34.3]}          # README, stage 8B: test MAE, mean of 2 seeds
FM = {"tfm25": "TimesFM 2.5 (Google, zero-shot)", "chronos2": "Chronos-2 (Amazon, zero-shot)",
      "chronos-bolt": "Chronos-Bolt (Amazon, zero-shot)"}
RES = {"grid": [], "tracks": {}, "significance": {}, "claims": {}}
T0 = time.time()


RESFILE = "atlasw_results.json"


def save():
    os.makedirs(R.OUT, exist_ok=True)
    json.dump(RES, open(os.path.join(R.OUT, RESFILE), "w"), indent=1, default=float)


def build(D, d, **kw):
    return AtlasW(d=d, L=R.L, H=H, C=D.K + D.Ca, U=4, static=2 * DM + 2 * H + 2,
                  lo=[0.0] * D.K + [float("-inf")] * D.Ca, **kw).to(R.DEV)


def grid2(a, widths):
    """Day 3b (README): this run's widths plus the day-1 grid (atlasw_results.json from run atlasw-v0), one threshold
    function over all of them, and the best width at each data amount."""
    prior = sorted(glob.glob(os.path.join("/kaggle/input", "**", "atlasw_results.json"), recursive=True))
    rows = list(RES["grid"])
    if prior:
        old = json.load(open(prior[0]))["grid"]
        rows += [r for r in old if r["width"] not in widths]
        log(f"day-1 grid: {len(old)} runs from {prior[0]}")
    allw = sorted({r["width"] for r in rows})
    cell = lambda d, mo, k: float(np.mean([r[k] for r in rows if r["width"] == d and r["months_asked"] == mo]))
    table = {d: {str(mo): dict(test=cell(d, mo, "test_MAE"), val=cell(d, mo, "val_MAE"),
                              params=next(r["params"] for r in rows if r["width"] == d)) for mo in MONTHS} for d in allw}
    best = {str(mo): min(allw, key=lambda d: table[d][str(mo)]["val"]) for mo in MONTHS}
    f = TH.fit(rows, y="test_MAE")
    pr = {str(d): float(TH.pred(f, max(r["N"] for r in rows), table[d][str(MONTHS[0])]["params"])) for d in allw}
    RES["grid2"] = dict(widths=allw, runs=len(rows), table=table, best_width_by_validation=best, fit=f,
                        fit_at_full_data_by_width=pr)
    log("THRESHOLD2 " + json.dumps(RES["grid2"], default=float))
    o = ["# Atlas-W day 3b: the threshold function with the parameter axis (generated)", "",
         "| width | parameters | " + " | ".join("all (15 mo)" if m == 99 else f"{m} mo" for m in MONTHS) + " |", "|---|---|" + "---|" * len(MONTHS)]
    for d in allw:
        o.append(f"| {d} | {table[d][str(MONTHS[0])]['params']:,} | " + " | ".join(f"{table[d][str(m)]['test']:.1f}" for m in MONTHS) + " |")
    o += ["", "Best width by validation at each amount: " + json.dumps(best), "",
          f"Fit: floor {f['floor']:.2f}, a {f['a']:.3g}, alpha {f['alpha']:.3f}, b {f['b']:.3g}, beta {f['beta']:.3f}, misfit x{math.exp(f['rms_log']):.3f}, {f['n']} runs"]
    RES["minutes"] = round((time.time() - T0) / 60, 1)
    save()
    open(os.path.join(R.OUT, "GRID2_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o)); log(f"done in {RES['minutes']} min")


def main(a):
    q = a.quick
    D = Delhi(targets=TARGETS, backbone=False, wxfc=False)
    log(D.describe())
    tr, va, te = D.origins("train", R.TRAIN_STRIDE), D.origins("val", R.VAL_STRIDE), D.origins("test", R.TEST_STRIDE)
    tr = tr[tr >= max(DM * SPD, 7 * SPD) + R.L + (0 if q else 264)]          # exactly stage 8's training windows
    va_fast, va4 = va[::2], va[::4]
    if q:
        va, va_fast, va4, te = va[:30], va[:30:2], va[:30:4], te[:40]
    S, U, ALL = D.seen, D.unseen, np.arange(D.N)
    yS, yU, yv4 = R.truth(D, te, S), R.truth(D, te, U), R.truth(D, va4, S)
    steps = 60 if q else a.steps
    widths = [int(x) for x in a.widths.split(",")]
    span = D.bounds["train"][1]
    kw = dict(exchange=not a.no_exchange)
    log(f"Atlas-W parameters: " + ", ".join(f"width {d}: {build(D, d, **kw).n_params():,}" for d in widths) + f"; device {R.DEV}")
    keep = {}                                                                  # full-data models, for part 2

    def fit(d, sub, seed, name):
        torch.manual_seed(seed)
        m = build(D, d, **kw)
        info = RL.train(D, m, sub, va_fast, seed, steps, name, 1e-3, a.cap, 100 if not q else 30, 10)
        mae = float(np.nanmean(np.abs(R.predict(m, D, te, S)[..., 1] - yS)))
        return m, info, mae

    # ------------------------------------------------------------------ 1: data threshold grid
    for seed in (0, 1):
        for mo in (MONTHS if not q else [0.5, 99]):
            sub = tr if mo == 99 else tr[tr >= span - int(mo * 30.4 * SPD)]
            if mo != 99 and len(sub) >= len(tr):
                continue
            for d in widths:
                m, info, mae = fit(d, sub, seed, f"W{d}-{mo}mo-s{seed}")
                RES["grid"].append(dict(width=d, params=m.n_params(), months_asked=mo, months=round(len(sub) * R.TRAIN_STRIDE / (30.4 * SPD), 2),
                                        N=len(sub), seed=seed, val_MAE=info["val_MAE"], test_MAE=mae, steps=info["steps"], minutes=info["minutes"]))
                log("ATLASW-GRID " + json.dumps(RES["grid"][-1], default=float)); save()
                if mo == 99:
                    keep[(d, seed)] = m
    # rule 2 ------------------------------------------------------------------------------------------------
    mean = lambda d, mo, key="test_MAE": float(np.mean([r[key] for r in RES["grid"] if r["width"] == d and r["months_asked"] == mo]))
    table = {d: [mean(d, mo) for mo in MONTHS] for d in widths} if not q else {}
    if table:
        bestW = [min(table[d][i] for d in widths) for i in range(len(MONTHS))]
        bestA = [min(v[i] for v in ATLAS_8B.values()) for i in range(len(MONTHS))]
        first = lambda xs, thr: next((MONTHS[i] if MONTHS[i] != 99 else 15 for i, x in enumerate(xs) if x < thr), None)
        RES["rule2"] = dict(months=MONTHS, atlasw=table, atlasw_best=bestW, atlas_best=bestA,
                            more_data_efficient=bool(all(bestW[i] < bestA[i] for i in range(4))),
                            months_to_below_same_hour_yesterday_40_30=dict(atlasw=first(bestW, 40.30), atlas=first(bestA, 40.30)),
                            months_to_below_36=dict(atlasw=first(bestW, 36.0), atlas=first(bestA, 36.0)))
        log("RULE2 " + json.dumps(RES["rule2"], default=float))
        try:                                                                   # rule 4: threshold function, extrapolation
            f = TH.fit(RES["grid"], y="test_MAE")
            pmax = max(r["params"] for r in RES["grid"])
            RES["threshold"] = dict(fit=f, need={n: dict(target=t, N=TH.need_data(f, t, pmax), measured_max_N=int(len(tr)))
                                                 for n, t in (("TimesFM 2.5", 30.83), ("Chronos-2", 31.17), ("Chronos-Bolt", 31.35))})
            log("THRESHOLD-FIT " + json.dumps(RES["threshold"], default=float))
        except Exception as e:
            log(f"threshold fit failed: {type(e).__name__}: {e}")
        save()
    if a.grid_only:                                                            # day 3b: the parameter axis
        grid2(a, widths)
        return
    # ------------------------------------------------------------------ 2: full data, 3 seeds, ensemble
    vmean = {d: np.mean([r["val_MAE"] for r in RES["grid"] if r["width"] == d and r["months_asked"] == 99]) for d in widths}
    dbest = min(vmean, key=vmean.get)
    RES["full"] = dict(val_mean_by_width={str(k): float(v) for k, v in vmean.items()}, chosen_width=dbest)
    models = [keep[(dbest, 0)], keep[(dbest, 1)]]
    m, info, mae = fit(dbest, tr, 2, f"W{dbest}-all-s2")
    models.append(m)
    RES["full"]["seed2"] = dict(val_MAE=info["val_MAE"], test_MAE=mae)

    def ens(org):
        f = np.zeros((len(org), D.N, H, 3), np.float32)
        f[:, S] = np.mean([R.predict(x, D, org, S) for x in models], 0)
        f[:, U] = np.mean([R.predict(x, D, org, ALL)[:, U] for x in models], 0)
        return f
    qv, qt = ens(va4), ens(te)
    dq = E.fit_cqr(qv[:, S], yv4)
    qc = E.apply_cqr(qt, dq)
    sc = lambda qq, yy: E.score(qq, yy, horizons=HZ, floor=FLOOR["PM2.5"], step_min=60)
    A = f"Atlas-W v0 ({models[0].n_params():,} parameters, 3 seeds, 16 months of Delhi)"
    P = {A: qc}
    RES["tracks"][A] = {"S": sc(qc[:, S], yS), "U": sc(qc[:, U], yU)}
    log(f"TEST {A}: Track S MAE {RES['tracks'][A]['S']['MAE']:.2f}, Track U MAE {RES['tracks'][A]['U']['MAE']:.2f}")
    os.makedirs(os.path.join(R.OUT, "league2"), exist_ok=True)
    np.savez_compressed(os.path.join(R.OUT, "league2", "atlasw_v0.npz"), qv=qv, qt=qt, name=np.array(A),
                        meta=np.array(json.dumps(dict(params=models[0].n_params(), width=dbest, seeds=3, data="DELHI.npz, 16 months"))))
    torch.save({"cfg": models[0].cfg, "states": [x.state_dict() for x in models], "stations": D.stations}, os.path.join(R.OUT, "atlasw_v0.pt"))
    for k, nm in FM.items():
        hits = sorted(glob.glob(os.path.join(R.OUT, "**", "opponents", k + ".npz"), recursive=True) +
                      glob.glob(os.path.join("/kaggle/input", "**", "opponents", k + ".npz"), recursive=True))
        if not hits or q:
            continue
        o = np.load(hits[0])
        qo = E.apply_cqr(o["qt"], E.fit_cqr(o["qv"][:, S], yv4))
        RES["tracks"][nm] = {"S": sc(qo[:, S], yS), "U": sc(qo[:, U], yU)}
        r = {t: {mm: E.compare(qc[:, c], qo[:, c], yy, PER_DAY, mm, reps=2000, floor=FLOOR["PM2.5"]) for mm in ("MAE", "QL")}
             for t, c, yy in (("S", S, yS), ("U", U, yU))}
        RES["significance"][nm] = r
        vS, vU = r["S"]["MAE"]["verdict"], r["U"]["MAE"]["verdict"]
        RES["claims"][nm] = "Atlas-W BEATS it" if (vS, vU) == ("WIN", "WIN") else ("Atlas-W LOSES to it" if "LOSS" in (vS, vU) else "level")
        log(f"TEST {nm}: Track S MAE {RES['tracks'][nm]['S']['MAE']:.2f}, Track U MAE {RES['tracks'][nm]['U']['MAE']:.2f}")
        log(f"SIG Atlas-W v0 vs {nm}: S {vS} {r['S']['MAE']['rel_diff_pct']:+.2f}% p={r['S']['MAE']['p']:.2g}; "
            f"U {vU} {r['U']['MAE']['rel_diff_pct']:+.2f}% p={r['U']['MAE']['p']:.2g} -> {RES['claims'][nm]}")
    RES["reference"] = {"Atlas v1.0 (967,632 parameters, 3 seeds, same 16 months)": [33.42, 29.07]}
    RES["minutes"] = round((time.time() - T0) / 60, 1)
    save()
    # report ------------------------------------------------------------------------------------------------
    o = ["# Atlas-W air core v0 on Delhi (generated)", "", "## Data threshold: single-model test MAE on trained stations, mean of 2 seeds", "",
         "| model | parameters | " + " | ".join("all (15 mo)" if m == 99 else f"{m} mo" for m in MONTHS) + " |", "|---|---|" + "---|" * len(MONTHS)]
    for d in (widths if table else []):
        o.append(f"| Atlas-W width {d} | {build(D, d, **kw).n_params():,} | " + " | ".join(f"{x:.1f}" for x in table[d]) + " |")
    for p, v in ATLAS_8B.items():
        o.append(f"| Atlas (stage 8B) | {p:,} | " + " | ".join(f"{x:.1f}" for x in v) + " |")
    o += ["", "Rule 2: " + json.dumps(RES.get("rule2", {}), default=float), "", "## Full data, 3-seed ensemble, calibrated", "",
          "| Entry | Trained: MAE | Never trained: MAE | QL | COV80 % | MAE@1h | MAE@6h | MAE@24h |", "|---|---|---|---|---|---|---|---|"]
    for nm, t in RES["tracks"].items():
        s = t["S"]
        o.append(f"| {nm} | {s['MAE']:.2f} | {t['U']['MAE']:.2f} | {s['QL']:.2f} | {s['COV80']:.0f} | {s['MAE@1h']:.2f} | {s['MAE@6h']:.2f} | {s['MAE@24h']:.2f} |")
    o += ["| Atlas v1.0 (recorded) | 33.42 | 29.07 | | | | | |", ""] + [f"- against {n}: {c}" for n, c in RES["claims"].items()]
    open(os.path.join(R.OUT, "ATLASW_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o)); log(f"done in {RES['minutes']} min")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--widths", default="32,64")
    ap.add_argument("--cap", type=float, default=50, help="minutes per run")
    ap.add_argument("--no-exchange", action="store_true")
    ap.add_argument("--grid-only", action="store_true", help="day 3b: the grid only, at --widths, merged with the day-1 grid")
    a = ap.parse_args()
    if a.grid_only:
        RESFILE = "atlasw_grid2_results.json"
    main(a)
