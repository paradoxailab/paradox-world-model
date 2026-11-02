"""Build LEADERBOARD.md from results/paradoxbench/*.json (every row scored by paradoxbench.metrics on the official
windows). Rows are sorted by MAE within each task and track."""
import glob, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pwm.data import ROOT
from paradoxbench.spec import TASKS, TRACKS, VERSION, STRIDE, STRIDE_BY_LOADER


def fmt(v, f="{:.2f}"):
    return "-" if v is None else f.format(v)


def main():
    rows = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(ROOT, "results", "paradoxbench", "*.json")))]
    L = [f"# {VERSION} leaderboard", "",
         f"Official windows: every {STRIDE}nd test window (tasks new in 1.1: every 6th). Lower is better for MAE, RMSE, QL and IS80; "
         "COV80 should be close to 80%.", ""]
    for task in TASKS:
        for tr in "ABRZ":
            rs = sorted([r for r in rows if r["task"] == task and r["track"] == tr], key=lambda r: r["metrics"]["MAE"])
            if not rs:
                continue
            L += [f"## {task} - Track {tr}", "", f"_{TRACKS[tr]}_", "",
                  "| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
            for i, r in enumerate(rs, 1):
                m = r["metrics"]
                p = r.get("params")
                ps = "-" if p is None else (f"{p/1e6:.1f}M" if p >= 1e5 else str(int(p)))
                L.append(f"| {i} | {r['model']} | {r.get('type','')} | {ps} | {r.get('context_steps','-')} | "
                         f"{fmt(m['MAE'])} | {fmt(m['RMSE'])} | {fmt(m.get('MAPE'), '{:.1f}%')} | "
                         f"{fmt(m.get('QL'), '{:.3f}')} | {fmt(m.get('IS80'))} | "
                         f"{fmt(m.get('COV80') and m['COV80']*100, '{:.1f}%')} |")
            L.append("")
    open(os.path.join(ROOT, "LEADERBOARD.md"), "w").write("\n".join(L))
    print("\n".join(L))
    json.dump(rows, open(os.path.join(ROOT, "results", "paradoxbench_all.json"), "w"))


if __name__ == "__main__":
    main()
