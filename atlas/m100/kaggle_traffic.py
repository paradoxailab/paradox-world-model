"""Atlas-100M traffic, Track B helper for a Kaggle GPU (rules: atlas/m100/PREREG.md, deviation 4).

Runs some of the zero-shot foundation-model jobs of pipeline.py (same script, same arguments: opponents/run_timesfm.py,
context 512, the pipeline's chunk sizes) on Kaggle's GPUs while Colab runs the rest. Only zero-shot models run here:
they have no training and no time budget, so the GPU type cannot change how well they do. The trained specialists
(STID, Graph WaveNet, STAEformer) stay on Colab, where their wall-clock budgets were set.

Two workers (one per GPU) take jobs from one queue, largest first. Every finished job leaves, in OUT:
  submissions/<task>__B__<model>.npz, results/<task>__B__<model>.json   (written by paradoxbench.score.record)
  logs/<job>.txt, done/<job>  and manifest.json (GPU, package versions, minutes per job)
atlas/m100/kaggle_bridge.py then copies them into the Colab pipeline's Drive store under the same job names.

  python atlas/m100/kaggle_traffic.py --out /kaggle/working/m100_kaggle
"""
import argparse, json, os, queue, shutil, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
V06 = os.path.join(REPO, "v0.6-conference")
sys.path.insert(0, HERE)
from pipeline import CHUNK, TFM_OPP                       # identical settings to the Colab pipeline

KAGGLE_TASKS = ["PEMS-BAY", "METR-LA"]                     # the last two networks of the pipeline's order
COST = {"tfm3": 3, "chronos2": 1, "tfm25": 1, "chronos-bolt": 1}


def jobs():
    js = [(t, m, mode) for t in KAGGLE_TASKS for m, mode in TFM_OPP]
    return sorted(js, key=lambda j: -COST[j[1]] * (2 if j[0] == "PEMS-BAY" else 1))


def name(t, m, mode):
    return f"t_opp_{t}_{m}_{mode}"


def gpu_name(i):
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader", "-i", str(i)],
                             capture_output=True, text=True).stdout.strip()
        return out or "unknown"
    except OSError:
        return "unknown"


def worker(gpu, q, out, man, lock):
    while True:
        try:
            t, m, mode = q.get_nowait()
        except queue.Empty:
            return
        nm = name(t, m, mode)
        if os.path.exists(os.path.join(out, "done", nm)):
            continue
        cmd = [sys.executable, "-u", "opponents/run_timesfm.py", "--task", t, "--model", m, "--mode", mode,
               "--ctx", "512", "--chunk", str(CHUNK[t])]
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu))
        t0 = time.time()
        with open(os.path.join(out, "logs", nm + ".txt"), "w") as f:
            f.write(f"+ {' '.join(cmd)}  (GPU {gpu}: {gpu_name(gpu)})\n"); f.flush()
            rc = subprocess.run(cmd, cwd=V06, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
        mins = round((time.time() - t0) / 60, 1)
        with lock:
            for d in ("submissions", "results/paradoxbench"):        # copy whatever record() wrote so far
                src = os.path.join(V06, d)
                if os.path.isdir(src):
                    shutil.copytree(src, os.path.join(out, d.split("/")[0]), dirs_exist_ok=True)
            man["jobs"][nm] = dict(rc=rc, minutes=mins, gpu=gpu_name(gpu))
            json.dump(man, open(os.path.join(out, "manifest.json"), "w"), indent=1)
            if rc == 0:
                open(os.path.join(out, "done", nm), "w").write(f"{mins} min on Kaggle {gpu_name(gpu)}")
        print(f"[{'done' if rc == 0 else 'FAIL'}] {nm} rc={rc} {mins} min (GPU {gpu})", flush=True)


def main(a):
    for d in ("submissions", "results", "logs", "done"):
        os.makedirs(os.path.join(a.out, d), exist_ok=True)
    import importlib.metadata as md
    vers = {}
    for p in ("timesfm", "chronos-forecasting", "torch", "transformers"):
        try:
            vers[p] = md.version(p)
        except md.PackageNotFoundError:
            vers[p] = None
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    man = dict(where="Kaggle", commit=commit, packages=vers, started=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
               jobs={})
    import torch
    n = max(1, torch.cuda.device_count())
    print(f"{n} GPU(s): {[gpu_name(i) for i in range(n)]}; jobs: {[name(*j) for j in jobs()]}", flush=True)
    q = queue.Queue()
    for j in jobs():
        q.put(j)
    lock = threading.Lock()
    th = [threading.Thread(target=worker, args=(g, q, a.out, man, lock)) for g in range(n)]
    for x in th:
        x.start()
    for x in th:
        x.join()
    man["finished"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    json.dump(man, open(os.path.join(a.out, "manifest.json"), "w"), indent=1)
    ok = sum(os.path.exists(os.path.join(a.out, "done", name(*j))) for j in jobs())
    print(f"KAGGLE-TRAFFIC-DONE {ok}/{len(jobs())} jobs", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/kaggle/working/m100_kaggle")
    main(ap.parse_args())
