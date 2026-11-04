"""PWM-Dyn v0.8 study (one Kaggle session, 2 GPUs): close the remaining gaps to TimesFM 3.0 on Track B (open context)
without any extra data. Every model is still trained only on its own network's training split.

Where v0.6 lost to TimesFM 3.0 zero-shot (Track B): PEMS03 on every metric (our PEMS03 model read 12 steps, TimesFM
512), MAPE on PEMS08 / PEMS04 (low night-time flows), MAPE on rainfall. v0.8 gives every network the long-context
input (the same series' own history, at most 300 steps, inside TimesFM's 512) with v0.7's frozen real-condition
recipe, and tests a relative-error loss term.

Stage 1  validation ablation, seed 0, PEMS08 and METR-LA, long-context v0.7 recipe: rel_w 0 vs 0.5.
         Rule fixed before any run: rel_w 0.5 is kept if, averaged over both networks, validation MAPE falls by >= 2%,
         validation MAE rises by <= 0.3% and validation RMSE rises by <= 0.5%.
Stage 2  long-context models, FRESH seeds 300-302, six traffic networks; rainfall (IMD-CI, IMD-WC) standard and
         long-context models with the same seeds (rainfall has no v0.7 models).
Stage 3  Track B per network: candidates = v0.7 standard ensemble (attached v0.7 output) and v0.8 long-context
         ensemble, each with online correction chosen on validation; the candidate with the lower validation MAE
         after correction is scored once on test. Rainfall: Tracks A, B, R with v0.8.

  python run_v08.py --roots /kaggle/input
"""
import argparse, glob, json, os, shutil, subprocess

from studylib import ROOT, PY, log, run_parallel, n_gpus, minutes

TRAFFIC = ["PEMS08", "PEMS04", "PEMS03", "PEMS07", "METR-LA", "PEMS-BAY"]
RAIN = {"IMD-CI": "IMD_central_india", "IMD-WC": "IMD_west_coast"}
BIG_FIRST = ["PEMS07", "PEMS-BAY", "PEMS03", "PEMS04", "METR-LA", "PEMS08"]
AB_TASKS = ["PEMS08", "METR-LA"]


def v07_recipe(roots):
    """The configuration v0.7 froze (results/v07_frozen_config.json of the attached v0.7 output)."""
    for r in roots:
        for f in glob.glob(os.path.join(r, "**", "results", "v07_frozen_config.json"), recursive=True):
            return json.load(open(f))["args"]
    raise SystemExit("attach the v0.7 session's output: its frozen configuration is needed")


def find_models(roots, pattern):
    found = {}
    for r in roots:
        for d in glob.glob(os.path.join(r, "**", "models", "*", pattern), recursive=True):
            if os.path.exists(os.path.join(d, "weights.pt")):
                found.setdefault(os.path.basename(os.path.dirname(d)), {})[os.path.basename(d)] = d
    return found


def val_metric(task, version, key):
    f = os.path.join(ROOT, "models", task, version, "report.json")
    return json.load(open(f))["val"][key] if os.path.exists(f) else float("nan")


def main(a):
    global AB_TASKS, TRAFFIC, RAIN
    AB_TASKS, TRAFFIC = a.ab_tasks, a.tasks
    if a.no_rain:
        RAIN = {}
    g = n_gpus()
    q = ["--epochs", "1", "--max_minutes", "1"] if a.quick else []
    budget = a.budget_hours * 60
    base = v07_recipe(a.roots)
    lc = base + ["--lc"]
    log(f"PWM-Dyn v0.8 study, GPUs: {g}, budget {budget:.0f} min, v0.7 recipe: {' '.join(base)}")
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    from pwm.data import download_imd, imd_cache_path
    for ld in RAIN.values():                                            # IMD rainfall (imdlib), cached as .npz
        if not os.path.exists(imd_cache_path(ld[4:], 2000, 2024)):
            log("IMD: " + download_imd(ld[4:], 2000, 2024))
    for t, vers in find_models(a.roots, "v07-s20[0-2]").items():        # v0.7 standard models (Track B candidate)
        for v, d in vers.items():
            dst = os.path.join(ROOT, "models", t, v)
            if not os.path.exists(dst):
                shutil.copytree(d, dst)

    # ---- stage 1 --------------------------------------------------------------------------------------------
    run_parallel([("ablation", ["train.py", "--data", t, "--version", f"ab8-rel{w}-s0", "--seed", "0"] + lc +
                   (["--rel_w", w] if w != "0" else []) + q) for t in AB_TASKS for w in ("0", "0.5")], g)
    r = {k: sum(val_metric(t, "ab8-rel0.5-s0", k) / val_metric(t, "ab8-rel0-s0", k) for t in AB_TASKS) / len(AB_TASKS)
         for k in ("MAE", "RMSE", "MAPE")}
    keep = r["MAPE"] <= 0.98 and r["MAE"] <= 1.003 and r["RMSE"] <= 1.005
    log(f"[ablation] rel_w 0.5 vs 0: validation MAE ratio {r['MAE']:.4f} RMSE {r['RMSE']:.4f} MAPE {r['MAPE']:.4f} "
        f"-> {'KEEP' if keep else 'drop'}")
    rec = lc + (["--rel_w", "0.5"] if keep else [])
    json.dump({"ratios": r, "rel_w_kept": keep, "args": rec}, open(os.path.join(ROOT, "results", "v08_frozen_config.json"), "w"))

    # ---- stage 2 --------------------------------------------------------------------------------------------
    seeds = [300] if a.quick else [300, 301, 302]
    jobs = [("pwm-lc", ["train.py", "--data", t, "--version", f"v08-lc-s{s}", "--seed", str(s)] + rec + q)
            for t in BIG_FIRST if t in TRAFFIC for s in seeds]
    for ld in RAIN.values():
        std = [x for x in rec if x != "--lc"]
        jobs += [("rain", ["train.py", "--data", ld, "--version", f"v08-s{s}", "--seed", str(s)] + std + q) for s in seeds]
        jobs += [("rain-lc", ["train.py", "--data", ld, "--version", f"v08-lc-s{s}", "--seed", str(s)] + rec + q) for s in seeds]
    run_parallel(jobs, g, deadline_min=budget - a.reserve)

    # ---- stage 3 --------------------------------------------------------------------------------------------
    def have(t, p):
        ss = (200, 201, 202) if p == "v07-s" else seeds
        return [f"{p}{s}" for s in ss if os.path.exists(os.path.join(ROOT, "models", t, f"{p}{s}", "weights.pt"))]
    jobs = []
    for t in TRAFFIC:
        cands = [c for c in (have(t, "v07-s"), have(t, "v08-lc-s")) if c]
        if cands:
            jobs.append(("trackB", ["paradoxbench/run_online.py", "--task", t, "--tag", "v0.8", "--select_on_val",
                                    "--candidates"] + [",".join(c) for c in cands]))
    for task, ld in RAIN.items():
        std, lcv = have(ld, "v08-s"), have(ld, "v08-lc-s")
        if std:
            for tr in ("A", "R"):
                jobs.append(("rain-score", ["paradoxbench/run_pwm.py", "--task", task, "--track", tr, "--tag", "v0.8",
                                            "--versions"] + std))
        jobs.append(("rain-B", ["paradoxbench/run_online.py", "--task", task, "--tag", "v0.8", "--select_on_val",
                                "--candidates"] + [",".join(c) for c in (std, lcv) if c]))
    run_parallel(jobs, g)
    log(f"=== v0.8 session done in {minutes():.1f} min ===")
    subprocess.run([PY, "check_provenance.py"], cwd=ROOT, capture_output=True, text=True)
    try:
        log("PROVENANCE: " + json.load(open(os.path.join(ROOT, "PROVENANCE_REPORT.json")))["verdict"])
    except Exception as e:
        log(f"PROVENANCE: report unavailable ({e})")
    subprocess.run([PY, "run_v07_analysis.py", "--tag", "v0.8", "--prev", "v0.7", "--roots"] + (a.roots or ["/nonexistent"]), cwd=ROOT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--budget_hours", type=float, default=6.0)
    ap.add_argument("--reserve", type=float, default=40)
    ap.add_argument("--roots", nargs="*", default=[])
    ap.add_argument("--tasks", nargs="+", default=TRAFFIC, help="(pipeline checks) traffic networks")
    ap.add_argument("--ab_tasks", nargs="+", default=AB_TASKS, help="(pipeline checks) ablation networks")
    ap.add_argument("--no_rain", action="store_true", help="(pipeline checks) skip the rainfall tasks")
    main(ap.parse_args())
