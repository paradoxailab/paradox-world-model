"""PWM-W data-threshold study: how much of a station network's own history does PWM-W need to beat the zero-shot
time-series foundation models (Google TimesFM 2.5 / 3.0, Amazon Chronos-2)?

For each league and each budget of M months, PWM-W is trained on ONLY the last M months before the validation period
(training windows, their inputs, and every normalisation statistic all inside the budget; no partner network). The
model setting is fixed in advance: v0.8's 14-day encoder + weight averaging, d=128, 3 layers (no tuning per budget).
Validation (fixed period) picks the checkpoint; 3 seeds are averaged; the test period and stations are the league's.
Each budget is compared with each foundation model on the same test windows (Diebold-Mariano + day-block bootstrap,
the leagues' rule). The foundation models use no training data at all; they read each series' last 512 hours.
Disclosed: the fixed validation period (2-3 months, the same for every budget) is used only to pick the training
checkpoint, so "M months" means M months of training data plus that checkpoint-selection period.

  python run_threshold.py --leagues CPCB METAR WMO
"""
import argparse, json, os, time

import numpy as np
import torch

import run_weather as RW
from pw.leagues import TARGETS
from pw.wdata import Wx
from pw import wtrain as WT
from pw import evaluate as EV

CFG = dict(d=128, layers=3, heads=4, ff=2, experts=0, use_graph=True, longctx=True, ema=True)
MONTH = 30 * 24


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", nargs="+", default=["CPCB", "METAR", "WMO"])
    ap.add_argument("--months", default="1,2,3,6,12,24,48")
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--opponents", default="chronos2,tfm25,tfm3")
    a = ap.parse_args()
    os.makedirs(RW.CACHE, exist_ok=True)
    allres = {}
    for lg in a.leagues:
        log = RW.log
        full = Wx(lg)
        tag = lg.lower()
        va = full.origins("val", 6)
        te = full.origins("test", 1)
        te = te[full.tod[te] % 6 == 0]
        avail_h = full.bounds["train"][1] - full.bounds["train"][0]
        entries, kinds, fm_meta = {}, {}, {}
        RW.run_fms(a.opponents, tag, full, te, entries, kinds, fm_meta)
        _, Y = WT.predict(WT.build(CFG, full), full, te)              # truth [W, n, K, H], NaN = not observed
        res = {"league": lg, "stations": full.N, "available_months": round(avail_h / MONTH, 1), "budgets": {}}
        months = [float(m) for m in a.months.split(",")] + [avail_h / MONTH]
        months = sorted(set(m for m in months if m * MONTH <= avail_h + 1))
        for M in months:
            D = Wx(lg, train_hours=int(M * MONTH))
            assert np.array_equal(D.keep, full.keep)
            tr = D.origins("train", 1)
            if len(tr) < 100:
                log(f"{lg} {M:.0f} months: only {len(tr)} training windows, skipped")
                continue
            t0 = time.time()
            qs, vs = [], []
            for s in (100, 101, 102):
                m, info = WT.train(dict(CFG), D, tr, None, va, a.steps, seed=s, log=lambda *x: None)
                q, _ = WT.predict(m, D, te)
                qs.append(q); vs.append(info["val_score"])
                del m; torch.cuda.empty_cache()
            q = np.mean(qs, 0)
            r = {"months": round(M, 1), "train_windows": int(len(tr)), "val": float(np.mean(vs)), "vs": {}}
            for k, v in enumerate(TARGETS):
                obs = np.isfinite(Y[:, :, k])
                r.setdefault("MAE", {})[v] = float(np.abs(q[:, :, k, :, 1] - np.nan_to_num(Y[:, :, k]))[obs].mean())
                for name in [n for n in entries if kinds[n] == "tsfm"]:
                    mk = obs & np.isfinite(entries[name][:, :, k, :, 1])
                    t = EV.compare(q[:, :, k], entries[name][:, :, k], np.where(mk, Y[:, :, k], np.nan), 4, "MAE")
                    r["vs"].setdefault(name, {})[v] = {kk: t[kk] for kk in ("verdict", "rel_diff_pct", "p", "ci95_pct")}
            res["budgets"][f"{M:.1f}"] = r
            line = "; ".join(f"{n.split(' (')[0]}: " + "/".join(f"{x['rel_diff_pct']:+.1f}%{'W' if x['verdict']=='WIN' else ('L' if x['verdict']=='LOSS' else '=')}"
                                                              for x in r["vs"][n].values()) for n in r["vs"])
            log(f"THRESHOLD {lg} {M:5.1f} months ({len(tr)} windows, {time.time() - t0:.0f}s): val {r['val']:.4f}; "
                f"vs [AT/RH/WS] {line}")
        # smallest budget from which PWM-W significantly beats each model on each variable at every larger budget
        th = {}
        keys = sorted(res["budgets"], key=float)
        for name in [n for n in entries if kinds[n] == "tsfm"]:
            for v in TARGETS:
                win = [res["budgets"][kk]["vs"][name][v]["verdict"] == "WIN" for kk in keys]
                first = next((i for i in range(len(win)) if all(win[i:])), None)
                th.setdefault(name, {})[v] = None if first is None else float(keys[first])
        res["threshold_months"] = th
        # smallest budget from which PWM-W is never significantly worse (tie or win) at every larger budget
        th0 = {}
        for name in [n for n in entries if kinds[n] == "tsfm"]:
            for v in TARGETS:
                ok = [res["budgets"][kk]["vs"][name][v]["verdict"] != "LOSS" for kk in keys]
                first = next((i for i in range(len(ok)) if all(ok[i:])), None)
                th0.setdefault(name, {})[v] = None if first is None else float(keys[first])
        res["no_loss_threshold_months"] = th0
        for name, d in th0.items():
            log(f"NO-LOSS-THRESHOLD {lg} vs {name}: " + ", ".join(
                f"{v} {'never' if m is None else str(m) + ' months'}" for v, m in d.items()))
        for name, d in th.items():
            log(f"THRESHOLD-RESULT {lg} vs {name}: " + ", ".join(
                f"{v} {'never (within ' + str(res['available_months']) + ' months)' if m is None else str(m) + ' months'}"
                for v, m in d.items()))
        allres[lg] = res
        json.dump(allres, open(os.path.join(RW.OUT, "threshold_results.json"), "w"), indent=1, default=float)
    json.dump({"log": RW.LOG}, open(os.path.join(RW.OUT, "threshold_log.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
