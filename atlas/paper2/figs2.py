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

# atlas-analysis version 1 (2026-11-15): weights vs advantage (a) and lead-time MAE relative to TimesFM 2.5 (b)
LEAD = {"india": ([9.55,13.99,16.63,18.03,18.64,19.09,19.65,20.61,21.47,21.84,21.78,21.75,21.96,22.63,23.35,23.53,23.31,23.05,23.08,23.58,24.13,24.28,24.02,23.88],
                  [9.51,13.55,16.23,17.91,18.62,19.07,19.72,20.53,21.21,21.78,21.91,21.95,21.98,22.39,22.96,23.39,23.30,23.07,23.05,23.39,23.72,24.01,23.83,23.66]),
        "tfm": ([9.54,14.33,17.42,19.16,20.03,20.67,21.23,22.10,23.17,23.68,23.57,23.46,23.52,24.14,24.95,25.17,24.80,24.46,24.34,24.83,25.51,25.72,25.42,25.16],
                [9.01,13.53,16.54,18.55,19.67,20.35,20.94,21.70,22.57,23.29,23.28,23.21,23.27,23.76,24.38,24.85,24.61,24.29,24.00,24.37,24.85,25.31,25.06,24.85]),
        "F": ([9.22,13.60,16.27,17.72,18.37,18.88,19.42,20.35,21.22,21.62,21.56,21.54,21.78,22.38,23.10,23.32,23.08,22.84,22.85,23.34,23.91,24.10,23.84,23.70],
              [8.92,12.94,15.56,17.29,18.13,18.62,19.21,20.02,20.79,21.39,21.46,21.49,21.62,22.04,22.61,23.07,22.95,22.72,22.64,22.99,23.37,23.74,23.53,23.38]),
        "equal": ([9.17,13.65,16.40,17.93,18.63,19.17,19.72,20.62,21.53,21.97,21.89,21.84,21.98,22.59,23.32,23.53,23.24,22.97,22.95,23.45,24.02,24.24,23.98,23.81],
                  [8.84,12.96,15.68,17.47,18.35,18.92,19.48,20.30,21.03,21.64,21.71,21.72,21.79,22.23,22.82,23.25,23.08,22.84,22.69,23.07,23.44,23.85,23.65,23.49])}
fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.45), gridspec_kw=dict(width_ratios=[1.05, 1, 1]))
ax = axs[0]
ax.scatter(adv, w, s=14, color="#1f5fbf")
for n, xi, yi in zip(names, adv, w):
    if n in ("Delhi", "Kerala", "Maharashtra", "Gujarat", "Uttar Pradesh"):
        ax.annotate(n.replace("Uttar Pradesh", "U.P."), (xi, yi), xytext=(3, 2), textcoords="offset points", fontsize=6.5)
ax.set_xlabel("Atlas-India MAE vs TimesFM 2.5 (%)", fontsize=8); ax.set_ylabel("mean weight on Atlas", fontsize=8)
ax.set_title("(a) learned weights, trained st.", fontsize=8.5); ax.grid(color="#eee", lw=0.6)
hh = np.arange(1, 25)
for t, ax in enumerate(axs[1:]):
    base = np.array(LEAD["tfm"][t])
    ax.axhline(0, color="#888", lw=0.8, label="TimesFM 2.5")
    for k, lab, c, ls in (("india", "Atlas-India", "#c0504d", "-"), ("equal", "equal weights", "#9aa5b1", "--"), ("F", "Atlas-F", "#1f5fbf", "-")):
        ax.plot(hh, 100 * (np.array(LEAD[k][t]) / base - 1), color=c, ls=ls, lw=1.4, label=lab)
    ax.set_xlabel("lead (h)", fontsize=8); ax.set_xticks([1, 6, 12, 18, 24]); ax.grid(color="#eee", lw=0.6)
    ax.set_title(["(b) trained stations", "(c) never-trained stations"][t], fontsize=8.5)
    ax.set_ylim(-11, 7)
axs[1].set_ylabel("MAE vs TimesFM 2.5 (%)", fontsize=8)
axs[2].legend(frameon=False, fontsize=6.5, loc="upper right")
fig.tight_layout(); fig.savefig("figures/weights_lead.pdf"); fig.savefig("figures/weights_lead.png", dpi=150)

# I1 by hour (atlas-analysis version 1): MAE of Atlas and same-hour-yesterday, and the measured Delhi mean
A_H = [10.1,14.8,18.6,20.8,21.9,24.4,26.4,27.7,29.7,33.0,36.4,36.2,36.4,35.8,35.0,33.2,31.3,30.0,30.7,34.0,37.8,44.4,49.7,52.0]
Y_H = [59.1,57.8,54.3,50.8,49.5,47.7,47.2,46.8,48.8,51.9,54.1,50.6,48.0,46.1,44.0,41.7,38.6,37.0,37.1,38.7,44.8,51.0,56.7,58.7]
O_H = [194,191,184,179,176,172,169,166,169,174,173,162,147,130,117,108,104,106,118,143,165,182,193,196]
fig, ax = plt.subplots(figsize=(7.0, 2.3))
hr = np.arange(24)
ax.plot(hr, A_H, color="#1f5fbf", lw=1.6, label="Atlas (issued 00:00 IST, so hour = lead $-$ 1)")
ax.plot(hr, Y_H, color="#9aa5b1", lw=1.4, ls="--", label="same hour yesterday")
ax.axhline(58.75, color="#c0504d", lw=1, ls=":", label="WRF-Chem Day-1 MAE (CEEW, all hours)")
ax.set_xlabel("hour of day (IST)"); ax.set_ylabel("MAE (µg/m³)"); ax.set_xticks(range(0, 24, 3)); ax.grid(color="#eee", lw=0.6)
ax2 = ax.twinx(); ax2.fill_between(hr, O_H, color="#f2a541", alpha=0.15, lw=0); ax2.set_ylabel("measured mean", fontsize=8, color="#b07020")
ax2.set_ylim(0, 420); ax2.spines["right"].set_visible(True)
ax.set_zorder(ax2.get_zorder() + 1); ax.patch.set_visible(False)
ax.set_ylim(0, 72)
ax.legend(frameon=False, fontsize=7, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
fig.tight_layout(); fig.savefig("figures/i1_byhour.pdf"); fig.savefig("figures/i1_byhour.png", dpi=150)
print("figs ok")
