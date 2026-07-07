import pandas as pd
import ast
import matplotlib.pyplot as plt
import re

BORDA_CSV_PATH = "/Users/belle/Desktop/build/condorcet_analysis/Diversity/tvr_comparison/data/tvr_australia.csv"
CSV2_PATH = "/Users/belle/Desktop/build/rcv/results/current/australia.csv"
OUTPUT_CSV = "tvr_australia.csv"
OUTPUT_PLOT = "tvr_australia.png"

METHOD_COLS = [
    'plurality', 'IRV', 'top-two', 'borda-pm', 'borda-om', 'borda-avg',
    'top-3-truncation', 'condorcet', 'minimax', 'smith_plurality',
    'smith_irv', 'smith-minimax', 'ranked-pairs', 'bucklin', 'approval', 'smith'
]

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

# borda = pd.read_csv(BORDA_CSV_PATH)

def parse_line(line):
    # Match: filename, method, winner (winner may contain commas)
    match = re.match(r'^(.*?),(PM|AVG|OM),(.+)$', line.strip())
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None

with open(BORDA_CSV_PATH, 'r') as f:
    next(f)  # skip header
    rows = [parse_line(line) for line in f if line.strip()]

borda = pd.DataFrame(rows, columns=['file', 'threshold', 'winner'])
borda.to_csv('borda_output.csv', index=False)

df2 = pd.read_csv(CSV2_PATH)
df2['file'] = df2['file'].str.split('/').str[-1]

available_methods = [c for c in METHOD_COLS if c in df2.columns]

merged = borda.merge(df2[['file'] + available_methods], on='file', how='left')

for col in available_methods:
    merged[f'{col}_match'] = merged.apply(
        lambda row: classify_match(row['winner'], row.get(col, '[]')), axis=1
    )

output_cols = list(borda.columns) + [f'{c}_match' for c in available_methods]
merged[output_cols].to_csv(OUTPUT_CSV, index=False)
print(f"Saved: {OUTPUT_CSV}")

# PLOT
method = merged['threshold'].unique()
colors = plt.cm.tab10.colors

fig, axes = plt.subplots(len(method), 1,
                         figsize=(13, 5 * len(method)),
                         sharex=True)
if len(method) == 1:
    axes = [axes]

for ax, threshold in zip(axes, method):
    subset = merged[merged['threshold'] == threshold]
    total = len(subset)

    rates = [
        (subset[f'{col}_match'] == 'match').sum() / total * 100
        for col in available_methods
    ]

    bars = ax.bar(available_methods, rates, color='steelblue', edgecolor='white', width=0.6)
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=8)

    ax.set_ylim(0, 110)
    ax.set_title(f'Threshold: {threshold}  (n={total})', fontsize=12)
    ax.set_ylabel('Percent of elections', fontsize=10)
    ax.spines[['top', 'right']].set_visible(False)

axes[-1].set_xticks(range(len(available_methods)))
axes[-1].set_xticklabels(available_methods, rotation=45, ha='right', fontsize=9)

fig.suptitle('How often the TVR elects the same winner as other methods', fontsize=14, y=1.01)
# fig.text(0.5, 0.99, 'For PM and AVG, there are 2 elections where TVR does not elect anyone', fontsize=9, ha='center', transform=fig.transFigure)
plt.tight_layout()
plt.savefig(OUTPUT_PLOT, dpi=150, bbox_inches='tight')
print(f"Saved: {OUTPUT_PLOT}")