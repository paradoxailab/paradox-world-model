"""PWM-Dyn v0.7 study, analysis (CPU): merge the v0.6 sessions' rows and saved forecasts, then compare v0.7 with
v0.6 and with every other model on Tracks A, B, R and G, with the same paired tests as v0.6.

  python run_v07_analysis.py --roots /kaggle/input/<v0.6 session 1> /kaggle/input/<v0.6 session 2>

Rows already present (this session's) are never overwritten by merged ones.
"""
import argparse, glob, json, os, shutil, sys

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from paradoxbench.spec import stride_for, windows_per_day
from paradoxbench.score import truth, task_data, slug
from paradoxbench.significance import compare

TRAFFIC = ["PEMS08", "PEMS04", "PEMS03", "PEMS07", "METR-LA", "PEMS-BAY"]
ALL = TRAFFIC + ["IMD-CI", "IMD-WC"]
RES, SUB = os.path.join(ROOT, "results", "paradoxbench"), os.path.join(ROOT, "submissions")


def merge(roots):
    os.makedirs(RES, exist_ok=True); os.makedirs(SUB, exist_ok=True)
    n = 0
    for r in roots:
        for f in glob.glob(os.path.join(r, "**", "results", "paradoxbench", "*.json"), recursive=True):
            d = os.path.join(RES, os.path.basename(f))
            if not os.path.exists(d):
                shutil.copy(f, d); n += 1
        for f in glob.glob(os.path.join(r, "**", "submissions", "*.npz"), recursive=True):
            d = os.path.join(SUB, os.path.basename(f))
            if not os.path.exists(d):
                shutil.copy(f, d)
    print(f"merged {n} rows from {len(roots)} roots", flush=True)


def rows():
    return [json.load(open(f)) for f in sorted(glob.glob(os.path.join(RES, "*.json")))]


def sub_path(r):
    return os.path.join(SUB, f"{r['task']}__{r['track']}__{slug(r['model'])}.npz")


def pick(rs, task, track, prefix):
    c = [r for r in rs if r["task"] == task and r["track"] == track and r["model"].startswith(prefix)
         and "ablation" not in r["model"]]
    return min(c, key=lambda r: r["metrics"]["MAE"]) if c else None


def cell(r):
    return "-" if r is None else f"{r['metrics']['MAE']:.2f}"


def main(a):
    merge(a.roots)
    rs = rows()
    NEW, OLD = f"PWM-Dyn {a.tag}", f"PWM-Dyn {a.prev}"
    out = {"tables": {}, "seeds": {}, "significance": []}
    cols = [(NEW, NEW), (OLD, OLD), ("STID", "STID"),
            ("Graph WaveNet", "Graph WaveNet"), ("STAEformer", "STAEformer"), ("Climatology", "Climatology"),
            ("Last value", "Last")]
    L = ["# PWM-Dyn v0.7 study: tables", ""]
    for tr, title in (("A", "Track A (standard 12-step context)"), ("R", "Track R (30% of sensors dark)"),
                      ("G", "Track G (replayed real outages, new in ParadoxBench-1.2)")):
        L += [f"## {title}: test MAE", "", "| Task | " + " | ".join(c for c, _ in cols) + " |",
              "|---" * (len(cols) + 1) + "|"]
        for t in (TRAFFIC if tr == "G" else ALL):
            L.append(f"| {t} | " + " | ".join(cell(pick(rs, t, tr, p)) for _, p in cols) + " |")
        L.append("")
    L += ["## Track B (open context), every metric: new PWM-Dyn entry vs TimesFM 3.0", "",
          "| Task | Metric | " + NEW + " | TimesFM 3.0 | Better |", "|---|---|---|---|---|"]
    for t in ALL:
        p, o = pick(rs, t, "B", NEW), pick(rs, t, "B", "TimesFM-3.0")
        if not (p and o):
            continue
        for k in ("MAE", "RMSE", "MAPE", "QL", "IS80", "COV80"):
            x, z = p["metrics"].get(k), o["metrics"].get(k)
            if x is None or z is None:
                continue
            win = (abs(x - 0.8) < abs(z - 0.8)) if k == "COV80" else (x < z)
            L.append(f"| {t} | {k} | {x:.4g} | {z:.4g} | {'PWM-Dyn' if win else 'TimesFM'} |")
    L += ["", "## Single-model test MAE (Track A)", "", "| Task | v0.7 seeds | v0.7 mean | v0.6 seeds | v0.6 mean |",
          "|---|---|---|---|---|"]
    for t in TRAFFIC:
        s = []
        for p in (NEW, OLD):
            r = pick(rs, t, "A", p)
            m = np.array([v["MAE"] for v in r["member_test"].values()]) if r and "member_test" in r else np.array([])
            s.append(m)
            out["seeds"][f"{t}/{p}"] = m.tolist()
        f = lambda m: (" ".join(f"{x:.2f}" for x in m), f"{m.mean():.2f}" if len(m) else "-")
        L.append(f"| {t} | {f(s[0])[0]} | {f(s[0])[1]} | {f(s[1])[0]} | {f(s[1])[1]} |")

    L += ["", f"## Paired tests: {NEW} vs each model (negative = new model better)", "",
          "| Task | Track | Opponent | v0.7 MAE | Opp. MAE | Rel. diff | 95% CI | DM p |", "|---|---|---|---|---|---|---|---|"]
    for t in ALL:
        if not any(r["task"] == t for r in rs):
            continue
        ds = task_data(t)
        for tr in ("A", "B", "R", "G"):
            p = pick(rs, t, tr, NEW)
            if not p or not os.path.exists(sub_path(p)):
                continue
            _, y, valid = truth(t, tr, ds)
            qa = np.load(sub_path(p))["q50"]
            for o in [r for r in rs if r["task"] == t and r["track"] == tr and not r["model"].startswith(NEW)
                      and "Seasonal" not in r["model"] and "ablation" not in r["model"]]:
                if not os.path.exists(sub_path(o)):
                    continue
                qb = np.load(sub_path(o))["q50"]
                if qb.shape != qa.shape:
                    continue
                c = compare(qa, qb, y, valid, windows_per_day(ds))
                c.update(task=t, track=tr, pwm=p["model"], opponent=o["model"])
                out["significance"].append(c)
                L.append(f"| {t} | {tr} | {o['model']} | {c['MAE_a']:.2f} | {c['MAE_b']:.2f} | {c['rel_diff_pct']:+.1f}% | "
                         f"[{c['rel_ci95_pct'][0]:+.1f}, {c['rel_ci95_pct'][1]:+.1f}] | {c['p_value']:.2g} |")
    stem = a.tag.replace(".", "")
    json.dump(out, open(os.path.join(ROOT, "results", f"{stem}_summary.json"), "w"), indent=1)
    fz = os.path.join(ROOT, "results", f"{stem}_frozen_config.json")
    if os.path.exists(fz):
        print("FROZEN|" + json.dumps(json.load(open(fz))), flush=True)
    f = lambda v, d=4: "" if v is None else (f"{v:.{d}f}" if isinstance(v, float) else str(v))
    for r in rs:
        m = r["metrics"]
        extra = {k: r[k] for k in ("epochs_run", "stopped_by", "budget_minutes", "seed") if k in r}
        if "member_test" in r:
            extra["members"] = [round(v["MAE"], 4) for v in r["member_test"].values()]
        if "online" in r:
            extra["online"] = {k: r["online"][k] for k in ("beta", "tau", "val_MAE_uncorrected")}
        print("ROW|" + "|".join([r["task"], r["track"], r["model"], f(m["MAE"]), f(m["RMSE"]), f(m.get("MAPE"), 3),
                                 f(m.get("QL")), f(m.get("IS80")), f(m.get("COV80")), f(r.get("params"), 0),
                                 str(r.get("context_steps", "")), json.dumps(extra)]), flush=True)
    for c in out["significance"]:
        print("SIG|" + "|".join([c["task"], c["track"], c["opponent"], f(c["MAE_a"]), f(c["MAE_b"]),
                                 f(c["rel_diff_pct"], 3), f(c["rel_ci95_pct"][0], 3), f(c["rel_ci95_pct"][1], 3),
                                 f"{c['p_value']:.3g}", f(c["dm_stat"], 3), str(c["windows"])]), flush=True)
    for t in TRAFFIC:
        for v in sorted(glob.glob(os.path.join(ROOT, "models", t, "*", "val_conditions.json"))):
            print(f"VALCOND|{t}|{os.path.basename(os.path.dirname(v))}|" + json.dumps(json.load(open(v))), flush=True)
    open(os.path.join(ROOT, "results", f"{stem}_tables.md"), "w").write("\n".join(L))
    print("\n".join(L))
    import subprocess
    subprocess.run([sys.executable, os.path.join(ROOT, "paradoxbench", "leaderboard.py")], capture_output=True)
    print("ANALYSIS-DONE", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--tag", default="v0.7")
    ap.add_argument("--prev", default="v0.6")
    main(ap.parse_args())
