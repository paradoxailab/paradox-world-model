"""WB1-T (README, "WB1-T: the data threshold function at 1M parameters on WEATHER-5K", written before these runs).

Reads the 1M Atlas-5K runs at H = 24 (w5k_atlas_1m_h24[_f<share>]_s600.json), each a nested share of the 2014-2021
training days (all 5,672 stations), and their 2022 validation MAE (every 4th station, every 6th hour). Error measure:
E = mean over the five variables of validation MAE / the benchmark's scale (standardised), and temperature MAE.
Fits three candidate threshold functions on the four smallest shares and predicts the larger ones:
  A  pure power law          E = a n^-alpha
  B  power law + floor       E = c + a n^-alpha            (the project's threshold function, atlas/threshold.py)
  C  saturating (Hill)       E = c + a / (1 + (n / n0)^alpha)
n = training station-days. Score = mean |log(predicted / measured)| on the held-out shares.

  python score_w5k_thr.py
"""
import glob, json, os, re

import numpy as np
from scipy.optimize import curve_fit

OUT = os.environ.get("ATLAS_OUT", "/kaggle/working/out")
STD = np.array([13.08167293, 12.13875438, 99.67403125, 2.65729403, 9.17480999])
NAMES = ["Temperature", "Dewpoint", "Wind direction", "Wind speed", "Sea-level pressure"]
FORMS = {
    "A power law": (lambda n, a, al: a * n ** -al, [1.0, 0.1]),
    "B power law + floor": (lambda n, c, a, al: c + a * n ** -al, [0.2, 1.0, 0.3]),
    "C saturating": (lambda n, c, a, n0, al: c + a / (1 + (n / n0) ** al), [0.2, 0.5, 1e5, 1.0]),
}


def log(*a):
    print(*a, flush=True)


def load():
    pts = {}
    for f in set(glob.glob(os.path.join(OUT, "w5k_atlas_1m_h24*.json")) + glob.glob("/kaggle/input/**/w5k_atlas_1m_h24*.json", recursive=True)):
        if "_v2" in os.path.basename(f):                  # improvement candidates are not points of the data curve
            continue
        r = json.load(open(f))
        fr = float(r.get("frac") or 1.0)
        v = r["val"]["MAE"]
        E = float(np.mean([v[k] / s for k, s in zip(NAMES, STD)]))
        n = float(r.get("train_station_days") or 0) or 2920 * r["stations"] * fr
        pts[fr] = dict(n=n, E=E, T=v["Temperature"], best_step=r.get("best_step"), params=r.get("params"))
    return dict(sorted(pts.items()))


def fit(form, n, y):
    f, p0 = FORMS[form]
    lo = [0] * len(p0); hi = [np.inf] * len(p0)
    p, _ = curve_fit(lambda x, *q: np.log(f(np.exp(x), *q)), np.log(n), np.log(y), p0=p0, bounds=(lo, hi), maxfev=200000)
    return p


def main():
    P = load()
    for fr, d in P.items():
        log(f"share {fr:<9g} station-days {d['n']:>12,.0f}  E {d['E']:.4f}  T {d['T']:.3f}  (best step {d['best_step']})")
    shares = sorted(P)
    small = [s for s in shares if s <= 0.125]
    held = [s for s in shares if s > 0.125]
    res = {"points": P, "forms": {}}
    for y_key in ("E", "T"):
        for form in FORMS:
            n = np.array([P[s]["n"] for s in small]); y = np.array([P[s][y_key] for s in small])
            if len(small) < len(FORMS[form][1]):
                continue
            try:
                p = fit(form, n, y)
            except Exception as e:                          # a form that cannot be fitted counts as failed
                res["forms"][f"{y_key} {form}"] = dict(error=str(e)); continue
            f = FORMS[form][0]
            pred = {s: float(f(P[s]["n"], *p)) for s in held}
            err = {s: float(np.log(pred[s] / P[s][y_key])) for s in held}
            score = float(np.mean(np.abs(list(err.values())))) if err else float("nan")
            res["forms"][f"{y_key} {form}"] = dict(params=p.tolist(), pred=pred, log_err=err, score=score)
            log(f"{y_key} {form}: params {np.round(p, 4).tolist()}; held-out " +
                ", ".join(f"{s:g}: pred {pred[s]:.4f} meas {P[s][y_key]:.4f} ({100 * err[s]:+.1f}%)" for s in held) +
                f"; mean |error| {100 * score:.2f}%")
    b = res["forms"].get("E B power law + floor", {})
    ok = bool(b) and "score" in b and all(abs(e) <= 0.03 for e in b["log_err"].values())
    best = min((k for k in res["forms"] if k.startswith("E ") and "score" in res["forms"][k]),
               key=lambda k: res["forms"][k]["score"], default=None)
    res["rule"] = dict(verified="YES" if ok else "no", best_form=best,
                       adopt_new_form=(best is not None and best != "E B power law + floor" and
                                       res["forms"][best]["score"] < 0.5 * b.get("score", np.inf)))
    log("W5K-THR-RULE " + json.dumps(res["rule"]))
    json.dump(res, open(os.path.join(OUT, "w5k_thr.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
