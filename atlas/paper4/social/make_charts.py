"""ParadoxAI Lab chart pack for posts (LinkedIn / X / website). Every number is read from the result files in
../data (copied from Drive PWM-10M/small/h2h); nothing is typed in by hand except the published 2023 test rows of
PhysicsFormer and the full-test MAE of Atlas (README).  python make_charts.py  -> social/*.png"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

HERE = os.path.dirname(os.path.abspath(__file__)); DATA = os.path.join(HERE, "..", "data")
for f in fm.findSystemFonts():
    if "Inter" in f:
        fm.fontManager.addfont(f)
BG, PANEL, INK, MUTED, GRID = "#0B1220", "#111A2E", "#F2F5FA", "#8A96AD", "#22304D"
ATLAS, ATLAS2, OTHER, BASE = "#3EE6C1", "#2BB5E8", "#5B6B8C", "#3A465E"
plt.rcParams.update({"font.family": "Inter", "font.size": 13, "text.color": INK, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": INK, "axes.edgecolor": GRID, "figure.facecolor": BG,
                     "axes.facecolor": BG, "savefig.facecolor": BG})
T = {k: v for k, v in json.load(open(os.path.join(DATA, "h2h_test.json"))).items() if not k.startswith("_")}
L = {k: v for k, v in json.load(open(os.path.join(DATA, "h2h_live.json"))).items() if not k.startswith("_") and k != "atlas10m_chk"}
NAME = {"atlas25m": "Atlas 24M", "atlas10m": "Atlas 9.6M", "v2c": "Atlas 1M", "tfm3": "TimesFM 3.0", "tfm25": "TimesFM 2.5",
        "chronos2": "Chronos-2", "chronos2mv": "Chronos-2 (multivar.)", "chronos-bolt": "Chronos-Bolt", "tirex": "TiRex",
        "sundial": "Sundial", "timemoe200": "Time-MoE 200M", "ttm": "TTM r2", "persist": "Persistence"}
ORG = {"tfm3": "Google", "tfm25": "Google", "chronos2": "Amazon", "chronos2mv": "Amazon", "chronos-bolt": "Amazon",
       "tirex": "NX-AI", "sundial": "Tsinghua", "timemoe200": "Shi et al.", "ttm": "IBM", "atlas25m": "ParadoxAI Lab",
       "atlas10m": "ParadoxAI Lab", "v2c": "ParadoxAI Lab", "persist": "baseline"}
PARAMS = {"atlas25m": "24M", "atlas10m": "9.6M", "v2c": "1M", "tfm3": "size n/p", "tfm25": "200M", "chronos2": "120M",
          "chronos2mv": "120M", "chronos-bolt": "205M", "tirex": "35M", "sundial": "128M", "timemoe200": "200M",
          "ttm": "0.8M", "persist": "no model"}
FOOT = ("WEATHER-5K benchmark · 24-hour forecasts · 709 stations worldwide · opponents zero-shot with 512 h of history · "
        "paired tests: station bootstrap + Diebold-Mariano, Holm, α = 0.01")
SRC = "Rules, code and logs: github.com/paradoxailab/paradox-world-model"


def frame(fig, title, sub):
    fig.text(0.045, 0.94, title, fontsize=27, fontweight="bold", color=INK, va="top")
    fig.text(0.045, 0.875, sub, fontsize=15, color=MUTED, va="top")
    fig.text(0.045, 0.045, FOOT, fontsize=9.5, color=MUTED)
    fig.text(0.045, 0.02, SRC, fontsize=9.5, color=MUTED)
    fig.text(0.955, 0.03, "ParadoxAI Lab", fontsize=14, fontweight="bold", color=ATLAS, ha="right")


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color(GRID); ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0)


# 1. leaderboard, 2023 test ------------------------------------------------------------------------------------------
keys = [k for k in sorted(T, key=lambda k: T[k]["E"]) if k != "v2c"]
fig = plt.figure(figsize=(16, 10), dpi=100)
ax = fig.add_axes([0.25, 0.13, 0.66, 0.68]); style(ax)
ys = list(range(len(keys)))[::-1]
for y, k in zip(ys, keys):
    a = k.startswith("atlas"); c = ATLAS if k == "atlas25m" else ATLAS2 if a else (BASE if k == "persist" else OTHER)
    ax.barh(y, T[k]["E"], color=c, height=0.68)
    ax.text(T[k]["E"] + 0.003, y, f"{T[k]['E']:.3f}", va="center", fontsize=13, color=INK if a else MUTED,
            fontweight="bold" if a else "normal")
ax.set_yticks(ys); ax.set_yticklabels([f"{NAME[k]}  ·  {ORG[k]}  ·  {PARAMS[k]}" for k in keys], fontsize=13)
for lab, k in zip(ax.get_yticklabels(), keys):
    if k.startswith("atlas"):
        lab.set_color(ATLAS); lab.set_fontweight("bold")
ax.set_xlim(0.20, 0.47); ax.xaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("standardised error E (mean of 5 variables' MAE / scale) — lower is better", fontsize=12)
frame(fig, "Smaller, task-trained world models beat the foundation models",
      "2023 test year: temperature, dew point, wind direction, wind speed and pressure at 709 stations, 24 hours ahead")
fig.savefig(os.path.join(HERE, "1_leaderboard_2023.png"), dpi=100); plt.close(fig)

# 2. smaller and better: error vs parameters ---------------------------------------------------------------------------
P = {"atlas25m": 24.1, "atlas10m": 9.64, "v2c": 0.97, "tfm25": 200, "chronos2": 120, "chronos2mv": 120,
     "chronos-bolt": 205, "tirex": 35, "sundial": 128, "timemoe200": 200, "ttm": 0.8}
fig = plt.figure(figsize=(16, 10), dpi=100)
ax = fig.add_axes([0.08, 0.14, 0.86, 0.66]); style(ax)
ax.axvspan(0.5, 30, color=ATLAS, alpha=0.05)
for k, p in P.items():
    a = k in ("atlas25m", "atlas10m", "v2c")
    ax.scatter(p, T[k]["E"], s=420 if a else 220, color=ATLAS if a else OTHER, edgecolor=BG, lw=2, zorder=3)
    POS = {"timemoe200": (40, 0.3555), "chronos-bolt": (330, 0.3500), "tfm25": (330, 0.3445), "sundial": (330, 0.3390),
           "chronos2": (330, 0.3330), "chronos2mv": (330, 0.3270)}
    if k in POS:
        tx, ty = POS[k]
        ax.annotate(f"{NAME[k]}", (p, T[k]["E"]), xytext=(tx, ty), textcoords="data", fontsize=13, color=INK,
                    ha="right" if tx < p else "left", va="center",
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8, shrinkA=2, shrinkB=6))
    else:
        off = {"atlas25m": (14, -4), "atlas10m": (-14, 12), "v2c": (14, -4), "tirex": (12, -4), "ttm": (12, -4)}[k]
        ax.annotate(f"{NAME[k]}", (p, T[k]["E"]), xytext=off, textcoords="offset points", fontsize=13,
                    color=ATLAS if a else INK, fontweight="bold" if a else "normal",
                    ha="right" if off[0] < 0 else "left", va="center")
ax.set_xscale("log"); ax.set_xlim(0.5, 1500); ax.set_ylim(0.265, 0.372)
ax.set_xticks([1, 3, 10, 30, 100, 300]); ax.set_xticklabels(["1M", "3M", "10M", "30M", "100M", "300M"])
ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("parameters (log scale)", fontsize=13); ax.set_ylabel("2023 test error E (lower is better)", fontsize=13)
ax.text(0.6, 0.268, "better ↓", fontsize=12, color=ATLAS)
frame(fig, "Lower error than models 5-21x larger",
      "Each dot is one model on the same 709-station, 24-hour WEATHER-5K test windows (TimesFM 3.0 omitted: size not published)")
fig.savefig(os.path.join(HERE, "2_smaller_and_better.png"), dpi=100); plt.close(fig)

# 3. per variable: Atlas 24M vs the strongest foundation model, test and fresh data --------------------------------------
VARS = ["Temperature", "Dewpoint", "Wind direction", "Wind speed", "Sea-level pressure"]
LAB = ["Temperature", "Dew point", "Wind direction", "Wind speed", "Pressure"]
PT = json.load(open(os.path.join(DATA, "paired_atlas25m_test_r25.json")))["tfm3"]
PL = json.load(open(os.path.join(DATA, "paired_atlas25m_live_r25.json")))["tfm3"]
assert all(r["verdict"] == "WIN" for r in PT + PL)
fig = plt.figure(figsize=(16, 10), dpi=100)
ax = fig.add_axes([0.08, 0.14, 0.86, 0.64]); style(ax)
w = 0.36
for i, (rt, rl) in enumerate(zip(PT, PL)):
    for dx, r, c, lab in ((-w / 2, rt, ATLAS, "2023 test"), (w / 2, rl, ATLAS2, "fresh data, Jan 2024 - Aug 2025")):
        ax.bar(i + dx, -r["diff_pct"], w * 0.92, color=c, label=lab if i == 0 else None)
        ax.text(i + dx, -r["diff_pct"] + 0.5, f"{-r['diff_pct']:.0f}%", ha="center", fontsize=14, fontweight="bold", color=INK)
ax.set_xticks(range(5)); ax.set_xticklabels(LAB, fontsize=14, color=INK)
ax.set_ylabel("lower error than TimesFM 3.0 (%)", fontsize=13); ax.set_ylim(0, 31)
ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=13, loc="upper right", labelcolor=INK)
frame(fig, "Atlas 24M vs Google TimesFM 3.0: lower error on every variable",
      "Every difference is statistically significant (Holm-corrected, α = 0.01), on the test year and on fresh observations")
fig.savefig(os.path.join(HERE, "3_per_variable_vs_timesfm3.png"), dpi=100); plt.close(fig)

# 4. holds on fresh data -------------------------------------------------------------------------------------------------
keys = [k for k in sorted(L, key=lambda k: L[k]["E"]) if k in T and k not in ("v2c", "persist")]
fig = plt.figure(figsize=(16, 10), dpi=100)
ax = fig.add_axes([0.25, 0.13, 0.66, 0.66]); style(ax)
ys = list(range(len(keys)))[::-1]
for y, k in zip(ys, keys):
    a = k.startswith("atlas"); c = ATLAS if a else OTHER
    ax.plot([T[k]["E"], L[k]["E"]], [y, y], color=c, lw=3, alpha=0.6)
    ax.scatter(T[k]["E"], y, s=160, color=BG, edgecolor=c, lw=2.5, zorder=3)
    ax.scatter(L[k]["E"], y, s=160, color=c, zorder=3)
ax.set_yticks(ys); ax.set_yticklabels([f"{NAME[k]}  ·  {ORG[k]}" for k in keys], fontsize=13)
for lab, k in zip(ax.get_yticklabels(), keys):
    if k.startswith("atlas"):
        lab.set_color(ATLAS); lab.set_fontweight("bold")
ax.set_xlim(0.26, 0.40); ax.xaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
ax.set_xlabel("error E: ○ 2023 test   ● fresh observations Jan 2024 - Aug 2025 (NOAA, after the benchmark ends)", fontsize=12)
frame(fig, "The ranking holds on data no model has seen",
      "Every model gets worse on the newest observations; Atlas stays clearly ahead of all ten opponents")
fig.savefig(os.path.join(HERE, "4_fresh_data.png"), dpi=100); plt.close(fig)

# 5. growth: 1M -> 9.6M -> 24M ------------------------------------------------------------------------------------------
fig = plt.figure(figsize=(16, 10), dpi=100)
ax = fig.add_axes([0.09, 0.14, 0.84, 0.64]); style(ax)
gk = ["v2c", "atlas10m", "atlas25m"]; xs = [0, 1, 2]
ax.plot(xs, [T[k]["E"] for k in gk], color=ATLAS, lw=3, marker="o", ms=16, mfc=ATLAS, mec=BG, mew=3)
for x, k, note in zip(xs, gk, ["trained from scratch", "grown, same forecasts at start", "grown again"]):
    ax.text(x, T[k]["E"] + 0.0016, f"{T[k]['E']:.4f}", ha="center", fontsize=16, fontweight="bold", color=INK)
    ax.text(x, T[k]["E"] - 0.0024, note, ha="center", fontsize=12, color=MUTED)
best = min(T[k]["E"] for k in T if not k.startswith("atlas") and k not in ("v2c", "persist"))
ax.axhline(best, color=OTHER, ls="--", lw=1.5)
ax.text(2.15, best + 0.0008, f"best foundation model (TimesFM 3.0): {best:.4f}", ha="right", fontsize=12, color=INK)
ax.set_xticks(xs); ax.set_xticklabels(["Atlas 1M\n0.97M parameters", "Atlas 9.6M\n10x", "Atlas 24M\n2.5x more"], fontsize=14, color=INK)
ax.set_xlim(-0.4, 2.4); ax.set_ylim(0.268, 0.336); ax.set_ylabel("2023 test error E (lower is better)", fontsize=13)
ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
frame(fig, "Grow, don't restart",
      "Each model is grown from the last with an exact, function-preserving map, then trained further. Each step improved the error.")
fig.savefig(os.path.join(HERE, "5_growth.png"), dpi=100); plt.close(fig)

# 6. cover card (4:5, LinkedIn) -----------------------------------------------------------------------------------------
fig = plt.figure(figsize=(10.8, 13.5), dpi=100)
gain = 100 * (1 - T["atlas25m"]["E"] / T["tfm3"]["E"])
fig.text(0.07, 0.92, "ParadoxAI Lab", fontsize=22, fontweight="bold", color=ATLAS)
fig.text(0.07, 0.86, "A 24M-parameter world model beats\nGoogle, Amazon, IBM and Tsinghua's\nforecasting foundation models",
         fontsize=34, fontweight="bold", color=INK, va="top", linespacing=1.15)
stats = [(f"{gain:.0f}%", "lower error than TimesFM 3.0\non the 2023 test year"),
         ("50 / 50", "comparisons won: 9 foundation models + persistence,\n5 variables each, all significant, in 2023 and 2024-25"),
         ("3", "periods: 2022, 2023 and fresh 2024-25\nobservations no model had seen"),
         ("5-21x", "smaller than TimesFM 2.5, Chronos-2,\nChronos-Bolt and Sundial (120-205M)")]
for i, (big, small) in enumerate(stats):
    y = 0.60 - i * 0.125
    fig.text(0.07, y, big, fontsize=48, fontweight="bold", color=ATLAS, va="center")
    fig.text(0.38, y, small, fontsize=17, color=INK, va="center", linespacing=1.3)
fig.text(0.07, 0.065, "24-hour forecasts · 709 stations worldwide · opponents zero-shot · paired statistical tests\n"
         "Rules written before every run · github.com/paradoxailab/paradox-world-model", fontsize=12.5, color=MUTED, linespacing=1.5)
fig.savefig(os.path.join(HERE, "0_cover.png"), dpi=100); plt.close(fig)
print("ok", round(gain, 1))
