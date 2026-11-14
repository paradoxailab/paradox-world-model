"""Figures for the follow-up paper. Every number is copied from the Kaggle logs named in the captions."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({"font.family": "Liberation Serif", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42})
# atlas-fusion-f version 2 (2026-11-15): MAE trained / never-trained
NET = {"Uttar Pradesh": ([20.89, 22.46], [22.78, 24.32], [20.8, 22.34]), "Delhi": ([37.34, 35.56], [41.87, 40.54], [37.27, 35.56]),
       "Haryana": ([24.32, 22.31], [25.72, 23.2], [24.12, 22.09]), "Maharashtra": ([19.68, 24.92], [19.45, 22.25], [18.96, 22.16]),
       "Karnataka": ([8.87, 9.2], [8.98, 9.43], [8.64, 9.0]), "Other states": ([15.12, 9.12], [15.19, 9.4], [14.71, 9.0]),
       "Madhya Pradesh": ([16.23, 13.86], [17.07, 13.88], [16.04, 13.42]), "West Bengal": ([14.65, 14.81], [15.79, 15.69], [14.59, 14.69]),
       "Bihar": ([27.74, 25.05], [29.35, 26.1], [27.47, 24.7]), "Rajasthan": ([19.07, 15.33], [19.67, 15.87], [18.86, 15.09]),
       "Gujarat": ([18.47, 18.41], [18.2, 19.49], [17.86, 18.25]), "Tamil Nadu": ([12.64, 16.39], [13.39, 16.73], [12.56, 16.04]),
       "Punjab": ([17.31, 28.08], [18.2, 28.09], [17.16, 27.64]), "Kerala": ([8.51, 12.32], [7.96, 12.36], [7.93, 12.02])}
W = {"Uttar Pradesh": .80, "Delhi": .86, "Haryana": .71, "Maharashtra": .46, "Karnataka": .53, "Other states": .53, "Madhya Pradesh": .69,
     "West Bengal": .79, "Bihar": .71, "Rajasthan": .66, "Gujarat": .42, "Tamil Nadu": .73, "Punjab": .70, "Kerala": .23}
names = list(NET)
fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.3), sharey=True)
y = np.arange(len(names))[::-1]
for t, ax in enumerate(axs):
    a = np.array([100 * (NET[n][0][t] / NET[n][1][t] - 1) for n in names])
    f = np.array([100 * (NET[n][2][t] / NET[n][1][t] - 1) for n in names])
    ax.axvline(0, color="#888", lw=0.8)
    ax.scatter(a, y, s=18, marker="o", facecolor="white", edgecolor="#c0504d", label="Atlas-India (v1.3)", zorder=3)
    ax.scatter(f, y, s=18, marker="o", color="#1f5fbf", label="Atlas-F", zorder=3)
    for yi, ai, fi in zip(y, a, f):
        ax.plot([ai, fi], [yi, yi], color="#bbb", lw=0.8, zorder=2)
    ax.set_title(["(a) stations trained on", "(b) never-trained stations"][t], fontsize=9)
    ax.set_xlabel("MAE relative to TimesFM 2.5 (%)")
    ax.set_yticks(y); ax.set_yticklabels(names)
    ax.grid(axis="x", color="#eee", lw=0.6)
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, frameon=False, loc="lower center", ncol=2, fontsize=8)
fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig("figures/fusion_networks.pdf"); fig.savefig("figures/fusion_networks.png", dpi=150)
# weight on Atlas against Atlas's own advantage over TimesFM 2.5 (trained stations)
fig, ax = plt.subplots(figsize=(3.4, 2.7))
adv = np.array([100 * (NET[n][0][0] / NET[n][1][0] - 1) for n in names]); w = np.array([W[n] for n in names])
ax.scatter(adv, w, s=16, color="#1f5fbf")
for n, xi, yi in zip(names, adv, w):
    if n in ("Delhi", "Kerala", "Maharashtra", "Gujarat", "Uttar Pradesh"):
        ax.annotate(n, (xi, yi), xytext=(4, 2), textcoords="offset points", fontsize=7)
ax.set_xlabel("Atlas-India MAE vs TimesFM 2.5 (%)"); ax.set_ylabel("mean weight on Atlas")
ax.grid(color="#eee", lw=0.6); fig.tight_layout(); fig.savefig("figures/fusion_weights.pdf"); fig.savefig("figures/fusion_weights.png", dpi=150)
print("ok")

# I1: atlas-i1-score version 1 (2026-11-15) and CEEW (Oct 2025), Delhi average hourly PM2.5, 1 Oct 2024 - 28 Feb 2025
I1 = [("Atlas\n(this paper)", 31.27, 54.24, "#1f5fbf"), ("Same hour\nyesterday", 48.38, 76.67, "#9aa5b1"),
      ("Last observed\nvalue", 56.27, 83.32, "#9aa5b1"), ("IITM WRF-Chem\n400 m, Day 1*", 58.75, 92.53, "#c0504d"),
      ("IMD SILAM\nDay 1*", 71.68, 107.95, "#c0504d")]
fig, ax = plt.subplots(figsize=(7.0, 2.5))
x = np.arange(len(I1)); wd = 0.36
for i, (n, mae, rmse, c) in enumerate(I1):
    ax.bar(i - wd / 2, mae, wd, color=c); ax.bar(i + wd / 2, rmse, wd, color=c, alpha=0.45, hatch="///", edgecolor="white")
    ax.text(i - wd / 2, mae + 2, f"{mae:.1f}", ha="center", fontsize=7.5); ax.text(i + wd / 2, rmse + 2, f"{rmse:.1f}", ha="center", fontsize=7.5)
ax.set_xticks(x); ax.set_xticklabels([t[0] for t in I1], fontsize=8)
ax.set_ylabel("µg/m³"); ax.set_ylim(0, 120); ax.grid(axis="y", color="#eee", lw=0.6); ax.set_axisbelow(True)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#555", label="MAE"), Patch(facecolor="#555", alpha=0.45, hatch="///", edgecolor="white", label="RMSE")],
          frameon=False, fontsize=8, loc="upper left")
fig.tight_layout(); fig.savefig("figures/i1_compare.pdf"); fig.savefig("figures/i1_compare.png", dpi=150)
