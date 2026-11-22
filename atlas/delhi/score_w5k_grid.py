"""Phase 3 of "Head-to-head on WEATHER-5K and the minimum threshold function" (README, rules written 2026-11-17 14:45 IST;
form C and the bootstrap made exact on 2026-11-22, before any grid run, README "Threshold grid on Colab").

Reads the Atlas-5K runs from scratch at H = 24 h on the size x data grid (validation 2022, every 4th station, every 6th
hour), E = mean over the five variables of MAE / the benchmark's scale. Grid: sizes 0.1M, 0.3M, 1M, 3M, 10M x nested
shares 1/64, 1/16, 1/4, all of the 2014-2021 training days (the 1M cells are the WB1-T runs), plus second seeds of 1M-all
and 10M-all for the noise level.

Forms, fitted by least squares in log E on the 12 cells with share <= 1/4 and size <= 3M:
  A  data only, per size    E = c_P + a_P n^-alpha_P        (cannot predict an unseen size)
  B  additive               E = c + a n^-alpha + b P^-beta  (the project's function, atlas/atlas/threshold.py)
  C  interacting            E = c + (a n^(-alpha/g) + b P^(-beta/g))^g   (g = 1 gives B)
Held out (8 cells): the all-data column (0.1M, 0.3M, 1M, 3M) and the 10M row (1/64, 1/16, 1/4, all).
Verified: median |pred/meas - 1| <= 3 % and largest <= 6 % on the held-out cells, and lower median error than the
nearest-cell baseline; a miss within twice the seed-to-seed spread counts as within noise. The verified form with the
lowest held-out median error is the MTF; it is inverted for E* = 0.97 x each opponent's validation E (Phase 1a).
Phase 4 (a 37.7M model) is indicated only if the MTF predicts >= 1 % lower E at all data than 10M, with the lower end of
its 80 % bootstrap interval still a gain. If no form passes, that is reported and no extrapolated claim is made.

  ATLAS_OUT=<dir with the run JSONs> python score_w5k_grid.py
"""
import glob, json, os, re

import numpy as np
from scipy.optimize import curve_fit

OUT = os.environ.get("ATLAS_OUT", "/kaggle/working/out")
STD = np.array([13.08167293, 12.13875438, 99.67403125, 2.65729403, 9.17480999])
NAMES = ["Temperature", "Dewpoint", "Wind direction", "Wind speed", "Sea-level pressure"]
N_ALL = 2920 * 5672                                     # training station-days at share 1
SIZES = {"100k": 1e5, "300k": 3e5, "1m": 1e6, "3m": 3e6, "10m": 1e7}
SHARES = [1 / 64, 1 / 16, 1 / 4, 1.0]
OPP = {"TimesFM 3.0": 0.33197, "Chronos-2 multivariate": 0.33267, "Chronos-2": 0.33594, "TimesFM 2.5": 0.33770,
       "Chronos-Bolt": 0.33894}                         # Phase 1a validation E (README)


def log(*a):
    print(*a, flush=True)


def E_of(r):
    v = r["val"]["MAE"]
    return float(np.mean([v[k] / s for k, s in zip(NAMES, STD)]))


def load():
    cells, seeds = {}, {}
    files = set(glob.glob(os.path.join(OUT, "*.json")))
    for f in sorted(files):
        b = os.path.basename(f)
        m = re.match(r"w5k_(seed2_)?(?:atlas_1m|grid_(100k|300k|3m|10m))_h24(?:_f(\d+))?_s(\d+)\.json$", b)
        if not m:
            continue
        r = json.load(open(f))
        if "val" not in r:
            continue
        size = m.group(2) or "1m"
        fr = float(r.get("frac") or 1.0)
        key = (size, round(fr, 6))
        d = dict(file=b, P=float(r.get("params") or SIZES[size]), n=float(r.get("train_station_days") or N_ALL * fr),
                 E=E_of(r), T=r["val"]["MAE"]["Temperature"], best_step=r.get("best_step"))
        (seeds if m.group(1) else cells)[key] = d
    return cells, seeds


def f_B(x, c, a, al, b, be):
    n, P = x
    return c + a * n ** -al + b * P ** -be


def f_C(x, c, a, al, b, be, g):
    n, P = x
    return c + (a * n ** (-al / g) + b * P ** (-be / g)) ** g


def f_A(n, c, a, al):
    return c + a * n ** -al


def fit_log(f, X, y, p0, lo, hi):
    p, _ = curve_fit(lambda x, *q: np.log(np.maximum(f(x, *q), 1e-9)), X, np.log(y), p0=p0, bounds=(lo, hi), maxfev=400000)
    return p


FORMS = {"B additive": (f_B, [0.2, 1.0, 0.2, 1.0, 0.2], [0, 0, 0, 0, 0], [np.inf, np.inf, 3, np.inf, 3]),
         "C interacting": (f_C, [0.2, 1.0, 0.2, 1.0, 0.2, 1.0], [0, 0, 0, 0, 0, 0.1], [np.inf, np.inf, 3, np.inf, 3, 10])}


def main():
    cells, seeds = load()
    for k in sorted(cells, key=lambda k: (SIZES[k[0]], k[1])):
        d = cells[k]
        log(f"{k[0]:>5} share {k[1]:<9g} P {d['P']:>11,.0f} n {d['n']:>12,.0f} E {d['E']:.5f} T {d['T']:.3f}  [{d['file']}]")
    need = [(s, round(fr, 6)) for s in SIZES for fr in SHARES]
    missing = [k for k in need if k not in cells]
    res = dict(cells={f"{k[0]}@{k[1]:g}": v for k, v in cells.items()}, seeds={f"{k[0]}@{k[1]:g}": v for k, v in seeds.items()},
               missing=[f"{k[0]}@{k[1]:g}" for k in missing])
    if missing:
        log("GRID-INCOMPLETE missing: " + ", ".join(res["missing"]) + " -- no fit is reported until every cell exists.")
        json.dump(res, open(os.path.join(OUT, "w5k_grid.json"), "w"), indent=1, default=float); return

    fit_k = [k for k in need if k[1] <= 0.25 + 1e-9 and SIZES[k[0]] <= 3e6]
    held = [k for k in need if k not in fit_k]
    assert len(fit_k) == 12 and len(held) == 8
    X = lambda ks: (np.array([cells[k]["n"] for k in ks]), np.array([cells[k]["P"] for k in ks]))
    Y = lambda ks: np.array([cells[k]["E"] for k in ks])

    # noise: seed-to-seed spread on 1M-all and 10M-all (relative)
    spread = [abs(seeds[k]["E"] / cells[k]["E"] - 1) for k in (("1m", 1.0), ("10m", 1.0)) if k in seeds]
    noise = float(np.mean(spread)) if spread else 0.0
    log(f"seed-to-seed spread: {[round(100 * s, 2) for s in spread]} %  -> noise allowance 2x = {200 * noise:.2f} %")

    # nearest-cell baseline: the fitted cell one grid step away (fewer data, or the next smaller size)
    si = {s: i for i, s in enumerate(SIZES)}; fi = {round(f, 6): i for i, f in enumerate(SHARES)}
    def nearest(k):
        best = min(fit_k, key=lambda j: (max(abs(si[j[0]] - si[k[0]]), abs(fi[j[1]] - fi[k[1]])),
                                         abs(si[j[0]] - si[k[0]]) + abs(fi[j[1]] - fi[k[1]])))
        return cells[best]["E"]
    base_err = np.array([abs(nearest(k) / cells[k]["E"] - 1) for k in held])
    res["baseline"] = dict(median=float(np.median(base_err)), max=float(base_err.max()))
    log(f"nearest-cell baseline: median {100 * np.median(base_err):.2f} %, largest {100 * base_err.max():.2f} %")

    forms = {}
    # A: per size, data only (predicts only the all-data column of sizes it has seen)
    predA = {}
    for s in SIZES:
        ks = [k for k in fit_k if k[0] == s]
        if len(ks) < 3:
            continue
        try:
            p, _ = curve_fit(lambda x, c, a, al: np.log(np.maximum(f_A(x, c, a, al), 1e-9)), X(ks)[0], np.log(Y(ks)),
                             p0=[0.2, 1.0, 0.2], bounds=([0, 0, 0], [np.inf, np.inf, 3]), maxfev=400000)
            for k in held:
                if k[0] == s:
                    predA[k] = float(f_A(cells[k]["n"], *p))
        except Exception as e:
            log(f"A {s}: fit failed ({e})")
    errA = {f"{k[0]}@{k[1]:g}": predA[k] / cells[k]["E"] - 1 for k in predA}
    forms["A data only, per size"] = dict(pred={f"{k[0]}@{k[1]:g}": v for k, v in predA.items()}, rel_err=errA,
                                          predicts=len(predA), note="cannot predict the unseen 10M row; not verifiable")
    for name, (f, p0, lo, hi) in FORMS.items():
        try:
            p = fit_log(f, X(fit_k), Y(fit_k), p0, lo, hi)
        except Exception as e:
            forms[name] = dict(error=str(e)); log(f"{name}: fit failed ({e})"); continue
        pred = {k: float(f((np.array([cells[k]["n"]]), np.array([cells[k]["P"]])), *p)[0]) for k in held}
        rel = np.array([pred[k] / cells[k]["E"] - 1 for k in held])
        tol = lambda e, t: abs(e) <= t or abs(e) <= 2 * noise
        med = float(np.median(np.abs(rel)))
        ok = (tol(med, 0.03) and all(tol(e, 0.06) for e in rel) and med < np.median(base_err))
        forms[name] = dict(params=p.tolist(), pred={f"{k[0]}@{k[1]:g}": v for k, v in pred.items()},
                           rel_err={f"{k[0]}@{k[1]:g}": float(e) for k, e in zip(held, rel)},
                           median=med, max=float(np.abs(rel).max()), verified=bool(ok))
        log(f"{name}: params {np.round(p, 4).tolist()}  held-out median {100 * med:.2f} %, largest "
            f"{100 * np.abs(rel).max():.2f} %  -> {'VERIFIED' if ok else 'not verified'}")
        for k, e in zip(held, rel):
            log(f"   {k[0]:>5} @ {k[1]:<7g} pred {pred[k]:.5f} meas {cells[k]['E']:.5f} ({100 * e:+.2f} %)")
    res["forms"] = forms
    ver = [k for k, v in forms.items() if v.get("verified")]
    mtf = min(ver, key=lambda k: forms[k]["median"]) if ver else None
    res["MTF"] = mtf
    if not mtf:
        log("W5K-GRID-RULE no form verified: no threshold function is adopted and no extrapolated claim is made.")
        json.dump(res, open(os.path.join(OUT, "w5k_grid.json"), "w"), indent=1, default=float); return

    # refit the MTF on all 20 cells for inversion, with a residual bootstrap (1,000) for intervals
    f, p0, lo, hi = FORMS[mtf]
    allk = need
    p_all = fit_log(f, X(allk), Y(allk), p0, lo, hi)
    resid = np.log(Y(allk)) - np.log(f(X(allk), *p_all))
    rng = np.random.default_rng(0); boots = []
    for _ in range(1000):
        yb = np.exp(np.log(f(X(allk), *p_all)) + rng.choice(resid, len(resid)))
        try:
            boots.append(fit_log(f, X(allk), yb, p_all, lo, hi))
        except Exception:
            pass
    Ef = lambda n, P, q: float(f((np.array([n]), np.array([P])), *q)[0])
    inv = {}
    for opp, e_opp in OPP.items():
        target = 0.97 * e_opp
        # smallest size that reaches the target at all data, and the data a 1M model needs
        Ps = np.logspace(4, 9, 400)
        hitP = next((P for P in Ps if Ef(N_ALL, P, p_all) <= target), None)
        ns = np.logspace(3, 10, 400)
        hitN = next((n for n in ns if Ef(n, 1e6, p_all) <= target), None)
        inv[opp] = dict(target_E=target, min_params_all_data=hitP, station_days_at_1M=hitN)
        log(f"E* = 0.97 x {opp} ({target:.4f}): smallest size at all data {hitP and f'{hitP:,.0f}'}; "
            f"station-days needed at 1M {hitN and f'{hitN:,.0f}'}")
    g10 = Ef(N_ALL, 1e7, p_all); g37 = Ef(N_ALL, 3.77e7, p_all)
    gb = [Ef(N_ALL, 3.77e7, q) / Ef(N_ALL, 1e7, q) - 1 for q in boots]
    lo80 = float(np.quantile(gb, 0.9)) if gb else float("nan")           # the least favourable end of the 80 % interval
    gain = g37 / g10 - 1
    phase4 = bool(gain <= -0.01 and lo80 < 0)
    res.update(mtf_params_all=p_all.tolist(), inversion=inv,
               phase4=dict(pred_E_10M=g10, pred_E_37_7M=g37, rel_change=gain, worst_end_80=lo80, indicated=phase4))
    log(f"Phase 4: predicted E at all data 10M {g10:.5f}, 37.7M {g37:.5f} ({100 * gain:+.2f} %, 80 % interval worst end "
        f"{100 * lo80:+.2f} %) -> {'indicated' if phase4 else 'not indicated'}")
    log("W5K-GRID-RULE " + json.dumps(dict(MTF=mtf, phase4=phase4)))
    json.dump(res, open(os.path.join(OUT, "w5k_grid.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
