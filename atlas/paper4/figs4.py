"""Figures for the Atlas-5K growth paper (1M -> 10M -> 24M). Every number is copied from a run log or result file:
  10M curve: results/colab/w5k_atlas_10m_h24_g1/log (also atlas/paper3/figs3.py)
  25M curve: Drive PWM-10M/out/log_w5k_atlas_25m_h24_g2.txt (README "Atlas-5K 25M results, part 1")
  head-to-head: data/h2h_{test,live}.json and data/paired_atlas10m_{test,live}.json (Drive PWM-10M/small/h2h)
  python figs4.py  -> figures/curve.pdf, figures/h2h.pdf"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "font.family": "serif"})
BLUE, DARK, GREY = "#1F5FBF", "#0B2E6B", "#8a8a8a"

# ---- 1. validation E on the 300 checking stations, every 2,000 steps (step 0 = grown model before training)
s = [x / 1000 for x in range(0, 80001, 2000)]
E10 = [0.2796, 0.2837, 0.2832, 0.2825, 0.2826, 0.2838, 0.2835, 0.2829, 0.2825, 0.2820, 0.2831, 0.2831, 0.2822, 0.2805,
       0.2812, 0.2809, 0.2800, 0.2801, 0.2790, 0.2783, 0.2785, 0.2780, 0.2778, 0.2778, 0.2769, 0.2773, 0.2768, 0.2764,
       0.2762, 0.2754, 0.2752, 0.2750, 0.2749, 0.2743, 0.2745, 0.2744, 0.2744, 0.2745, 0.2741, 0.2742, 0.2742]
E25 = [0.2741, 0.2771, 0.2772, 0.2765, 0.2767, 0.2773, 0.2769, 0.2779, 0.2759, 0.2771, 0.2758, 0.2754, 0.2754, 0.2766,
       0.2747, 0.2753, 0.2746, 0.2745, 0.2743, 0.2739, 0.2742, 0.2738, 0.2739, 0.2736, 0.2729, 0.2724, 0.2727, 0.2719,
       0.2720, 0.2717, 0.2718, 0.2717, 0.2716, 0.2713, 0.2712, 0.2715, 0.2712, 0.2714, 0.2713, 0.2712, 0.2712]
assert len(E10) == len(s) == len(E25)
fig, ax = plt.subplots(figsize=(5.4, 2.6))
ax.plot(s, E10, color=BLUE, lw=1.4, marker="o", ms=2, label="10M, grown from 1M (v2c)")
ax.plot([80 + x for x in s], E25, color=DARK, lw=1.4, marker="s", ms=2, label="24M, grown from 10M")
ax.axhline(0.2796, color=GREY, ls="--", lw=0.9); ax.text(160, 0.2799, "1M (v2c) best", color=GREY, fontsize=7.5, va="bottom", ha="right")
ax.axvline(80, color=GREY, ls=":", lw=0.9); ax.text(82, 0.2848, "grow 10M$\\to$24M (same forecasts)", fontsize=7.5, color=GREY, va="top")
ax.annotate("0.2741", xy=(76, 0.2741), xytext=(62, 0.2722), fontsize=7.5, color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.7))
ax.annotate("0.2712", xy=(152, 0.2712), xytext=(132, 0.2697), fontsize=7.5, color=DARK, arrowprops=dict(arrowstyle="->", color=DARK, lw=0.7))
ax.set_xlabel("cumulative training steps after growth from 1M (thousands)"); ax.set_ylabel("validation E (300 stations)")
ax.set_ylim(0.269, 0.285); ax.set_xlim(-2, 162)
ax.legend(frameon=False, loc="lower left", fontsize=7.5)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "figures/curve.pdf")); plt.close(fig)

# ---- 2. paired head-to-head: Atlas-5K 24M MAE relative to each foundation model, per variable, test 2023 and live
OPP = [("tfm3", "TimesFM 3.0"), ("tfm25", "TimesFM 2.5"), ("chronos2mv", "Chronos-2 (multivar.)"), ("chronos2", "Chronos-2"),
       ("chronos-bolt", "Chronos-Bolt"), ("tirex", "TiRex"), ("sundial", "Sundial"), ("timemoe200", "Time-MoE"), ("ttm", "TTM r2")]
VARS = ["Temp.", "Dew pt.", "Wind dir.", "Wind spd.", "Pressure"]
cmap = plt.get_cmap("Blues")
cols = [cmap(0.95 - 0.07 * k) for k in range(len(OPP))]
fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)
for ax, yr, title in zip(axs, ["test", "live"], ["2023 test", "Live: Jan 2024 - Aug 2025 (NOAA ISD-Lite)"]):
    P = json.load(open(os.path.join(HERE, f"data/paired_atlas25m_{yr}_r25.json")))
    w = 0.09
    for k, (key, lab) in enumerate(OPP):
        rows = P[key]
        assert all(r["verdict"] == "WIN" for r in rows)
        ax.bar([i + (k - 4) * w for i in range(5)], [r["diff_pct"] for r in rows], w, color=cols[k], label=lab)
    ax.axhline(0, color="black", lw=0.7); ax.set_xticks(range(5)); ax.set_xticklabels(VARS, fontsize=7.5)
    ax.set_title(title, fontsize=8.5); ax.set_ylim(-50, 0)
axs[0].set_ylabel("Atlas-5K 24M MAE vs. opponent (%)\n(every bar: significant win)")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, frameon=False, fontsize=6.6, loc="lower center", ncol=5)
fig.tight_layout(rect=(0, 0.1, 1, 1)); fig.savefig(os.path.join(HERE, "figures/h2h.pdf")); plt.close(fig)
print("ok")
