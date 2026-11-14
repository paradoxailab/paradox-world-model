"""I1 (README, "Atlas v1.4 programme"): Atlas against India's operational forecasts on Delhi, winter 2024-25.

India's operational systems publish no archive of station forecasts, so a paired test is impossible. The independent
evaluation by CEEW (issue brief "How Well can Delhi Predict Air Quality?", October 2025) reports the skill of IITM's
WRF-Chem (400 m, the Air Quality Early Warning System) and IMD's SILAM on the same quantity for 1 Oct 2024 - 28 Feb
2025: Delhi's spatially averaged hourly PM2.5, Day-1 forecast. Atlas is scored on that quantity and window here:

  * Atlas is trained on nothing after 2024-09-30: pre-trained on the 13 other all-India networks (data to 2022), then
    trained on Delhi's history to 2024-07-31 (validation 2024-08-01 .. 2024-09-30), by the v1.3 recipe
    (kaggle_i1.sh; PW_SPLIT="2024-08-01,2024-10-01,2025-03-01"). Stage B or C is chosen on validation, as in v1.1.
  * Forecasts issued at 00:00 IST every day for that day's 24 hours (lead 1-24 h); the seeds' medians averaged.
  * Delhi average at each hour = mean over the stations reporting PM2.5 that hour (forecast and measurement alike).
  * Metrics on the hourly series, as CEEW: RMSE, MAE, mean bias (forecast - measured), Pearson r, MAPE.
The comparison is by number only. Known differences: CEEW's observations came from the AQEWS portal (station set not
stated); its Day-1 lead time is not stated and may be longer than Atlas's 1-24 h; its hour count (3,512) is below the
window's 3,624 hours. Our measured mean is printed beside CEEW's for a check of the observation sets.

  python score_i1.py
"""
import argparse, json, os, sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.dirname(ROOT))
from pw.ddata import Delhi, TARGETS, SPD, RAW
import run_atlas_delhi as R
from score_india import found

OUT, H = R.OUT, R.H
CEEW = {"source": "CEEW issue brief 'How Well can Delhi Predict Air Quality?' (October 2025), winter 2024-25 = 1 Oct 2024 - 28 Feb 2025",
        "IITM WRF-Chem 400 m (AQEWS), Day 1": dict(RMSE=92.53, MAE=58.75, MBE=-25.21, R=0.61, MAPE=35, obs_mean=175, pred_mean=149),
        "IMD SILAM, Day 1": dict(RMSE=107.95, MAE=71.68, MBE=-22.88, R=0.47, MAPE=45, obs_mean=177, pred_mean=154)}


def log(*a):
    print(*a, flush=True)


def metrics(p, y):
    m = np.isfinite(p) & np.isfinite(y)
    p, y = p[m], y[m]
    e = p - y
    pos = y > 0
    return dict(hours=int(m.sum()), RMSE=float(np.sqrt(np.mean(e ** 2))), MAE=float(np.mean(np.abs(e))), MBE=float(np.mean(e)),
                R=float(np.corrcoef(p, y)[0, 1]), MAPE=float(100 * np.mean(np.abs(e[pos]) / y[pos])), obs_mean=float(y.mean()),
                pred_mean=float(p.mean()))


def main(a):
    D = Delhi(path=os.path.join(RAW, "DELHI_LONG.npz"), targets=TARGETS, backbone=False, wxfc=False, first=a.first)
    log(D.describe())
    Z = [np.load(f) for f in found(f"{a.tag}_s*.npz")]
    assert Z, f"no {a.tag}_s*.npz attached"
    metas = [json.loads(str(z["meta"])) for z in Z]
    vB, vC = np.mean([m["B"]["val_MAE"] for m in metas]), np.mean([m["C"]["val_MAE"] for m in metas])
    st = "C" if vC < vB else "B"
    log(f"I1 stage chosen on validation: {st} (mean validation MAE B {vB:.3f}, C {vC:.3f}; seeds {[m['seed'] for m in metas]})")
    te = Z[0]["test_origins"]
    for z in Z:
        assert (z["test_origins"] == te).all()
    q = np.mean([z[f"{st}_t"] for z in Z], 0)[..., 1]          # [W, N, H] seed-averaged median
    mid = (D.tod[te] == 0)                                      # forecasts issued at 00:00 IST
    org = te[mid]
    fo = org[:, None] + np.arange(H)[None]                      # the issue day's 24 hours
    y = D.Y[fo][..., 0].transpose(0, 2, 1)                      # [days, N, H]
    p = q[mid]
    obs = np.isfinite(y)
    with np.errstate(all="ignore"):
        ym = np.where(obs.any(1), np.nansum(np.where(obs, y, 0), 1) / obs.sum(1), np.nan)       # Delhi average [days, H]
        pm = np.where(obs.any(1), np.nansum(np.where(obs, p, 0), 1) / obs.sum(1), np.nan)
    hrs = D.dates[fo].reshape(-1)
    res = {"stage": st, "days": int(len(org)), "first_hour": str(hrs[0]), "last_hour": str(hrs[-1]), "stations": D.N, "ceew": CEEW}
    res["Atlas (00 IST, lead 1-24 h)"] = metrics(pm.reshape(-1), ym.reshape(-1))
    # reference forecasts on the same series
    yd = D.Y[fo - SPD][..., 0].transpose(0, 2, 1)               # same hour yesterday, per station
    with np.errstate(all="ignore"):
        pd = np.where(obs.any(1), np.nansum(np.where(obs & np.isfinite(yd), yd, 0), 1) / (obs & np.isfinite(yd)).sum(1), np.nan)
    res["Same hour yesterday"] = metrics(pd.reshape(-1), ym.reshape(-1))
    last = D.Y[org - 1][..., 0]                                 # 23:00 the day before, held for the day
    with np.errstate(all="ignore"):
        pl = np.where(obs.any(1), np.nansum(np.where(obs & np.isfinite(last)[:, :, None], last[:, :, None], 0), 1)
                      / (obs & np.isfinite(last)[:, :, None]).sum(1), np.nan)
    res["Last observed value"] = metrics(pl.reshape(-1), ym.reshape(-1))
    for k in ("Atlas (00 IST, lead 1-24 h)", "Same hour yesterday", "Last observed value"):
        r = res[k]
        log(f"I1 {k}: RMSE {r['RMSE']:.2f}, MAE {r['MAE']:.2f}, MBE {r['MBE']:+.2f}, r {r['R']:.2f}, MAPE {r['MAPE']:.0f}%, "
            f"{r['hours']} hours, measured mean {r['obs_mean']:.0f}, forecast mean {r['pred_mean']:.0f}")
    A = res["Atlas (00 IST, lead 1-24 h)"]
    res["by_number"] = {s: dict(MAE=A["MAE"] < v["MAE"], RMSE=A["RMSE"] < v["RMSE"],
                                verdict="lower error by number" if (A["MAE"] < v["MAE"] and A["RMSE"] < v["RMSE"]) else
                                ("higher error by number" if (A["MAE"] > v["MAE"] and A["RMSE"] > v["RMSE"]) else "mixed"))
                        for s, v in CEEW.items() if s != "source"}
    log("I1-BY-NUMBER " + json.dumps(res["by_number"]))
    o = ["# I1: Atlas against India's operational forecasts, Delhi winter 2024-25 (generated)", "",
         f"Delhi average of the stations reporting each hour, {res['first_hour']} .. {res['last_hour']}; Atlas stage {st}, {len(Z)} seeds.", "",
         "| Forecast | RMSE | MAE | MBE | r | MAPE % | hours | measured mean | forecast mean |", "|---|---|---|---|---|---|---|---|---|"]
    for k in ("Atlas (00 IST, lead 1-24 h)", "Same hour yesterday", "Last observed value"):
        r = res[k]
        o.append(f"| {k} | {r['RMSE']:.2f} | {r['MAE']:.2f} | {r['MBE']:+.2f} | {r['R']:.2f} | {r['MAPE']:.0f} | {r['hours']} | {r['obs_mean']:.0f} | {r['pred_mean']:.0f} |")
    for s, v in CEEW.items():
        if s != "source":
            o.append(f"| {s} (CEEW) | {v['RMSE']:.2f} | {v['MAE']:.2f} | {v['MBE']:+.2f} | {v['R']:.2f} | {v['MAPE']} | 3512 (stated) | {v['obs_mean']} | {v['pred_mean']} |")
    o += ["", f"Source of the operational numbers: {CEEW['source']}. By number only; see the caveats in score_i1.py."]
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "i1_results.json"), "w"), indent=1, default=float)
    open(os.path.join(OUT, "I1_REPORT.md"), "w").write("\n".join(o) + "\n")
    log("\n".join(o))
    if a.extra:
        extra(D, Z, st, mid, org, fo, y, obs, ym, pm, pd, res)


def extra(D, Z, st, mid, org, fo, y, obs, ym, pm, pd, res):
    """Post-hoc additions for the paper (not pre-registered; no verdict changes): a day-block bootstrap interval for
    Atlas's MAE and RMSE and for its difference from same-hour-yesterday, each seed alone, metrics on the daily mean,
    and MAE by hour of day (= lead hour, since forecasts are issued at 00:00 IST)."""
    rng = np.random.default_rng(0)
    nd = len(org)
    def boot(f, reps=5000):
        v = np.array([f(rng.integers(0, nd, nd)) for _ in range(reps)])
        return [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]
    e = pm - ym
    ep = pd - ym
    ok = np.isfinite(e)
    mae_d = lambda E_, i: np.nanmean(np.abs(E_[i]))
    rmse_d = lambda E_, i: np.sqrt(np.nanmean(E_[i] ** 2))
    x = {"MAE_ci95": boot(lambda i: mae_d(e, i)), "RMSE_ci95": boot(lambda i: rmse_d(e, i)),
         "MAE_minus_yesterday_ci95": boot(lambda i: mae_d(e, i) - mae_d(ep, i))}
    log(f"I1-EXTRA bootstrap (days, 5000): Atlas MAE 95% CI {x['MAE_ci95'][0]:.2f}..{x['MAE_ci95'][1]:.2f}, RMSE "
        f"{x['RMSE_ci95'][0]:.2f}..{x['RMSE_ci95'][1]:.2f}; MAE minus same-hour-yesterday "
        f"{x['MAE_minus_yesterday_ci95'][0]:.2f}..{x['MAE_minus_yesterday_ci95'][1]:.2f}")
    per = []
    for z in Z:
        m = json.loads(str(z["meta"]))
        p1 = z[f"{st}_t"][..., 1][mid]
        with np.errstate(all="ignore"):
            pm1 = np.where(obs.any(1), np.nansum(np.where(obs, p1, 0), 1) / obs.sum(1), np.nan)
        r = metrics(pm1.reshape(-1), ym.reshape(-1))
        per.append(dict(seed=m["seed"], **r))
        log(f"I1-EXTRA seed {m['seed']} alone: RMSE {r['RMSE']:.2f}, MAE {r['MAE']:.2f}, MBE {r['MBE']:+.2f}, r {r['R']:.3f}")
    x["per_seed"] = per
    dm = lambda arr: np.where(np.isfinite(arr).sum(1) >= 18, np.nanmean(arr, 1), np.nan)     # daily mean, >= 18 of 24 hours
    for k, arr in (("Atlas", pm), ("Same hour yesterday", pd)):
        r = metrics(dm(np.where(np.isfinite(ym), arr, np.nan)), dm(ym))
        x[f"daily_{k}"] = r
        log(f"I1-EXTRA daily mean ({r['hours']} days) {k}: RMSE {r['RMSE']:.2f}, MAE {r['MAE']:.2f}, MBE {r['MBE']:+.2f}, r {r['R']:.3f}")
    x["MAE_by_hour"] = [float(np.nanmean(np.abs(e[:, h]))) for h in range(e.shape[1])]
    x["MAE_by_hour_yesterday"] = [float(np.nanmean(np.abs(ep[:, h]))) for h in range(ep.shape[1])]
    log("I1-EXTRA MAE by hour (00-23 IST) Atlas: " + " ".join(f"{v:.1f}" for v in x["MAE_by_hour"]))
    log("I1-EXTRA MAE by hour (00-23 IST) yesterday: " + " ".join(f"{v:.1f}" for v in x["MAE_by_hour_yesterday"]))
    x["obs_by_hour"] = [float(np.nanmean(ym[:, h])) for h in range(ym.shape[1])]
    log("I1-EXTRA measured mean by hour: " + " ".join(f"{v:.0f}" for v in x["obs_by_hour"]))
    res["extra"] = x
    json.dump(res, open(os.path.join(OUT, "i1_results.json"), "w"), indent=1, default=float)
    log("I1-EXTRA-DONE")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="i1")
    ap.add_argument("--first", default="2018-01-01")
    ap.add_argument("--extra", action="store_true", help="post-hoc additions for the paper (bootstrap, seeds, daily, by hour)")
    a = ap.parse_args()
    main(a)
