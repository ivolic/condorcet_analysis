import json
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib.ticker import PercentFormatter

# Your data
with open('/Users/belle/Desktop/build/condorcet_analysis/Diversity/metadata.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Short labels for experiment names
exp_labels = {
    "/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/diversity_simulations_australia.csv": "Australia",
    "/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/diversity_simulations_scotland.csv": "Scotland",
    "/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/diversity_simulations_usa.csv": "America"
}

fig = plt.figure(figsize=(18, 14))
# fig.suptitle("Diversity Scoring Analysis", fontsize=16, fontweight="bold", y=0.98)
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

no_change_raw = [data["Experiments"][e]["winner_stability"]["no_change"] for e in exps]
change_raw    = [data["Experiments"][e]["winner_stability"]["change"]    for e in exps]

# convert counts to percentages of each experiment's total
totals = [nc + c for nc, c in zip(no_change_raw, change_raw)]
# no_change = [nc / t * 100 for nc, t in zip(no_change_raw, totals)]
change    = [c  / t * 100 for c,  t in zip(change_raw, totals)]

x = np.arange(len(exps))
w = 0.35
# ax1.bar(x - w/2, no_change, w, label="No Change", color="#55A868")
ax1.bar(x + w/2, change,    w, label="Change",    color="#C44E52")
ax1.set_xticks(x); ax1.set_xticklabels(short, rotation=30, ha="right", fontsize=8)
ax1.set_title("Diversity threshold stability")
ax1.set_ylabel("Pct of elections where a different threshold changed the winner")
ax1.yaxis.set_major_formatter(PercentFormatter(xmax=100))
ax1.set_ylim(0, 100)
ax1.legend(fontsize=8)

# ── 2. Threshold Changes — Baseline, Condensed, Highest (line chart) ───────
ax2 = fig.add_subplot(gs[0, 1])
highlight_exps = [
    "/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/diversity_simulations_australia.csv",
    "/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/diversity_simulations_scotland.csv",
    "/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/diversity_simulations_usa.csv"
]
for i, exp in enumerate(highlight_exps):
    exp_data = data["Experiments"][exp]
    tc = exp_data["threshold_changes"]
    n_experiments = exp_data["winner_stability"]["no_change"] + exp_data["winner_stability"]["change"]
    xs = [float(k) for k in tc]
    ys = [v / n_experiments * 100 for v in tc.values()]  # convert to percent
    ax2.plot(xs, ys, marker="o", markersize=4, label=exp_labels[exp], color=colors[i*3])

ax2.set_title("Threshold Changes (steps of 0.01)")
ax2.set_xlabel("Threshold")
ax2.set_ylabel("Pct of elections whose winners changed after this threshold")
ax2.yaxis.set_major_formatter(PercentFormatter(xmax=100))  # forces "%" labels, fixed 0-100 scale
ax2.set_ylim(0, 100)  # optional: locks the axis range so it's always comparable
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)

plt.savefig("diversity_results.png", dpi=150, bbox_inches="tight")