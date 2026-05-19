import pandas as pd
import ast
import matplotlib.pyplot as plt

# CONFIG
CSV1_PATH = "/Users/belle/Desktop/build/condorcet_analysis/Diversity/data_and_logs/condorcet_condense.csv" 
CSV2_PATH = "/Users/belle/Desktop/build/condorcet_analysis/Diversity/new_db/comparison_helper.csv" 
OUTPUT_PLOT = "diversity_comparison_all.png"
OUTPUT_PLOT_BAR = "diversity_comparison.png"

METHOD_COLS = [
    'plurality', 'IRV', 'top-two', 'borda-pm', 'borda-om', 'borda-avg',
    'top-3-truncation', 'condorcet', 'minimax', 'smith_plurality',
    'smith_irv', 'smith-minimax', 'ranked-pairs', 'bucklin', 'approval', 'smith'
]

THRESHOLDS = [round(x * 0.01, 2) for x in range(10)]  # 0.00, 0.01, ..., 0.09

def parse_winner_list(val):
    try:
        lst = ast.literal_eval(str(val))
        return [x.strip() for x in lst] if lst else []
    except Exception:
        return []

def classify_match(winner, method_val):
    winners = parse_winner_list(method_val)
    if not winners:
        return 'no_winner'
    return 'match' if winner in winners else 'no_match'

df1_full = pd.read_csv(CSV1_PATH)
df2 = pd.read_csv(CSV2_PATH, index_col=0)

available_methods = [c for c in METHOD_COLS if c in df2.columns]

results = {}

for thresh in THRESHOLDS:
    df1 = df1_full[df1_full["threshold"] == thresh]
    merged = df1.merge(df2[['file'] + available_methods], on='file', how='left')

    for col in available_methods:
        merged[f'{col}_match'] = merged.apply(
            lambda row: classify_match(row['winner'], row.get(col, '[]')), axis=1
        )

    total = len(merged)
    rates = []
    for col in available_methods:
        rate = (merged[f'{col}_match'] == 'match').sum() / total * 100 if total > 0 else 0
        rates.append(rate)
    results[thresh] = (rates, total)

fig, ax = plt.subplots(figsize=(14, 7))

colors = plt.cm.tab20c.colors
x = range(len(available_methods))

for i, thresh in enumerate(THRESHOLDS):
    rates, n = results[thresh]
    ax.plot(x, rates, marker='o', label=f'{thresh:.2f} (n={n})',
            color=colors[i % len(colors)], linewidth=1.8, markersize=5)

ax.set_xlabel('Voting method', fontsize=11)
ax.set_ylabel('Match rate (% of elections)', fontsize=11)
ax.set_title('How often diversity scoring elects the same winner as other methods\nwhen there are no condorcet winners (n=16)', fontsize=13)
ax.set_xticks(x)
ax.set_xticklabels(available_methods, rotation=45, ha='right', fontsize=9)
ax.set_ylim(0, 110)
ax.axhline(100, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
ax.legend(title='Threshold', loc='lower right', fontsize=8, framealpha=0.7)
ax.spines[['top', 'right']].set_visible(False)

plt.tight_layout()
plt.savefig(OUTPUT_PLOT, dpi=150)
print(f"Saved: {OUTPUT_PLOT}")

bar_rates, _ = results[0.05]

fig2, ax2 = plt.subplots(figsize=(12, 6))
bars = ax2.bar(available_methods, bar_rates, color='steelblue', edgecolor='white', width=0.6)

for bar, rate in zip(bars, bar_rates):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
             f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)

ax2.set_ylim(0, 110)
ax2.set_ylabel('Match rate (% of elections)', fontsize=11)
ax2.set_title(f'How often diversity scoring elects the same winner as other methods\nwhen there are no condorcet winners at threshold = 0.05 (n=16)', fontsize=13)
ax2.set_xticks(range(len(available_methods)))
ax2.set_xticklabels(available_methods, rotation=45, ha='right', fontsize=9)
ax2.axhline(100, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
ax2.spines[['top', 'right']].set_visible(False)

plt.tight_layout()
plt.savefig(OUTPUT_PLOT_BAR, dpi=150)
print(f"Saved: {OUTPUT_PLOT_BAR}")