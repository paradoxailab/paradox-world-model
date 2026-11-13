"""Figures for the Atlas paper. Every number below is copied from the recorded Kaggle logs / atlas/README.md."""
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
import glob as _g
for f in _g.glob("/usr/share/fonts/truetype/liberation/LiberationSerif-*.ttf"):
    font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": "Liberation Serif", "mathtext.fontset": "stix",
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "lines.linewidth": 1.3, "pdf.fonttype": 42})
BLUE, GREY, LGREY = "#1f5fbf", "#8a8a8a", "#c8c8c8"
GREEN, RED = "#3f8f4f", "#c0392b"
OUT = "src/figures/"

# ---------------- Fig 2: Delhi league -- (a) MAE by lead time, (b) Atlas's advantage on both tracks
lead = [1, 6, 12, 24]
L = {  # MAE@1h, 6h, 12h, 24h, trained stations (Kaggle run atlas-league2-score-w1)
 "Atlas v1.3 (0.97M)": [13.59, 26.23, 30.85, 33.22],
 "Moirai 2.0 (11M)": [14.15, 29.27, 32.48, 34.40],
 "TiRex (35M)": [13.77, 29.38, 32.69, 35.09],
 "TimesFM 2.5 (200M)": [13.95, 29.17, 32.91, 35.34],
 "Chronos-2 (120M)": [14.10, 29.29, 32.93, 35.99],
 "Chronos-Bolt (205M)": [14.21, 29.33, 33.35, 36.26],
 "Granite TTM r2 (0.8M)": [16.50, 30.73, 33.42, 34.92]}
# relative MAE difference, Atlas v1.3 vs opponent (negative = Atlas lower), trained / never-trained; all p < 0.001
D = [("Moirai 2.0", -5.2, -4.8), ("TiRex", -5.9, -5.7), ("TimesFM 2.5", -6.2, -5.7), ("Chronos-2", -7.3, -6.8),
     ("Chronos-Bolt", -7.8, -8.5), ("Granite TTM r2", -8.6, -8.0), ("TSFM fusion (3)", -5.0, -4.7),
     ("CAMS + bias corr.", -29.0, -32.5), ("CAMS raw", -53.7, -51.7)]
fig, ax = plt.subplots(1, 2, figsize=(5.5, 2.15), gridspec_kw={"width_ratios": [1.05, 1]})
a = ax[0]
for k, v in L.items():
    atl = k.startswith("Atlas")
    a.plot(lead, v, marker="o", ms=3 if atl else 2.2, color=BLUE if atl else LGREY, lw=1.6 if atl else 0.9,
           zorder=3 if atl else 2, label=k if atl else None)
a.plot([], [], color=LGREY, lw=0.9, marker="o", ms=2.2, label="six zero-shot TSFMs")
a.set_xticks(lead); a.set_xlabel("lead time (h)"); a.set_ylabel(r"MAE ($\mu$g/m$^3$)")
a.set_title(r"(a) Delhi PM$_{2.5}$, trained stations", loc="left")
a.legend(frameon=False, loc="lower right")
a.annotate("gap opens by 6 h", xy=(6, 26.6), xytext=(8.5, 21.5), fontsize=6.5, color=GREY,
           arrowprops=dict(arrowstyle="-", color=GREY, lw=0.5))
b = ax[1]
names = [d[0] for d in D][:7]; s = [d[1] for d in D][:7]; u = [d[2] for d in D][:7]
y = np.arange(len(names))[::-1]
b.barh(y + 0.18, s, height=0.34, color=BLUE, label="trained stations")
b.barh(y - 0.18, u, height=0.34, color=BLUE, alpha=0.45, label="never-trained stations")
for yi, si in zip(y, s):
    b.text(si - 0.15, yi + 0.18, f"{si:.1f}".replace("-", "\u2212"), va="center", ha="right", fontsize=6)
b.set_yticks(y); b.set_yticklabels(names); b.axvline(0, color="k", lw=0.6)
b.set_xlim(-10.5, 0); b.set_xlabel("Atlas MAE relative to opponent (%)")
b.set_title(r"(b) Atlas vs. each opponent (all $p<10^{-3}$)", loc="left")
b.set_ylim(-1.9, len(names) - 0.5); b.legend(frameon=False, loc="lower left", fontsize=6.3, ncol=2, handlelength=1.2, columnspacing=0.8)
fig.tight_layout(pad=0.3, w_pad=1.2); fig.savefig(OUT + "delhi_league.pdf"); plt.close(fig)

# ---------------- Fig 3: all-India, per network (Atlas-India vs TimesFM 2.5, trained stations)
N = [("Delhi", 37.34, 41.87, "W", 140), ("Uttar Pradesh", 20.89, 22.78, "W", 77), ("West Bengal", 14.65, 15.79, "W", 75),
     ("Tamil Nadu", 12.64, 13.39, "W", 42), ("Haryana", 24.32, 25.72, "W", 86), ("Bihar", 27.74, 29.35, "W", 121),
     ("Madhya Pradesh", 16.23, 17.07, "W", 57), ("Punjab", 17.31, 18.20, "W", 65), ("Rajasthan", 19.07, 19.67, "W", 63),
     ("Karnataka", 8.87, 8.98, "T", 34), ("Other states", 15.12, 15.19, "T", 55), ("Maharashtra", 19.68, 19.45, "T", 74),
     ("Gujarat", 18.47, 18.20, "T", 67), ("Kerala", 8.51, 7.96, "L", 43)]
rel = [100 * (a_ / t_ - 1) for _, a_, t_, _, _ in N]
order = np.argsort(rel)
fig, a = plt.subplots(figsize=(5.5, 1.95))
x = np.arange(len(N))
col = {"W": BLUE, "T": LGREY, "L": RED}
for i, j in enumerate(order):
    nm, at, tf, v, mean = N[j]
    a.bar(i, rel[j], color=col[v], width=0.7)
    a.text(i, (rel[j] - 0.5) if rel[j] < 0 else (rel[j] + 0.4), f"{rel[j]:+.1f}".replace("-", "\u2212"), ha="center",
           va="top" if rel[j] < 0 else "bottom", fontsize=5.8, zorder=4,
           bbox=dict(facecolor="white", edgecolor="none", pad=0.4))
a.set_xticks(x); a.set_xticklabels([N[j][0] for j in order], rotation=35, ha="right")
a.axhline(0, color="k", lw=0.6); a.set_ylim(-13.5, 9)
a.axhline(-6.07, color=BLUE, lw=0.6, ls="--", zorder=1); a.text(13.4, -6.07 - 0.4, "pooled \u22126.1%", color=BLUE, fontsize=6.3, ha="right", va="top")
a.set_ylabel("MAE vs. TimesFM 2.5 (%)")
from matplotlib.patches import Patch
a.legend(handles=[Patch(color=BLUE, label="Atlas significantly better (9)"), Patch(color=LGREY, label="level (4)"),
                  Patch(color=RED, label="TimesFM 2.5 better (1)")], frameon=False, loc="upper left", ncol=3, fontsize=6.3)
fig.tight_layout(pad=0.3); fig.savefig(OUT + "india_networks.pdf"); plt.close(fig)

# ---------------- Fig 4: Atlas-W -- (a) data efficiency, (b) removals
months = ["0.5", "1", "2", "4", "8", "15"]
W = [37.1, 37.4, 39.5, 37.3, 33.0, 32.1]; A = [42.7, 42.8, 44.2, 40.0, 35.4, 34.3]
R = [("physics update", 5.0, 5.6, 6.5), ("exchange $\\kappa$", 3.2, 0.9, 1.2), ("forecast-hour calendar", 2.0, 11.9, 10.8),
     ("6/24/72 h means", 0.9, 0.2, 0.6), ("weather inputs", 0.8, 0.6, 1.1), ("summary mixing", 0.7, 0.4, 0.8),
     ("PM$_{10}$, NO$_2$, O$_3$ inputs", 0.4, 0.7, 0.5), ("long history", 0.2, -0.5, -0.1)]
fig, ax = plt.subplots(1, 2, figsize=(5.5, 2.1), gridspec_kw={"width_ratios": [1, 1.1]})
a = ax[0]; xx = np.arange(6)
a.plot(xx, A, marker="o", ms=2.6, color=GREY, label=r"best Atlas ($\leq$0.97M)")
a.plot(xx, W, marker="o", ms=3, color=BLUE, lw=1.6, label="Atlas-W (14K)")
a.axhline(40.30, color=GREY, ls=":", lw=0.8); a.text(5.15, 40.6, "same hour\nyesterday", fontsize=6, color=GREY, ha="right", va="bottom")
a.set_xticks(xx); a.set_xticklabels(months); a.set_xlabel("months of Delhi training data"); a.set_ylabel(r"test MAE ($\mu$g/m$^3$)")
a.set_title("(a) data efficiency (2 seeds per point)", loc="left"); a.legend(frameon=False, loc="lower left", bbox_to_anchor=(0.0, 0.0))
b = ax[1]; yy = np.arange(len(R))[::-1]
b.barh(yy + 0.18, [r[1] for r in R], height=0.34, color=BLUE, label="validation")
b.barh(yy - 0.18, [r[2] for r in R], height=0.34, color=BLUE, alpha=0.45, label="test, trained stations")
b.axvline(1.0, color=GREY, ls=":", lw=0.8); b.axvline(0, color="k", lw=0.6)
b.set_yticks(yy); b.set_yticklabels([r[0] for r in R]); b.set_xlabel("error increase when removed (%)")
b.set_title(r"(b) removing one part at a time", loc="left"); b.legend(frameon=False, loc="lower right", fontsize=6.3)
b.set_ylim(-1.1, len(R) - 0.4); b.text(1.15, -0.95, "1% rule", fontsize=6, color=GREY)
fig.tight_layout(pad=0.3, w_pad=1.0); fig.savefig(OUT + "atlasw.pdf"); plt.close(fig)
print("ok")
