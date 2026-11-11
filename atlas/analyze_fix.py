"""v0.2 report: plain Atlas against Atlas with in-context identification, same training protocol.
Reads results/runs_fix.jsonl -> results/REPORT_v02.md, results/summary_v02.json"""
import json

import numpy as np

from atlas import threshold as T

R = [json.loads(l) for l in open("results/runs_fix.jsonl") if l.strip()]
BL = json.load(open("results/baselines.json")); BS = json.load(open("results/baselines_sysid.json"))
NS = [30, 100, 300, 1000, 3000, 10000]
out, S = [], {}
P = lambda *a: out.append(" ".join(str(x) for x in a))
f3 = lambda x: "–" if x is None or not np.isfinite(x) else (f"{x:.3f}" if x >= 0.01 else f"{x:.4f}")


def get(r, k):
    for part in k.split("."):
        r = None if r is None else r.get(part)
    return r


def cell(name, N, sysid, k, size=250_000):
    v = [get(r, k) for r in R if r["system"] == name and r["N"] == N and r["sysid"] == sysid and r["size"] == size]
    v = [x for x in v if x is not None]
    return (float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else float("nan"), len(v)) if v else None


def row(label, name, sysid, k, sd=False):
    cs = []
    for N in NS:
        c = cell(name, N, sysid, k)
        cs.append("–" if c is None else f3(c[0]) + (f" ±{c[1]:.3f}" if sd and c[2] > 1 else ""))
    P(f"| {label} | " + " | ".join(cs) + " |")


P(f"# Atlas v0.2: fixing the three failures — measured results\n\n{len(R)} training runs (250K-parameter models unless stated; 2 seeds; "
  "both variants trained with the same protocol, early-stopping patience 10).\n")
P("*plain* = Atlas v0.1. *ID* = Atlas with in-context identification of the dynamics.\n")
names = ("harmonic", "damped", "diffusion", "advdiff")
for name in names:
    b, s_in, s_ood = BL[name], BS[f"{name}_in"], BS[f"{name}_ood"]
    P(f"## {name}\n\nReferences: oracle {f3(b['oracle'])} (seen range), {f3(b['oracle_ood'])} (unseen range); identification with no training "
      f"{f3(s_in['all'])} (seen), {f3(s_ood['all'])} (unseen).\n")
    P("| trajectories N | " + " | ".join(str(n) for n in NS) + " |"); P("|---" * (len(NS) + 1) + "|")
    row("seen range, plain", name, 0, "nmse", True); row("seen range, ID", name, 1, "nmse", True)
    row("unseen range, plain", name, 0, "nmse_ood"); row("unseen range, ID", name, 1, "nmse_ood")
    row("unseen range, ID + fallback when flagged", name, 1, "nmse_fb_ood"); row("seen range, ID + fallback when flagged", name, 1, "nmse_fb")
    row("intervention error, plain", name, 0, "interv_nmse"); row("intervention error, ID", name, 1, "interv_nmse")
    row("30% inputs missing, plain", name, 0, "nmse_missing30"); row("30% inputs missing, ID", name, 1, "nmse_missing30")
    row("flag AUROC: interval width, plain", name, 0, "ood_auroc"); row("flag AUROC: latent distance, plain", name, 0, "novelty.z.auroc")
    row("flag AUROC: identified dynamics, ID", name, 1, "novelty.theta.auroc")
    row("unseen cases flagged, ID", name, 1, "novelty.theta.flagged_ood"); row("false alarms on seen cases, ID", name, 1, "novelty.theta.false_alarm")
    row("seen-range error of flagged cases, ID", name, 1, "flag_err.flagged"); row("seen-range error of unflagged cases, ID", name, 1, "flag_err.unflagged")
    row("80% interval coverage, ID", name, 1, "cover80"); row("training steps used, plain", name, 0, "steps"); row("training steps used, ID", name, 1, "steps")
    row("CPU seconds per run, plain", name, 0, "secs"); row("CPU seconds per run, ID", name, 1, "secs")
    P("")

P("## Does the structural prior lower the data needed?\n\nTrajectories needed to reach a test error in the seen range (log-log interpolation of the mean curve).\n")
P("| system | target error | plain | ID | ratio |"); P("|---|---|---|---|---|"); S["need"] = {}
for name in names:
    for tgt in (0.3, 0.1, 0.03, 0.01):
        res = []
        for sysid in (0, 1):
            ns = [n for n in NS if cell(name, n, sysid, "nmse")]
            res.append(T.crossing(ns, [cell(name, n, sysid, "nmse")[0] for n in ns], tgt))
        if all(r[1] == "not reached" for r in res): continue
        sh = lambda r: f"{r[0]:,.0f}" if r[1] == "measured" else ("≤ 30" if r[1].startswith("at") else "not reached by 10,000")
        ratio = f"{res[0][0] / res[1][0]:.1f}×" if res[0][1] == res[1][1] == "measured" else "–"
        S["need"][f"{name}_{tgt}"] = dict(plain=res[0], id=res[1])
        P(f"| {name} | {tgt} | {sh(res[0])} | {sh(res[1])} | {ratio} |")
P("")
P("## Model size with identification (damped oscillator, seed 0)\n")
P("| parameters | N=100 seen / unseen | N=1,000 seen / unseen | N=10,000 seen / unseen |"); P("|---|---|---|---|")
for size in (50_000, 250_000, 1_000_000, 10_000_000):
    cs = []
    for N in (100, 1000, 10000):
        v = [r for r in R if r["system"] == "damped" and r["N"] == N and r["sysid"] == 1 and r["size"] == size and r["seed"] == 0]
        cs.append(f"{f3(v[0]['nmse'])} / {f3(v[0]['nmse_ood'])}" if v else "–")
    pr = [r["params"] for r in R if r["size"] == size and r["sysid"] == 1 and r["system"] == "damped"]
    if pr: P(f"| {pr[0]:,} | " + " | ".join(cs) + " |")
P("")
S["cells"] = {f"{n}_{N}_{s}": {k: (cell(n, N, s, k) or [None])[0] for k in ("nmse", "nmse_ood", "nmse_fb", "nmse_fb_ood", "interv_nmse", "nmse_missing30", "ood_auroc", "novelty.z.auroc", "novelty.theta.auroc", "novelty.theta.flagged_ood", "novelty.theta.false_alarm", "cover80")}
              for n in names for N in NS for s in (0, 1)}
open("results/REPORT_v02.md", "w").write("\n".join(out) + "\n")
json.dump(S, open("results/summary_v02.json", "w"), indent=1, default=float)
print("\n".join(out))
