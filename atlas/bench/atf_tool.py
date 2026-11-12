"""ATF tool: how good will my forecaster get, and how much data do I need? (works on any hourly multi-series data)

Give it a table of hourly measurements (one column per sensor / customer / station, or an npz in the curves.py
format). It trains Atlas on the most recent 0.5, 1 and 2 months (2 seeds each; about 10-20 CPU-minutes), scores
them on the most recent held-out period, and applies the frozen ATF law (atf_law.json) to predict:
  * the error with every larger amount of data, with an 80% interval;
  * the months of data needed to reach a target error, or that more data alone will not reach it;
  * the gain to expect from doubling the data you have.
Errors are in standardised units of each series (MAE / spread of that series before the held-out period), so they are
comparable across series and datasets. --verify also trains on all the data you have and prints measured vs predicted.

  python atf_tool.py --csv my.csv --time-col timestamp --holdout-days 60 [--target-error 0.25] [--verify]
  python atf_tool.py --npz BENCH_ELEC.npz --target load --series 256:321 --verify
"""
import argparse, json, math, os, sys, tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import curves as CV


def to_npz(a, tmp):
    if a.csv:
        import pandas as pd
        d = pd.read_csv(a.csv, parse_dates=[a.time_col]).set_index(a.time_col).sort_index()
        d = d.select_dtypes("number").resample("h").mean()
        X = d.to_numpy(np.float32)[:, :, None]
        p = os.path.join(tmp, "DATA.npz")
        np.savez_compressed(p, X=X, vars=np.array(["value"]), stations=np.array([str(c) for c in d.columns]),
                            start=np.array(str(d.index[0])[:13].replace(" ", "T")))
        return "DATA.npz", "value"
    z = np.load(a.npz)
    X = z["X"]
    if a.series:                                     # "lo:hi" or a comma-separated list of series indices
        X = X[:, slice(*(int(v) for v in a.series.split(":")))] if ":" in a.series else X[:, [int(v) for v in a.series.split(",")]]
    p = os.path.join(tmp, "DATA.npz")
    np.savez_compressed(p, X=X, vars=z["vars"], stations=np.array([f"s{i}" for i in range(X.shape[1])]), start=z["start"])
    return "DATA.npz", a.target


def law_pred(law, e2, N):
    r = N / law["pilot_months"]
    p = e2 * (law["phi"] + (1 - law["phi"]) * r ** (-law["alpha"]))
    return p, p * math.exp(law["interval_log"][0]), p * math.exp(law["interval_log"][1])


def months_needed(law, e2, target):
    rel = target / e2
    if rel >= 1:
        return 0.0
    if rel <= law["phi"]:
        return float("inf")
    return law["pilot_months"] * ((rel - law["phi"]) / (1 - law["phi"])) ** (-1 / law["alpha"])


def main(a):
    law = json.load(open(a.law))
    tmp = tempfile.mkdtemp()
    fname, target = to_npz(a, tmp)
    CV.RAW = tmp
    spec = dict(name="your-data", file=fname, targets=[target], test_days=a.holdout_days, val_days=a.holdout_days,
                offset=0.0, amounts=[0.5, 1, 2], standardize=True)
    net = CV.Net(spec)
    print(net.describe())
    have = net.max_months
    yt = net.truth(net.test_org)
    pil = {}
    for mo in (0.5, 1, 2):
        e = []
        for seed in (0, 1):
            m, mu, sd, info = CV.run_one(net, mo, seed, a.steps, a.cap, a.size)
            e.append(float(np.nanmean(np.abs(CV.predict(net, m, net.test_org, mu, sd)[..., 1] - yt))))
        pil[mo] = float(np.mean(e))
        print(f"pilot {mo:>3} months: held-out MAE {pil[mo]:.4f} (seeds {', '.join(f'{x:.4f}' for x in e)})", flush=True)
    e2 = pil[2]
    pt, _ = CV.baselines(net, net.test_org)
    pers = float(np.nanmean(np.abs(pt - yt)))
    plan = sorted({x for x in (4, 8, 16, 32, 64) if x < have} | {round(have, 1)})
    out = dict(available_months=round(have, 1), pilot=pil, persistence=pers, law=law["version"], predictions={})
    print(f"\nYou have {have:.1f} months before the held-out period. Persistence (last value) scores {pers:.4f}.")
    print("Predicted held-out MAE with more of the most recent data (ATF, 80% interval):")
    for N in plan:
        p, lo, hi = law_pred(law, e2, N)
        out["predictions"][N] = dict(pred=p, lo=lo, hi=hi)
        print(f"  {N:>6} months: {p:.4f}  ({lo:.4f} - {hi:.4f})")
    p_have = law_pred(law, e2, have)[0]
    p_dbl = law_pred(law, e2, 2 * have)[0]
    gain = 100 * (1 - p_dbl / p_have)
    print(f"Doubling your data ({have:.1f} -> {2 * have:.1f} months) is predicted to cut the error by {gain:.1f}%.")
    out["gain_from_doubling_pct"] = gain
    if a.target_error:
        need = months_needed(law, e2, a.target_error)
        msg = ("already reached by the 2-month pilot" if need == 0 else
               "not reachable by more data alone (the law's floor is " + f"{law['phi'] * e2:.4f})" if not math.isfinite(need) else
               f"about {need:.0f} months of data")
        print(f"To reach MAE {a.target_error}: {msg}.")
        out["months_for_target"] = need
    if a.verify:
        e = []
        for seed in (0, 1):
            m, mu, sd, info = CV.run_one(net, 999, seed, a.steps, a.cap, a.size)
            e.append(float(np.nanmean(np.abs(CV.predict(net, m, net.test_org, mu, sd)[..., 1] - yt))))
        meas = float(np.mean(e))
        print(f"\nVERIFY: trained on all {have:.1f} months: measured {meas:.4f}, predicted {p_have:.4f} "
              f"(off by x{max(meas, p_have) / min(meas, p_have):.3f}); 2-month pilot alone would have said {e2:.4f}.")
        out["verify"] = dict(measured=meas, predicted=p_have)
    print("ATF-TOOL " + json.dumps(out, default=float))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv"); ap.add_argument("--time-col", default="timestamp")
    ap.add_argument("--npz"); ap.add_argument("--target", default="value"); ap.add_argument("--series", default="")
    ap.add_argument("--holdout-days", type=int, default=60)
    ap.add_argument("--target-error", type=float, default=0.0)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--law", default=os.path.join(HERE, "atf_law.json"))
    ap.add_argument("--steps", type=int, default=4000); ap.add_argument("--cap", type=float, default=15)
    ap.add_argument("--size", type=int, default=250_000)
    main(ap.parse_args())
