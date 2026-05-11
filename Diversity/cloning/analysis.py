import pandas as pd
import ast

# ---- Load data ----
df = pd.read_csv("tvr_cloning.csv")

files_to_remove = df[
    (df["numCands"] == 1) & (df["candidate_cloned"] == "none")
]["file"].unique()

print(files_to_remove)

# Filter out all elections with those file names
df = df[~df["file"].isin(files_to_remove)]

borda_type = ["om", "avg", "pm"]

required_percents = {round(p, 1) for p in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]}

files_with_all_percents = (
    df.groupby("file")["percent"]
    .apply(lambda x: required_percents.issubset(set(x.round(1))))
)
valid_files = files_with_all_percents[files_with_all_percents].index

df = df[df["file"].isin(valid_files)]

print(f"Files remaining after percent filter: {df['file'].nunique()}")

import re

def clean_name(val):
    if pd.isna(val) or val is None:
        return val
    val = str(val).strip()
    val = re.sub(r'"+', '"', val)   # collapse multiple quotes into one
    val = val.strip('"').strip()    # strip leading/trailing quotes
    return val

# ---- Helper: extract winner name from string like "('Name', 5)" ----
def extract_winner(val):
    if pd.isna(val):
        return None
    try:
        parsed = ast.literal_eval(val)
        return parsed[0]  # candidate name
    except:
        return None

# ---- Apply extraction ----
for col in borda_type:
    df[col] = df[col]

# ---- Get baseline rows ----
baseline = df[df["candidate_cloned"] == "none"].copy()

# key: (file, percent, threshold) -> baseline winner
baseline_map = {}
for _, row in baseline.iterrows():
    for t in borda_type:
        baseline_map[(row["file"], row["percent"], t)] = row[t]

# ---- Function to extract cloned candidate name ----
def parse_cloned(val):
    if val == "none":
        return None
    try:
        inner = val.replace("frozenset({", "").replace("})", "")
        return inner.strip("'\"")
    except:
        return None

df["cloned_name"] = df["candidate_cloned"].apply(parse_cloned)

# ---- Compare winners ----
results = []

print(df.head())

for _, row in df.iterrows():
    if row["candidate_cloned"] == "none":
        continue

    for t in borda_type:
        base = clean_name(baseline_map.get((row["file"], row["percent"], t)))
        curr = clean_name(row[t])

        if base is None or curr is None:
            continue
        
        cloned_cand = clean_name(row["cloned_name"])

        # ---- Apply exclusion rule ----
        if (
            cloned_cand == base and
            curr == 'Clone'
        ):
            continue

        changed = (curr != base) and curr != "TIED"

        results.append({
            "file": row["file"],
            "percent": row["percent"],
            "borda_type": t,
            "original_winner": base,
            "new_winner": curr,
            "cloned_candidate": row["cloned_name"],
            "cloned_becomes_winner": changed and (cloned_cand == curr),
            "tied": (curr != base) and curr == "TIED",
            "changed_cloned_not_winner": changed and (cloned_cand != curr),
            "num_cands": row["numCands"]
        })

res_df = pd.DataFrame(results)

print(res_df.head())

# ---- Count number of files where winner changed ----

changed_detail = (
    res_df[res_df["changed_cloned_not_winner"]]
    [["file", "percent", "borda_type", "cloned_candidate", "original_winner", "new_winner", "num_cands"]]
    .drop_duplicates()
    .sort_values(["percent", "borda_type", "file"])
)

summary = (
    res_df
    .groupby(["percent", "borda_type"])["changed_cloned_not_winner"]
    .apply(lambda g: res_df.loc[g.index[g], "file"].nunique())
    .reset_index(name="num_files_changed")
)


changed_detail2 = (
    res_df[res_df["tied"]]
    [["file", "percent", "borda_type", "cloned_candidate", "original_winner", "new_winner", "num_cands"]]
    .drop_duplicates()
    .sort_values(["percent", "borda_type", "file"])
)
summary2 = (
    res_df
    .groupby(["percent", "borda_type"])["tied"]
    .apply(lambda g: res_df.loc[g.index[g], "file"].nunique())
    .reset_index(name="num_files_changed")
)

changed_detail3 = (
    res_df[res_df["cloned_becomes_winner"]]
    [["file", "percent", "borda_type", "cloned_candidate", "original_winner", "new_winner", "num_cands"]]
    .drop_duplicates()
    .sort_values(["percent", "borda_type", "file"])
)

# ---- Export ----
summary.to_csv("winner_changes_summary.csv", index=False)
summary2.to_csv("winner_tied_summary.csv", index=False)
changed_detail.to_csv("winner_changes_detail.csv", index=False)   # <-- added
changed_detail2.to_csv("winner_tied_detail.csv", index=False)   # <-- added
changed_detail3.to_csv("winner_cloned_becomes_winner_detail.csv", index=False)   # <-- added

print(summary)
print("\n---- Changed Elections Detail ----")
print(changed_detail)