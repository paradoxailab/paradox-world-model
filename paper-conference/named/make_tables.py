"""Build the paper's LaTeX tables from the analysis log dump (ROW| and SIG| lines) - no number is typed by hand.

  python make_tables.py rows.txt   ->  tables/*.tex
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tables")
os.makedirs(OUT, exist_ok=True)
lines = open(sys.argv[1]).read().splitlines()

rows, sig = [], []
for l in lines:
    p = l.split("|")
    if p[0] == "ROW":
        num = lambda s: float(s) if s not in ("", "None") else None
        rows.append(dict(task=p[1], track=p[2], model=p[3], MAE=num(p[4]), RMSE=num(p[5]), MAPE=num(p[6]),
                         QL=num(p[7]), IS80=num(p[8]), COV80=num(p[9]), params=p[10], ctx=p[11],
                         extra=json.loads(p[12]) if len(p) > 12 and p[12] else {}))
    elif p[0] == "SIG":
        sig.append(dict(task=p[1], track=p[2], opp=p[3], a=float(p[4]), b=float(p[5]), rel=float(p[6]),
                        lo=float(p[7]), hi=float(p[8]), p=float(p[9]), z=float(p[10]), n=int(p[11])))

TRAFFIC = ["PEMS08", "PEMS04", "PEMS03", "PEMS07", "METR-LA", "PEMS-BAY"]
RAIN = ["IMD-CI", "IMD-WC"]
HEAD = {"PEMS08": "PEMS08", "PEMS04": "PEMS04", "PEMS03": "PEMS03$^\\ast$", "PEMS07": "PEMS07$^\\ast$",
        "METR-LA": "METR-LA$^\\ast$", "PEMS-BAY": "PEMS-BAY$^\\ast$", "IMD-CI": "IMD-CI", "IMD-WC": "IMD-WC"}


def find(task, track, prefix):
    c = [r for r in rows if r["task"] == task and r["track"] == track and r["model"].startswith(prefix)]
    return min(c, key=lambda r: r["MAE"]) if c else None


def pwm(task, track):
    return find(task, track, "PWM-Dyn v0.6") or find(task, track, "PWM-Dyn v0.4")


def capped(r):
    return r is not None and r["extra"].get("stopped_by") == "wall-clock budget"


def fmt(v, d=2):
    return "--" if v is None else f"{v:.{d}f}"


# ---------------------------------------------------------------- Table: main point accuracy
MODELS = [("Last value", "Last value", "A"), ("Climatology", "Climatology quantiles", "A"),
          None,
          ("STID", "STID", "A"), ("Graph WaveNet", "Graph WaveNet", "A"), ("STAEformer", "STAEformer", "A"),
          ("PWM-Dyn (ours)", "PWM", "A"),
          None,
          ("TimesFM 2.5", "TimesFM-2.5", "B"), ("TimesFM 3.0 mv", "TimesFM-3.0", "B"),
          ("PWM-Dyn (ours), Track B", "PWM", "B")]
TASKS = TRAFFIC + RAIN
best = {}
for t in TASKS:
    for tr in ("A", "B"):
        c = [r for r in rows if r["task"] == t and r["track"] == tr and "ablation" not in r["model"]
             and not r["model"].startswith("Seasonal")]
        if c:
            best[(t, tr)] = min(r["MAE"] for r in c)
L = [r"\begin{table*}[t]", r"\caption{Point accuracy: test MAE (RMSE below) on the official windows. Upper block: Track A, 12-step context,"
     r" every model trained on the task's training split; lower block: Track B, foundation models zero-shot with 512 steps"
     r" (365 days on rainfall). Bold: best MAE in the block. $^\dagger$\,stopped by its wall-clock budget before its authors'"
     r" schedule ended (Table~\ref{tab:budget}). $^\ast$\,network never used during development. Rainfall PWM-Dyn entries are"
     r" v0.4; rainfall has no specialist entries. Units: vehicles/5\,min (PeMS flow), mph (METR-LA, PEMS-BAY), mm/day (IMD).}",
     r"\label{tab:main}", r"\small", r"\setlength{\tabcolsep}{4pt}",
     r"\begin{tabular}{@{}l" + "r" * len(TASKS) + "@{}}", r"\toprule",
     "Model & " + " & ".join(HEAD[t] for t in TASKS) + r" \\", r"\midrule"]
for m in MODELS:
    if m is None:
        L.append(r"\midrule"); continue
    name, key, tr = m
    cells, cells2 = [], []
    for t in TASKS:
        r = pwm(t, tr) if key == "PWM" else find(t, tr, key)
        if r is None and key == "Climatology quantiles":
            r = find(t, "B", key)
        if r is None:
            cells.append("--"); cells2.append(""); continue
        v = fmt(r["MAE"])
        pw = pwm(t, tr)
        if tr == "A":
            blk = [x for x in rows if x["task"] == t and x["track"] == "A" and not x["model"].startswith("PWM")
                   and not x["model"].startswith("Seasonal")] + ([pw] if pw else [])
            blk += [find(t, "B", "Climatology")] if find(t, "A", "Climatology") is None and find(t, "B", "Climatology") else []
        else:
            blk = [x for x in rows if x["task"] == t and x["track"] == "B" and x["model"].startswith("TimesFM")] + ([pw] if pw else [])
        if blk and abs(r["MAE"] - min(x["MAE"] for x in blk)) < 1e-9:
            v = r"\textbf{" + v + "}"
        if capped(r):
            v += r"$^\dagger$"
        cells.append(v); cells2.append(r"{\scriptsize " + fmt(r["RMSE"]) + "}")
    L.append(name + " & " + " & ".join(cells) + r" \\")
    L.append(" & " + " & ".join(cells2) + r" \\[1pt]")
L += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
open(os.path.join(OUT, "main.tex"), "w").write("\n".join(L))

# ---------------------------------------------------------------- Table: uncertainty and dead sensors
L = [r"\begin{table}[t]", r"\caption{Probabilistic quality (Track B, IS80 with 80\% coverage) and dead sensors (Track R,"
     r" MAE on the 30\% of locations with no test-period readings). Specialists without a missing-data mechanism are fed"
     r" zeros, their repositories' missing-value convention.}", r"\label{tab:prob}", r"\small", r"\setlength{\tabcolsep}{3pt}",
     r"\begin{tabular}{@{}lrrrrr@{}}", r"\toprule",
     r" & \multicolumn{3}{c}{IS80 (coverage \%)} & \multicolumn{2}{c}{Track R MAE} \\",
     r"\cmidrule(lr){2-4}\cmidrule(l){5-6}",
     r"Task & PWM-Dyn & TimesFM 3.0 & Climat. & PWM-Dyn & best other \\", r"\midrule"]
for t in TASKS:
    p, f3, cl = pwm(t, "B"), find(t, "B", "TimesFM-3.0"), find(t, "B", "Climatology")
    c = lambda r: "--" if r is None or r["IS80"] is None else f"{r['IS80']:.2f} ({100*r['COV80']:.0f})"
    pr = pwm(t, "R")
    others = [r for r in rows if r["task"] == t and r["track"] == "R" and not r["model"].startswith("PWM")]
    bo = min(others, key=lambda r: r["MAE"]) if others else None
    bon = "--" if bo is None else fmt(bo["MAE"]) + r"\,{\scriptsize(" + ("clim." if bo["model"].startswith("Clim") else bo["model"].split(" ")[0]) + ")}"
    prv = "--" if pr is None else fmt(pr["MAE"])
    if pr is not None and bo is not None and pr["MAE"] < bo["MAE"]:
        prv = r"\textbf{" + prv + "}"
    elif pr is not None and bo is not None:
        bon = r"\textbf{" + fmt(bo["MAE"]) + r"}\,{\scriptsize(clim.)}"
    L.append(f"{HEAD[t]} & {c(p)} & {c(f3)} & {c(cl)} & {prv} & {bon} " + r"\\")
L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(os.path.join(OUT, "prob.tex"), "w").write("\n".join(L))

# ---------------------------------------------------------------- Table: paired tests
OPP = [("STID", "STID"), ("GWNet", "Graph WaveNet"), ("STAEf.", "STAEformer"), ("TimesFM 3.0", "TimesFM-3.0")]
L = [r"\begin{table}[t]", r"\caption{Paired tests of PWM-Dyn against each model on the same windows: relative MAE difference"
     r" (negative = PWM-Dyn better) and Diebold--Mariano $p$-value; in brackets the 95\% day-block bootstrap interval."
     r" Track A for specialists, Track B for TimesFM. $^\dagger$\,opponent budget-capped.}", r"\label{tab:sig}", r"\scriptsize",
     r"\setlength{\tabcolsep}{2.5pt}", r"\begin{tabular}{@{}l" + "c" * len(OPP) + "@{}}", r"\toprule",
     "Task & " + " & ".join(o[0] for o in OPP) + r" \\", r"\midrule"]
for t in TRAFFIC:
    cells = []
    for short, key in OPP:
        tr = "B" if key.startswith("TimesFM") else "A"
        s = [x for x in sig if x["task"] == t and x["track"] == tr and x["opp"].startswith(key)]
        if not s:
            cells.append("--"); continue
        s = s[0]
        pv = "<10^{-3}" if s["p"] < 1e-3 else f"{s['p']:.2f}"
        mark = r"$^\dagger$" if capped(find(t, tr, key)) else ""
        cells.append(f"${s['rel']:+.1f}\\%$ ($p{'' if pv.startswith('<') else '='}{pv}$){mark}\\newline"
                     if False else
                     f"\\shortstack{{${s['rel']:+.1f}\\%$, $p{'' if pv.startswith('<') else '='}{pv}${mark}\\\\"
                     f"{{}}[{s['lo']:+.1f}, {s['hi']:+.1f}]}}")
    L.append(HEAD[t] + " & " + " & ".join(cells) + r" \\[2pt]")
L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(os.path.join(OUT, "sig.tex"), "w").write("\n".join(L))

# ---------------------------------------------------------------- Table: opponent budgets
L = [r"\begin{table}[t]", r"\caption{Opponent training: epochs completed and what stopped the run (A = authors' schedule,"
     r" B = wall-clock budget, minutes in brackets). One seed each, official code and hyper-parameters, mixed precision.}",
     r"\label{tab:budget}", r"\scriptsize", r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{@{}lccc@{}}", r"\toprule",
     r"Task & STID & Graph WaveNet & STAEformer \\", r"\midrule"]
for t in TRAFFIC:
    cells = []
    for key in ("STID", "Graph WaveNet", "STAEformer"):
        r = find(t, "A", key)
        if r is None:
            cells.append("out of memory"); continue
        e = r["extra"]
        cells.append(f"{e.get('epochs_run')} {'B' if e.get('stopped_by') == 'wall-clock budget' else 'A'} ({e.get('budget_minutes'):.0f})")
    L.append(HEAD[t] + " & " + " & ".join(cells) + r" \\")
L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(os.path.join(OUT, "budget.tex"), "w").write("\n".join(L))

# ---------------------------------------------------------------- Table: seeds and ablation
L = [r"\begin{table}[t]", r"\caption{Left: what cost v0.4 accuracy. Validation MAE (selection criterion, seeds 0--1) and"
     r" test MAE of each configuration's ensemble; the frozen choice is marked. Right: test MAE of the three fresh"
     r" seeds of the frozen model and of their ensemble (Track A). The v0.4.1 row is its own three-seed run (seeds 0--2).}", r"\label{tab:abl}", r"\scriptsize",
     r"\setlength{\tabcolsep}{2.5pt}", r"\begin{tabular}{@{}lrrrr@{}}", r"\toprule",
     r"Configuration & \multicolumn{2}{c}{Val.\ MAE} & \multicolumn{2}{c}{Test MAE} \\",
     r"\cmidrule(lr){2-3}\cmidrule(l){4-5}", r" & P08 & P04 & P08 & P04 \\", r"\midrule"]
VAL = {"v03": (14.597, 18.611), "clim-vs1": (14.445, 18.835), "noclim-vs1": (14.610, 18.395), "v041": (14.520, 18.839)}
LAB = {"v03": "no clim., 60 ep., select every window", "clim-vs1": "clim., 100 ep., select every window",
       "noclim-vs1": "no clim., 100 ep., select every window (frozen)", "v041": "clim., 100 ep., select every 4th (v0.4.1)"}
V041_TEST = (14.498, 19.023)
for k in ("v041", "clim-vs1", "v03", "noclim-vs1"):
    if k == "v041":
        te = V041_TEST
    else:
        te = tuple(find(t, "A", f"PWM-Dyn ablation {k} ")["MAE"] for t in ("PEMS08", "PEMS04"))
    L.append(f"{LAB[k]} & {VAL[k][0]:.2f} & {VAL[k][1]:.2f} & {te[0]:.2f} & {te[1]:.2f} " + r"\\")
L += [r"\bottomrule", r"\end{tabular}", r"\vspace{4pt}", r"\begin{tabular}{@{}lrrr@{}}", r"\toprule",
      r"Task & Seeds (test MAE) & Mean $\pm$ SD & Ens. \\", r"\midrule"]
for t in TRAFFIC:
    r = find(t, "A", "PWM-Dyn v0.6")
    m = r["extra"]["members"]
    import statistics as st
    d = 3 if st.mean(m) < 5 else 2
    L.append(f"{HEAD[t]} & {' / '.join(f'{x:.{d}f}' for x in m)} & {st.mean(m):.{d}f} $\\pm$ {st.stdev(m):.{d}f} & {r['MAE']:.{d}f} " + r"\\")
L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(os.path.join(OUT, "abl.tex"), "w").write("\n".join(L))
print("tables:", sorted(os.listdir(OUT)))

# ---------------------------------------------------------------- Appendix: Track R, all entries
L = [r"\begin{table}[h]", r"\caption{Track R (30\% of locations dark during the test period): MAE on the dark locations."
     r" Specialists receive zeros for missing readings, their repositories' convention.}", r"\label{tab:trackr}", r"\scriptsize",
     r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{@{}lrrrrr@{}}", r"\toprule",
     r"Task & PWM-Dyn & Climatology & STID & Graph WaveNet & STAEformer \\", r"\midrule"]
for t in TRAFFIC:
    vals = [pwm(t, "R"), find(t, "R", "Climatology"), find(t, "R", "STID"), find(t, "R", "Graph WaveNet"), find(t, "R", "STAEformer")]
    L.append(HEAD[t] + " & " + " & ".join(fmt(v["MAE"]) if v else "--" for v in vals) + r" \\")
L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
open(os.path.join(OUT, "trackr.tex"), "w").write("\n".join(L))
print("trackr ok")
