import json
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

# Your data
with open('metadata.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Short labels for experiment names
exp_labels = {
    "data_and_logs/condorcet.csv": "Baseline",
    "data_and_logs/condorcet_fine.csv": "Fine",
    "data_and_logs/condorcet_condense.csv": "Condensed",
    "data_and_logs/condorcet_highest.csv": "Highest",
    "data_and_logs/condorcet_condense_highest.csv": "Condensed+Highest",
}

fig = plt.figure(figsize=(18, 14))
fig.suptitle("Diversity Scoring Analysis", fontsize=16, fontweight="bold", y=0.98)
gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

colors = [
    "#084c8d", "#1a6fa8", "#2e8fc4", "#42aedb", "#67c4e8",
    "#8dd4ef", "#2d8a6e", "#3aaa85", "#4ec9a0", "#76d9b8",
    "#a8e8d0", "#d0f5e8"
]
# ── 1. Winner Stability (grouped bar) ──────────────────────────────────────
ax1 = fig.add_subplot(gs[0, 0])
exps = list(data["Experiments"].keys())
short = [exp_labels[e] for e in exps]
no_change = [data["Experiments"][e]["winner_stability"]["no_change"] for e in exps]
change    = [data["Experiments"][e]["winner_stability"]["change"]    for e in exps]
x = np.arange(len(exps))
w = 0.35
ax1.bar(x - w/2, no_change, w, label="No Change", color="#55A868")
ax1.bar(x + w/2, change,    w, label="Change",    color="#C44E52")
ax1.set_xticks(x); ax1.set_xticklabels(short, rotation=30, ha="right", fontsize=8)
ax1.set_title("Winner Stability by Experiment")
ax1.set_ylabel("Count"); ax1.legend(fontsize=8); ax1.set_ylim(0, 18)

# ── 2. Threshold Changes — Baseline, Condensed, Highest (line chart) ───────
ax2 = fig.add_subplot(gs[0, 1])
highlight_exps = ["data_and_logs/condorcet.csv",
                  "data_and_logs/condorcet_condense.csv",
                  "data_and_logs/condorcet_highest.csv"]
for i, exp in enumerate(highlight_exps):
    tc = data["Experiments"][exp]["threshold_changes"]
    xs = [float(k) for k in tc]; ys = list(tc.values())
    ax2.plot(xs, ys, marker="o", markersize=4, label=exp_labels[exp], color=colors[i*3])
ax2.set_title("Threshold Changes (steps of 0.01)")
ax2.set_xlabel("Threshold"); ax2.set_ylabel("# Changes")
ax2.legend(fontsize=8); ax2.grid(True, alpha=0.3)

# ── 3. Threshold Changes — Fine (dedicated plot) ───────────────────────────
ax3 = fig.add_subplot(gs[0, 2])
tc_fine = data["Experiments"]["data_and_logs/condorcet_fine.csv"]["threshold_changes"]
xs_f = [float(k) for k in tc_fine]; ys_f = list(tc_fine.values())
ax3.plot(xs_f, ys_f, color=colors[1], linewidth=1.5)
ax3.fill_between(xs_f, ys_f, alpha=0.2, color=colors[1])
ax3.set_title("Threshold Changes (steps of 0.001)")
ax3.set_xlabel("Threshold"); ax3.set_ylabel("# Changes"); ax3.grid(True, alpha=0.3)

# ── 4. Pairwise Comparisons (horizontal bar) ───────────────────────────────
ax5 = fig.add_subplot(gs[1, 0:])
comps = data["Comparisons"]
labels = [k.replace(", ", "\nvs ").replace("winner_", "") for k in comps]
vals   = list(comps.values())
y = np.arange(len(labels))
bars = ax5.barh(y, vals, color=[colors[i % len(colors)] for i in range(len(vals))])
ax5.set_yticks(y); ax5.set_yticklabels(labels, fontsize=8)
ax5.set_title("Pairwise Winner Comparisons")
ax5.set_xlabel("Agreements (n=160; 16 elections, 10 thresholds each)")
for bar, val in zip(bars, vals):
    ax5.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
             str(val), va="center", fontsize=8)
ax5.set_xlim(0, max(vals) + 15)
ax5.grid(True, axis="x", alpha=0.3)

plt.savefig("diversity_results.png", dpi=150, bbox_inches="tight")