"""PWM-Dyn v0.6 study, session 1 of 2 (2 GPUs): explain the v0.3 gap, freeze one configuration on validation,
then train it with FRESH seeds on six traffic networks and score ParadoxBench-1.1 once.

Stage 1  ablation on PEMS08 and PEMS04 VALIDATION (seeds 0, 1): which v0.4 change cost accuracy under the
         standard 12-step context? Factors: climatology input (on/off), epochs (60/100), checkpoint selection
         on every validation window vs every 4th.
           v03         = no climatology, 60 epochs, select on every window      (the v0.3 recipe)
           clim-vs1    = climatology,    100 epochs, select on every window
           noclim-vs1  = no climatology, 100 epochs, select on every window
           v041        = climatology,    100 epochs, select on every 4th window  (v0.4.1, measured 2026-11-01)
         The configuration with the lowest validation MAE (relative to v0.4.1, averaged over both networks) is
         frozen. Each ablation ensemble is also scored on Track A test and reported as an ablation only.
Stage 2  frozen configuration, seeds 100-102 (never used before), on PEMS08, PEMS04, PEMS03, PEMS07, METR-LA and
         PEMS-BAY, with the optimisation-step budget it has on PEMS08; plus the long-context variant (with
         climatology, needed for dead sensors) on PEMS08 and PEMS04.
Stage 3  score Tracks A, B and R for all six networks (tag v0.6), reference baselines, leaderboard, provenance.

  python run_v06_pwm.py            # full study (budget ~9.5 h)
  python run_v06_pwm.py --quick    # pipeline check
"""
import argparse, json, os, subprocess

from studylib import ROOT, PY, log, run_parallel, n_gpus, val_mae, minutes

LOADER = {"PEMS08": "PEMS08", "PEMS04": "PEMS04", "PEMS03": "PEMS03", "PEMS07": "PEMS07",
          "METR-LA": "METR-LA", "PEMS-BAY": "PEMS-BAY"}
BIG_FIRST = ["PEMS07", "PEMS-BAY", "PEMS03", "METR-LA", "PEMS04", "PEMS08"]
REC = ["--bs", "32", "--lr", "2e-3"]
CONFIGS = {
    "v03":        ["--no_clim", "--epochs", "60", "--val_stride", "1"] + REC,
    "clim-vs1":   ["--epochs", "100", "--val_stride", "1"] + REC,
    "noclim-vs1": ["--no_clim", "--epochs", "100", "--val_stride", "1"] + REC,
    "v041":       ["--epochs", "100", "--val_stride", "4"] + REC,
}
V041_VAL = {"PEMS08": 14.520, "PEMS04": 18.839}   # v0.4.1 run of 2026-11-01, 3-seed mean validation MAE
STEPS_PER_EPOCH_PEMS08 = 335                        # ceil(10,690 train windows / 32)


def epochs_of(cfg):
    return int(cfg[cfg.index("--epochs") + 1])


def main(a):
    g = n_gpus()
    q = ["--epochs", "1", "--max_minutes", "1"] if a.quick else []
    budget = a.budget_hours * 60
    log(f"PWM-Dyn v0.6 study, GPUs: {g}, budget {budget:.0f} min")
    ab_seeds = [0] if a.quick else [0, 1]

    # ---- stage 1: ablation on validation --------------------------------------------------------
    jobs = [("ablation", ["train.py", "--data", t, "--version", f"ab-{c}-s{s}", "--seed", str(s)] + args + q)
            for t in ("PEMS04", "PEMS08") for c, args in CONFIGS.items() if c != "v041" for s in ab_seeds]
    if a.frozen:                                   # re-run / test: skip stage 1, use the given configuration
        jobs = []
    run_parallel(jobs, g)
    rel = {"v041": 1.0}
    for c in CONFIGS:
        if c == "v041" or a.frozen:
            continue
        v = {t: sum(val_mae(t, f"ab-{c}-s{s}") for s in ab_seeds) / len(ab_seeds) for t in ("PEMS08", "PEMS04")}
        rel[c] = sum(v[t] / V041_VAL[t] for t in v) / 2
        log(f"[ablation] {c}: validation MAE PEMS08 {v['PEMS08']:.3f} PEMS04 {v['PEMS04']:.3f} "
            f"(relative to v0.4.1: {rel[c]:.4f})")
    chosen = a.frozen or min(rel, key=rel.get)
    cfg = CONFIGS[chosen]
    log(f"[ablation] frozen configuration: {chosen} {' '.join(cfg)}")
    json.dump({"relative_val_MAE": rel, "chosen": chosen, "args": cfg},
              open(os.path.join(ROOT, "results", "v06_frozen_config.json"), "w"), indent=1)
    jobs = [("ablation-score", ["paradoxbench/run_pwm.py", "--task", t, "--track", "A", "--tag", f"ablation {c}",
                                "--versions"] + [f"ab-{c}-s{s}" for s in ab_seeds])
            for t in ("PEMS08", "PEMS04") for c in CONFIGS if c != "v041" and not a.frozen]
    run_parallel(jobs, g)

    # ---- stage 2: frozen configuration, fresh seeds, six networks --------------------------------
    seeds = [100] if a.quick else [100, 101, 102]
    budget_steps = epochs_of(cfg) * STEPS_PER_EPOCH_PEMS08
    tasks = a.tasks
    jobs = [("pwm", ["train.py", "--data", LOADER[t], "--version", f"v06-s{s}", "--seed", str(s),
                     "--step_budget", str(budget_steps)] + cfg + q) for t in BIG_FIRST if t in tasks for s in seeds]
    lc_cfg = [x for x in cfg if x != "--no_clim"] + ["--lc"]
    jobs += [("pwm-lc", ["train.py", "--data", t, "--version", f"v06-lc-s{s}", "--seed", str(s)] + lc_cfg + q)
             for t in ("PEMS04", "PEMS08") if t in tasks for s in seeds]
    run_parallel(jobs, g, deadline_min=budget - 25)

    # ---- stage 3: score once ------------------------------------------------------------------------
    jobs = []
    for t in tasks:
        std = [f"v06-s{s}" for s in seeds if os.path.exists(os.path.join(ROOT, "models", LOADER[t], f"v06-s{s}"))]
        lc = [f"v06-lc-s{s}" for s in seeds if os.path.exists(os.path.join(ROOT, "models", LOADER[t], f"v06-lc-s{s}"))]
        if not std:
            log(f"[score] {t}: no trained model, skipped"); continue
        vs = sum(val_mae(LOADER[t], v) for v in std) / len(std)
        vl = sum(val_mae(LOADER[t], v) for v in lc) / len(lc) if lc else float("inf")
        best = lc if vl <= vs else std
        log(f"[score] {t}: validation MAE standard {vs:.3f} | long-context {vl:.3f} -> Track B/R use "
            f"{'long-context' if best is lc else 'standard'}")
        for tr, vers in (("A", std), ("B", best), ("R", best)):
            jobs.append(("score", ["paradoxbench/run_pwm.py", "--task", t, "--track", tr, "--tag", "v0.6",
                                   "--versions"] + vers))
    jobs.append(("baselines", ["paradoxbench/baselines.py"] + tasks))
    run_parallel(jobs, g)
    log(f"=== v0.6 PWM session done in {minutes():.1f} min ===")
    subprocess.run([PY, "paradoxbench/leaderboard.py"], cwd=ROOT, capture_output=True)
    subprocess.run([PY, "check_provenance.py"], cwd=ROOT, capture_output=True, text=True)
    log("PROVENANCE: " + json.load(open(os.path.join(ROOT, "PROVENANCE_REPORT.json")))["verdict"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--budget_hours", type=float, default=9.5)
    ap.add_argument("--tasks", nargs="+", default=list(LOADER))
    ap.add_argument("--frozen", choices=list(CONFIGS), default=None, help="skip the ablation and use this configuration")
    main(ap.parse_args())
