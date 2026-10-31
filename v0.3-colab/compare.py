"""Build RESULTS.md: PWM vs Google TimesFM and baselines, from results/*.json only.
Stub runs and synthetic test data are refused - only real runs are reported."""
import glob, json, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))

# Published PEMS08 numbers (STAEformer paper, arXiv 2308.10425, Table 3: 6:2:2 split, 12->12, avg of
# 12 horizons). Reported by their authors - NOT re-run here.
PUBLISHED_PEMS08 = [("STAEformer", 13.46, 23.25, 8.88), ("PDFormer", 13.58, 23.41, 9.05),
                    ("STID", 14.21, 23.28, 9.27), ("GWNet", 14.40, 23.39, 9.21),
                    ("MTGNN", 15.18, 24.24, 10.20), ("DCRNN", 15.22, 24.17, 10.21),
                    ("GMAN", 15.31, 24.92, 10.13), ("AGCRN", 15.32, 24.41, 10.03),
                    ("STGCN", 16.08, 25.39, 10.60)]


def row(name, kind, r):
    cov = f"{r['interval_80_coverage']*100:.1f}%" if "interval_80_coverage" in r else "-"
    return f"| {name} | {kind} | {r['MAE']:.2f} | {r['RMSE']:.2f} | {r['MAPE']:.1f}% | {cov} |"


def main():
    by_ds = defaultdict(dict)
    for f in sorted(glob.glob(f"{ROOT}/results/*__*.json")):
        ds, tag = os.path.basename(f)[:-5].split("__", 1)
        if ds.startswith("SYNTHETIC") or tag == "STUB":
            continue
        by_ds[ds][tag] = json.load(open(f))
    L = ["# Paradox World Model - benchmark results", "",
         "All rows in each dataset table were scored by the same code (`pwm/evaluation.py`) on the "
         "same held-out test windows. PWM-Dyn is trained from scratch on that dataset's training "
         "period; Google TimesFM is a pretrained foundation model run **zero-shot** with a much longer "
         "history. Lower MAE/RMSE/MAPE is better; a well-calibrated 80% interval covers ~80%.", ""]
    claims = []
    for ds, runs in by_ds.items():
        if "PWM-Dyn" not in runs:
            continue
        pw = runs["PWM-Dyn"]
        st = pw["setup"]
        L += [f"## {ds}", "",
              f"Units: {st['units']}. Input {st['input_steps']} steps -> forecast {st['output_steps']} steps. "
              f"Zero values {'excluded (standard PeMS protocol)' if st['zero_masked'] else 'included (real dry days)'}.", "",
              "| Model | Type | MAE | RMSE | MAPE | 80% interval coverage |", "|---|---|---|---|---|---|",
              row(f"**PWM-Dyn** (ensemble of {len(pw['members'])})", "Paradox-trained", pw["ensemble_test"])]
        for v, r in pw["per_member"].items():
            L.append(row(f"PWM-Dyn {v}", "Paradox-trained (single seed)", r))
        opp = {k: v for k, v in runs.items() if k.startswith("TimesFM")}
        for k, v in opp.items():
            L.append(row(f"{v['model']} (context {v['context_steps']})", "Google, zero-shot", v["test"]))
        if "baselines" in runs:
            L.append(row("Historical average", "baseline", runs["baselines"]["historical_average"]))
            L.append(row("Last value", "baseline", runs["baselines"]["last_value"]))
        L.append("")
        p = pw["ensemble_test"]["MAE"]
        for k, v in opp.items():
            o = v["test"]["MAE"]
            if v.get("stride", 1) != pw["setup"]["stride"]:
                claims.append(f"- {ds}: {k} was run on a different window stride; not compared.")
                continue
            word = "lower" if p < o else "higher"
            claims.append(f"- **{ds}**: PWM-Dyn MAE {p:.2f} vs {v['model']} {o:.2f} -> PWM is "
                          f"**{abs(o - p) / o * 100:.1f}% {word}** error "
                          f"({'PWM wins' if p < o else 'Google wins'}).")
        if ds == "PEMS08":
            L += ["Published PEMS08 leaderboard (authors' own runs, not re-run here):", "",
                  "| Model | MAE | RMSE | MAPE |", "|---|---|---|---|"]
            L += [f"| {n} | {a:.2f} | {b:.2f} | {c:.2f}% |" for n, a, b, c in PUBLISHED_PEMS08]
            L.append("")
    L += ["## Head-to-head summary", ""] + (claims or ["- No opponent runs found yet."]) + ["",
          "## What these results do and do not show", "",
          "- They show how PWM-Dyn compares with Google's TimesFM on these specific physical forecasting tasks.",
          "- PWM is trained on each dataset's own history; TimesFM is not. A PWM win means a small specialist "
          "trained on the region beats a general zero-shot model there - not that PWM is a better general model.",
          "- They say nothing about Genie, Cosmos, V-JEPA or WeatherNext, which solve different tasks.",
          "- What-if outputs from the reasoning layer are unvalidated model responses.", "",
          "Provenance: see PROVENANCE_REPORT.json (run `python check_provenance.py`)."]
    open(f"{ROOT}/RESULTS.md", "w").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
