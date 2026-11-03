"""PWM-Dyn v0.6 study, session 2 of 2 (2 GPUs): the opponents.

  GPU 1 first: Google TimesFM 3.0 multivariate, zero-shot, 512-step context, on the four ParadoxBench-1.1 networks
               (its PEMS08 / PEMS04 results come from the v0.4 study of 2026-11-01 on the same windows).
  Both GPUs:   STID, Graph WaveNet and STAEformer, official code, trained on each of the six networks' train split
               within a per-run wall-clock budget, scored on Tracks A, B and R.

  python run_v06_opponents.py            # full (budget ~10 h)
  python run_v06_opponents.py --quick    # pipeline check: stub TimesFM, specialists on a few windows
"""
import argparse, json, os, subprocess

from studylib import ROOT, PY, log, run_parallel, n_gpus, minutes

NEW = ["PEMS07", "PEMS-BAY", "PEMS03", "METR-LA"]
ALL = ["PEMS07", "PEMS-BAY", "PEMS03", "METR-LA", "PEMS04", "PEMS08"]
SIZE = {"PEMS08": "small", "PEMS04": "small", "PEMS03": "mid", "METR-LA": "mid", "PEMS07": "large", "PEMS-BAY": "large"}
MINUTES = {"stid": {"small": 6, "mid": 8, "large": 12},
           "gwnet": {"small": 30, "mid": 40, "large": 50},
           "staeformer": {"small": 30, "mid": 40, "large": 55}}
CHUNK = {"PEMS07": 8, "PEMS-BAY": 16, "PEMS03": 16, "METR-LA": 32}


def main(a):
    g = n_gpus()
    ext = os.path.join(ROOT, "ext")
    log(f"v0.6 opponents session, GPUs: {g}")
    tfm = [("tfm3", ["opponents/run_timesfm.py", "--task", t, "--model", "stub" if a.quick else "tfm3",
                     "--mode", "multivariate", "--ctx", "512", "--chunk", str(CHUNK[t])]) for t in NEW if t in a.tasks]
    spec = []
    for m in ("staeformer", "gwnet", "stid"):
        for t in ALL:
            if t in a.tasks:
                spec.append(("spec", ["opponents/run_specialists.py", "--task", t, "--model", m, "--ext", ext,
                                      "--minutes", str(MINUTES[m][SIZE[t]])] + (["--quick"] if a.quick else [])))
    lanes = {1 if g >= 2 else 0: tfm}
    run_parallel(spec, g, deadline_min=a.budget_hours * 60 - 60, lanes=lanes)
    log(f"=== v0.6 opponents session done in {minutes():.1f} min ===")
    subprocess.run([PY, "paradoxbench/leaderboard.py"], cwd=ROOT, capture_output=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--budget_hours", type=float, default=10.0)
    ap.add_argument("--tasks", nargs="+", default=ALL)
    main(ap.parse_args())
