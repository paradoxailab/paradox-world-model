"""Shared helpers for the v0.6 study drivers: run jobs on N GPUs from one queue, keep only result lines in the
log, and stop starting new jobs once the session's time budget is used up."""
import json, os, queue, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
KEEP = ("ParadoxBench", "best val", "Error", "Traceback", "error:", "time budget", "step budget", "stopped after",
        "windows x", "on PEMS", "on METR", "parameters,", "external sources")
LOCK = threading.Lock()
T0 = time.time()


def log(msg):
    with LOCK:
        print(msg, flush=True)


def sh(lane, args, gpu, keep=KEEP):
    env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), PYTHONUNBUFFERED="1")
    t = time.time()
    p = subprocess.Popen([PY] + args, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    tail = []
    for line in p.stdout:
        tail = (tail + [line.rstrip()])[-15:]
        if any(k in line for k in keep):
            log(f"[{lane} gpu{gpu} {time.strftime('%H:%M:%S')}] {line.rstrip()}")
    p.wait()
    if p.returncode:
        log(f"[{lane}] FAILED ({p.returncode}): {' '.join(args)}\n" + "\n".join(tail))
    return p.returncode == 0, (time.time() - t) / 60


def run_parallel(jobs, n_gpu, deadline_min=None, lanes=None):
    """jobs: list of (lane, args). lanes: optional {gpu: [jobs only that gpu runs first]}."""
    q = queue.Queue()
    for j in jobs:
        q.put(j)
    skipped = []

    def worker(g):
        for j in (lanes or {}).get(g, []):
            if deadline_min and (time.time() - T0) / 60 > deadline_min:
                skipped.append(j); continue
            sh(j[0], j[1], g)
        while True:
            try:
                j = q.get_nowait()
            except queue.Empty:
                return
            if deadline_min and (time.time() - T0) / 60 > deadline_min:
                skipped.append(j); continue
            sh(j[0], j[1], g)

    ts = [threading.Thread(target=worker, args=(g,)) for g in range(max(n_gpu, 1))]
    [t.start() for t in ts]
    [t.join() for t in ts]
    for j in skipped:
        log(f"[budget] SKIPPED (session time budget used up): {' '.join(j[1])}")
    return skipped


def n_gpus():
    try:
        import torch
        return torch.cuda.device_count()
    except Exception:
        return 0


def val_mae(loader, version):
    f = os.path.join(ROOT, "models", loader, version, "report.json")
    return json.load(open(f))["val"]["MAE"] if os.path.exists(f) else float("inf")


def minutes():
    return (time.time() - T0) / 60
