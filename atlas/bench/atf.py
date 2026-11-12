"""ATF v1.1: test threshold functions on networks they have not seen (rules fixed in the README before results).

Input: the CURVE and NETWORK lines printed by curves.py (any number of log files). For every network-target the
learning curve is e(N) = test MAE of Atlas trained on the most recent N months (mean of the seeds that ran).

Leave-one-network-out: for each network, every function is fitted on the other networks only, then predicts this
network's error at every data amount above 2 months from this network's own pilot runs (N <= 2 months).
  M0  no improvement            e(N) = e(2)
  M1  per-network power law     log e = a - alpha log N, least squares on the 0.5-, 1-, 2-month pilots
  M2  ATF, pooled               e(N) = e(2) [phi + (1 - phi)(N/2)^-alpha], alpha and phi pooled from other networks
  M3  ATF, pooled per variable  as M2, alpha and phi pooled per target variable
Primary measure: median |log(predicted / measured)| at each network-target's largest data amount. ATF "works" only if
M2 or M3 beats both M0 and M1 there AND a two-sided sign test over network-targets gives p < 0.05.

  python atf.py logs/*.txt            # -> ATF_REPORT.md, atf_results.json
"""
import glob, json, math, os, sys
from collections import defaultdict

import numpy as np
from scipy.optimize import least_squares
from scipy.stats import binomtest

P_N = 2.0                                     # pilot amount (months)


def read(paths):
    curves, nets = [], {}
    for p in paths:
        for line in open(p, errors="ignore"):
            line = line.strip()
            if line.startswith("CURVE "):
                curves.append(json.loads(line[6:]))
            elif line.startswith("NETWORK "):
                r = json.loads(line[8:]); nets[r["network"]] = r
    seen, out = set(), []
    for r in curves:                          # a run printed twice (log + tee) is counted once
        k = (r["network"], r["amount"], r["seed"])
        if k not in seen:
            seen.add(k); out.append(r)
    return out, nets


def build(curves, split="test"):
    """{(network, target): {"var": target, "N": [months...], "e": [mean MAE...], "n_seeds": [...], "sd": [...]}}"""
    g = defaultdict(lambda: defaultdict(list))
    for r in curves:
        for v, m in r[split].items():
            g[(r["network"], v)][r["months"] if r["amount"] < 999 else ("all", r["months"])].append(m["MAE"])
    out = {}
    for key, d in g.items():
        pts = []
        for a, vals in d.items():
            N = a[1] if isinstance(a, tuple) else a
            pts.append((float(N), float(np.mean(vals)), len(vals), float(np.std(vals, ddof=1)) if len(vals) > 1 else float("nan")))
        pts.sort()
        out[key] = dict(var=key[1], N=[p[0] for p in pts], e=[p[1] for p in pts], n=[p[2] for p in pts], sd=[p[3] for p in pts])
    return out


def pilot(c):
    """errors at the pilot amounts (<= 2 months, closest to 0.5, 1, 2)."""
    N, e = np.array(c["N"]), np.array(c["e"])
    sel = N <= P_N + 0.05
    return N[sel], e[sel]


def e2(c):
    N, e = pilot(c)
    return float(e[np.argmin(np.abs(N - P_N))]) if len(N) else float("nan")


def m1_fit(c):
    N, e = pilot(c)
    if len(N) < 2:
        return None
    b = np.polyfit(np.log(N), np.log(e), 1)
    return lambda x: float(np.exp(np.polyval(b, np.log(x))))


def g(r, phi, alpha):
    return phi + (1 - phi) * r ** (-alpha)


def pool_fit(train):
    """alpha, phi from the training curves' points above the pilot, relative to each curve's own e(2)."""
    X, Y = [], []
    for c in train:
        base = e2(c)
        if not np.isfinite(base) or base <= 0: continue
        for N, e in zip(c["N"], c["e"]):
            if N > P_N + 0.05:
                X.append(N / P_N); Y.append(math.log(e / base))
    X, Y = np.array(X), np.array(Y)
    if len(X) < 3:
        return 0.0, 1.0
    best = None
    for p0 in (0.3, 0.7):
        for a0 in (0.2, 1.0):
            r = least_squares(lambda q: np.log(g(X, q[0], q[1])) - Y, [p0, a0], bounds=([0.0, 0.0], [1.5, 5.0]))
            if best is None or r.cost < best.cost: best = r
    return float(best.x[1]), float(best.x[0])                 # alpha, phi


def predict_all(curves):
    keys = sorted(curves)
    nets = sorted({k[0] for k in keys})
    rows = []
    for net in nets:
        train = [curves[k] for k in keys if k[0] != net]
        a_all, p_all = pool_fit(train)
        per_var = {}
        for k in keys:
            if k[0] != net: continue
            c = curves[k]
            base = e2(c)
            f1 = m1_fit(c)
            if c["var"] not in per_var:
                tv = [t for t in train if t["var"] == c["var"]]
                per_var[c["var"]] = pool_fit(tv) if len(tv) >= 2 else (a_all, p_all)
            a_v, p_v = per_var[c["var"]]
            # 80% predictive interval: the training curves' own scatter around the pooled law (log residuals)
            res_ = [math.log(e_ / e2(t)) - math.log(g(N_ / P_N, p_all, a_all)) for t in train
                    for N_, e_ in zip(t["N"], t["e"]) if N_ > P_N + 0.05 and e2(t) > 0]
            lo_q, hi_q = (np.percentile(res_, 10), np.percentile(res_, 90)) if res_ else (0.0, 0.0)
            for i, (N, e) in enumerate(zip(c["N"], c["e"])):
                if N <= P_N + 0.05: continue
                r = N / P_N
                rows.append(dict(network=net, var=c["var"], N=N, measured=e, largest=(i == len(c["N"]) - 1),
                                 M0=base, M1=f1(N) if f1 else float("nan"), M2=base * g(r, p_all, a_all), M3=base * g(r, p_v, a_v),
                                 M2_lo=base * g(r, p_all, a_all) * math.exp(lo_q), M2_hi=base * g(r, p_all, a_all) * math.exp(hi_q),
                                 alpha=a_all, phi=p_all, alpha_v=a_v, phi_v=p_v))
    return rows


def evaluate(rows, methods=("M0", "M1", "M2", "M3")):
    res = {}
    for subset, sel in (("largest amount", [r for r in rows if r["largest"]]), ("all amounts > 2 months", rows)):
        if not sel: continue
        err = {m: np.array([abs(math.log(r[m] / r["measured"])) if r[m] > 0 and np.isfinite(r[m]) else np.inf for r in sel]) for m in methods}
        res[subset] = dict(n=len(sel), median_abs_log={m: float(np.median(err[m])) for m in methods},
                           mean_abs_log={m: float(np.mean(np.minimum(err[m], 5))) for m in methods},
                           within_10pct={m: float(np.mean(err[m] < math.log(1.1))) for m in methods})
        tests = {}
        for a in ("M2", "M3"):
            for b in ("M0", "M1"):
                wins = int(np.sum(err[a] < err[b])); losses = int(np.sum(err[a] > err[b]))
                tests[f"{a} vs {b}"] = dict(wins=wins, losses=losses, p=float(binomtest(wins, wins + losses).pvalue) if wins + losses else 1.0)
        res[subset]["sign_tests"] = tests
        res[subset]["M2_interval_coverage"] = float(np.mean([(r["M2_lo"] <= r["measured"] <= r["M2_hi"]) for r in sel]))
    big = res.get("largest amount")
    if big:
        med = big["median_abs_log"]
        ok = []
        for a in ("M2", "M3"):
            t = big["sign_tests"]
            if med[a] < med["M0"] and med[a] < med["M1"] and t[f"{a} vs M0"]["p"] < 0.05 and t[f"{a} vs M1"]["p"] < 0.05:
                ok.append(a)
        res["verdict"] = ("ATF WORKS (pre-registered rule met by " + ", ".join(ok) + ")") if ok else "ATF does NOT meet the pre-registered rule"
    return res


def report(curves, nets, rows, res, out):
    o = ["# ATF v1.1: threshold functions tested on unseen networks (generated)", "",
         f"{len(curves)} network-targets, {len({k[0] for k in curves})} networks.", "", "## Learning curves (test MAE; mean of seeds)", ""]
    for k in sorted(curves):
        c = curves[k]
        b = nets.get(k[0], {}).get("baselines", {}).get("test", {})
        pers = b.get("persistence", {}).get(k[1], {}).get("MAE"); yd = b.get("yesterday", {}).get(k[1], {}).get("MAE")
        o.append(f"- **{k[0]} {k[1]}**: " + ", ".join(f"{N:g} mo {e:.3f}" for N, e in zip(c["N"], c["e"]))
                 + (f" | persistence {pers:.3f}, same hour yesterday {yd:.3f}" if pers else ""))
    o += ["", "## Prediction of unseen networks' errors from 2-month pilots", ""]
    for subset in ("largest amount", "all amounts > 2 months"):
        r = res.get(subset)
        if not r: continue
        o += [f"### {subset} ({r['n']} predictions)", "", "| method | median abs log error | within 10% | mean abs log error (capped at 5) |", "|---|---|---|---|"]
        names = {"M0": "M0 no improvement", "M1": "M1 per-network power law", "M2": "M2 ATF pooled", "M3": "M3 ATF pooled per variable"}
        for m in ("M0", "M1", "M2", "M3"):
            o.append(f"| {names[m]} | {r['median_abs_log'][m]:.3f} (x{math.exp(r['median_abs_log'][m]):.3f}) | {100 * r['within_10pct'][m]:.0f}% | {r['mean_abs_log'][m]:.3f} |")
        o += ["", "Sign tests (wins / losses, two-sided p): " + "; ".join(f"{k} {v['wins']}/{v['losses']} p={v['p']:.3g}" for k, v in r["sign_tests"].items()),
              f"M2 80% interval covers the measured error in {100 * r['M2_interval_coverage']:.0f}% of cases.", ""]
    o += [f"**Verdict:** {res.get('verdict', 'not enough data')}", ""]
    open(os.path.join(out, "ATF_REPORT.md"), "w").write("\n".join(o) + "\n")
    json.dump(dict(results=res, rows=rows), open(os.path.join(out, "atf_results.json"), "w"), indent=1, default=float)
    print("\n".join(o))


if __name__ == "__main__":
    paths = [p for a in sys.argv[1:] for p in glob.glob(a)]
    curves_raw, nets = read(paths)
    curves = build(curves_raw)
    rows = predict_all(curves)
    res = evaluate(rows)
    report(curves, nets, rows, res, os.environ.get("ATF_OUT", "."))
