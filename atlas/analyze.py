"""Turn the run files into results/REPORT.md and results/summary.json. Every number comes from results/*.jsonl."""
import json

import numpy as np

from atlas import threshold as T

R = T.load(["results/runs_ladder.jsonl", "results/runs_systems.jsonl"])
BL = json.load(open("results/baselines.json"))
out, S = [], {}
P = lambda *a: out.append(" ".join(str(x) for x in a))
f3 = lambda x: "inf" if not np.isfinite(x) else (f"{x:.3f}" if x >= 0.01 else f"{x:.4f}")
fn = lambda x: "not reachable" if not np.isfinite(x) or x > 1e12 else f"{x:,.0f}"


def table(runs, rows, cols, rk="params", ck="N", y="nmse", sd=True):
    c = T.cells(runs, (rk, ck), y)
    P("| " + rk + " \\ " + ck + " | " + " | ".join(str(x) for x in cols) + " |"); P("|---" * (len(cols) + 1) + "|")
    for r in rows:
        cs = []
        for x in cols:
            v = c.get((r, x))
            cs.append("–" if v is None else (f3(v[0]) + (f" ±{v[1]:.3f}" if sd and v[2] > 1 else "")))
        P(f"| {r:,} | " + " | ".join(cs) + " |")
    P("")


P(f"# Atlas threshold experiments: measured results\n\n{len(R)} training runs, all from random initialisation, CPU only.\n")
NS = [30, 100, 300, 1000, 3000, 10000]

# ---------------- A. size x data, damped oscillator
lad = T.sel(R, system="damped", max_steps=3000)
sizes = sorted({r["params"] for r in lad})
P("## A. Model size x data amount (damped oscillator)\n\nTest error (normalised MSE on 2,000 fresh trajectories; mean ± spread over seeds where more than one seed ran). "
  f"Persistence {BL['damped']['persistence']:.3f}; ridge regression at N=10,000: {np.mean(BL['damped']['ridge']['10000']):.3f}; equation-aware oracle {BL['damped']['oracle']:.3f}.\n")
table(lad, sizes, [10, 18, 30, 55, 100, 180, 300, 550, 1000, 1800, 3000, 5500, 10000] if False else NS)
P("Training-set error for the same cells (how much is memorised):\n"); table(lad, sizes, NS, y="nmse_train", sd=False)
P("Runs that stopped at the step limit (training compute, not data, may be the limit there): "
  + ", ".join(f"P={r['params']:,} N={r['N']} seed {r['seed']}" for r in lad if r["steps"] >= r["max_steps"]) + "\n")
secs = T.cells(lad, ("params",), "secs")
P("Training time per run, CPU seconds (mean over that size's runs): " + ", ".join(f"{k[0]:,}: {v[0]:.0f}s" for k, v in secs.items()) + "\n")

# ---------------- B. fit + honest extrapolation test
grid6 = [r for r in lad if r["N"] in NS]
fall = T.fit(grid6)
S["fit_all"] = fall
P("## B. Threshold function\n\n`error(N, P) = floor + a·N^-alpha + b·P^-beta`, fitted to all " + str(fall["n"]) + " runs of table A:\n")
P(f"floor = {fall['floor']:.4f}, a = {fall['a']:.3f}, alpha = {fall['alpha']:.3f}, b = {fall['b']:.3g}, beta = {fall['beta']:.3f}; "
  f"typical misfit ×{np.exp(fall['rms_log']):.2f} (RMS of log error {fall['rms_log']:.3f}).\n")
small = [r for r in grid6 if r["N"] <= 3000 and r["size"] <= 1_000_000]
held = [r for r in grid6 if not (r["N"] <= 3000 and r["size"] <= 1_000_000)]
if held and small:
    fs = T.fit(small)
    e = np.array([np.log(T.pred(fs, r["N"], r["params"]) / r["nmse"]) for r in held])
    # naive reference: the nearest measured cell inside the fitting range (same or largest small size, largest small N)
    cs = T.cells(small)
    def naive(r):
        p = max(k[0] for k in cs if k[0] <= r["params"]); n = max(k[1] for k in cs if k[0] == p and k[1] <= r["N"])
        return cs[(p, n)][0]
    en = np.array([np.log(naive(r) / r["nmse"]) for r in held])
    S["extrapolation"] = dict(n_fit=len(small), n_held=len(held), fit_small=fs, rms_log=float(np.sqrt((e ** 2).mean())),
                              bias_log=float(e.mean()), naive_rms_log=float(np.sqrt((en ** 2).mean())))
    P(f"**Does it predict runs it has not seen?** Fitted only on runs with N ≤ 3,000 and size ≤ 1M ({len(small)} runs), then asked to predict the "
      f"{len(held)} runs with N = 10,000 or size ≥ 2M: typical error ×{np.exp(np.sqrt((e ** 2).mean())):.2f} "
      f"(mean bias ×{np.exp(e.mean()):.2f}; above 1 = predicts too high an error). "
      f"Naive reference (reuse the nearest measured cell): ×{np.exp(np.sqrt((en ** 2).mean())):.2f}.\n")
    P(f"Small-range fit: floor {fs['floor']:.4f}, alpha {fs['alpha']:.3f}, beta {fs['beta']:.3f}.\n")
    hc = T.cells(held)
    P("| held-out cell (P, N) | measured | predicted from the small runs |"); P("|---|---|---|")
    for k, v in hc.items(): P(f"| {k[0]:,}, {k[1]:,} | {f3(v[0])} | {f3(float(T.pred(fs, k[1], k[0])))} |")
    P("")
P("### Minimum data for a target error (inverting the fit; 10–90% bootstrap interval)\n")
P("| target error | model size | fitted minimum N | interval | measured crossing | inside measured range? |"); P("|---|---|---|---|---|---|")
cl = T.cells(grid6); S["need"] = []; BF = T.boot_fits(grid6, 100)
for tgt in (0.4, 0.3, 0.2, 0.15, 0.1, 0.05):
    for size in (sizes[3], sizes[5], sizes[-1]):
        nd = T.need_data(fall, tgt, size)
        lo, md, hi = T.interval(BF, lambda f: T.need_data(f, tgt, size))
        ns = [n for n in NS if (size, n) in cl]
        cr, how = T.crossing(ns, [cl[(size, n)][0] for n in ns], tgt)
        S["need"].append(dict(target=tgt, params=size, fit=nd, lo=lo, hi=hi, measured=cr, how=how))
        P(f"| {tgt} | {size:,} | {fn(nd)} | {fn(lo)} – {fn(hi)} | {fn(cr) if how == 'measured' else how} | {'yes' if np.isfinite(nd) and nd <= 10000 else 'no (extrapolated)'} |")
P("")
sd_seed = float(np.nanmean([v[1] for v in cl.values() if v[2] > 1]))
P(f"### What to add next (adaptive advice from the fit)\n\nSeed-to-seed spread of a single run is {sd_seed:.3f}, so a gain smaller than that needs several seeds to confirm.\n")
P("| you have (N, P) | predicted error | gain from 2× data | gain from 2× parameters | share of the excess error due to data | advice |"); P("|---|---|---|---|---|---|")
S["advice"] = []
for n, p in ((100, sizes[0]), (100, sizes[5]), (1000, sizes[0]), (1000, sizes[3]), (10000, sizes[0]), (10000, sizes[3]), (10000, sizes[-1]), (100000, sizes[-1]), (1000000, sizes[-1])):
    a = T.advise(fall, n, p); S["advice"].append(dict(N=n, P=p, **a))
    P(f"| {n:,}, {p:,} | {a['error_now']:.3f} | {a['gain_2x_data']:.3f} | {a['gain_2x_params']:.4f} | {100 * a['data_share_of_excess']:.0f}% | {a['advice']} |")
P("")

# ---------------- C. sudden or gradual
dense = [r for r in T.sel(R, system="damped", max_steps=3000) if r["size"] == 250_000]
dc = T.cells(dense, ("N",)); dn = [k[0] for k in dc]; de = [dc[k][0] for k in dc]
tr = T.transition(dn, de); S["transition"] = tr
gt = T.cells(dense, ("N",), "nmse_train")
P("## C. Is there a sudden threshold in data? (damped oscillator, 250K-parameter model, 13 data amounts)\n")
P("| N | " + " | ".join(str(n) for n in dn) + " |"); P("|---" * (len(dn) + 1) + "|")
P("| test error | " + " | ".join(f3(e) for e in de) + " |")
P("| seed spread | " + " | ".join(f"{dc[(n,)][1]:.3f}" for n in dn) + " |")
P("| training error | " + " | ".join(f3(gt[(n,)][0]) for n in dn) + " |\n")
P(f"Power law: error ∝ N^-{tr['power_slope']:.2f} (AICc {tr['aicc_power']:.1f}). Step (logistic in log N) centred at N ≈ {tr['step_centre_N']:.0f}: AICc {tr['aicc_step']:.1f}. "
  f"Largest local slope {tr['max_local_slope']:.2f} against an average of {tr['mean_slope']:.2f}. Lower AICc fits better; a difference under about 4 is not decisive.\n")

# ---------------- D. systems
P("## D. Four systems (sizes up to 1M here)\n")
S["systems"] = {}
for name in ("harmonic", "damped", "diffusion", "advdiff"):
    rs = [r for r in T.sel(R, system=name) if r["N"] in NS and r["max_steps"] in (2000, 3000) and r["size"] <= 1_000_000]
    if not rs: continue
    ps = sorted({r["params"] for r in rs}); b = BL[name]
    P(f"**{name}** — persistence {f3(b['persistence'])}, ridge at N=10,000 {f3(float(np.mean(b['ridge']['10000'])))}, oracle {f3(b['oracle'])}; "
      f"bits to state its parameters for error 0.1 / 0.03 / 0.01: {b['complexity_bits']['0.1'][0]:.1f} / {b['complexity_bits']['0.03'][0]:.1f} / {b['complexity_bits']['0.01'][0]:.1f}\n")
    table(rs, ps, NS)
    c = T.cells(rs); best_p = max(ps, key=lambda p: -c.get((p, 10000), (9,))[0])
    row = {}
    for tgt in (0.3, 0.1, 0.03):
        ns = [n for n in NS if (best_p, n) in c]
        row[tgt] = T.crossing(ns, [c[(best_p, n)][0] for n in ns], tgt)
    S["systems"][name] = dict(best_params=best_p, best_error=c[(best_p, 10000)][0], crossings={str(k): v for k, v in row.items()},
                              ridge=float(np.mean(b["ridge"]["10000"])), oracle=b["oracle"], bits=b["complexity_bits"])
P("Measured data threshold (trajectories needed by the best size ≤ 1M to reach a test error), next to the system's complexity in bits:\n")
P("| system | bits for 0.1 | N for error 0.3 | N for 0.1 | N for 0.03 | best error at N=10,000 | bits captured / available per value |"); P("|---|---|---|---|---|---|---|")
for name, s in S["systems"].items():
    g = lambda t: fn(s["crossings"][str(t)][0]) if s["crossings"][str(t)][1] == "measured" else s["crossings"][str(t)][1]
    s["bits_model"], s["bits_oracle"] = T.bits(s["best_error"]), T.bits(s["oracle"])
    P(f"| {name} | {s['bits']['0.1'][0]:.1f} | {g(0.3)} | {g(0.1)} | {g(0.03)} | {f3(s['best_error'])} | {s['bits_model']:.2f} / {s['bits_oracle']:.2f} |")
P("")

# ---------------- E. quality, diversity, compute
P("## E. Data quality, diversity and training compute (damped oscillator, 250K parameters)\n")
P("| setting | " + " | ".join(str(n) for n in NS) + " | oracle floor |"); P("|---" * (len(NS) + 2) + "|")
S["quality"] = {}
for noise in (0.0, 0.05, 0.2, 0.5):
    rs = [r for r in T.sel(R, system="damped", noise=noise, max_steps=3000) if r["size"] == 250_000 and r["N"] in NS]
    c = T.cells(rs, ("N",)); orc = BL["damped"]["oracle"] if noise == 0.05 else BL[f"damped_noise{noise}"]["oracle"]
    S["quality"][noise] = {n: c[(n,)][0] for n in NS if (n,) in c}
    P(f"| noise {noise} | " + " | ".join(f3(c[(n,)][0]) if (n,) in c else "–" for n in NS) + f" | {f3(orc)} |")
from atlas import systems as SY
sig = float(SY.make("damped", 4000, 5, 0.0)["clean_ctx"].var())
P(f"\n**Is the threshold a fixed number of Shannon bits?** One noisy observation can carry at most ½·log2(1 + signal variance / noise variance) bits "
  f"(signal variance {sig:.2f}). If a fixed amount of information were what matters, the data needed for one target error, counted in bits, would be the same at every noise level.\n")
P("| noise | bits per observation (upper bound) | N to reach error 0.4 | total bits at that N | N to reach error 0.3 | total bits at that N |"); P("|---|---|---|---|---|---|"); S["bits_threshold"] = {}
for noise in (0.05, 0.2, 0.5):
    q = S["quality"][noise]; b = 0.5 * np.log2(1 + sig / noise ** 2); row = [f"{noise}", f"{b:.2f}"]; S["bits_threshold"][noise] = {}
    for tgt in (0.4, 0.3):
        cr, how = T.crossing(list(q), list(q.values()), tgt)
        tot = cr * 0.8 * 16 * b
        S["bits_threshold"][noise][tgt] = dict(N=cr, bits=tot, how=how)
        row += [fn(cr) if how == "measured" else how, f"{tot:,.0f}" if how == "measured" else "–"]
    P("| " + " | ".join(row) + " |")
P("")
rs = [r for r in T.sel(R, system="damped", width=0.25, max_steps=3000) if r["size"] == 250_000]
c = T.cells(rs, ("N",)); S["narrow"] = {n: c[(n,)][0] for n in NS if (n,) in c}
P("| narrow diversity (¼ of the parameter range), tested on the full range | " + " | ".join(f3(c[(n,)][0]) if (n,) in c else "–" for n in NS) + " | |\n")
P("| training steps allowed | N = 1,000 | N = 10,000 |"); P("|---|---|---|"); S["compute"] = {}
for ms in (300, 1000, 3000, 10000):
    rs = [r for r in T.sel(R, system="damped", max_steps=ms) if r["size"] == 250_000]
    c = T.cells(rs, ("N",)); st = T.cells(rs, ("N",), "steps")
    S["compute"][ms] = {n: c[(n,)][0] for n in (1000, 10000) if (n,) in c}
    P(f"| {ms:,} | " + " | ".join((f3(c[(n,)][0]) + f" (used {st[(n,)][0]:.0f})") if (n,) in c else "–" for n in (1000, 10000)) + " |")
P("")

# ---------------- F. physics rule
P("## F. Hard conservation rule on / off (ring systems, 250K parameters)\n")
P("| system | rule | " + " | ".join(str(n) for n in NS) + " |"); P("|---" * (len(NS) + 2) + "|"); S["physics"] = {}
for name in ("diffusion", "advdiff"):
    for ph in (0, 1):
        rs = [r for r in T.sel(R, system=name, physics=ph) if r["size"] == 250_000 and r["max_steps"] == 2000]
        c = T.cells(rs, ("N",)); S["physics"][f"{name}_{ph}"] = {n: c[(n,)][0] for n in NS if (n,) in c}
        P(f"| {name} | {'on' if ph else 'off'} | " + " | ".join((f3(c[(n,)][0]) + f" ±{c[(n,)][1]:.3f}") if (n,) in c else "–" for n in NS) + " |")
P("")

# ---------------- G. the other abilities
P("## G. Other abilities at N = 10,000 (largest size run per system)\n")
P("| system | params | forecast error | unseen parameter range (model / oracle) | 30% of inputs missing | intervention error | 80% interval coverage | width–error rank correlation | AUROC: width flags unseen range |"); P("|---|---|---|---|---|---|---|---|---|")
S["abilities"] = {}
for name in ("harmonic", "damped", "diffusion", "advdiff"):
    rs = [r for r in T.sel(R, system=name) if r["N"] == 10000 and r["max_steps"] in (2000, 3000)]
    if not rs: continue
    p = max(r["params"] for r in rs); rs = [r for r in rs if r["params"] == p]
    m = lambda k: float(np.mean([r[k] for r in rs]))
    S["abilities"][name] = {k: m(k) for k in ("nmse", "nmse_ood", "oracle_ood", "nmse_missing30", "interv_nmse", "cover80", "width_err_spearman", "ood_auroc")} | {"params": p}
    P(f"| {name} | {p:,} | {f3(m('nmse'))} | {f3(m('nmse_ood'))} / {f3(m('oracle_ood'))} | {f3(m('nmse_missing30'))} | {f3(m('interv_nmse'))} | {100 * m('cover80'):.0f}% | {m('width_err_spearman'):.2f} | {m('ood_auroc'):.2f} |")
P("")
open("results/REPORT.md", "w").write("\n".join(out) + "\n")
json.dump(S, open("results/summary.json", "w"), indent=1, default=float)
print("\n".join(out))
