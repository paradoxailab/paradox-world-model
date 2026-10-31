"""Run the whole ParadoxBench-1 study end to end on a 2-GPU machine (e.g. Kaggle T4 x2).

  lane 0 (GPU 0): train PWM-Dyn v0.4 (3 seeds x 4 tasks x {standard, long-context} + 3 inductive
                  seeds on PEMS04), score every track, baselines, then TimesFM 2.5 on 3 tasks
  lane 1 (GPU 1): TimesFM 3.0 multivariate on 4 tasks, then TimesFM 2.5 on IMD-WC
Then builds LEADERBOARD.md and runs the provenance audit.

  python run_paradoxbench.py            # full study
  python run_paradoxbench.py --quick    # pipeline check: 1 epoch, 1 seed, stub opponents
"""
import argparse, glob, json, os, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
LOADER = {"PEMS08": "PEMS08", "PEMS04": "PEMS04", "IMD-CI": "IMD_central_india", "IMD-WC": "IMD_west_coast"}
CTX = {"PEMS08": 512, "PEMS04": 512, "IMD-CI": 365, "IMD-WC": 365}
KEEP = ("ParadoxBench ", "best val", "Error", "Traceback", "error:", "windows x", "time budget")


def sh(lane, args, gpu):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), PYTHONUNBUFFERED="1")
    t0 = time.time()
    p = subprocess.Popen([PY] + args, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    tail = []
    for line in p.stdout:
        tail = (tail + [line.rstrip()])[-15:]
        if any(k in line for k in KEEP):
            print(f"[{lane} {time.strftime('%H:%M:%S')}] {line.rstrip()}", flush=True)
    p.wait()
    if p.returncode:
        print(f"[{lane}] FAILED ({p.returncode}): {' '.join(args)}\n" + "\n".join(tail), flush=True)
    return p.returncode == 0, (time.time() - t0) / 60


def val_mae(task, versions):
    v = []
    for ver in versions:
        f = os.path.join(ROOT, "models", LOADER[task], ver, "report.json")
        if os.path.exists(f):
            v.append(json.load(open(f))["val"]["MAE"])
    return sum(v) / len(v) if v else float("inf")


def lane0(a, tasks, seeds, opp):
    tr = ["train.py"] + (["--epochs", "1", "--max_minutes", "2"] if a.quick else [])
    for t in tasks:
        for s in seeds:
            sh("pwm", tr + ["--data", LOADER[t], "--version", f"v04-s{s}", "--seed", str(s)], 0)
            sh("pwm", tr + ["--data", LOADER[t], "--version", f"v04-lc-s{s}", "--seed", str(s), "--lc"], 0)
    if "PEMS04" in tasks and "PEMS08" in tasks:
        for s in seeds:
            sh("pwm", tr + ["--data", "PEMS04", "--version", f"v04-ind-lc-s{s}", "--seed", str(s),
                            "--lc", "--variant", "inductive", "--no_clim"], 0)
    for t in tasks:
        std, lc = [f"v04-s{s}" for s in seeds], [f"v04-lc-s{s}" for s in seeds]
        best_b = lc if val_mae(t, lc) <= val_mae(t, std) else std     # chosen on VALIDATION only
        print(f"[pwm] {t}: val MAE std {val_mae(t, std):.3f} | lc {val_mae(t, lc):.3f} -> Track B/R use "
              f"{'long-context' if best_b is lc else 'standard'}", flush=True)
        sh("pwm", ["paradoxbench/run_pwm.py", "--task", t, "--track", "A", "--versions"] + std, 0)
        sh("pwm", ["paradoxbench/run_pwm.py", "--task", t, "--track", "B", "--versions"] + best_b, 0)
        sh("pwm", ["paradoxbench/run_pwm.py", "--task", t, "--track", "R", "--versions"] + best_b, 0)
    if "PEMS04" in tasks and "PEMS08" in tasks:
        sh("pwm", ["paradoxbench/run_pwm.py", "--task", "PEMS08", "--track", "Z", "--source", "PEMS04",
                   "--versions"] + [f"v04-ind-lc-s{s}" for s in seeds], 0)
    sh("pwm", ["paradoxbench/baselines.py"] + tasks, 0)
    for t in [t for t in tasks if t != "IMD-WC"]:
        sh("tfm25", ["opponents/run_timesfm.py", "--task", t, "--model", opp["25"], "--ctx", str(CTX[t])], 0)


def lane1(a, tasks, opp, gpu):
    for t in tasks:
        sh("tfm3", ["opponents/run_timesfm.py", "--task", t, "--model", opp["3"], "--mode", "multivariate",
                    "--ctx", str(CTX[t])], gpu)
    if "IMD-WC" in tasks:
        sh("tfm25", ["opponents/run_timesfm.py", "--task", "IMD-WC", "--model", opp["25"], "--ctx", "365"], gpu)


def main(a):
    tasks = a.tasks
    seeds = [0] if a.quick else [0, 1, 2]
    opp = {"25": "stub", "3": "stub"} if a.quick else {"25": "tfm25", "3": "tfm3"}
    t0 = time.time()
    try:
        import torch
        n_gpu = torch.cuda.device_count()
    except Exception:
        n_gpu = 0
    print(f"GPUs visible: {n_gpu} (lane 1 on GPU {1 if n_gpu >= 2 else 0})", flush=True)
    th = threading.Thread(target=lane1, args=(a, tasks, opp, 1 if n_gpu >= 2 else 0))
    th.start()
    lane0(a, tasks, seeds, opp)
    th.join()
    print(f"=== all lanes done in {(time.time()-t0)/60:.1f} min ===", flush=True)
    subprocess.run([PY, "paradoxbench/leaderboard.py"], cwd=ROOT)
    r = subprocess.run([PY, "check_provenance.py"], cwd=ROOT, capture_output=True, text=True)
    print("PROVENANCE:", json.loads(open(os.path.join(ROOT, "PROVENANCE_REPORT.json")).read())["verdict"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--tasks", nargs="+", default=list(LOADER))
    main(ap.parse_args())
