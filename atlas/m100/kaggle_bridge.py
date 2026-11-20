"""Colab side of the Kaggle helper (atlas/m100/kaggle_traffic.py; PREREG deviation 4).

  hold   keep the Kaggle jobs' locks fresh on Drive, so the Colab pipeline skips them ("running on the other GPU"),
         and hold t_score's lock too, so traffic is not scored before the Kaggle results are in. Stops by itself
         once every Kaggle job has a done-marker.
  fetch  download the Kaggle notebook's output (public notebook: no key needed) into a local folder.
  import copy the finished jobs (submissions, results, logs) into the Drive store under the pipeline's job names and
         write their done-markers. Only jobs that finished with exit code 0 on Kaggle are imported.

  python kaggle_bridge.py hold   --store /content/drive/MyDrive/PWM-100M
  python kaggle_bridge.py fetch  --notebook <kaggle-user>/<notebook-slug> --to /content/kaggle_out
  python kaggle_bridge.py import --store /content/drive/MyDrive/PWM-100M --src /content/kaggle_out
"""
import argparse, glob, json, os, shutil, sys, time

TASKS = ["PEMS-BAY", "METR-LA"]
TFM_OPP = [("chronos-bolt", "univariate"), ("chronos2", "univariate"), ("tfm25", "univariate"),
           ("tfm3", "univariate"), ("tfm3", "multivariate")]
JOBS = [f"t_opp_{t}_{m}_{mode}" for t in TASKS for m, mode in TFM_OPP]


def hold(a):
    d = os.path.join(a.store, "done")
    while True:
        left = [j for j in JOBS if not os.path.exists(os.path.join(d, j))]
        for j in left + (["t_score"] if left else []):
            open(os.path.join(d, j + ".running"), "w").write(f"held for Kaggle {time.time()}")
        if not left:
            for j in JOBS + ["t_score"]:
                p = os.path.join(d, j + ".running")
                if os.path.exists(p) and open(p).read().startswith("held for Kaggle"):
                    os.remove(p)
            print("all Kaggle jobs imported; locks released", flush=True); return
        time.sleep(300)


def find_root(src):
    m = glob.glob(os.path.join(src, "**", "manifest.json"), recursive=True)
    assert m, f"no manifest.json under {src}"
    return os.path.dirname(m[0])


def fetch(a):
    import kagglehub
    p = kagglehub.notebook_output_download(a.notebook)
    os.makedirs(a.to, exist_ok=True)
    shutil.copytree(p, a.to, dirs_exist_ok=True)
    print("fetched", find_root(a.to), flush=True)


def imp(a):
    root = find_root(a.src)
    man = json.load(open(os.path.join(root, "manifest.json")))
    st = a.store
    for d in ("v06/submissions", "v06/results/paradoxbench", "logs", "done"):
        os.makedirs(os.path.join(st, d), exist_ok=True)
    n = 0
    for j in JOBS:
        info = man["jobs"].get(j)
        if not info or info["rc"] != 0 or not os.path.exists(os.path.join(root, "done", j)):
            print(f"not imported: {j} ({'not run' if not info else 'rc=' + str(info['rc'])})", flush=True); continue
        t = j.split("_")[2]
        shutil.copy(os.path.join(root, "logs", j + ".txt"), os.path.join(st, "logs", j + ".txt"))
        n += 1
        open(os.path.join(st, "done", j), "w").write(open(os.path.join(root, "done", j)).read())
    for f in glob.glob(os.path.join(root, "submissions", "*__B__*.npz")):
        if f.split("/")[-1].split("__")[0] in TASKS:
            shutil.copy(f, os.path.join(st, "v06", "submissions"))
    for f in glob.glob(os.path.join(root, "results", "**", "*__B__*.json"), recursive=True):
        if f.split("/")[-1].split("__")[0] in TASKS:
            shutil.copy(f, os.path.join(st, "v06", "results", "paradoxbench"))
    shutil.copy(os.path.join(root, "manifest.json"), os.path.join(st, "logs", "kaggle_manifest.json"))
    print(f"imported {n}/{len(JOBS)} Kaggle jobs from {root} (commit {man.get('commit', '?')[:7]})", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["hold", "fetch", "import"])
    ap.add_argument("--store", default="/content/drive/MyDrive/PWM-100M")
    ap.add_argument("--notebook", default="")
    ap.add_argument("--to", default="/content/kaggle_out")
    ap.add_argument("--src", default="/content/kaggle_out")
    a = ap.parse_args()
    {"hold": hold, "fetch": fetch, "import": imp}[a.cmd](a)
