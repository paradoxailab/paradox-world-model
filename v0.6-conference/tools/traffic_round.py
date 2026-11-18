"""ParadoxBench-1.3 traffic head-to-head (rules: RESULTS.md, section 5): our models (<= 10M parameters) against
TimesFM 2.5, TimesFM 3.0 (uni- and multivariate), Chronos-2 and Chronos-Bolt, zero-shot, on Track B of all six traffic
networks, with paired tests. Runs as a resumable queue: every finished job is mirrored to --store (Google Drive) and
skipped on the next run, so a disconnect loses at most the job in progress.

  python tools/traffic_round.py --store /content/drive/MyDrive/PWM-10M/traffic [--stage all|data|opp|train|score|tests]
"""
import argparse, glob, json, math, os, shutil, subprocess, sys, time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
TASKS = ["PEMS08", "PEMS04", "PEMS03", "PEMS07", "METR-LA", "PEMS-BAY"]
BIG_FIRST = ["PEMS03", "PEMS08"]              # where TimesFM 3.0 led or tied PWM-Dyn v0.6 (RESULTS.md section 3)
SEEDS = [100, 101, 102]
SMALL = dict(tag="v0.6r", args=["--no_clim", "--bs", "32", "--lr", "2e-3", "--step_budget", "33500"])
BIG = dict(tag="8M", args=["--no_clim", "--bs", "32", "--lr", "2e-3", "--step_budget", "33500", "--d", "320", "--layers", "8"])
OPP = [("chronos-bolt", "univariate"), ("chronos2", "univariate"), ("tfm25", "univariate"),
       ("tfm3", "univariate"), ("tfm3", "multivariate")]
DIRS = ["data/raw", "models", "results/paradoxbench", "submissions"]


def sh(cmd, log):
    print("+", " ".join(cmd), flush=True)
    with open(log, "a") as f:
        p = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            if "Warning" in line or "warn(" in line:
                continue
            print(line, end="", flush=True); f.write(line)
        return p.wait()


class Store:
    def __init__(self, path):
        self.p = path; os.makedirs(os.path.join(path, "done"), exist_ok=True)

    def restore(self):
        for d in DIRS:
            src = os.path.join(self.p, d)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(ROOT, d), dirs_exist_ok=True)

    def save(self):
        for d in DIRS:
            src = os.path.join(ROOT, d)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(self.p, d), dirs_exist_ok=True)

    def done(self, job):
        return os.path.exists(os.path.join(self.p, "done", job))

    def mark(self, job, info=""):
        open(os.path.join(self.p, "done", job), "w").write(info)


def run_job(st, job, cmd, log):
    if st.done(job):
        print(f"[skip] {job} (done)", flush=True); return True
    t0 = time.time()
    rc = sh(cmd, log)
    if rc != 0:
        print(f"[FAIL] {job} rc={rc}", flush=True); return False
    st.save(); st.mark(job, f"{(time.time() - t0) / 60:.1f} min")
    print(f"[done] {job} in {(time.time() - t0) / 60:.1f} min", flush=True)
    return True


def val_mean(task, tag):
    from paradoxbench.spec import TASKS as T
    vals = []
    for s in SEEDS:
        f = os.path.join(ROOT, "models", T[task][0], f"{tag}-s{s}", "report.json")
        if not os.path.exists(f):
            return None
        vals.append(json.load(open(f))["val"]["MAE"])
    return float(np.mean(vals))


def holm(ps):
    order = np.argsort(ps); m = len(ps); adj = np.empty(m); run = 0.0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (m - r) * ps[i])); adj[i] = run
    return adj


def main(a):
    global TASKS, OPP
    if a.tasks:
        TASKS = a.tasks.split(",")
    if a.test_steps:                                         # pipeline test only: never reported
        for c in (SMALL, BIG):
            c["args"] = [x if x != "33500" else str(a.test_steps) for x in c["args"]]
        OPP = [("stub", "univariate")]
        SEEDS[:] = [100]
        BIG["args"] = BIG["args"][:-4] + ["--d", "32", "--layers", "1"]
    st = Store(a.store); st.restore()
    log = os.path.join(a.store, "traffic_log.txt")
    py = sys.executable
    from paradoxbench.spec import TASKS as T
    stages = a.stage.split(",")
    big_tasks = [t for t in BIG_FIRST if t in TASKS] + ([t for t in TASKS if t not in BIG_FIRST] if a.big_all else [])
    if "all" in stages or "data" in stages:
        run_job(st, "data", [py, "tools/fetch_all.py"], log)
    if "all" in stages or "train" in stages:
        for task in TASKS:                                   # the 0.3M v0.6 recipe, 3 fresh seeds
            for s in SEEDS:
                run_job(st, f"train_{SMALL['tag']}_{task}_s{s}", [py, "train.py", "--data", T[task][0], "--version",
                        f"{SMALL['tag']}-s{s}", "--seed", str(s)] + SMALL["args"], log)
        for task in big_tasks:                               # the 10M-class model
            for s in SEEDS:
                run_job(st, f"train_{BIG['tag']}_{task}_s{s}", [py, "train.py", "--data", T[task][0], "--version",
                        f"{BIG['tag']}-s{s}", "--seed", str(s)] + BIG["args"], log)
    if "all" in stages or "score" in stages:                 # choose by validation, THEN touch the test once
        sel = {}
        for task in TASKS:
            vs, vb = val_mean(task, SMALL["tag"]), val_mean(task, BIG["tag"])
            if vs is None:
                continue
            pick = BIG if (vb is not None and vb < vs) else SMALL
            sel[task] = dict(val_small=vs, val_big=vb, chosen=pick["tag"])
            json.dump(sel, open(os.path.join(a.store, "selection.json"), "w"), indent=1)
            run_job(st, f"score_{task}", [py, "paradoxbench/run_pwm.py", "--task", task, "--track", "B", "--tag",
                    pick["tag"], "--versions"] + [f"{pick['tag']}-s{s}" for s in SEEDS], log)
        print("SELECTION " + json.dumps(sel), flush=True)
    if "all" in stages or "opp" in stages:
        for task in TASKS:
            for model, mode in OPP:
                run_job(st, f"opp_{task}_{model}_{mode}", [py, "opponents/run_timesfm.py", "--task", task, "--model",
                        model, "--mode", mode, "--ctx", "512"], log)
    if "all" in stages or "tests" in stages:
        from paradoxbench.significance import test_pair
        rows = []
        for task in TASKS:
            sub = sorted(glob.glob(os.path.join(ROOT, "submissions", f"{task}__B__*.npz")))
            ours = [f for f in sub if "PWM-Dyn" in f and ("v0.6r" in f or "8M" in f)]
            opps = [f for f in sub if any(k in f for k in ("TimesFM", "Chronos", "STUB"))]
            if not ours:
                continue
            for f in opps:
                r = test_pair(task, "B", ours[0], f)
                r.update(task=task, ours=os.path.basename(ours[0]), opponent=os.path.basename(f))
                rows.append(r)
        if rows:
            adj = holm(np.array([r["p_value"] for r in rows]))
            for r, p in zip(rows, adj):
                r["p_holm"] = float(p)
                ci_ok = r["rel_ci95_pct"][1] < 0 if r["diff"] < 0 else r["rel_ci95_pct"][0] > 0
                r["verdict"] = ("WIN" if r["diff"] < 0 else "LOSS") if (p < 0.05 and ci_ok) else "TIE"
            json.dump(rows, open(os.path.join(a.store, "traffic_tests.json"), "w"), indent=1)
            for r in rows:
                print(f"TEST {r['task']:<9} {r['opponent'][:60]:<60} ours {r['MAE_a']:.3f} theirs {r['MAE_b']:.3f} "
                      f"{r['rel_diff_pct']:+.2f}% [{r['rel_ci95_pct'][0]:+.2f}, {r['rel_ci95_pct'][1]:+.2f}] "
                      f"p_holm {r['p_holm']:.2g} {r['verdict']}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--stage", default="all")
    ap.add_argument("--big-all", action="store_true", help="train the 10M-class model on all six networks")
    ap.add_argument("--tasks", default="", help="subset of tasks (default: all six)")
    ap.add_argument("--test-steps", type=int, default=0, help="PIPELINE TEST ONLY: tiny step budget, stub opponent")
    main(ap.parse_args())
