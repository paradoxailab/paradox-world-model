"""Atlas-100M, the whole programme as one resumable queue (rules: atlas/m100/PREREG.md).

Every job writes a done-marker to the store (Google Drive); re-running skips finished jobs, so a disconnect loses at most
the job in progress (training itself also resumes mid-run). Test windows are read only by the *_score jobs, after
training has finished.

  python atlas/m100/pipeline.py --store /content/drive/MyDrive/PWM-100M --w10 /content/drive/MyDrive/PWM-10M --stage all
Stages: data, train, opponents, weather, aq, traffic, hybrid (comma-separated), or all.
Two GPUs at once: run "data,train,weather,aq,traffic,hybrid" on one account and "data,opponents" on another;
both use the same Drive store (different jobs, different files).
"""
import argparse, glob, json, os, shutil, subprocess, sys, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.dirname(HERE); REPO = os.path.dirname(ATLAS)
DELHI = os.path.join(ATLAS, "delhi"); V06 = os.path.join(REPO, "v0.6-conference")
PY = sys.executable
TRAFFIC = ["PEMS08", "PEMS04", "PEMS03", "PEMS07", "METR-LA", "PEMS-BAY"]
SIZE = {"PEMS08": "small", "PEMS04": "small", "PEMS03": "mid", "METR-LA": "mid", "PEMS07": "large", "PEMS-BAY": "large"}
MINUTES = {"stid": {"small": 6, "mid": 8, "large": 12}, "gwnet": {"small": 30, "mid": 40, "large": 50},
           "staeformer": {"small": 30, "mid": 40, "large": 55}}            # paper 1's budgets (run_v06_opponents.py)
TFM_OPP = [("chronos-bolt", "univariate"), ("chronos2", "univariate"), ("tfm25", "univariate"),
           ("tfm3", "univariate"), ("tfm3", "multivariate")]
AQ_OPP = "chronos-bolt,chronos2,tfm25,tfm3,tfm3mv,ttm,tirex,sundial,timemoe200"
AQ_OPP_OLD_TF = "sundial,timemoe200"          # their remote code needs transformers==4.40.1 (PREREG deviation 1)
TF440 = "/content/tf440"
CHUNK = {"PEMS07": 8, "PEMS-BAY": 16, "PEMS03": 16, "METR-LA": 32, "PEMS04": 32, "PEMS08": 64}
W5K_OPP = ["persist", "chronos-bolt", "chronos2", "chronos2mv", "tfm25", "tfm3", "ttm", "tirex", "sundial", "timemoe200"]
TAG = "atlas100m"


class Store:
    def __init__(self, path):
        self.p = path
        for d in ("done", "out", "data", "logs", "v06", "nwp"):
            os.makedirs(os.path.join(path, d), exist_ok=True)

    def done(self, job):
        return os.path.exists(os.path.join(self.p, "done", job))

    def mark(self, job, info=""):
        open(os.path.join(self.p, "done", job), "w").write(info)

    def restore_v06(self):                                      # traffic submissions / results / models live in the repo
        for d in ("submissions", "results/paradoxbench", "models"):
            src = os.path.join(self.p, "v06", d)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(V06, d), dirs_exist_ok=True)

    def save_v06(self):
        for d in ("submissions", "results/paradoxbench", "models"):
            src = os.path.join(V06, d)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(self.p, "v06", d), dirs_exist_ok=True)


def sh(cmd, log, cwd=None, env=None, lock=None):
    print("+", " ".join(cmd), flush=True)
    e = dict(os.environ, **(env or {}))
    alive = [True]

    def beat():                                                       # heartbeat: the other GPU sees this job is alive
        while alive[0]:
            try:
                open(lock, "w").write(str(time.time()))
            except OSError:
                pass
            time.sleep(60)
    if lock:
        threading.Thread(target=beat, daemon=True).start()
    try:
        with open(log, "a") as f:
            p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=e)
            for line in p.stdout:
                if "Warning" in line or "warn(" in line:
                    continue
                print(line, end="", flush=True); f.write(line)
            return p.wait()
    finally:
        alive[0] = False


def job(st, name, cmd, cwd=None, env=None, after=None):
    if st.done(name):
        print(f"[skip] {name} (done)", flush=True); return True
    lock = os.path.join(st.p, "done", name + ".running")
    if os.path.exists(lock) and time.time() - os.path.getmtime(lock) < 20 * 60:
        print(f"[skip] {name} (running on the other GPU)", flush=True); return False
    open(lock, "w").write(str(time.time()))
    t0 = time.time()
    try:
        rc = sh(cmd, os.path.join(st.p, "logs", f"{name}.txt"), cwd, env, lock)
    finally:
        if os.path.exists(lock):
            os.remove(lock)
    if after:
        after()
    if rc != 0:
        print(f"[FAIL] {name} rc={rc}", flush=True); return False
    st.mark(name, f"{(time.time() - t0) / 60:.1f} min"); print(f"[done] {name} in {(time.time() - t0) / 60:.1f} min", flush=True)
    return True


def traffic_jobs():
    return ([f"t_opp_{t}_{m}_{mode}" for t in TRAFFIC for m, mode in TFM_OPP] +
            [f"t_spec_{t}_{m}" for t in TRAFFIC for m in ("stid", "gwnet", "staeformer")] + ["t_pwmdyn"])


def traffic_opponents(st):
    for t in TRAFFIC:
        for m, mode in TFM_OPP:
            job(st, f"t_opp_{t}_{m}_{mode}", [PY, "opponents/run_timesfm.py", "--task", t, "--model", m, "--mode", mode,
                                              "--ctx", "512", "--chunk", str(CHUNK[t])], cwd=V06, after=st.save_v06)
        for m in ("stid", "gwnet", "staeformer"):
            job(st, f"t_spec_{t}_{m}", [PY, "opponents/run_specialists.py", "--task", t, "--model", m, "--ext",
                                        os.path.join(V06, "ext"), "--minutes", str(MINUTES[m][SIZE[t]])], cwd=V06, after=st.save_v06)
    job(st, "t_pwmdyn", [PY, "tools/traffic_round.py", "--store", os.path.join(st.p, "pwmdyn"), "--stage", "train,score"],
        cwd=V06, after=st.save_v06)


def main(a):
    st = Store(a.store)
    RAW, LIVE, OUT = a.raw, a.live, os.path.join(st.p, "out")
    env = dict(PW_RAW=RAW, ATLAS_OUT=OUT)
    stages = a.stage.split(",")
    on = lambda s: "all" in stages or s in stages
    st.restore_v06()
    view = lambda d: os.path.join(OUT, f"{TAG}_{d}_view.pt")
    trained = lambda: os.path.exists(os.path.join(OUT, f"{TAG}_summary.json"))

    if on("data"):
        os.makedirs(RAW, exist_ok=True); os.makedirs(LIVE, exist_ok=True)
        for f in ("W5K_X.npy", "W5K_META.npz"):                       # the WEATHER-5K copy made for papers 5 (Drive)
            if not os.path.exists(os.path.join(RAW, f)):
                shutil.copy(os.path.join(a.w10, "data", f), RAW)
        for f in ("W5K_X.npy", "W5K_OBS.npy", "W5K_META.npz"):        # the NOAA live period (1 Jan 2024 .. 24 Aug 2025)
            if not os.path.exists(os.path.join(LIVE, f)):
                shutil.copy(os.path.join(a.w10, "live", f), LIVE)
        india = os.path.join(st.p, "data", "INDIA_LONG.npz")
        if not os.path.exists(india):                                 # papers 3/4: CPCB via the public Kaggle dataset
            code = ("import kagglehub,os;p=kagglehub.dataset_download('abhisheksjha/time-series-air-quality-data-of-india-2010-2023');"
                    "print('KAGGLE',p)")
            out = subprocess.run([PY, "-c", code], capture_output=True, text=True).stdout
            p = [l.split(" ", 1)[1] for l in out.splitlines() if l.startswith("KAGGLE")]
            assert p, "the Kaggle download failed: " + out[-400:]
            if job(st, "data_india", [PY, "tools/build_india_long.py"], cwd=DELHI, env=dict(env, LONG_SEARCH=p[0])) \
                    and os.path.exists(os.path.join(RAW, "INDIA_LONG.npz")):
                shutil.copy(os.path.join(RAW, "INDIA_LONG.npz"), india)
            for _ in range(240):                                      # the other GPU may be building it: wait for it
                if os.path.exists(india):
                    break
                time.sleep(30)
            assert os.path.exists(india), "INDIA_LONG.npz was not built"
        if not os.path.exists(os.path.join(RAW, "INDIA_LONG.npz")):
            shutil.copy(india, RAW)
        assert job(st, "data_traffic", [PY, "tools/fetch_all.py", "--opponents"], cwd=V06) or True
        if not os.path.exists(os.path.join(V06, "data", "raw", "PEMS07.npz")):
            sh([PY, "tools/fetch_all.py", "--opponents"], os.path.join(st.p, "logs", "data_traffic_restore.txt"), cwd=V06)

    if on("train"):
        job(st, "train", [PY, "-u", os.path.join(HERE, "train.py"), "--init", a.init, "--out", OUT, "--tag", TAG,
                          "--cap", str(a.cap)], env=env)
        if not trained():
            print("TRAINING NOT FINISHED (paused or stopped): run the notebook again to resume.", flush=True); return

    if on("weather") and trained():
        H2 = os.path.join(a.w10, "small")                             # the opponents' saved per-window errors (paper 5)
        e2 = dict(env, ATLAS_OUT=H2)
        job(st, "w_full", [PY, "-u", "run_atlas_5k.py", "--eval", view("weather"), "--H", "24", "--k", "32",
                           "--tag", f"{TAG}_eval"], cwd=DELHI, env=env)
        job(st, "w_h2h_val", [PY, "-u", "score_tsfm_w5k.py", "--stations-every", "8", "--year", "val", "--origin-every", "48",
                              "--atlas", f"{TAG}={view('weather')}", "--models", ""], cwd=DELHI, env=e2)
        job(st, "w_h2h_test", [PY, "-u", "score_tsfm_w5k.py", "--stations-every", "8", "--year", "test", "--origin-every", "48",
                               "--atlas", f"{TAG}={view('weather')}", "--models", ""], cwd=DELHI, env=e2)
        job(st, "w_h2h_live", [PY, "-u", "score_tsfm_w5k.py", "--stations-every", "8", "--year", "live", "--origin-every", "96",
                               "--atlas", f"{TAG}={view('weather')}", "--models", ""], cwd=DELHI, env=dict(e2, PW_RAW=LIVE))
        for yr in ("test", "live"):
            have = [k for k in W5K_OPP if os.path.exists(os.path.join(H2, "h2h", f"{k}_{yr}.npz"))]
            job(st, f"w_paired_{yr}", [PY, "paired_w5k.py", "--year", yr, "--ours", TAG, "--vs", ",".join(have), "--suffix", "_m100"],
                cwd=DELHI, env=e2)
            job(st, f"w_paired_{yr}_vs25m", [PY, "paired_w5k.py", "--year", yr, "--ours", TAG, "--vs", "atlas25m", "--suffix", "_m100vs25m"],
                cwd=DELHI, env=e2)

    if on("opponents") or (on("aq") and trained()):              # opponents need no Atlas-100M: can run on a 2nd GPU
        job(st, "aq_opp", [PY, "-u", "india_opponents.py", "--keys", AQ_OPP], cwd=DELHI, env=env)
        if not os.path.exists(os.path.join(TF440, "transformers")):    # transformers 4.40.1 beside the current one
            subprocess.run([PY, "-m", "pip", "install", "-q", "--no-deps", "--target", TF440, "transformers==4.40.1"])
            t = os.path.join(TF440, "transformers", "dependency_versions_table.py")   # tokenizers / hub: unused here
            txt = open(t).read().replace(",<0.20", "").replace(",<1.0", "")
            open(t, "w").write(txt)
        job(st, "aq_opp_tf440", [PY, "-u", "india_opponents.py", "--keys", AQ_OPP_OLD_TF], cwd=DELHI,
            env=dict(env, PYTHONPATH=TF440))
    if on("opponents") or (on("traffic") and trained()):
        traffic_opponents(st)
    if on("opponents") or (on("hybrid") and trained()):
        NWP = os.path.join(st.p, "nwp")
        if not os.path.exists(os.path.join(NWP, "NWP_W5K.npz")):
            sh([PY, "-u", os.path.join(HERE, "hybrid.py"), "fetch", "--raw", LIVE, "--out", NWP], os.path.join(st.p, "logs", "h_fetch.txt"))

    if on("aq") and trained():
        v1 = os.path.join(REPO, "models", "series", "40_atlas_india_v1.0.pt")   # paper 3's released weights
        first = os.path.join(OUT, f"{TAG}_aq_results.json"); keep = os.path.join(OUT, f"{TAG}_aq_results_first7.json")
        if st.done("aq_score") and os.path.exists(first) and not os.path.exists(keep):
            shutil.copy(first, keep)                                  # the first (seven-opponent) score, kept as it was
        job(st, "aq_score_full", [PY, "-u", os.path.join(HERE, "score_aq.py"), "--view", view("aq"), "--india-v1", v1,
                             "--opp-dir", OUT, "--out", OUT], env=env)

    if on("traffic") and trained():
        if not all(st.done(j) for j in traffic_jobs()):
            print("TRAFFIC: opponents not finished yet (stage 'opponents' or this stage will run them).", flush=True)
            traffic_opponents(st)
        st.restore_v06()
        for f in glob.glob(os.path.join(st.p, "pwmdyn", "submissions", "*.npz")):     # PWM-Dyn v0.6r (paper 1's recipe)
            shutil.copy(f, os.path.join(V06, "submissions"))
        job(st, "t_score", [PY, "-u", os.path.join(HERE, "score_traffic.py"), "--view", view("traffic"), "--summary",
                            os.path.join(OUT, f"{TAG}_summary.json"), "--out", OUT], cwd=V06, after=st.save_v06)

    if on("hybrid") and trained():
        NWP = os.path.join(st.p, "nwp")
        if os.path.exists(os.path.join(NWP, "NWP_W5K.npz")):
            job(st, "h_train", [PY, "-u", os.path.join(HERE, "hybrid.py"), "train", "--raw", LIVE, "--nwp", os.path.join(NWP, "NWP_W5K.npz"),
                                "--view", view("weather"), "--out", OUT])
            job(st, "h_score", [PY, "-u", os.path.join(HERE, "hybrid.py"), "score", "--raw", LIVE, "--nwp", os.path.join(NWP, "NWP_W5K.npz"),
                                "--hybrid", os.path.join(OUT, "hybrid_best.pt"), "--pure", view("weather"), "--out", OUT])
        else:
            print("HYBRID: the forecast archive is still being fetched (free daily limit). Run the hybrid stage again tomorrow.", flush=True)
    print("PIPELINE PASS FINISHED", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--w10", required=True, help="the papers-5 Drive folder (PWM-10M): data copy, live data, saved opponents")
    ap.add_argument("--init", default=os.path.join(REPO, "models", "series", "59_atlas-5k-25m_weather5k_adopted.pt"))
    ap.add_argument("--raw", default="/content/raw")
    ap.add_argument("--live", default="/content/live")
    ap.add_argument("--stage", default="all")
    ap.add_argument("--cap", type=float, default=600)
    main(ap.parse_args())
