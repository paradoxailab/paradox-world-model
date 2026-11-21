"""Atlas-100M on the six ParadoxBench traffic networks (rules: atlas/m100/PREREG.md). Test windows are read once.

For each network: the traffic view forecasts the validation windows (to fit the 80% band by the harness's own
conformal calibration, pwm/calibration.py) and the official test windows; the submission is recorded with
paradoxbench.score.record on Track A (12-step context: it is within the standard context) and, the same forecasts,
on Track B. Then paired tests (paradoxbench.significance: Diebold-Mariano, day-block bootstrap) against every other
submission on the same task and track, Holm-corrected over the whole family; a WIN needs p_holm < 0.01 and a 95%
interval that excludes 0 (stricter than ParadoxBench's 0.05).

  cd v0.6-conference && python ../atlas/m100/score_traffic.py --view $OUT/atlas100m_traffic_view.pt
  Atlas-100M-T (PREREG_TRAFFIC.md):  ... score_traffic.py --plus $STORE/traffic_plus/atlas100mT_best.pt --name Atlas-100M-T
"""
import argparse, glob, json, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from m100 import domains as Dm
from atlas.grow import load_any

MODEL = "Atlas-100M"


def holm(ps):
    order = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (m - r) * ps[i])); adj[i] = run
    return adj


def main(a):
    from pwm.calibration import fit_cqr, apply_cqr
    from paradoxbench.score import record, SUB
    from paradoxbench.significance import test_pair
    global MODEL
    MODEL = a.name
    if a.plus:
        from m100.traffic_plus import load_plus
        view = load_plus(a.plus, Dm.DEV)
    else:
        view = load_any(a.view, Dm.DEV).to(Dm.DEV).eval()
    P = int(json.load(open(a.summary))["params"]["total"]) if a.summary and os.path.exists(a.summary) else None
    if a.plus and P is not None:                                          # the old 80,322-parameter traffic adapter is
        P += view.counts()["trainable"] - 80_322                          # replaced by everything traffic trains now
    tasks = a.tasks.split(",") if a.tasks else Dm.TRAFFIC
    ctx = getattr(view, "ctx", 12)
    tracks = ("A", "B") if ctx <= 12 else ("B",)                        # Track A allows 12 steps of look-back only
    res = {"model": MODEL, "params_total": P, "context_steps": ctx, "networks": {}}
    for task in tasks:
        n = Dm.TrafficNet(task)
        n.L = ctx
        qv = n.predict(view, n.val_idx)                                   # [W, H, N, 3]
        yv = n.ds.raw[n.val_idx[:, None] + np.arange(n.H)[None]]
        delta = fit_cqr(n.ds, qv[..., 0], qv[..., 2], yv, n.ds.valid(yv))
        qt = n.predict(view, n.test_idx)                                  # the test windows, read once
        c10, c50, c90 = apply_cqr(n.ds, qt[..., 0], qt[..., 1], qt[..., 2], delta)
        kind = ("trained (Atlas-100M with a larger traffic adapter: LoRA on the frozen shared core + sensor embeddings)"
                if a.plus else "trained (one model for weather, air quality and traffic)")
        meta = {"type": kind, "params": P, "context_steps": n.L,
                "trained_on": "train splits of the six traffic networks + WEATHER-5K 2014-2021 + all-India PM2.5 train period"}
        out = {}
        for tr in tracks:
            out[tr] = record(task, tr, MODEL, c10, c50, c90, meta, n.ds)["metrics"]
        res["networks"][task] = out
    rows = []
    for task in tasks:
        for tr in tracks:
            ours = os.path.join(SUB, f"{task}__{tr}__{MODEL}.npz")
            for f in sorted(glob.glob(os.path.join(SUB, f"{task}__{tr}__*.npz"))):
                if f == ours or "STUB" in f:
                    continue
                r = test_pair(task, tr, ours, f)
                r.update(task=task, track=tr, opponent=os.path.basename(f)[len(f"{task}__{tr}__"):-4])
                rows.append(r)
    if rows:
        adj = holm(np.array([r["p_value"] for r in rows]))
        for r, p in zip(rows, adj):
            r["p_holm"] = float(p)
            ci_ok = r["rel_ci95_pct"][1] < 0 if r["diff"] < 0 else r["rel_ci95_pct"][0] > 0
            r["verdict"] = ("WIN" if r["diff"] < 0 else "LOSS") if (p < 0.01 and ci_ok) else "TIE"
            print(f"TEST {r['task']:<9} {r['track']} vs {r['opponent'][:48]:<48} ours {r['MAE_a']:.3f} theirs {r['MAE_b']:.3f} "
                  f"{r['rel_diff_pct']:+.2f}% [{r['rel_ci95_pct'][0]:+.2f}, {r['rel_ci95_pct'][1]:+.2f}] p_holm {r['p_holm']:.2g} "
                  f"{r['verdict']}", flush=True)
    res["tests"] = rows
    os.makedirs(a.out, exist_ok=True)
    fn = "atlas100m_traffic_results.json" if MODEL == "Atlas-100M" else MODEL.lower().replace("-", "") + "_traffic_results.json"
    json.dump(res, open(os.path.join(a.out, fn), "w"), indent=1, default=float)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--view", default="")
    ap.add_argument("--plus", default="")
    ap.add_argument("--name", default="Atlas-100M")
    ap.add_argument("--summary", default="")
    ap.add_argument("--tasks", default="")
    ap.add_argument("--out", default=os.environ.get("ATLAS_OUT", "out"))
    main(ap.parse_args())
