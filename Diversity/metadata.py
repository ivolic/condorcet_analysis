import pandas as pd
import json
import matplotlib.pyplot as plt
import ast
from functools import reduce
from itertools import combinations

# df = pd.read_csv('condorcet_simulations.csv')

# # 1. Identify all threshold columns (exclude 'election_id')
# threshold_cols = [col for col in df.columns if col != 'election_id']

# # 2. Count unique values in each row for the threshold columns
# # .nunique(axis=1) returns the number of unique winners per election
# df['unique_winners'] = df[threshold_cols].nunique(axis=1)

# # 3. Filter for elections where there is more than 1 unique winner
# changed_elections = df[df['unique_winners'] > 1]

# if not changed_elections.empty:
#     print(f"Found {len(changed_elections)} elections where the winner changed:")
#     print(changed_elections[['election_id', 'unique_winners']])
    
#     # Optional: See what the winners were
#     for idx, row in changed_elections.iterrows():
#         winners = row[threshold_cols].unique()
#         print(f"Election {row['election_id']} changed between: {winners}")
# else:
#     print("No elections found where the winner changed.")
    

# PREV ANALYSIS
files = {
    "australia": "/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/diversity_simulations_australia.csv",
    "scotland": "/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/diversity_simulations_scotland.csv",
    "usa": "/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/diversity_simulations_usa.csv",
    # "one_round": "data_and_logs/condorcet_highest.csv",
    # "one_round_condensed": "data_and_logs/condorcet_condense_highest.csv"
}

metadata = {
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
    print(f"reading {file}")
    df = pd.read_csv(file)

    # Threshold columns are everything except 'file'
    threshold_cols = [c for c in df.columns if c != 'file']
    
    df["election_name"] = df["file"].str.split("__").str[0]

    counts = df["election_name"].value_counts()
    df = df[df["election_name"].isin(counts[counts >= 200].index)]
    df = df.drop(columns=["election_name"])

    # Extract the base file name (strip __hitN suffix)
    df['base_file'] = df['file']

    # --- Winner stability ---
    # For each base_file, collect the set of winners across all thresholds
    # "no change" = same winner at every threshold for that file
    def winners_are_stable(group):
        all_winners = group[threshold_cols].values.flatten()
        return len(set(all_winners)) == 1

    stability = df.groupby('base_file').apply(winners_are_stable)
    num_no_change = int(stability.sum())
    num_change = int((~stability).sum())

    # --- Threshold changes ---
    # For each threshold, count how many base_files have >1 unique winner across hits
    threshold_changes = {}
    t = 10
    # if file == "data_and_logs/condorcet_fine.csv":
    #     t = 100

    all_threshold_cols_as_float = [float(c) for c in threshold_cols]

    for thresholds in range(0, t):
        threshold = thresholds / (t * 10)
        # Keep only columns with value > threshold
        cols_above = [c for c, v in zip(threshold_cols, all_threshold_cols_as_float) if v >= threshold]
        print(cols_above)
        if not cols_above:
            threshold_changes[str(threshold)] = 0
            continue

        def has_change(group):
            all_winners = group[cols_above].values.flatten()
            return len(set(all_winners)) > 1

        filtered_changes = df.groupby('base_file').apply(has_change)
        num_filtered_changes = int(filtered_changes.sum())
        threshold_changes[str(threshold)] = num_filtered_changes

    # --- candsLeft distribution ---
    # This field doesn't exist directly in the new format.
    # If you have a separate source for rounds/numCands, join it here.
    # Otherwise we skip or set to empty.
    cands_distribution = {}  # placeholder

    metadata["Experiments"][file] = {
        "winner_stability": {
            "no_change": num_no_change,
            "change": num_change
        },
        "threshold_changes": threshold_changes,
        "candsLeft_distribution": cands_distribution
    }

    # --- Build normalized winner df for merging ---
    # Melt back to long form for downstream use
    melted = df.melt(
        id_vars=['file', 'base_file'],
        value_vars=threshold_cols,
        var_name='threshold',
        value_name='winner'
    )
    melted['threshold'] = melted['threshold'].astype(float)
    melted['winner'] = melted['winner'].apply(normalize_winner)
    melted['winner'] = melted['winner'].apply(lambda x: tuple(sorted(x)))

    dfs[name] = melted[['base_file', 'threshold', 'winner']].rename(
        columns={'base_file': 'file', 'winner': f'winner_{name}'}
    )

    
# for name, file in files.items():
#     df = pd.read_csv(file)

#     winners = df.groupby('file')['winner'].nunique()
#     num_no_change = int((winners == 1).sum())
#     num_change = int((winners != 1).sum())

#     threshold_changes = {}
#     t = 10
#     if file == "data_and_logs/condorcet_fine.csv":
#         t = 100
#     for thresholds in range(0, t):
#         threshold = thresholds / (t*10)
#         filtered = df[df['threshold'] > threshold]
#         filtered_winners = filtered.groupby('file')['winner'].nunique()
#         num_filtered_changes = int((filtered_winners != 1).sum())

#         threshold_changes[str(threshold)] = num_filtered_changes

#     df["candsLeft"] = (df["numCands"] - df["rounds"] + 1).astype(int)
#     cands_distribution = (
#         df["candsLeft"]
#         .value_counts()
#         .sort_index()
#         .to_dict()
#     )

#     metadata["Experiments"][file] = {
#         "winner_stability": {
#             "no_change": num_no_change,
#             "change": num_change
#         },
#         "threshold_changes": threshold_changes,
#         "candsLeft_distribution": cands_distribution
#     }
    
#     df["winner"] = df["winner"].apply(normalize_winner)
#     df["winner"] = df["winner"].apply(lambda x: tuple(sorted(x)))
    
#     dfs[name] = df[["file", "threshold", "winner"]].rename(
#         columns={"winner": f"winner_{name}"}
#     )

# merged = reduce(
#     lambda left, right: pd.merge(left, right, on=["file", "threshold"]),
#     dfs.values()
# )

# merged.to_csv("metadata.csv", index=False)

# Count similarity and export data
# winner_cols = [
#     "america",
#     "winner_fine",
#     "winner_condensed",
#     "winner_one_round",
#     "winner_one_round_condensed"
# ]

# def has_common(a, b):
#     return bool(set(a) & set(b))

# pair_counts = {}

# for col1, col2 in combinations(winner_cols, 2):
#     count = sum(merged.apply(lambda row: has_common(row[col1], row[col2]), axis=1))
#     pair_counts[f"{col1}, {col2}"] = count

# metadata["Comparisons"] = pair_counts

# def differs1(row):
#     return row["winner_baseline"] != row["winner_condensed"]

# df_filtered1 = merged[merged.apply(differs1, axis=1)]
# df_filtered1 = df_filtered1[['file', 'threshold', 'winner_baseline', 'winner_condensed']]

# df_filtered1.to_csv("baseline_v_condensed.csv", index=False)

# def differs2(row):
#     return not has_common(row["winner_baseline"], row["winner_one_round"])

# df_filtered2 = merged[merged.apply(differs2, axis=1)]
# df_filtered2 = df_filtered2[['file', 'threshold', 'winner_baseline', 'winner_one_round']]
# df_filtered2.to_csv("baseline_v_oneround.csv", index=False)

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