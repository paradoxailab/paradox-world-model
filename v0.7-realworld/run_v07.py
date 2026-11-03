"""PWM-Dyn v0.7 study (one Kaggle session, 2 GPUs): make the model hold up under real operating conditions.

What v0.7 changes (each one a switch of train.py):
  --fallback   the forecast is an offset from the last OBSERVED reading, or from the train-split climatology when a
               location has no reading in its window (v0.6 used the last reading even when it was missing, i.e. the
               global mean). Two input cues are added: age of the last reading, "no reading" flag.
  --gap_p 0.2  training also removes burst outages (uniform start, mean length 6 steps = 30 min) inside the input
               window, on top of v0.6's whole-window sensor dropout. Real outages usually run to the latest reading.
  --ema 0.999  validation and the saved checkpoint use an exponential moving average of the weights.
  online       Track B entry: forecasts shifted by the recent resolved errors (paradoxbench/run_online.py),
               strength chosen on the validation stream (zero is an option).

Stage 1  ablation on VALIDATION, seed 0, PEMS08 and METR-LA, v0.6's frozen recipe as the base:
         base | fallback | robust (= fallback + gaps) | robust+ema. Each model is scored on validation clean, with a
         validation-only 30% of sensors dark, and with validation-only replayed real outages (tools/val_conditions.py).
         Decision rules, fixed before any run (ratios = mean over both networks of MAE / MAE of the reference):
           1. robust is kept if, against base, the dark and outage ratios average <= 0.99 and the clean ratio is
              <= 1.005; otherwise fallback is kept under the same test; otherwise base is kept.
           2. only if robust was kept: ema is added if, against robust, the clean ratio is <= 0.997 and the
              dark/outage ratio is <= 1.005.
Stage 2  the chosen configuration, FRESH seeds 200-202 (never used before), six traffic networks, the same
         33,500-step budget as v0.6.
Stage 3  score once: Tracks A, R, G (new: real-outage replay) and B (online) for v0.7; v0.6's models (from the v0.6
         session's output, if attached) on Track G; reference baselines; analysis against every v0.6-session row.

  python run_v07.py --roots /kaggle/input/...   # full study
  python run_v07.py --quick                     # pipeline check
"""
import argparse, glob, json, os, shutil, subprocess

from studylib import ROOT, PY, log, run_parallel, n_gpus, minutes

TASKS = ["PEMS08", "PEMS04", "PEMS03", "PEMS07", "METR-LA", "PEMS-BAY"]
BIG_FIRST = ["PEMS07", "PEMS-BAY", "PEMS03", "PEMS04", "METR-LA", "PEMS08"]
BASE = ["--no_clim", "--epochs", "100", "--val_stride", "1", "--bs", "32", "--lr", "2e-3", "--step_budget", "33500"]
ROBUST = ["--fallback", "--gap_p", "0.2", "--gap_mean", "6"]
EMA = ["--ema", "0.999"]
CONFIGS = {"base": BASE, "fallback": BASE + ROBUST[:1], "robust": BASE + ROBUST, "robust-ema": BASE + ROBUST + EMA}
AB_TASKS = ["PEMS08", "METR-LA"]


def vc(task, version):
    f = os.path.join(ROOT, "models", task, version, "val_conditions.json")
    return json.load(open(f)) if os.path.exists(f) else None


def ratio(pairs, keys):
    r = []
    for c1, c0 in pairs:
        for t in AB_TASKS:
            a, b = vc(t, f"ab-{c1}-s0"), vc(t, f"ab-{c0}-s0")
            if a and b:
                r += [a[k] / b[k] for k in keys]
    return sum(r) / len(r) if r else float("nan")


def find_v06(roots):
    """v0.6 session-1 model folders (v06-s100..102 per network), from the attached v0.6 output."""
    found = {}
    for r in roots:
        for d in glob.glob(os.path.join(r, "**", "models", "*", "v06-s10[0-2]"), recursive=True):
            t = os.path.basename(os.path.dirname(d))
            found.setdefault(t, {})[os.path.basename(d)] = d
    return found


def main(a):
    global AB_TASKS
    AB_TASKS = a.ab_tasks
    g = n_gpus()
    q = ["--epochs", "1", "--max_minutes", "1"] if a.quick else []
    budget = a.budget_hours * 60
    log(f"PWM-Dyn v0.7 study, GPUs: {g}, budget {budget:.0f} min")
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)

    # ---- v0.6 models on Track G (cheap; done first so the comparison exists whatever happens later) ------
    v06 = find_v06(a.roots)
    log(f"[v0.6] model folders found for: {sorted(v06)}")
    jobs = []
    for t, vers in v06.items():
        for v, d in vers.items():
            dst = os.path.join(ROOT, "models", t, v)
            if not os.path.exists(dst):
                shutil.copytree(d, dst)
        vs = sorted(vers)
        jobs += [("v06-score", ["paradoxbench/run_pwm.py", "--task", t, "--track", "G", "--tag", "v0.6",
                                "--versions"] + vs)]
    jobs.append(("baselines", ["paradoxbench/baselines.py"] + a.tasks))
    run_parallel(jobs, g)

    # ---- stage 1: 2x2 ablation on validation -----------------------------------------------------------
    jobs = [("ablation", ["train.py", "--data", t, "--version", f"ab-{c}-s0", "--seed", "0"] + args + q)
            for t in AB_TASKS for c, args in CONFIGS.items()]
    run_parallel(jobs, g)
    run_parallel([("valcond", ["tools/val_conditions.py", "--data", t, "--version", f"ab-{c}-s0"])
                  for t in AB_TASKS for c in CONFIGS], g)
    rob, cln = ("dark", "gaps"), ("clean",)
    dec = {c: {"vs": ref, "clean": ratio([(c, ref)], cln), "dark_gaps": ratio([(c, ref)], rob)}
           for c, ref in (("robust", "base"), ("fallback", "base"), ("robust-ema", "robust"))}
    ok = lambda c: dec[c]["dark_gaps"] <= 0.99 and dec[c]["clean"] <= 1.005
    chosen = "robust" if ok("robust") else ("fallback" if ok("fallback") else "base")
    keep_e = chosen == "robust" and dec["robust-ema"]["clean"] <= 0.997 and dec["robust-ema"]["dark_gaps"] <= 1.005
    if keep_e:
        chosen = "robust-ema"
    for t in AB_TASKS:
        for c in CONFIGS:
            v = vc(t, f"ab-{c}-s0")
            if v:
                log(f"[ablation] {t} {c}: validation MAE clean {v['clean']:.3f} dark {v['dark']:.3f} gaps {v['gaps']:.3f}")
    for c, d in dec.items():
        log(f"[ablation] {c} vs {d['vs']}: clean ratio {d['clean']:.4f}, dark/outage ratio {d['dark_gaps']:.4f}")
    cfg = CONFIGS[chosen]
    log(f"[ablation] frozen configuration: {chosen} {' '.join(cfg)}")
    json.dump({"ratios": dec, "chosen": chosen, "args": cfg,
               "val_conditions": {t: {c: vc(t, f"ab-{c}-s0") for c in CONFIGS} for t in AB_TASKS}},
              open(os.path.join(ROOT, "results", "v07_frozen_config.json"), "w"), indent=1)

    # ---- stage 2: frozen configuration, fresh seeds --------------------------------------------------------
    seeds = [200] if a.quick else [200, 201, 202]
    jobs = [("pwm", ["train.py", "--data", t, "--version", f"v07-s{s}", "--seed", str(s)] + cfg + q)
            for t in BIG_FIRST if t in a.tasks for s in seeds]
    run_parallel(jobs, g, deadline_min=budget - a.reserve)

    # ---- stage 3: score once --------------------------------------------------------------------------------
    jobs = []
    for t in a.tasks:
        vers = [f"v07-s{s}" for s in seeds if os.path.exists(os.path.join(ROOT, "models", t, f"v07-s{s}", "weights.pt"))]
        if not vers:
            log(f"[score] {t}: no trained model, skipped"); continue
        if len(vers) < len(seeds):
            log(f"[score] {t}: only {len(vers)} of {len(seeds)} seeds finished in the budget")
        for tr in ("A", "R", "G"):
            jobs.append(("score", ["paradoxbench/run_pwm.py", "--task", t, "--track", tr, "--tag", "v0.7",
                                   "--versions"] + vers))
        jobs.append(("online", ["paradoxbench/run_online.py", "--task", t, "--tag", "v0.7", "--versions"] + vers))
        jobs += [("valcond", ["tools/val_conditions.py", "--data", t, "--version", v]) for v in vers]
    run_parallel(jobs, g)
    log(f"=== v0.7 PWM session done in {minutes():.1f} min ===")
    subprocess.run([PY, "check_provenance.py"], cwd=ROOT, capture_output=True, text=True)
    try:
        log("PROVENANCE: " + json.load(open(os.path.join(ROOT, "PROVENANCE_REPORT.json")))["verdict"])
    except Exception as e:
        log(f"PROVENANCE: report unavailable ({e})")
    subprocess.run([PY, "run_v07_analysis.py", "--roots"] + (a.roots or ["/nonexistent"]), cwd=ROOT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--budget_hours", type=float, default=4.6)
    ap.add_argument("--reserve", type=float, default=35, help="minutes kept for scoring and analysis")
    ap.add_argument("--roots", nargs="*", default=[])
    ap.add_argument("--tasks", nargs="+", default=TASKS, help="(pipeline checks) networks to train and score")
    ap.add_argument("--ab_tasks", nargs="+", default=AB_TASKS, help="(pipeline checks) ablation networks")
    main(ap.parse_args())
