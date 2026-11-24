"""Every results table in the Atlas-5K growth paper's appendix and in the repository READMEs, generated from the result
files in data/ (copies of Drive PWM-10M/small/h2h and PWM-10M/out; the same files are in atlas/results/colab/atlas5k_grown).
Nothing here is typed by hand.

  python make_tables.py          -> tables/*.tex (appendix) and tables/readme_tables.md
  python make_tables.py --check  -> also checks the numbers printed in main.tex's tab:h2h, tab:test and tab:val against
                                    the files, and fails on any mismatch
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data"); T = os.path.join(HERE, "tables"); os.makedirs(T, exist_ok=True)
VARS = ["Temperature", "Dewpoint", "Wind direction", "Wind speed", "Sea-level pressure"]
SHORT = ["Temp.", "Dew pt.", "Wind dir.", "Wind spd.", "Pressure"]
UNITS = ["°C", "°C", "°", "m/s", "hPa"]
OPP = [("tfm3", "TimesFM 3.0", "Google", "0.3B", "non-commercial research (eval. only)"),
       ("chronos2mv", "Chronos-2 multivariate", "Amazon", "120M", "Apache-2.0"),
       ("tirex", "TiRex", "NX-AI", "35M", "NXAI community (eval. only)"),
       ("chronos2", "Chronos-2", "Amazon", "120M", "Apache-2.0"),
       ("tfm25", "TimesFM 2.5", "Google", "200M", "Apache-2.0"),
       ("sundial", "Sundial base", "Tsinghua THUML", "128M", "Apache-2.0"),
       ("chronos-bolt", "Chronos-Bolt base", "Amazon", "205M", "Apache-2.0"),
       ("timemoe200", "Time-MoE", "Shi et al.", "200M", "Apache-2.0"),
       ("ttm", "TTM r2", "IBM Research", "0.8M", "Apache-2.0"),
       ("persist", "Persistence", "--", "0", "--")]
OURS = [("atlas100m", "Atlas-100M (ours)", "98.6M"), ("atlas25m", "Atlas-5K 25M (ours)", "24.1M"), ("atlas10m", "Atlas-5K 10M (ours)", "9.64M"), ("v2c", "Atlas-5K v2c (ours)", "0.97M")]
PF = [1.55, 1.59, 57.37, 1.21, 1.43]; HRES = [1.76, 1.85, 63.8, 1.48, 0.86]          # published, WEATHER-5K paper
PER = {"test": "2023 test", "live": "Live, Jan 2024 – Aug 2025"}


def J(name):
    return json.load(open(os.path.join(D, name)))


H = {p: J(f"h2h_{p}.json") for p in PER}
P = {(m, p): J(f"paired_{m}_{p}_r25.json") for m in ("atlas25m", "atlas10m") for p in PER}
V = {p: J(f"paired_atlas25m_{p}_vs10m.json")["atlas10m"] for p in ("val", "test", "live")}
RUN = {"atlas25m": J("w5k_atlas_25m_h24_g2_s600.json"), "atlas10m": J("w5k_atlas_10m_h24_g1_s600.json")}
M100D = os.path.join(HERE, "..", "m100", "results")          # Atlas-100M (atlas/m100/RESULTS.md): same windows
M100 = {p: json.load(open(os.path.join(M100D, f"paired_atlas100m_{p}_m100.json"))) for p in PER}
M100v25 = {p: json.load(open(os.path.join(M100D, f"paired_atlas100m_{p}_m100vs25m.json")))["atlas25m"] for p in PER}
RUN["atlas100m"] = json.load(open(os.path.join(M100D, "atlas100m_eval_s600.json")))
STD = [13.08167293, 12.13875438, 99.67403125, 2.65729403, 9.17480999]   # the benchmark's scales (E = mean MAE / scale)
for p in PER:
    mae = {r["variable"]: r["ours"] for r in M100v25[p]}
    H[p]["atlas100m"] = dict(MAE=mae, E=sum(mae[v] / sd for v, sd in zip(VARS, STD)) / 5)
V2C = json.load(open(os.path.join(HERE, "..", "results", "colab", "atlas5k_grown", "w5k_atlas_1m_h24_v2c_final_s600.json")))


def fmt(v, k):
    return f"{v:.2f}" if VARS[k] == "Wind direction" else f"{v:.3f}"


def order(p):
    keys = [k for k, *_ in OURS] + [k for k, *_ in OPP]
    return sorted(keys, key=lambda k: H[p][k]["E"])


def label(k):
    for kk, n, pr in OURS:
        if kk == k:
            return n, pr
    for kk, n, org, pr, _ in OPP:
        if kk == k:
            return (f"{n} ({org})" if org != "--" else n), pr


def pct(a, b):
    return 100 * (a / b - 1)


# ------------------------------------------------------------------ sanity checks on the files themselves
for p in PER:
    for m in ("atlas25m", "atlas10m"):
        assert sorted(P[(m, p)]) == sorted(k for k, *_ in OPP), (m, p)
        for k, rows in P[(m, p)].items():
            assert [r["variable"] for r in rows] == VARS
            for r, v in zip(rows, VARS):                     # paired file and h2h file agree on both MAEs
                assert abs(r["ours"] / H[p][m]["MAE"][v] - 1) < 1e-4 and abs(r["theirs"] / H[p][k]["MAE"][v] - 1) < 1e-4, (m, p, k, v)
    assert H[p]["atlas25m"]["points"] == H[p]["tfm3"]["points"]
for p in PER:
    assert abs(sum(H[p]["atlas25m"]["MAE"][v] / sd for v, sd in zip(VARS, STD)) / 5 - H[p]["atlas25m"]["E"]) < 2e-4, p
    for r in M100v25[p]:
        assert abs(r["theirs"] / H[p]["atlas25m"]["MAE"][r["variable"]] - 1) < 1e-3, (p, r)
    assert sorted(M100[p]) == sorted(k for k, *_ in OPP)
    for k, rows in M100[p].items():
        for r in rows:
            assert abs(r["ours"] / H[p]["atlas100m"]["MAE"][r["variable"]] - 1) < 1e-3 and abs(r["theirs"] / H[p][k]["MAE"][r["variable"]] - 1) < 1e-3, (p, k, r)
assert all(abs(H["live"]["atlas10m_chk"]["MAE"][v] - H["live"]["atlas10m"]["MAE"][v]) < 1e-3 for v in VARS)

P.update({("atlas100m", p): M100[p] for p in PER})
wins = {(m, p): sum(r["verdict"] == "WIN" for rows in P[(m, p)].values() for r in rows) for (m, p) in P}
pmax = {(m, p): max(r["p_holm"] for rows in P[(m, p)].values() for r in rows) for (m, p) in P}
fm = [k for k, *_ in OPP if k != "persist"]
rng = {(m, p): (min(-r["diff_pct"] for k in fm for r in P[(m, p)][k]), max(-r["diff_pct"] for k in fm for r in P[(m, p)][k]))
       for (m, p) in P}
best_fm = {p: min(fm, key=lambda k: H[p][k]["E"]) for p in PER}

# ------------------------------------------------------------------ README markdown
md = []
for p in PER:
    w = H[p]["_windows"]
    md.append(f"**{PER[p]}** ({w['stations']} stations, {w['starts']} forecast starts from {w['first_start'][:10]} to "
              f"{w['last_start'][:10]}, 24 h each; up to {H[p]['atlas25m']['points']:,} scored values per variable; hours with no observation are not scored). "
              f"E = standardised mean error, lower is better.\n")
    md.append("| Rank | Model | Params | E | " + " | ".join(f"{s} ({u})" for s, u in zip(SHORT, UNITS)) + " |")
    md.append("|---|---|---|---|" + "---|" * 5)
    ks = order(p); Es = [f"{H[p][k]['E']:.4f}" for k in ks]
    for i, k in enumerate(ks):
        r = Es.index(Es[i]) + 1; tie = Es.count(Es[i]) > 1          # equal E at the printed precision: shared rank
        n, pr = label(k); b = "**" if k in ("atlas25m", "atlas100m") else ""
        be = b if r == 1 else ""                                      # bold E only for the best
        md.append(f"| {r}{'=' if tie else ''} | {b}{n}{b} | {pr} | {be}{Es[i]}{be} | " +
                  " | ".join(fmt(H[p][k]["MAE"][v], j) for j, v in enumerate(VARS)) + " |")
    md.append("")
    vv = {r["variable"]: r for r in M100v25[p]}
    md.append("Atlas-100M against Atlas-5K 25M, paired on the same windows: " + "; ".join(
        f"{sh} {vv[v]['diff_pct']:+.2f}% {vv[v]['verdict']}" for sh, v in zip(SHORT, VARS)) + "." +
        (" Ranks marked = share the same E at four decimals." if len(set(Es)) < len(Es) else "") + "\n")
md.append("**Paired verdicts** (station-block bootstrap, 10,000 resamples, and Diebold–Mariano; the larger p-value, "
          "Holm-corrected over the 50 opponent × variable pairs, α = 0.01):\n")
md.append("| Our model | Period | Significant wins | Largest Holm p | Margin vs the 9 foundation models (per variable) |")
md.append("|---|---|---|---|---|")
for m, n, _ in OURS[:3]:
    for p in PER:
        lo, hi = rng[(m, p)]
        md.append(f"| {n} | {PER[p]} | {wins[(m, p)]}/50 | {pmax[(m, p)]:.3g} | {lo:.1f}% to {hi:.1f}% lower MAE |")
md.append("")
md.append("**Against the closest opponent, TimesFM 3.0** (25M's MAE change, paired, with 95% bootstrap interval):\n")
md.append("| Period | " + " | ".join(SHORT) + " |")
md.append("|---|" + "---|" * 5)
for p in PER:
    md.append(f"| {PER[p]} | " + " | ".join(f"{r['diff_pct']:+.1f}% [{r['ci95_pct'][0]:+.1f}, {r['ci95_pct'][1]:+.1f}]"
                                          for r in P[("atlas25m", p)]["tfm3"]) + " |")
md.append("")
md.append("**25M against 10M** (paired, same windows; Holm over the five variables):\n")
md.append("| Period | " + " | ".join(SHORT) + " | Significant |")
md.append("|---|" + "---|" * 5 + "---|")
for p, lab in (("val", "2022 validation"), ("test", "2023 test"), ("live", "Live 2024–25")):
    md.append(f"| {lab} | " + " | ".join(f"{r['diff_pct']:+.2f}% (p {r['p_holm']:.2g})" for r in V[p]) +
              f" | {sum(r['verdict'] == 'WIN' for r in V[p])}/5 |")
md.append("")
md.append("**Full 2023 test** (all 5,672 stations, every hourly window, about 1.18 × 10⁹ values per variable; WEATHER-5K "
          "protocol, MAE). Published rows are from the WEATHER-5K paper, compared by number only:\n")
md.append("| Model | Params | " + " | ".join(SHORT) + " |")
md.append("|---|---|" + "---|" * 5)
for k, n, pr in (("atlas100m", "Atlas-100M (ours)", "98.6M"), ("atlas25m", "**Atlas-5K 25M (ours)**", "24.1M"), ("atlas10m", "Atlas-5K 10M (ours)", "9.64M")):
    md.append(f"| {n} | {pr} | " + " | ".join(fmt(RUN[k]["test"]["MAE"][v], j) for j, v in enumerate(VARS)) + " |")
md.append("| Atlas-5K v2c (ours) | 0.97M | " + " | ".join(fmt(V2C["test"]["MAE"][v], j) for j, v in enumerate(VARS)) + " |")
md.append("| PhysicsFormer (published) | 19.3M | " + " | ".join(str(x) for x in PF) + " |")
md.append("| ECMWF-HRES at stations (published) | – | " + " | ".join(str(x) for x in HRES) + " |")
md.append("| 25M vs PhysicsFormer | | " + " | ".join(f"{pct(RUN['atlas25m']['test']['MAE'][v], b):+.1f}%" for v, b in zip(VARS, PF)) + " |")
md.append("| 100M vs PhysicsFormer | | " + " | ".join(f"{pct(RUN['atlas100m']['test']['MAE'][v], b):+.1f}%" for v, b in zip(VARS, PF)) + " |")
md.append("| 25M vs ECMWF-HRES | | " + " | ".join(f"{pct(RUN['atlas25m']['test']['MAE'][v], b):+.1f}%" for v, b in zip(VARS, HRES)) + " |")
open(os.path.join(T, "readme_tables.md"), "w").write("\n".join(md) + "\n")

# ------------------------------------------------------------------ appendix LaTeX
def tex_paired(m, p):
    n = "Atlas-5K 24M" if m == "atlas25m" else "Atlas-5K 10M"
    L = [r"\begin{table}[H]", r"\centering\scriptsize", r"\setlength{\tabcolsep}{2.4pt}",
         rf"\caption{{{n} against each opponent, {PER[p].replace('–', '--')}: paired MAE difference in \% with the 95\% "
         rf"station-block bootstrap interval. All {wins[(m, p)]} of 50 pairs are significant wins (largest Holm-adjusted "
         rf"$p={pmax[(m, p)]:.3g}$).}}", rf"\label{{tab:paired_{m}_{p}}}",
         r"\begin{tabular}{l" + "c" * 5 + "}", r"\toprule", "Opponent & " + " & ".join(SHORT) + r"\\", r"\midrule"]
    for k, nm, org, *_ in OPP:
        L.append(f"{nm} & " + " & ".join(f"${r['diff_pct']:+.1f}$ [{r['ci95_pct'][0]:+.1f}, {r['ci95_pct'][1]:+.1f}]"
                                       for r in P[(m, p)][k]) + r"\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(L)


for m in ("atlas25m", "atlas10m"):
    for p in PER:
        open(os.path.join(T, f"paired_{m}_{p}.tex"), "w").write(tex_paired(m, p) + "\n")

L = [r"\begin{table}[H]", r"\centering\scriptsize", r"\setlength{\tabcolsep}{3pt}",
     r"\caption{Atlas-5K 24M against its parent 10M, paired on identical windows: MAE difference in \%, 95\% bootstrap "
     r"interval, and Holm-adjusted $p$ (over the five variables). Validation: the adoption rule's 2022 stations.}",
     r"\label{tab:vs10m}", r"\begin{tabular}{l" + "c" * 5 + "}", r"\toprule", "Period & " + " & ".join(SHORT) + r"\\", r"\midrule"]
for p, lab in (("val", "2022 validation"), ("test", "2023 test"), ("live", "Live 2024--25")):
    L.append(f"{lab} & " + " & ".join(f"${r['diff_pct']:+.2f}$ [{r['ci95_pct'][0]:+.2f}, {r['ci95_pct'][1]:+.2f}]" for r in V[p]) + r"\\")
    L.append(" & " + " & ".join(f"$p={r['p_holm']:.2g}$" + ("" if r["verdict"] == "WIN" else " (tie)") for r in V[p]) + r"\\[2pt]")
L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(os.path.join(T, "vs10m.tex"), "w").write("\n".join(L) + "\n")

L = [r"\begin{table}[H]", r"\centering\scriptsize", r"\setlength{\tabcolsep}{4pt}",
     r"\caption{Opponents as run. All are zero-shot with 512 hourly context values per station and variable, the median "
     r"(or point) forecast is scored, and no opponent was fine-tuned. Minutes: wall-clock on one A100 for the 2023 test "
     r"windows. Licences as stated by each model's publisher at the time of the run.}", r"\label{tab:opp}",
     r"\begin{tabular}{lllrrl}", r"\toprule", r"Model & Publisher & Params & Context & Minutes & Licence\\", r"\midrule"]
for k, nm, org, pr, lic in OPP:
    L.append(f"{nm} & {org} & {pr} & {H['test'][k].get('context_hours', '--')} & {H['test'][k].get('minutes_total', 0):.1f} & {lic}\\\\")
L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(os.path.join(T, "opponents.tex"), "w").write("\n".join(L) + "\n")

S = dict(wins=wins, pmax=pmax, rng=rng, best_fm=best_fm,
         E={p: {k: round(H[p][k]["E"], 4) for k in order(p)} for p in PER})
json.dump({k: ({str(kk): vv for kk, vv in v.items()} if isinstance(v, dict) else v) for k, v in S.items()}, open(os.path.join(T, "summary.json"), "w"), indent=1, default=str)

# ------------------------------------------------------------------ check main.tex numbers
if "--check" in sys.argv:
    tex = open(os.path.join(HERE, "main.tex")).read(); bad = []

    def num(s):
        return float(re.sub(r"[^0-9.\-]", "", s))

    names = {"Atlas-5K 24M": "atlas25m", "Atlas-5K 10M": "atlas10m", "Atlas-5K v2c": "v2c", "TimesFM 3.0": "tfm3",
             "Chronos-2 multivar.": "chronos2mv", "TiRex": "tirex", "Chronos-2 (Amazon": "chronos2", "TimesFM 2.5": "tfm25",
             "Sundial": "sundial", "Chronos-Bolt": "chronos-bolt", "Time-MoE": "timemoe200", "TTM r2": "ttm", "Persistence": "persist"}
    blk = tex[tex.index(r"\label{tab:h2h}"):]; blk = blk[:blk.index(r"\end{tabular}")]
    per = None; n = 0
    for line in blk.split("\n"):
        if "2023 test &" in line: per = "test"
        if "Live 2024" in line: per = "live"
        cells = [c.strip() for c in line.rstrip("\\ ").split("&")]
        if per and len(cells) == 8:
            key = next((v for k, v in names.items() if k in cells[1]), None)
            if key is None: continue
            vals = [num(c) for c in cells[2:]]
            want = [H[per][key]["E"]] + [H[per][key]["MAE"][v] for v in VARS]
            for j, (a, b) in enumerate(zip(vals, want)):
                tol = 0.5 * 10 ** -(len(cells[2 + j].split(".")[-1].rstrip("}").rstrip()) if "." in cells[2 + j] else 0) + 1e-9
                tol = max(tol, 5.1e-5 if j == 0 else 5.1e-4)
                if abs(a - b) > tol: bad.append((per, key, j, a, b))
            n += 1
    blk = tex[tex.index(r"\label{tab:test}"):]; blk = blk[:blk.index(r"\end{tabular}")]
    for line in blk.split("\n"):
        cells = [c.strip() for c in line.rstrip("\\ ").split("&")]
        if len(cells) != 7: continue
        src = (RUN["atlas25m"] if "24M" in cells[0] else RUN["atlas10m"] if "10M" in cells[0] else V2C if "v2c" in cells[0] else None)
        if src is None: continue
        for j, v in enumerate(VARS):
            if abs(num(cells[2 + j]) - src["test"]["MAE"][v]) > 5.1e-3 if j == 2 else abs(num(cells[2 + j]) - src["test"]["MAE"][v]) > 5.1e-4:
                bad.append(("test", cells[0], v, cells[2 + j], src["test"]["MAE"][v]))
        n += 1
    blk = tex[tex.index(r"\label{tab:val}"):]; blk = blk[:blk.index(r"\end{tabular}")]
    for line in blk.split("\n"):
        cells = [c.strip() for c in line.rstrip("\\ ").split("&")]
        if len(cells) != 9 or "Model" in cells[0]: continue
        src = RUN["atlas25m"] if "24M" in cells[0] else RUN["atlas10m"] if "10M" in cells[0] else V2C
        for j, v in enumerate(VARS):
            if abs(num(cells[2 + j]) - src["val"]["MAE"][v]) > (5.1e-3 if j == 2 else 5.1e-4):
                bad.append(("val", cells[0], v, cells[2 + j], src["val"]["MAE"][v]))
        if abs(num(cells[7].split("$")[0]) - src["val_E"]) > 5.1e-6: bad.append(("valE", cells[0], cells[7], src["val_E"]))
        n += 1
    print(f"checked {n} table rows in main.tex;", "ALL MATCH" if not bad else f"{len(bad)} MISMATCHES")
    for b in bad: print("  ", b)
    sys.exit(1 if bad else 0)
print("tables written to", T)
