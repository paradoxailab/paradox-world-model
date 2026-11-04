"""Fetch every public input the v0.6 study needs, record exactly which version of each was used, and build the
ParadoxBench-1.1 traffic tasks. Nothing fetched here is redistributed with this kit.

  python tools/fetch_all.py              # data only (PWM-Dyn session)
  python tools/fetch_all.py --opponents  # + official code of STID, Graph WaveNet, STAEformer (opponents session)
"""
import argparse, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
EXT = os.path.join(ROOT, "ext")
ASTGNN = "https://raw.githubusercontent.com/guoshnBJTU/ASTGNN/main/data"
DCRNN = "https://raw.githubusercontent.com/liyaguang/DCRNN/master/data/sensor_graph"
REPOS = {"STAEformer": "https://github.com/XDZhelheim/STAEformer",
         "STID": "https://github.com/GestaltCogTeam/STID",
         "Graph-WaveNet": "https://github.com/nnzhan/Graph-WaveNet"}


def run(cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def curl(url, dst):
    run(["curl", "-sSfL", "-o", dst, url])


def main(a):
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(os.path.join(EXT, "astgnn"), exist_ok=True)
    os.makedirs(os.path.join(EXT, "dcrnn"), exist_ok=True)
    for d in ("PEMS08", "PEMS04"):
        for e in ("npz", "csv"):
            if not os.path.exists(f"{RAW}/{d}.{e}"):
                curl(f"{ASTGNN}/{d}/{d}.{e}", f"{RAW}/{d}.{e}")
    for f in ("PEMS03/PEMS03.csv", "PEMS03/PEMS03.txt", "PEMS07/PEMS07.csv"):
        curl(f"{ASTGNN}/{f}", os.path.join(EXT, "astgnn", os.path.basename(f)))
    for f in ("adj_mx.pkl", "adj_mx_bay.pkl"):
        curl(f"{DCRNN}/{f}", os.path.join(EXT, "dcrnn", f))
    want = ["STAEformer"] + (["STID", "Graph-WaveNet"] if a.opponents else [])
    shas = {}
    for name in want:
        dst = os.path.join(EXT, name)
        if not os.path.exists(dst):
            run(["git", "clone", "-q", "--depth", "1", REPOS[name], dst])
        shas[name] = subprocess.run(["git", "-C", dst, "rev-parse", "HEAD"], capture_output=True,
                                    text=True).stdout.strip()
    run([sys.executable, os.path.join(ROOT, "tools", "prepare_traffic_data.py"), "--staeformer",
         os.path.join(EXT, "STAEformer"), "--astgnn", os.path.join(EXT, "astgnn"),
         "--dcrnn", os.path.join(EXT, "dcrnn")])
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    json.dump({"repositories": {k: {"url": REPOS[k], "commit": v} for k, v in shas.items()},
               "files": {"ASTGNN": ASTGNN, "DCRNN": DCRNN}},
              open(os.path.join(ROOT, "results", "external_sources.json"), "w"), indent=1)
    print("external sources:", json.dumps(shas), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--opponents", action="store_true")
    main(ap.parse_args())
