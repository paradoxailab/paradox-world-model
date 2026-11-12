"""Report for the 32-64-month diagnostic (curves.py --diag). Pre-registered test: the early-stopping hypothesis is
supported if, with a fixed training length, the dip (32 or 64 months worse than 16 by more than 3%, mean over the three
targets) is absent in at least 5 of the 6 all-India regions.   python diag_report.py log_india_diag_s0.txt [curves_v10.txt]"""
import json, re, sys
from collections import defaultdict

import numpy as np

recs, years = [], []
for line in open(sys.argv[1], errors="ignore"):
    if line.startswith("DIAG "): recs.append(json.loads(line[5:]))
    elif line.startswith("YEAR "): years.append(json.loads(line[5:]))
es = {}
if len(sys.argv) > 2:                                   # the v1.0 early-stopped curves for comparison
    for l in open(sys.argv[2]):
        m = re.match(r"- (isd-r\d) (\S+): (.*) \| persistence", l.strip())
        if m:
            es[(m.group(1), m.group(2))] = {float(a): float(b) for a, b in re.findall(r"([\d.]+) mo ([\d.]+)", m.group(3))}
fx = defaultdict(dict)
for r in recs:
    for v, x in r["test"].items():
        fx[(r["network"], v)][r["months"] if r["amount"] < 999 else "all"] = x["MAE"]
print("| region | target | fixed 16 | fixed 32 | fixed 64 | fixed all | early-stopped 16 / 32 / 64 / all (v1.0) |")
print("|---|---|---|---|---|---|---|")
dips = {}
for (net, v) in sorted(fx):
    f = fx[(net, v)]; e = es.get((net, v), {})
    g = lambda k: f"{f[k]:.3f}" if k in f else "–"
    eall = [x for k, x in e.items() if k > 100]
    print(f"| {net} | {v} | {g(16.0)} | {g(32.0)} | {g(64.0)} | {g('all')} | " +
          (" / ".join(f"{e.get(k, float('nan')):.3f}" for k in (16.0, 32.0, 64.0)) + f" / {eall[0]:.3f}" if e else "–") + " |")
regions = sorted({k[0] for k in fx})
present = {}
for net in regions:
    ts = [v for (n, v) in fx if n == net and 16.0 in fx[(n, v)]]
    r32 = np.mean([fx[(net, v)].get(32.0, np.nan) / fx[(net, v)][16.0] for v in ts])
    r64 = np.mean([fx[(net, v)].get(64.0, np.nan) / fx[(net, v)][16.0] for v in ts])
    present[net] = bool(max(np.nan_to_num(r32), np.nan_to_num(r64)) > 1.03)
    print(f"{net}: fixed-length 32/16 = {r32:.3f}, 64/16 = {r64:.3f} -> dip {'PRESENT' if present[net] else 'absent'}")
absent = sum(not x for x in present.values())
print(f"DIAG-VERDICT: dip absent in {absent} of {len(present)} regions -> early-stopping hypothesis "
      f"{'SUPPORTED' if absent >= 5 else 'NOT supported'}")
if years:
    print("\n| year | missing % (AT, RH, WS), mean over regions | stations reporting (sum) | mean AT | mean RH | mean WS |")
    print("|---|---|---|---|---|---|")
    for y in sorted({r["year"] for r in years}):
        s = [r for r in years if r["year"] == y]
        print(f"| {y} | {', '.join(f'{x:.1f}' for x in np.mean([r['missing_pct'] for r in s], 0))} | "
              f"{sum(r['stations_reporting'] for r in s)} | " + " | ".join(f"{x:.2f}" for x in np.nanmean([r['mean'] for r in s], 0)) + " |")
