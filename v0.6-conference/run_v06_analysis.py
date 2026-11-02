"""PWM-Dyn v0.6 study, analysis (CPU): merge the scored rows and submissions of every session, then build the
ParadoxBench-1.1 leaderboard, the seed table, the ablation table and paired significance tests.

  python run_v06_analysis.py --roots /kaggle/input/<session-1>/... /kaggle/input/<session-2>/... /kaggle/input/<v0.4>/...

Each root is a kit folder holding results/paradoxbench/*.json and submissions/*.npz. Rows from later roots never
overwrite rows already merged (ParadoxBench-1 rows from the v0.4 study are kept as they were scored).
"""
import argparse, glob, json, os, shutil, sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from paradoxbench.spec import TASKS, stride_for
from paradoxbench.score import truth, task_data, slug
from paradoxbench.significance import compare

TRAFFIC = ["PEMS08", "PEMS04", "PEMS03", "PEMS07", "METR-LA", "PEMS-BAY"]
RES, SUB = os.path.join(ROOT, "results", "paradoxbench"), os.path.join(ROOT, "submissions")


def merge(roots):
    os.makedirs(RES, exist_ok=True); os.makedirs(SUB, exist_ok=True)
    for r in roots:
        for f in glob.glob(os.path.join(r, "results", "paradoxbench", "*.json")):
            d = os.path.join(RES, os.path.basename(f))
            if not os.path.exists(d):
                shutil.copy(f, d)
        for f in glob.glob(os.path.join(r, "submissions", "*.npz")):
            d = os.path.join(SUB, os.path.basename(f))
            if not os.path.exists(d):
                shutil.copy(f, d)
        for f in ("results/v06_frozen_config.json", "results/external_sources.json"):
            if os.path.exists(os.path.join(r, f)) and not os.path.exists(os.path.join(ROOT, f)):
                shutil.copy(os.path.join(r, f), os.path.join(ROOT, f))


def rows():
    return [json.load(open(f)) for f in sorted(glob.glob(os.path.join(RES, "*.json")))]


def sub_path(r):
    return os.path.join(SUB, f"{r['task']}__{r['track']}__{slug(r['model'])}.npz")


def pick(rs, task, track, prefix):
    c = [r for r in rs if r["task"] == task and r["track"] == track and r["model"].startswith(prefix)]
    return min(c, key=lambda r: r["metrics"]["MAE"]) if c else None   # only ever several for TimesFM ctx variants


def main(a):
    merge(a.roots)
    rs = rows()
    out = {"seeds": {}, "significance": [], "ablation": []}
    L = ["# PWM-Dyn v0.6 study: tables", ""]

    # seeds: single-model test MAE of each fresh seed (Track A and B)
    L += ["## Seed variation (single-model test MAE of the three fresh seeds)", "",
          "| Task | Track | Seeds | Mean | SD | Ensemble |", "|---|---|---|---|---|---|"]
    for t in TRAFFIC:
        for tr in ("A", "B"):
            r = pick(rs, t, tr, "PWM-Dyn v0.6")
            if not r or "member_test" not in r:
                continue
            m = np.array([v["MAE"] for v in r["member_test"].values()])
            out["seeds"][f"{t}/{tr}"] = {"members": m.tolist(), "mean": float(m.mean()), "sd": float(m.std(ddof=1)),
                                        "ensemble": r["metrics"]["MAE"]}
            L.append(f"| {t} | {tr} | {' '.join(f'{x:.2f}' for x in m)} | {m.mean():.2f} | {m.std(ddof=1):.2f} | "
                     f"{r['metrics']['MAE']:.2f} |")

    # ablation (Track A test, selection was on validation)
    L += ["", "## v0.3-gap ablation (selection on validation; test shown for the record)", "",
          "| Task | Configuration | Test MAE (2-seed ensemble) |", "|---|---|---|"]
    for r in sorted([r for r in rs if "ablation" in r["model"]], key=lambda r: (r["task"], r["model"])):
        out["ablation"].append({"task": r["task"], "model": r["model"], "MAE": r["metrics"]["MAE"]})
        L.append(f"| {r['task']} | {r['model']} | {r['metrics']['MAE']:.3f} |")

    # significance: PWM-Dyn v0.6 vs every other model with a saved forecast, Tracks A and B
    L += ["", "## Paired tests: PWM-Dyn v0.6 vs each model (negative difference = PWM-Dyn better)", "",
          "| Task | Track | Opponent | PWM MAE | Opp. MAE | Rel. diff | 95% CI | DM p |", "|---|---|---|---|---|---|---|---|"]
    for t in TRAFFIC:
        ds = task_data(t)
        for tr in ("A", "B"):
            p = pick(rs, t, tr, "PWM-Dyn v0.6")
            if not p or not os.path.exists(sub_path(p)):
                continue
            _, y, valid = truth(t, tr, ds)
            qa = np.load(sub_path(p))["q50"]
            for o in [r for r in rs if r["task"] == t and r["track"] == tr and not r["model"].startswith("PWM-Dyn")
                      and "Seasonal" not in r["model"]]:
                if not os.path.exists(sub_path(o)):
                    continue
                qb = np.load(sub_path(o))["q50"]
                if qb.shape != qa.shape:
                    continue
                c = compare(qa, qb, y, valid, 288 // stride_for(ds))
                c.update(task=t, track=tr, pwm=p["model"], opponent=o["model"])
                out["significance"].append(c)
                L.append(f"| {t} | {tr} | {o['model']} | {c['MAE_a']:.2f} | {c['MAE_b']:.2f} | {c['rel_diff_pct']:+.1f}% | "
                         f"[{c['rel_ci95_pct'][0]:+.1f}, {c['rel_ci95_pct'][1]:+.1f}] | {c['p_value']:.2g} |")
    json.dump(out, open(os.path.join(ROOT, "results", "v06_summary.json"), "w"), indent=1)
    open(os.path.join(ROOT, "results", "v06_tables.md"), "w").write("\n".join(L))
    print("\n".join(L))
    import subprocess
    subprocess.run([sys.executable, os.path.join(ROOT, "paradoxbench", "leaderboard.py")], capture_output=True)
    print("ANALYSIS-DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    main(ap.parse_args())
