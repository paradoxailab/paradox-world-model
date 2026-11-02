"""PWM-Dyn v0.4.1: training-recipe check for the traffic tasks (same v0.4 architecture).

v0.4 halved the number of optimisation steps relative to v0.3 (batch 64 x 40 epochs instead of batch 32 x
60 epochs). This run chooses between the v0.4 recipe and the v0.3 recipe on VALIDATION only, then trains
3 seeds and scores ParadoxBench-1 Tracks A, B, R and Z. Rainfall tasks keep their v0.4 results.

Original v0.5 description follows.
PWM-Dyn v0.5: validation sweep, then full 3-seed training and ParadoxBench-1 scoring, on 2 GPUs.

Stage 1 - sweep (seed 0, long-context variant) on one traffic task (PEMS08) and one rainfall task (IMD-CI);
          the configuration with the lowest VALIDATION MAE is kept per domain.
Stage 2 - 3 seeds x 4 tasks x {standard (Track A), long-context (Track B/R)} with the chosen configuration,
          plus 3 inductive seeds on PEMS04 for zero-shot transfer (Track Z).
Stage 3 - score every track; write LEADERBOARD.md; provenance audit.
TimesFM is not re-run: its ParadoxBench-1 results are recorded by the v0.4 study on the same windows.

  python run_v05.py            # full
  python run_v05.py --quick    # pipeline check
"""
import argparse, json, os, queue, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
LOADER = {"PEMS08": "PEMS08", "PEMS04": "PEMS04", "IMD-CI": "IMD_central_india", "IMD-WC": "IMD_west_coast"}
DOMAIN = {"PEMS08": "traffic", "PEMS04": "traffic", "IMD-CI": "rain", "IMD-WC": "rain"}
SWEEP_TASK = {"traffic": "PEMS08"}
CONFIGS = {
    "v04-recipe":      [],
    "v03-recipe":      ["--bs", "32", "--epochs", "60", "--lr", "2e-3"],
    "v03-recipe-e100": ["--bs", "32", "--epochs", "100", "--lr", "2e-3"],
}
KEEP = ("ParadoxBench ", "best val", "Error", "Traceback", "error:", "time budget")
LOCK = threading.Lock()


def sh(lane, args, gpu):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), PYTHONUNBUFFERED="1")
    p = subprocess.Popen([PY] + args, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    tail = []
    for line in p.stdout:
        tail = (tail + [line.rstrip()])[-12:]
        if any(k in line for k in KEEP):
            with LOCK:
                print(f"[{lane} gpu{gpu} {time.strftime('%H:%M:%S')}] {line.rstrip()}", flush=True)
    p.wait()
    if p.returncode:
        with LOCK:
            print(f"[{lane}] FAILED ({p.returncode}): {' '.join(args)}\n" + "\n".join(tail), flush=True)


def run_parallel(jobs, n_gpu):
    """jobs: list of (lane, args). One worker per GPU pulls from a shared queue."""
    q = queue.Queue()
    for j in jobs:
        q.put(j)

    def worker(g):
        while True:
            try:
                lane, args = q.get_nowait()
            except queue.Empty:
                return
            sh(lane, args, g)
    ts = [threading.Thread(target=worker, args=(g,)) for g in range(max(n_gpu, 1))]
    [t.start() for t in ts]
    [t.join() for t in ts]


def val(task, version):
    f = os.path.join(ROOT, "models", LOADER[task], version, "report.json")
    return json.load(open(f))["val"]["MAE"] if os.path.exists(f) else float("inf")


def main(a):
    try:
        import torch
        n_gpu = torch.cuda.device_count()
    except Exception:
        n_gpu = 0
    quick = ["--epochs", "1", "--max_minutes", "1"] if a.quick else []
    configs = {k: (v if not a.quick else []) for k, v in CONFIGS.items()}
    if a.quick:
        configs = {"v04-recipe": [], "v03-recipe": ["--bs", "32"]}
    seeds = [0] if a.quick else [0, 1, 2]
    t0 = time.time()
    print(f"v0.4.1 recipe study, GPUs: {n_gpu}", flush=True)

    # ---- stage 1: validation sweep ------------------------------------------------------
    jobs = [("sweep", ["train.py", "--data", LOADER[t], "--version", f"sw41-{c}", "--seed", "0", "--lc"] + args + quick)
            for dom, t in SWEEP_TASK.items() if t in a.tasks for c, args in configs.items()]
    run_parallel(jobs, n_gpu)
    chosen = {}
    for dom, t in SWEEP_TASK.items():
        if t not in a.tasks:
            continue
        scores = {c: val(t, f"sw41-{c}") for c in configs}
        chosen[dom] = min(scores, key=scores.get)
        print(f"[sweep] {dom} ({t}) validation MAE: " + ", ".join(f"{c} {v:.3f}" for c, v in scores.items())
              + f" -> chosen {chosen[dom]}", flush=True)

    # ---- stage 2: full training ---------------------------------------------------------
    jobs = []
    for t in a.tasks:
        cfg = configs[chosen[DOMAIN[t]]]
        std_cfg = [x for x in cfg if x != "--profile"]                      # Track A: standard context only
        for s in seeds:
            jobs.append(("pwm", ["train.py", "--data", LOADER[t], "--version", f"v041-s{s}", "--seed", str(s)] + std_cfg + quick))
            jobs.append(("pwm", ["train.py", "--data", LOADER[t], "--version", f"v041-lc-s{s}", "--seed", str(s), "--lc"] + cfg + quick))
    if "PEMS04" in a.tasks and "PEMS08" in a.tasks:
        cfg = configs[chosen["traffic"]]
        for s in seeds:
            jobs.append(("pwm", ["train.py", "--data", "PEMS04", "--version", f"v041-ind-s{s}", "--seed", str(s), "--lc",
                                 "--variant", "inductive", "--no_clim"] + cfg + quick))
    run_parallel(jobs, n_gpu)

    # ---- stage 3: score ------------------------------------------------------------------
    jobs = []
    for t in a.tasks:
        std, lc = [f"v041-s{s}" for s in seeds], [f"v041-lc-s{s}" for s in seeds]
        vs, vl = sum(val(t, v) for v in std) / len(std), sum(val(t, v) for v in lc) / len(lc)
        best = lc if vl <= vs else std
        print(f"[pwm] {t}: val MAE std {vs:.3f} | long-context {vl:.3f} -> Track B/R use "
              f"{'long-context' if best is lc else 'standard'}", flush=True)
        for tr, vers in (("A", std), ("B", best), ("R", best)):
            jobs.append(("score", ["paradoxbench/run_pwm.py", "--task", t, "--track", tr, "--tag", "v0.4.1", "--versions"] + vers))
    if "PEMS04" in a.tasks and "PEMS08" in a.tasks:
        jobs.append(("score", ["paradoxbench/run_pwm.py", "--task", "PEMS08", "--track", "Z", "--source", "PEMS04",
                               "--tag", "v0.4.1", "--versions"] + [f"v041-ind-s{s}" for s in seeds]))
    run_parallel(jobs, n_gpu)
    print(f"=== v0.4.1 done in {(time.time()-t0)/60:.1f} min ===", flush=True)
    subprocess.run([PY, "paradoxbench/leaderboard.py"], cwd=ROOT)
    subprocess.run([PY, "check_provenance.py"], cwd=ROOT, capture_output=True, text=True)
    print("PROVENANCE:", json.load(open(os.path.join(ROOT, "PROVENANCE_REPORT.json")))["verdict"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--tasks", nargs="+", default=["PEMS08", "PEMS04"])
    main(ap.parse_args())
