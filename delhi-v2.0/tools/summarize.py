"""Print every significance test from a weather-league results file as one compact table.

  python tools/summarize.py out/wx_metar_results.json
Columns: ours | opponent | variable | lead band | verdict | MAE difference % (negative = ours better) | DM p | 95% CI.
"""
import json, sys


def main(path):
    R = json.load(open(path))
    print(f"league {R['league']}: {len(R['stations'])} stations")
    for ours, opps in R["tests"].items():
        for opp, per_var in opps.items():
            for v, bands in per_var.items():
                for band, t in bands.items():
                    if not t:
                        continue
                    ci = [round(x, 1) for x in t.get("ci95_pct", [])]
                    p = t.get("p", float("nan"))
                    print(f"TEST | {ours} | {opp} | {v} | {band} | {t.get('verdict')} | "
                          f"{t.get('rel_diff_pct', float('nan')):+.1f}% | p={p:.2g} | "
                          f"CI={ci}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
