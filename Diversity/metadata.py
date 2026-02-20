import pandas as pd
import json
import matplotlib.pyplot as plt
import ast
from functools import reduce
from itertools import combinations

files = {
    "baseline": "data_and_logs/condorcet.csv",
    "fine": "data_and_logs/condorcet_fine.csv",
    "condensed": "data_and_logs/condorcet_condense.csv",
    "one_round": "data_and_logs/condorcet_highest.csv",
    "one_round_condensed": "data_and_logs/condorcet_condense_highest.csv"
}

metadata = {
    "Sample size": {
        "scotland": 14,
        "america": 2,
        "total": 16
    },
    "Experiments": {},
    "Comparisons": {}
}

dfs = {}

def normalize_winner(x):
    try:
        parsed = ast.literal_eval(x)
        if isinstance(parsed, list):
            return parsed
        else:
            return [parsed]
    except (ValueError, SyntaxError):
        return [x]
    
for name, file in files.items():
    df = pd.read_csv(file)

    winners = df.groupby('file')['winner'].nunique()
    num_no_change = int((winners == 1).sum())
    num_change = int((winners != 1).sum())

    threshold_changes = {}
    t = 10
    if file == "data_and_logs/condorcet_fine.csv":
        t = 100
    for thresholds in range(0, t):
        threshold = thresholds / (t*10)
        filtered = df[df['threshold'] > threshold]
        filtered_winners = filtered.groupby('file')['winner'].nunique()
        num_filtered_changes = int((filtered_winners != 1).sum())

        threshold_changes[str(threshold)] = num_filtered_changes

    df["candsLeft"] = (df["numCands"] - df["rounds"] + 1).astype(int)
    cands_distribution = (
        df["candsLeft"]
        .value_counts()
        .sort_index()
        .to_dict()
    )

    metadata["Experiments"][file] = {
        "winner_stability": {
            "no_change": num_no_change,
            "change": num_change
        },
        "threshold_changes": threshold_changes,
        "candsLeft_distribution": cands_distribution
    }
    
    df["winner"] = df["winner"].apply(normalize_winner)
    df["winner"] = df["winner"].apply(lambda x: tuple(sorted(x)))
    
    dfs[name] = df[["file", "threshold", "winner"]].rename(
        columns={"winner": f"winner_{name}"}
    )

merged = reduce(
    lambda left, right: pd.merge(left, right, on=["file", "threshold"]),
    dfs.values()
)

merged.to_csv("metadata.csv", index=False)

# Count similarity and export data
winner_cols = [
    "winner_baseline",
    "winner_fine",
    "winner_condensed",
    "winner_one_round",
    "winner_one_round_condensed"
]

def has_common(a, b):
    return bool(set(a) & set(b))

pair_counts = {}

for col1, col2 in combinations(winner_cols, 2):
    count = sum(merged.apply(lambda row: has_common(row[col1], row[col2]), axis=1))
    pair_counts[f"{col1}, {col2}"] = count

metadata["Comparisons"] = pair_counts

def differs1(row):
    return row["winner_baseline"] != row["winner_condensed"]

df_filtered1 = merged[merged.apply(differs1, axis=1)]
df_filtered1 = df_filtered1[['file', 'threshold', 'winner_baseline', 'winner_condensed']]

df_filtered1.to_csv("baseline_v_condensed.csv", index=False)

def differs2(row):
    return not has_common(row["winner_baseline"], row["winner_one_round"])

df_filtered2 = merged[merged.apply(differs2, axis=1)]
df_filtered2 = df_filtered2[['file', 'threshold', 'winner_baseline', 'winner_one_round']]
df_filtered2.to_csv("baseline_v_oneround.csv", index=False)

with open("metadata.json", "w") as f:
    json.dump(metadata, f, indent=4)


# OLD METADATA

# print("Sample size: 14 (Scotland) + 2 (America) = 16\n")

# winners = df.groupby('file')['winner'].nunique()
# num_winners = (winners == 1).sum()
# num_winners2 = (winners != 1).sum()

# print(f"How many files have no change in winner regardless of threshold? {num_winners}")
# print(f"How many files have some change in winner regardless of threshold? {num_winners2}\n")

# for thresholds in range(0, 100):
#     threshold = thresholds / 1000
#     filtered_winners = df[df['threshold'] > threshold].groupby('file')['winner'].nunique()
#     num_filtered_winners = (filtered_winners != 1).sum()

#     print(f"How many files have a change in winner for thresholds after {threshold}? {num_filtered_winners}")

# df["candsLeft"] = (df["numCands"] - df["rounds"] + 1).astype(int)


# filtered = df[df["threshold"] == 0]
# counts = filtered["candsLeft"].value_counts().sort_index()

# plt.figure()
# plt.bar(counts.index, counts.values)
# plt.xticks(range(int(counts.index.min()), int(counts.index.max()) + 1))

# plt.xlabel("Candidates Left Before Selection")
# plt.ylabel("Elections")
# plt.title("Distribution of Candidates Left (Threshold = 0)")
# plt.savefig("candsLeft.png")