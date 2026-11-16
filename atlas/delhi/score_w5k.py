"""World benchmark WB1 (README, "World benchmarks"): the WEATHER-5K table, checks C2 and the WB1 rule, by number against
the published results (Han et al., arXiv 2406.14399 v3: Table 2 averages over the four leads; Tables 8-9 per lead for
ECMWF-HRES and PhysicsFormer). Reads every w5k_*_s<seed>.json run file attached.

  python score_w5k.py
"""
import glob, json, os, sys

import numpy as np

OUT = os.environ.get("ATLAS_OUT", "/kaggle/working/out")
V = ["Temperature", "Dewpoint", "Wind speed", "Sea-level pressure"]               # the four variables of Table 2
V5 = ["Temperature", "Dewpoint", "Wind speed", "Wind direction", "Sea-level pressure"]
LEADS = (24, 72, 120, 168)
PUB_AVG = {                                      # Table 2: mean over the four leads (T, Td, wind speed, SLP)
    "ECMWF-HRES": (1.94, 2.06, 1.56, 1.29), "PhysicsFormer (19.3M)": (2.34, 2.51, 1.44, 3.53),
    "Pyraformer (7.5M)": (2.49, 2.68, 1.51, 3.72), "iTransformer (4.8M)": (2.64, 2.87, 1.52, 4.11),
    "TimeMixer (0.06M)": (2.69, 2.84, 1.52, 4.06), "Corrformer (666M)": (2.72, 2.95, 1.55, 4.22),
    "Informer (11.3M)": (2.75, 2.87, 1.52, 4.17), "PatchTST (6.7M)": (2.84, 3.07, 1.59, 4.27),
    "Timer (84M)": (2.97, 3.12, 1.61, 4.73), "Chronos (48M)": (3.03, 3.28, 1.72, 4.62),
    "DLinear (0.01M)": (3.57, 3.49, 1.61, 4.60)}
PUB_LEAD = {                                     # Tables 8-9: T, Td, wind speed, wind direction, SLP
    "ECMWF-HRES": {24: (1.76, 1.85, 1.48, 63.8, 0.86), 72: (1.87, 1.94, 1.52, 72.4, 1.06),
                   120: (1.99, 2.14, 1.58, 75.4, 1.38), 168: (2.15, 2.32, 1.66, 78.3, 1.87)},
    "PhysicsFormer (19.3M)": {24: (1.55, 1.59, 1.21, 57.37, 1.43), 72: (2.22, 2.38, 1.46, 69.28, 3.42),
                              120: (2.68, 2.90, 1.54, 73.98, 4.40), 168: (2.93, 3.16, 1.59, 76.19, 4.92)}}


def log(*a):
    print(*a, flush=True)


def runs():
    R = {}
    for f in sorted(set(glob.glob(os.path.join(OUT, "w5k_*.json")) + glob.glob("/kaggle/input/**/w5k_*.json", recursive=True))):
        r = json.load(open(f))
        if "test" not in r:
            continue
        name = {"persist": "Persistence (last value)", "dlinear": "DLinear, our run"}.get(r["model"], f"Atlas-5K ({r.get('params', 0) / 1e6:.2f}M)")
        R.setdefault(name, {})[r["H"]] = r
    return R


def main():
    R = runs()
    res = {"runs": {k: {h: v["test"]["MAE"] for h, v in d.items()} for k, d in R.items()}, "checks": {}, "rule": {}}
    # C2: our DLinear against its published Table 2 average (temperature), within 5%
    dl = R.get("DLinear, our run", {})
    if all(h in dl for h in LEADS):
        m = float(np.mean([dl[h]["test"]["MAE"]["Temperature"] for h in LEADS]))
        ok = abs(m / 3.57 - 1) <= 0.05
        res["checks"]["C2"] = dict(ours=m, published=3.57, rel=m / 3.57 - 1, verdict="PASS" if ok else "FAIL",
                                   all_vars={v: float(np.mean([dl[h]["test"]["MAE"][v] for h in LEADS])) for v in V})
        log(f"C2: our DLinear temperature MAE, mean of 4 leads {m:.3f} vs published 3.57 ({100 * (m / 3.57 - 1):+.1f}%) -> {res['checks']['C2']['verdict']}")
    else:
        log(f"C2: needs our DLinear at all four leads (have {sorted(dl)})")
    # per-lead table and the rule
    for h in LEADS:
        rows = [(k, d[h]["test"]["MAE"]) for k, d in R.items() if h in d]
        if not rows:
            continue
        log(f"\nH = {h} h, test 2023 MAE (T / Td / wind speed / wind direction / SLP):")
        for k, mae in rows:
            log(f"  {k:<28} " + " / ".join(f"{mae[v]:.3f}" for v in V5))
        for k, vals in PUB_LEAD.items():
            log(f"  {k + ' (published)':<28} " + " / ".join(f"{x:.2f}" for x in vals[h]))
        for k, mae in rows:
            if not k.startswith("Atlas"):
                continue
            pf = dict(zip(V5, PUB_LEAD["PhysicsFormer (19.3M)"][h])); hr = dict(zip(V5, PUB_LEAD["ECMWF-HRES"][h]))
            wins_pf = [v for v in V5 if mae[v] < pf[v]]
            wins_hr = [v for v in V if mae[v] < hr[v]]
            res["rule"][f"{k} H={h}"] = dict(
                beats_PhysicsFormer="YES" if len(wins_pf) >= 4 else "no", vars_below_PhysicsFormer=wins_pf,
                beats_ECMWF_HRES="YES" if len(wins_hr) == 4 else "no", vars_below_ECMWF_HRES=wins_hr)
            log(f"  RULE {k} H={h}: below PhysicsFormer on {len(wins_pf)}/5 {wins_pf} -> {res['rule'][f'{k} H={h}']['beats_PhysicsFormer']}; "
                f"below ECMWF-HRES on {len(wins_hr)}/4 {wins_hr} -> {res['rule'][f'{k} H={h}']['beats_ECMWF_HRES']}")
    # Table-2 style averages where all four leads exist
    log("\nMean of the four leads (Table 2 style: T / Td / wind speed / SLP):")
    for k, d in R.items():
        if all(h in d for h in LEADS):
            log(f"  {k:<28} " + " / ".join(f"{np.mean([d[h]['test']['MAE'][v] for h in LEADS]):.2f}" for v in V))
    for k, vals in PUB_AVG.items():
        log(f"  {k + ' (published)':<28} " + " / ".join(f"{x:.2f}" for x in vals))
    log("W5K-SCORE " + json.dumps(res, default=float))
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "w5k_score.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
