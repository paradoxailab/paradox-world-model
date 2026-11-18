"""Figures for the Atlas-5K 10M paper. Every number is copied from the Colab run log
(results/colab/w5k_atlas_10m_h24_g1/log_w5k_atlas_10m_h24_g1.txt) or the README's WB1 tables.
  python figs3.py   -> figures/curve.pdf, figures/vs_physicsformer.pdf"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "font.family": "serif"})
BLUE, GREY, RED, GREEN = "#1F5FBF", "#8a8a8a", "#C0392B", "#2E8B57"

# validation E on the 300 checking stations, every 2,000 steps (step 0 = the grown model before training)
steps = list(range(0, 80001, 2000))
E = [0.2796, 0.2837, 0.2832, 0.2825, 0.2826, 0.2838, 0.2835, 0.2829, 0.2825, 0.2820, 0.2831, 0.2831, 0.2822, 0.2805,
     0.2812, 0.2809, 0.2800, 0.2801, 0.2790, 0.2783, 0.2785, 0.2780, 0.2778, 0.2778, 0.2769, 0.2773, 0.2768, 0.2764,
     0.2762, 0.2754, 0.2752, 0.2750, 0.2749, 0.2743, 0.2745, 0.2744, 0.2744, 0.2745, 0.2741, 0.2742, 0.2742]
assert len(E) == len(steps)
fig, ax = plt.subplots(figsize=(5.2, 2.5))
ax.plot([s / 1000 for s in steps], E, color=BLUE, lw=1.6, marker="o", ms=2.2, label="Atlas-5K 10M (grown from v2c)")
ax.axhline(0.2796, color=GREY, ls="--", lw=1)
ax.text(80.5, 0.2798, "v2c (1M) best", color=GREY, fontsize=8, va="bottom", ha="right")
ax.annotate("best 0.2741\n(step 76k)", xy=(76, 0.2741), xytext=(58, 0.2722), fontsize=8, color=BLUE,
            arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.8))
ax.set_xlabel("training step (thousands)"); ax.set_ylabel("validation E (300 stations)")
ax.set_ylim(0.271, 0.285); ax.set_xlim(-1, 81)
ax.legend(frameon=False, loc="upper right", fontsize=8)
fig.tight_layout(); fig.savefig("figures/curve.pdf"); plt.close(fig)

# 2023 test MAE relative to PhysicsFormer (19.3M), per variable
names = ["Temperature", "Dew point", "Wind dir.", "Wind speed", "Pressure"]
pf = [1.55, 1.59, 57.37, 1.21, 1.43]
models = {"Atlas-5K v1 (0.97M)": [1.553, 1.596, 56.46, 1.228, 1.664],
          "Atlas-5K v2c (0.97M)": [1.474, 1.520, 54.84, 1.202, 1.533],
          "Atlas-5K 10M (9.64M)": [1.429, 1.486, 53.93, 1.183, 1.477]}
cols = ["#b9c9e6", "#6f93d0", BLUE]
fig, ax = plt.subplots(figsize=(5.4, 2.6))
w = 0.26
for k, (m, v) in enumerate(models.items()):
    rel = [100 * (a / b - 1) for a, b in zip(v, pf)]
    xs = [i + (k - 1) * w for i in range(5)]
    ax.bar(xs, rel, w, color=cols[k], label=m)
    if k == 2:
        for x, r in zip(xs, rel):
            ax.text(x, r + (0.5 if r > 0 else -0.5), f"{r:+.1f}%", ha="center", va="bottom" if r > 0 else "top", fontsize=7, color=BLUE)
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(range(5)); ax.set_xticklabels(names)
ax.set_ylabel("MAE vs PhysicsFormer (%)\n(below 0 = better)")
ax.set_ylim(-10, 18)
ax.legend(frameon=False, fontsize=7.5, loc="upper left")
fig.tight_layout(); fig.savefig("figures/vs_physicsformer.pdf"); plt.close(fig)
print("ok")
