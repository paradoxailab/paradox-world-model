"""Atlas-W day 3a: the minimum-information table (rules: atlas/README.md, "Atlas-W days 2 and 3", written first).

Day 1's full-data setting (width 32, the league's 16 months, stage 8's windows, steps and caps). The base and each
removal R1..R8 are trained with seeds 0 and 1; the two seeds are averaged. Validation MAE on trained stations decides
the words (1% rule); test is reported, calibrated as every league entry, and tested against the base with the league's
test (day blocks, both tracks).

  python run_atlasw_ablate.py            # --quick: pipeline check, numbers meaningless
"""
import argparse, json, os, sys, time

import numpy as np
import torch

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
import run_atlas_delhi as R
import run_atlas_long as RL
from run_atlas_delhi import Delhi, TARGETS, E, FLOOR, SPD, DM, H, HZ, PER_DAY, log
from atlas.atlasw import AtlasW

T0 = time.time()
RES = {"runs": [], "variants": {}}


def save():
    os.makedirs(R.OUT, exist_ok=True)
    json.dump(RES, open(os.path.join(R.OUT, "atlasw_ablate.json"), "w"), indent=1, default=float)


def main(a):
    q = a.quick
    D = Delhi(targets=TARGETS, backbone=False, wxfc=False)
    log(D.describe())
    tr, va, te = D.origins("train", R.TRAIN_STRIDE), D.origins("val", R.VAL_STRIDE), D.origins("test", R.TEST_STRIDE)
    tr = tr[tr >= max(DM * SPD, 7 * SPD) + R.L + (0 if q else 264)]          # exactly day 1's (stage 8's) windows
    va_fast, va4 = va[::2], va[::4]
    if q:
        tr, va_fast, va4, te = tr[-200:], va[:30:2], va[:30:4], te[:40]
    S, U, ALL = D.seen, D.unseen, np.arange(D.N)
    yv4, yS, yU = R.truth(D, va4, S), R.truth(D, te, S), R.truth(D, te, U)
    names = TARGETS + ["CO", "SO2", "NH3", "NO", "AT", "RH", "WS", "WD sin", "WD cos", "SR", "BP"]
    assert len(names) == D.K + D.Ca, (len(names), D.K, D.Ca)
    weather = [i for i, v in enumerate(names) if v in ("AT", "RH", "WS", "WD sin", "WD cos", "SR", "BP")]
    others = [names.index(v) for v in ("PM10", "NO2", "Ozone")]
    V = {"base": {}, "R1": dict(exchange=False), "R2": dict(mix=False), "R3": dict(direct=True), "R4": dict(spans=()),
         "R5": dict(drop=tuple(weather)), "R6": dict(drop=tuple(others)), "R7": dict(use_static=False), "R8": dict(use_uf=False)}
    if a.only:
        V = {k: v for k, v in V.items() if k in a.only.split(",") or k == "base"}
    log(f"weather channels {[names[i] for i in weather]}; other pollutants {[names[i] for i in others]}; device {R.DEV}")
    steps = 60 if q else a.steps
    P, Pv = {}, {}
    for k, kw in V.items():
        fs, vs = [], []
        for seed in (0, 1):
            torch.manual_seed(seed)
            m = AtlasW(d=a.width, L=R.L, H=H, C=D.K + D.Ca, U=4, static=2 * DM + 2 * H + 2,
                       lo=[0.0] * D.K + [float("-inf")] * D.Ca, **kw).to(R.DEV)
            info = RL.train(D, m, tr, va_fast, seed, steps, f"{k}-s{seed}", 1e-3, a.cap, 30 if q else 100, 10)
            f = np.zeros((len(te), D.N, H, 3), np.float32)
            f[:, S] = R.predict(m, D, te, S)
            f[:, U] = R.predict(m, D, te, ALL)[:, U]
            fv = R.predict(m, D, va4, S)
            fs.append(f); vs.append(fv)
            RES["runs"].append(dict(variant=k, seed=seed, params=m.n_params(), val_MAE=info["val_MAE"], steps=info["steps"],
                                    minutes=info["minutes"], hit_time_cap=info["hit_time_cap"],
                                    test_S=float(np.nanmean(np.abs(f[:, S][..., 1] - yS))), test_U=float(np.nanmean(np.abs(f[:, U][..., 1] - yU)))))
            log("ABLATE-RUN " + json.dumps(RES["runs"][-1], default=float)); save()
        Pv[k] = np.sort(np.mean(vs, 0), -1)
        qt = np.sort(np.mean(fs, 0), -1)
        P[k] = E.apply_cqr(qt, E.fit_cqr(Pv[k], yv4))
    sc = lambda qq, yy: E.score(qq, yy, horizons=HZ, floor=FLOOR["PM2.5"], step_min=60)
    vb = float(np.nanmean(np.abs(Pv["base"][..., 1] - yv4)))
    for k in V:
        v = float(np.nanmean(np.abs(Pv[k][..., 1] - yv4)))
        r = dict(what=V[k], params=next(x["params"] for x in RES["runs"] if x["variant"] == k), val_MAE=v,
                 val_change_pct=100 * (v / vb - 1), test={"S": sc(P[k][:, S], yS), "U": sc(P[k][:, U], yU)})
        if k != "base":
            r["vs_base"] = {t: E.compare(P["base"][:, c], P[k][:, c], yy, PER_DAY, "MAE", reps=a.reps, floor=FLOOR["PM2.5"])
                            for t, c, yy in (("S", S, yS), ("U", U, yU))}
            ch = r["val_change_pct"]
            r["words"] = "earns its place" if ch >= 1.0 else ("is not needed" if abs(ch) < 1.0 else "removing it helps (validation)")
        RES["variants"][k] = r
        log("ABLATE " + k + " " + json.dumps(r, default=float))
    r3 = RES["variants"].get("R3")
    if r3:
        RES["physics_form_helps"] = bool(r3["val_change_pct"] >= 1.0 and r3["vs_base"]["S"]["verdict"] == "WIN")
    RES["minutes"] = round((time.time() - T0) / 60, 1)
    save()
    o = ["# Atlas-W day 3a: the minimum-information table (generated)", "",
         "Each row: 2-seed average, width 32, 16 months of Delhi. Validation MAE on trained stations decides; test calibrated.", "",
         "| Variant | removed | parameters | validation MAE | change | test: trained | never trained | base against it (trained / never trained) | words |",
         "|---|---|---|---|---|---|---|---|---|"]
    for k, r in RES["variants"].items():
        cmp = "–" if k == "base" else " / ".join(f"{r['vs_base'][t]['verdict']} {r['vs_base'][t]['rel_diff_pct']:+.1f}% (p={r['vs_base'][t]['p']:.2g})" for t in ("S", "U"))
        o.append(f"| {k} | {json.dumps(r['what'])} | {r['params']:,} | {r['val_MAE']:.3f} | {r['val_change_pct']:+.1f}% | "
                 f"{r['test']['S']['MAE']:.2f} | {r['test']['U']['MAE']:.2f} | {cmp} | {r.get('words', '–')} |")
    o += ["", f"The physics form helps (rule: R3 at least 1% worse on validation and the base significantly better on trained stations): {RES.get('physics_form_helps')}"]
    open(os.path.join(R.OUT, "ABLATE_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o)); log(f"done in {RES['minutes']} min")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--width", type=int, default=32)
    ap.add_argument("--cap", type=float, default=50, help="minutes per run")
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--only", default="", help="comma-separated variants (the base is always run)")
    main(ap.parse_args())
