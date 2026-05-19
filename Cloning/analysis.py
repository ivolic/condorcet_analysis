import pandas as pd
import ast
import re

# ---- Load data ----
df = pd.read_csv("ff_cloning.csv")

# ---- Remove elections with only 1 candidate ----
files_to_remove = df[
    (df["numCands"] == 1) & (df["candidate_cloned"] == "none")
]["file"].unique()

df = df[~df["file"].isin(files_to_remove)]

# ---- Filter to files that have all required percents ----
required_percents = {round(p, 1) for p in [0.1, 0.2, 0.3, 0.4, 0.5]}

files_with_all_percents = (
    df.groupby("file")["percent"]
    .apply(lambda x: required_percents.issubset(set(x.round(1))))
)
valid_files = files_with_all_percents[files_with_all_percents].index
df = df[df["file"].isin(valid_files)]

print(f"Files remaining after percent filter: {df['file'].nunique()}")

# ---- Helpers ----
def clean_name(val):
    if pd.isna(val) or val is None:
        return val
    val = str(val).strip()
    val = re.sub(r'"+', '', val)
    val = val.strip('"').strip()
    return val

def parse_name_list(val):
    if pd.isna(val) or val is None:
        return []
    try:
        parsed = ast.literal_eval(val)
        if isinstance(parsed, list):
            return parsed
    except:
        pass
    return [val.strip()]

def parse_cloned(val):
    if val == "none":
        return None
    try:
        inner = val.replace("frozenset({", "").replace("})", "")
        return inner.strip("'\"")
    except:
        return None

df["cloned_name"] = df["candidate_cloned"].apply(parse_cloned)

# ---- Build baseline map: (file, percent) -> ff winner ----
baseline = df[df["candidate_cloned"] == "none"].copy()

baseline_map = {}
for _, row in baseline.iterrows():
    baseline_map[row["file"]] = row["ff"]

# ---- Friendly fire analysis ----
results = []

for _, row in df.iterrows():
    if row["candidate_cloned"] == "none":
        continue

    cloned_cand = clean_name(row["cloned_name"])
    base = parse_name_list(clean_name(baseline_map.get(row["file"])))
    curr = parse_name_list(clean_name(row["ff"]))
        
    # print(cloned_cand, base, curr)
    if base is None or curr is None:
        continue

    winner_changed = (curr != base)
    
    # Self-clone: the cloned candidate was the original winner, clone splits their vote
    self_clone_ff = (
        cloned_cand in base and
        winner_changed and
        "Clone" in curr
    )
    
    # Other instances
    ff_fire = (
        winner_changed and not self_clone_ff
    )
    
    if ff_fire:
        print(cloned_cand, base, curr)


    results.append({
        "file": row["file"],
        "percent": row["percent"],
        "cloned_candidate": cloned_cand,
        "original_ff_winner": str(base),
        "new_ff_winner": str(curr),
        "winner_changed": winner_changed,
        "friendly_fire": ff_fire,
        "self_clone_ff": self_clone_ff,
        "num_cands": row["numCands"],
    })

res_df = pd.DataFrame(results)

# print(res_df.head())

# ---- Summaries ----
ff_summary = (
    res_df
    .groupby("percent")["friendly_fire"]
    .apply(lambda g: res_df.loc[g.index[g], "file"].nunique())
    .reset_index(name="num_files_ff")
)

self_clone_summary = (
    res_df
    .groupby("percent")["self_clone_ff"]
    .apply(lambda g: res_df.loc[g.index[g], "file"].nunique())
    .reset_index(name="num_files_self_clone_ff")
)

ff_detail = (
    res_df[res_df["friendly_fire"]]
    [["file", "percent", "cloned_candidate", "original_ff_winner", "new_ff_winner", "num_cands"]]
    .drop_duplicates()
    .sort_values(["percent", "file"])
)

self_clone_detail = (
    res_df[res_df["self_clone_ff"]]
    [["file", "percent", "cloned_candidate", "original_ff_winner", "new_ff_winner", "num_cands"]]
    .drop_duplicates()
    .sort_values(["percent", "file"])
)

# ---- Export ----
ff_summary.to_csv("ff_summary.csv", index=False)
self_clone_summary.to_csv("ff_self_clone_summary.csv", index=False)
ff_detail.to_csv("ff_detail.csv", index=False)
self_clone_detail.to_csv("ff_self_clone_detail.csv", index=False)

# print(ff_summary)
# print("\n---- Friendly Fire Detail ----")
# print(ff_detail)
# print("\n---- Self-Clone Friendly Fire Detail ----")
# print(self_clone_detail)