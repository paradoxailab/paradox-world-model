"""Runs WB1-T's remaining shares and the threshold grid (README "Threshold grid on Colab"), the same jobs, order and recipe
as notebooks/atlas_threshold_grid_colab.ipynb cell 2, then both scorers. Resumable: finished runs are skipped, an
interrupted run continues from its checkpoint. For a runtime that already has Drive mounted and WEATHER-5K in --raw:

  nohup python -u tools/run_thr_grid.py --raw /content/raw --out /content/drive/MyDrive/PWM-10M/thr > runner.log 2>&1 &
"""
import argparse, glob, json, os, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__)); DELHI = os.path.dirname(HERE); REPO = os.path.dirname(os.path.dirname(DELHI))


def main(a):
    os.makedirs(a.out, exist_ok=True)
    for f in glob.glob(f"{REPO}/atlas/results/kaggle/atlas-w5k-thr-a/w5k_atlas_1m_h24_f*_s600.json") + \
             [f"{REPO}/atlas/results/kaggle/atlas-w5k-atlas1m-h24/w5k_atlas_1m_h24_s600.json"]:
        if not os.path.exists(os.path.join(a.out, os.path.basename(f))):
            shutil.copy(f, a.out)
    env = dict(os.environ, PW_RAW=a.raw, ATLAS_OUT=a.out)
    lab = {100_000: "100k", 300_000: "300k", 3_000_000: "3m", 10_000_000: "10m"}
    sfx = lambda fr: "" if fr == 1 else "_f" + str(fr).replace(".", "")
    jobs = [(f"w5k_atlas_1m_h24{sfx(fr)}", 1_000_000, fr, 600) for fr in (0.03125, 0.125, 0.5)]
    for size in (100_000, 300_000, 3_000_000, 10_000_000):
        for fr in (0.015625, 0.0625, 0.25, 1):
            jobs.append((f"w5k_grid_{lab[size]}_h24{sfx(fr)}", size, fr, 600))
    jobs += [("w5k_seed2_atlas_1m_h24", 1_000_000, 1, 601), ("w5k_seed2_grid_10m_h24", 10_000_000, 1, 601)]
    if a.only_wb1t:
        jobs = jobs[:3]
    for tag, size, fr, seed in jobs:
        res = os.path.join(a.out, f"{tag}_s{seed}.json")
        tries = 0
        while not os.path.exists(res):
            cmd = ["python", "-u", "run_atlas_5k.py", "--model", "atlas", "--H", "24", "--size", str(size), "--seed", str(seed),
                   "--tag", tag, "--no-test", "--pause-at-cap", "--cap", "600", "--max-params", "11000000"]
            if fr != 1:
                cmd += ["--frac", str(fr)]
            print("RUN", tag, flush=True)
            with open(os.path.join(a.out, f"log_{tag}.txt"), "a") as lf:
                p = subprocess.run(cmd, cwd=DELHI, env=env, stdout=lf, stderr=subprocess.STDOUT)
            tries += 1
            if p.returncode != 0 and not os.path.exists(res) and tries >= 2:
                raise SystemExit(f"{tag} failed twice (see log_{tag}.txt)")
        print("DONE", tag, json.load(open(res)).get("val_best"), flush=True)
        if tag.endswith("_f05") and "atlas_1m" in tag:                          # WB1-T complete: score it at once
            subprocess.run(["python", "-u", "score_w5k_thr.py"], cwd=DELHI, env=env)
    subprocess.run(["python", "-u", "score_w5k_thr.py"], cwd=DELHI, env=env)
    subprocess.run(["python", "-u", "score_w5k_grid.py"], cwd=DELHI, env=env)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="/content/raw"); ap.add_argument("--out", default="/content/drive/MyDrive/PWM-10M/thr")
    ap.add_argument("--only-wb1t", action="store_true")
    main(ap.parse_args())
