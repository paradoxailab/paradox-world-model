"""ParadoxBench-1 results, transcribed from the two Kaggle run logs (2026-11-01).

v04  = https://www.kaggle.com/code/aditya16kumar/notebook0387a11c3a  (scriptVersionId 364310290, 254.6 min, 2x T4)
v041 = https://www.kaggle.com/code/aditya16kumar/notebookab27dd6f3e  (scriptVersionId 364348754, 93.1 min, 2x T4)
Both runs end with PROVENANCE: PASS.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC, FM, BASE = "specialist (Paradox, trained from scratch)", "foundation (Google, zero-shot)", "baseline"
# task, track, model, type, params, context, MAE, RMSE, MAPE%, QL, IS80, COV80%, run
R = [
    # ---------------- PEMS08 ----------------
    ("PEMS08", "A", "PWM-Dyn v0.4.1", SPEC, "0.3M", 12, 14.498, 23.991, 9.4, 4.696, 68.39, 79.7, "v041"),
    ("PEMS08", "A", "PWM-Dyn v0.4", SPEC, "0.3M", 12, 14.526, 23.915, 9.5, 4.719, 68.94, 79.7, "v04"),
    ("PEMS08", "A", "Climatology quantiles", BASE, "0", 0, 22.185, 40.769, 13.6, 7.625, 117.83, 71.4, "v04"),
    ("PEMS08", "A", "Last value", BASE, "0", 1, 25.297, 38.655, 15.7, None, None, None, "v04"),
    ("PEMS08", "B", "PWM-Dyn v0.4.1-LC", SPEC, "0.3M", 300, 14.148, 23.239, 9.2, 4.593, 67.05, 79.5, "v041"),
    ("PEMS08", "B", "PWM-Dyn v0.4-LC", SPEC, "0.3M", 300, 14.380, 23.477, 9.5, 4.660, 67.91, 79.7, "v04"),
    ("PEMS08", "B", "TimesFM 3.0 multivariate", FM, "-", 512, 14.549, 23.567, 9.2, 4.686, 67.84, 80.7, "v04"),
    ("PEMS08", "B", "TimesFM 2.5", FM, "200M", 512, 15.037, 24.093, 9.4, 4.857, 70.54, 82.4, "v04"),
    ("PEMS08", "B", "Climatology quantiles", BASE, "0", 0, 22.185, 40.769, 13.6, 7.625, 117.83, 71.4, "v04"),
    ("PEMS08", "B", "Last value", BASE, "0", 1, 25.297, 38.655, 15.7, None, None, None, "v04"),
    ("PEMS08", "B", "Seasonal naive", BASE, "0", 300, 36.543, 60.771, 24.6, None, None, None, "v04"),
    ("PEMS08", "R", "PWM-Dyn v0.4-LC", SPEC, "0.3M", 300, 18.698, 33.455, 12.4, 6.470, 100.61, 76.8, "v04"),
    ("PEMS08", "R", "PWM-Dyn v0.4.1-LC", SPEC, "0.3M", 300, 18.808, 33.486, 12.6, 6.468, 99.99, 76.4, "v041"),
    ("PEMS08", "R", "Climatology quantiles", BASE, "0", 0, 21.782, 41.079, 13.9, 7.411, 113.41, 72.4, "v04"),
    ("PEMS08", "Z", "PWM-Dyn v0.4-LC inductive (PEMS04 only)", SPEC, "0.2M", 300, 16.364, 25.730, 12.8, 5.510, 83.47, 86.7, "v04"),
    ("PEMS08", "Z", "PWM-Dyn v0.4.1-LC inductive (PEMS04 only)", SPEC, "0.2M", 300, 16.566, 25.942, 13.7, 5.514, 82.58, 85.3, "v041"),
    # ---------------- PEMS04 ----------------
    ("PEMS04", "A", "PWM-Dyn v0.4.1", SPEC, "0.3M", 12, 19.023, 31.806, 12.8, 6.101, 87.90, 79.8, "v041"),
    ("PEMS04", "A", "PWM-Dyn v0.4", SPEC, "0.3M", 12, 19.208, 31.753, 13.1, 6.156, 88.65, 79.6, "v04"),
    ("PEMS04", "A", "Climatology quantiles", BASE, "0", 0, 25.022, 41.360, 16.1, 8.431, 127.81, 71.5, "v04"),
    ("PEMS04", "A", "Last value", BASE, "0", 1, 31.556, 48.251, 21.3, None, None, None, "v04"),
    ("PEMS04", "B", "PWM-Dyn v0.4.1", SPEC, "0.3M", 12, 19.023, 31.806, 12.8, 6.101, 87.90, 79.8, "v041"),
    ("PEMS04", "B", "TimesFM 3.0 multivariate", FM, "-", 512, 19.135, 31.024, 12.6, 6.137, 88.42, 80.7, "v04"),
    ("PEMS04", "B", "PWM-Dyn v0.4-LC", SPEC, "0.3M", 300, 19.175, 31.518, 13.1, 6.135, 88.16, 80.0, "v04"),
    ("PEMS04", "B", "TimesFM 2.5", FM, "200M", 512, 19.702, 31.701, 13.2, 6.337, 91.61, 82.0, "v04"),
    ("PEMS04", "B", "Climatology quantiles", BASE, "0", 0, 25.022, 41.360, 16.1, 8.431, 127.81, 71.5, "v04"),
    ("PEMS04", "B", "Last value", BASE, "0", 1, 31.556, 48.251, 21.3, None, None, None, "v04"),
    ("PEMS04", "B", "Seasonal naive", BASE, "0", 300, 40.672, 66.641, 27.1, None, None, None, "v04"),
    ("PEMS04", "R", "PWM-Dyn v0.4.1", SPEC, "0.3M", 12, 24.690, 42.643, 18.0, 8.324, 126.27, 78.0, "v041"),
    ("PEMS04", "R", "PWM-Dyn v0.4-LC", SPEC, "0.3M", 300, 24.987, 43.030, 18.2, 8.484, 129.58, 78.1, "v04"),
    ("PEMS04", "R", "Climatology quantiles", BASE, "0", 0, 27.387, 45.599, 15.9, 9.199, 139.04, 71.3, "v04"),
    # ---------------- IMD central India ----------------
    ("IMD-CI", "A", "PWM-Dyn v0.4", SPEC, "0.4M", 30, 2.838, 10.419, 268.3, 1.073, 18.01, 84.7, "v04"),
    ("IMD-CI", "A", "Climatology quantiles", BASE, "0", 0, 2.886, 10.697, 229.0, 1.088, 18.21, 91.0, "v04"),
    ("IMD-CI", "A", "Last value", BASE, "0", 1, 4.366, 13.546, 1328.9, None, None, None, "v04"),
    ("IMD-CI", "B", "PWM-Dyn v0.4", SPEC, "0.4M", 30, 2.838, 10.419, 268.3, 1.073, 18.01, 84.7, "v04"),
    ("IMD-CI", "B", "Climatology quantiles", BASE, "0", 0, 2.886, 10.697, 229.0, 1.088, 18.21, 91.0, "v04"),
    ("IMD-CI", "B", "TimesFM 3.0 multivariate", FM, "-", 365, 2.924, 10.651, 204.0, 1.147, 19.79, 86.3, "v04"),
    ("IMD-CI", "B", "TimesFM 2.5", FM, "200M", 365, 2.960, 10.580, 277.4, 1.184, 20.72, 84.3, "v04"),
    ("IMD-CI", "B", "Last value", BASE, "0", 1, 4.366, 13.546, 1328.9, None, None, None, "v04"),
    ("IMD-CI", "B", "Seasonal naive", BASE, "0", 372, 4.684, 14.113, 1171.0, None, None, None, "v04"),
    ("IMD-CI", "R", "PWM-Dyn v0.4", SPEC, "0.4M", 30, 2.837, 10.378, 272.2, 1.072, 17.99, 85.5, "v04"),
    ("IMD-CI", "R", "Climatology quantiles", BASE, "0", 0, 2.883, 10.644, 211.4, 1.085, 18.12, 91.1, "v04"),
    # ---------------- IMD Konkan / Western Ghats ----------------
    ("IMD-WC", "A", "PWM-Dyn v0.4", SPEC, "0.4M", 30, 3.415, 12.013, 274.7, 1.245, 20.27, 82.9, "v04"),
    ("IMD-WC", "A", "Climatology quantiles", BASE, "0", 0, 3.651, 13.005, 289.7, 1.312, 21.09, 91.0, "v04"),
    ("IMD-WC", "A", "Last value", BASE, "0", 1, 4.880, 14.941, 737.4, None, None, None, "v04"),
    ("IMD-WC", "B", "PWM-Dyn v0.4", SPEC, "0.4M", 30, 3.415, 12.013, 274.7, 1.245, 20.27, 82.9, "v04"),
    ("IMD-WC", "B", "TimesFM 3.0 multivariate", FM, "-", 365, 3.621, 12.782, 208.7, 1.332, 21.85, 87.2, "v04"),
    ("IMD-WC", "B", "Climatology quantiles", BASE, "0", 0, 3.651, 13.005, 289.7, 1.312, 21.09, 91.0, "v04"),
    ("IMD-WC", "B", "TimesFM 2.5", FM, "200M", 365, 3.670, 12.652, 246.9, 1.378, 23.00, 85.2, "v04"),
    ("IMD-WC", "B", "Last value", BASE, "0", 1, 4.880, 14.941, 737.4, None, None, None, "v04"),
    ("IMD-WC", "B", "Seasonal naive", BASE, "0", 372, 5.686, 17.072, 1122.7, None, None, None, "v04"),
    ("IMD-WC", "R", "PWM-Dyn v0.4", SPEC, "0.4M", 30, 3.427, 12.069, 288.5, 1.263, 20.75, 83.2, "v04"),
    ("IMD-WC", "R", "Climatology quantiles", BASE, "0", 0, 3.598, 12.848, 307.5, 1.300, 21.00, 90.8, "v04"),
]
KEYS = ["task", "track", "model", "type", "params", "context", "MAE", "RMSE", "MAPE", "QL", "IS80", "COV80", "run"]
rows = [dict(zip(KEYS, r)) for r in R]
for r in rows:
    r["run"] = {"v04": "kaggle:notebook0387a11c3a/364310290", "v041": "kaggle:notebookab27dd6f3e/364348754"}[r["run"]]

TASKS = {"PEMS08": "PEMS08 traffic (170 sensors, 1 h ahead)", "PEMS04": "PEMS04 traffic (307 sensors, 1 h ahead)",
         "IMD-CI": "IMD rainfall, central India (7 days ahead)", "IMD-WC": "IMD rainfall, Konkan / Western Ghats (7 days ahead)"}
TRACKS = {"A": "Standard (12 steps / 30 days of history)", "B": "Open context (up to 512 steps / 365 days)",
          "R": "Robustness (30 % of locations hidden; scored on hidden only)", "Z": "Zero-shot transfer (never saw PEMS08)"}

json.dump({"benchmark": "ParadoxBench-1", "windows": "official test windows, stride 2",
           "tasks": TASKS, "tracks": TRACKS, "rows": rows}, open(os.path.join(HERE, "paradoxbench1_results.json"), "w"), indent=1)

f = lambda v, d: "-" if v is None else f"{v:.{d}f}"
out = ["# ParadoxBench-1 leaderboard", "",
       "Official test windows (every 2nd). Ranked by MAE. Lower is better for MAE, RMSE, QL and IS80; COV80 should be close to 80 %.",
       "Traffic in vehicles per 5 min (zero readings excluded); rainfall in mm/day (dry days included, so MAPE is not meaningful for rain).", ""]
for t in TASKS:
    for tr in TRACKS:
        rs = sorted([r for r in rows if r["task"] == t and r["track"] == tr], key=lambda r: r["MAE"])
        if not rs:
            continue
        out += [f"## {t} — Track {tr}: {TRACKS[tr]}", "",
                "| # | Model | Type | Params | Context | MAE | RMSE | MAPE | QL | IS80 | COV80 |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        for i, r in enumerate(rs, 1):
            name = f"**{r['model']}**" if i == 1 else r["model"]
            out.append(f"| {i} | {name} | {r['type']} | {r['params']} | {r['context']} | {f(r['MAE'],2)} | {f(r['RMSE'],2)} | "
                       f"{f(r['MAPE'],1)}% | {f(r['QL'],3)} | {f(r['IS80'],2)} | {f(r['COV80'],1)}{'%' if r['COV80'] else ''} |")
        out.append("")
open(os.path.join(HERE, "LEADERBOARD.md"), "w").write("\n".join(out))
print(len(rows), "rows written")
