"""
analyze_tvr.py
--------------
Analyzes tvr_cloning_tests.csv produced by run_tvr.py.

Questions answered:
  1. How often does cloning change the winner? (by election, method, percent)
  2. Do ties actually lead to different winners across fork branches?
  3. Does the clone percent threshold matter — at what point do changes kick in?
  4. Clone outcome split per threshold: how often does the Clone itself win vs spoiler wins?
  5. Agreement across methods: when OM/AVG/PM disagree on winner.

Filtering rule applied everywhere:
  Rows where percent == 0.5 AND the original winner == candidate_cloned are excluded.
  At 50% the clone is placed before the original winner on half the ballots, so the
  clone winning is a trivial self-displacement, not a meaningful result.

Run:
    python analyze_tvr.py                         # uses default RESULTS_FILE
    python analyze_tvr.py path/to/results.csv
"""

import sys
import os
import json
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

RESULTS_FILE = "./tvr_cloning_tests.csv"
METHODS = ["om", "avg", "pm"]
OUTPUT_DIR = "./analysis"

# ---------------------------------------------------------------------------
# Load & filter
# ---------------------------------------------------------------------------

def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"file", "candidate_cloned", "percent", "numCands",
                "om", "avg", "pm", "om_tie_path", "avg_tie_path", "pm_tie_path"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")
    df["percent"] = df["percent"].astype(float).round(2)
    for m in METHODS:
        df[f"{m}_tie_path"]    = df[f"{m}_tie_path"].fillna("")
        df[f"{m}_tie_dropped"] = df[f"{m}_tie_dropped"].fillna("")
    return df


def filter_trivial(df: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows where percent == 0.5 AND the original winner == candidate_cloned
    AND the Clone is the new winner. These are trivial: the clone is placed before
    the original winner on exactly half the ballots, so it winning is guaranteed
    and uninformative.
    """
    df = attach_baseline(df, baseline)
    trivial_mask = pd.Series(False, index=df.index)
    for m in METHODS:
        trivial_mask |= (
            (df["percent"] == 0.5) &
            (df["candidate_cloned"] == df[f"{m}_baseline"]) &
            (df[m] == "Clone")
        )
    return df[~trivial_mask].copy()


def split(df: pd.DataFrame):
    """Return (baseline_df, cloned_df). Baseline = candidate_cloned == 'none'."""
    baseline = df[df["candidate_cloned"] == "none"].copy()
    cloned   = df[df["candidate_cloned"] != "none"].copy()
    return baseline, cloned


# ---------------------------------------------------------------------------
# Helper: attach baseline winner columns to any dataframe that has a 'file' col
# ---------------------------------------------------------------------------

def attach_baseline(df: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    """
    Join the baseline winner for each (file, method) onto df.
    Each method gets a new column {method}_baseline.
    Baseline tie-forks are resolved by taking the modal winner per file.
    """
    for m in METHODS:
        if f"{m}_baseline" in df.columns:
            continue
        bw = (
            baseline.groupby("file")[m]
            .agg(lambda s: s.mode().iloc[0])
            .rename(f"{m}_baseline")
        )
        df = df.join(bw, on="file")
    return df


# ---------------------------------------------------------------------------
# 1. Clone-induced winner changes
# ---------------------------------------------------------------------------

def section_clone_changes(cloned: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Per method: which elections saw a flip, at which percents, from which candidate."""
    results = {}
    for m in METHODS:
        col_base = f"{m}_baseline"
        changed = cloned[cloned[m] != cloned[col_base]]
        per_election = (
            changed.groupby("file")
            .agg(
                num_flips=("candidate_cloned", "count"),
                percents_that_flip=("percent", lambda s: sorted(s.unique().tolist())),
                candidates_that_flip=("candidate_cloned", lambda s: sorted(s.unique().tolist())),
            )
            .reset_index()
        )
        results[m] = per_election
    return results


def summary_clone_changes(cloned: pd.DataFrame) -> pd.DataFrame:
    """Per method: how many elections saw at least one flip."""
    total_elections = cloned["file"].nunique()
    rows = []
    for m in METHODS:
        col_base = f"{m}_baseline"
        n = cloned[cloned[m] != cloned[col_base]]["file"].nunique()
        rows.append({
            "method":           m.upper(),
            "total_elections":  total_elections,
            "elections_w_flip": n,
            "pct_elections":    round(100 * n / total_elections, 1) if total_elections else 0,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2. Do ties lead to different winners?
# ---------------------------------------------------------------------------

def section_tie_divergence(df: pd.DataFrame) -> pd.DataFrame:
    """
    Among rows that have a tie_path, check whether fork branches produced
    different winners. Groups by (file, candidate_cloned, percent).
    """
    rows = []
    for m in METHODS:
        tie_rows = df[df[f"{m}_tie_path"] != ""].copy()
        if tie_rows.empty:
            continue
        grp = (
            tie_rows.groupby(["file", "candidate_cloned", "percent"])[m]
            .agg(list)
            .reset_index()
        )
        grp["unique_winners"] = grp[m].apply(lambda ws: sorted(set(ws)))
        grp["diverges"]       = grp["unique_winners"].apply(lambda u: len(u) > 1)
        grp["method"]         = m.upper()
        grp = grp.drop(columns=[m])
        rows.append(grp)

    if not rows:
        return pd.DataFrame()
    return (
        pd.concat(rows, ignore_index=True)
        .sort_values(["method", "diverges", "percent", "file"], ascending=[True, False, True, True])
        .reset_index(drop=True)
    )


def summary_tie_divergence(tie_div: pd.DataFrame) -> pd.DataFrame:
    if tie_div.empty:
        return pd.DataFrame()
    return (
        tie_div.groupby("method")
        .agg(
            total_tie_groups=("diverges", "count"),
            groups_that_diverge=("diverges", "sum"),
        )
        .assign(pct_diverge=lambda d: (100 * d["groups_that_diverge"] / d["total_tie_groups"]).round(1))
        .reset_index()
    )


# ---------------------------------------------------------------------------
# 3. Threshold effect
# ---------------------------------------------------------------------------

def section_threshold_effect(cloned: pd.DataFrame) -> pd.DataFrame:
    """Per (method, percent): how many elections flip at that percent."""
    rows = []
    for m in METHODS:
        col_base = f"{m}_baseline"
        for pct, grp in cloned.groupby("percent"):
            n     = grp[grp[m] != grp[col_base]]["file"].nunique()
            total = grp["file"].nunique()
            rows.append({
                "method":           m.upper(),
                "percent":          pct,
                "elections_w_flip": n,
                "total_elections":  total,
                "pct_elections":    round(100 * n / total, 1) if total else 0,
            })
    return pd.DataFrame(rows).sort_values(["method", "percent"])


def section_first_flip_percent(cloned: pd.DataFrame) -> pd.DataFrame:
    """Per (election, method): the lowest percent at which a flip first appears."""
    rows = []
    for m in METHODS:
        col_base = f"{m}_baseline"
        changed = cloned[cloned[m] != cloned[col_base]]
        if changed.empty:
            continue
        first = (
            changed.groupby("file")["percent"]
            .min()
            .rename("first_flip_percent")
            .reset_index()
        )
        first["method"] = m.upper()
        rows.append(first)
    if not rows:
        return pd.DataFrame()
    return (
        pd.concat(rows, ignore_index=True)
        .sort_values(["method", "first_flip_percent", "file"])
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# 4. Clone outcome split per threshold
# ---------------------------------------------------------------------------

def section_clone_outcome_split(cloned: pd.DataFrame) -> pd.DataFrame:
    """
    For each (method, percent), among rows where cloning flipped the winner:
      - clone_wins:   the Clone candidate itself is the new winner
      - spoiler_wins: cloning changed the winner but to a different real candidate
                      (the clone disrupted without winning)

    Reported as counts and percentages of all flips at that threshold.
    """
    rows = []
    for m in METHODS:
        col_base = f"{m}_baseline"
        changed = cloned[cloned[m] != cloned[col_base]].copy()
        changed["clone_wins"]   = changed[m] == "Clone"
        changed["spoiler_wins"] = ~changed["clone_wins"]

        for pct, grp in changed.groupby("percent"):
            total       = len(grp)
            clone_wins  = grp["clone_wins"].sum()
            spoiler_wins = grp["spoiler_wins"].sum()
            rows.append({
                "method":           m.upper(),
                "percent":          pct,
                "total_flips":      total,
                "clone_wins":       int(clone_wins),
                "spoiler_wins":     int(spoiler_wins),
                "pct_clone_wins":   round(100 * clone_wins  / total, 1) if total else 0,
                "pct_spoiler_wins": round(100 * spoiler_wins / total, 1) if total else 0,
            })
    return pd.DataFrame(rows).sort_values(["method", "percent"]) if rows else pd.DataFrame()


# ---------------------------------------------------------------------------
# 5. Method agreement
# ---------------------------------------------------------------------------

def section_method_agreement(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Do OM / AVG / PM agree on the winner? Per election and overall."""
    df = df.copy()
    df["all_agree"] = (df["om"] == df["avg"]) & (df["avg"] == df["pm"])
    df["om_avg"]    = df["om"] == df["avg"]
    df["om_pm"]     = df["om"] == df["pm"]
    df["avg_pm"]    = df["avg"] == df["pm"]

    per_election = (
        df.groupby(["file", "percent"])
        .agg(
            rows=("all_agree", "count"),
            all_agree_pct=("all_agree",  lambda s: round(100 * s.mean(), 1)),
            om_avg_agree_pct=("om_avg",  lambda s: round(100 * s.mean(), 1)),
            om_pm_agree_pct=("om_pm",    lambda s: round(100 * s.mean(), 1)),
            avg_pm_agree_pct=("avg_pm",  lambda s: round(100 * s.mean(), 1)),
        )
        .reset_index()
    )
    per_election = per_election[per_election["all_agree_pct"] == 100].reset_index(drop=True)

    overall = pd.DataFrame([{
        "all_agree_pct":    round(100 * df["all_agree"].mean(), 1),
        "om_avg_agree_pct": round(100 * df["om_avg"].mean(), 1),
        "om_pm_agree_pct":  round(100 * df["om_pm"].mean(), 1),
        "avg_pm_agree_pct": round(100 * df["avg_pm"].mean(), 1),
    }])

    return per_election, overall


# ---------------------------------------------------------------------------
# Summary JSON
# ---------------------------------------------------------------------------

def build_summary_json(df: pd.DataFrame, cloned: pd.DataFrame) -> dict:
    """Compact summary statistics for quick inspection."""
    summary = {
        "dataset": {
            "total_rows":       int(len(df)),
            "unique_elections": int(df["file"].nunique()),
            "percents_tested":  sorted(df["percent"].unique().tolist()),
        },
        "clone_induced_flips": {},
        "tie_divergence":      {},
        "threshold_effect":    {},
        "clone_outcome_split": {},
        "method_agreement":    {},
    }

    # flip summary
    sc = summary_clone_changes(cloned)
    for _, row in sc.iterrows():
        summary["clone_induced_flips"][row["method"]] = {
            "elections_with_flip": int(row["elections_w_flip"]),
            "total_elections":     int(row["total_elections"]),
            "pct_elections":       float(row["pct_elections"]),
        }

    # tie divergence
    tie_div = section_tie_divergence(df)
    std = summary_tie_divergence(tie_div)
    if not std.empty:
        for _, row in std.iterrows():
            summary["tie_divergence"][row["method"]] = {
                "total_tie_groups":    int(row["total_tie_groups"]),
                "groups_that_diverge": int(row["groups_that_diverge"]),
                "pct_diverge":         float(row["pct_diverge"]),
            }

    # threshold effect
    te = section_threshold_effect(cloned)
    for _, row in te.iterrows():
        key = f"{row['method']}_{row['percent']}"
        summary["threshold_effect"][key] = {
            "elections_w_flip": int(row["elections_w_flip"]),
            "pct_elections":    float(row["pct_elections"]),
        }

    # clone outcome split
    cos = section_clone_outcome_split(cloned)
    if not cos.empty:
        for _, row in cos.iterrows():
            key = f"{row['method']}_{row['percent']}"
            summary["clone_outcome_split"][key] = {
                "total_flips":      int(row["total_flips"]),
                "clone_wins":       int(row["clone_wins"]),
                "spoiler_wins":     int(row["spoiler_wins"]),
                "pct_clone_wins":   float(row["pct_clone_wins"]),
                "pct_spoiler_wins": float(row["pct_spoiler_wins"]),
            }

    # method agreement
    _, overall = section_method_agreement(df)
    summary["method_agreement"] = overall.iloc[0].to_dict()

    return summary


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def _hdr(title: str):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

def _sub(title: str):
    print(f"\n--- {title} ---")


def print_report(df: pd.DataFrame, cloned: pd.DataFrame):
    baseline, _ = split(df)

    _hdr("DATASET OVERVIEW")
    print(f"  Total rows:       {len(df):,}")
    print(f"  Unique elections: {df['file'].nunique():,}")
    print(f"  Percents tested:  {sorted(df['percent'].unique().tolist())}")

    _hdr("1. CLONE-INDUCED WINNER CHANGES")
    _sub("Summary: elections with at least one flip")
    print(summary_clone_changes(cloned).to_string(index=False))
    change_detail = section_clone_changes(cloned)
    for m, detail in change_detail.items():
        _sub(f"{m.upper()} — per-election flip detail")
        print("  None." if detail.empty else detail.to_string(index=False))

    _hdr("2. DO TIES LEAD TO DIFFERENT WINNERS?")
    tie_div = section_tie_divergence(df)
    _sub("Summary")
    print(summary_tie_divergence(tie_div).to_string(index=False))
    _sub("Cases where fork branches diverged")
    diverged = tie_div[tie_div["diverges"]] if not tie_div.empty else pd.DataFrame()
    if diverged.empty:
        print("  No divergence detected.")
    else:
        print(diverged[["method", "file", "candidate_cloned", "percent", "unique_winners"]].to_string(index=False))

    _hdr("3. EFFECT OF CLONE PERCENT THRESHOLD")
    _sub("Flips per percent level")
    print(section_threshold_effect(cloned).to_string(index=False))
    _sub("Lowest percent at which a flip first appears (per election)")
    ffp = section_first_flip_percent(cloned)
    print("  None." if ffp.empty else ffp.to_string(index=False))

    _hdr("4. CLONE OUTCOME SPLIT PER THRESHOLD")
    cos = section_clone_outcome_split(cloned)
    _sub("For each (method, percent): clone wins vs spoiler wins among flips")
    print("  No flips." if cos.empty else cos.to_string(index=False))

    _hdr("5. METHOD AGREEMENT (OM / AVG / PM)")
    _, overall = section_method_agreement(df)
    print(overall.to_string(index=False))


# ---------------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------------

def section_flip_detail(cloned: pd.DataFrame) -> pd.DataFrame:
    """
    Every row where cloning flipped the winner, showing:
      file, candidate_cloned, percent, method, baseline_winner, new_winner
    Sorted by file, method, percent.
    """
    rows = []
    for m in METHODS:
        col_base = f"{m}_baseline"
        changed = cloned[cloned[m] != cloned[col_base]].copy()
        if changed.empty:
            continue
        changed = changed[["file", "candidate_cloned", "percent", col_base, m]].copy()
        changed.rename(columns={col_base: "baseline_winner", m: "new_winner"}, inplace=True)
        changed["method"] = m.upper()
        rows.append(changed)

    if not rows:
        return pd.DataFrame()
    return (
        pd.concat(rows, ignore_index=True)
        [["file", "method", "candidate_cloned", "percent", "baseline_winner", "new_winner"]]
        .sort_values(["method", "file", "percent"])
        .reset_index(drop=True)
    )


def save_outputs(df: pd.DataFrame, cloned: pd.DataFrame, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    summary_clone_changes(cloned).to_csv(f"{out_dir}/01_flip_summary.csv", index=False)
    section_threshold_effect(cloned).to_csv(f"{out_dir}/02_threshold_effect.csv", index=False)
    section_first_flip_percent(cloned).to_csv(f"{out_dir}/03_first_flip_percent.csv", index=False)
    section_tie_divergence(df).to_csv(f"{out_dir}/04_tie_divergence.csv", index=False)
    section_clone_outcome_split(cloned).to_csv(f"{out_dir}/05_clone_outcome_split.csv", index=False)
    per_election, overall = section_method_agreement(df)
    per_election.to_csv(f"{out_dir}/06_method_agreement_per_election.csv", index=False)
    overall.to_csv(f"{out_dir}/07_method_agreement_overall.csv", index=False)

    summary = build_summary_json(df, cloned)
    with open(f"{out_dir}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    section_flip_detail(cloned).to_csv(f"{out_dir}/08_flip_detail.csv", index=False)

    print(f"\nOutputs saved to {out_dir}/")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else RESULTS_FILE
    print(f"Loading {path} ...")

    raw = load(path)
    baseline, cloned_raw = split(raw)

    # Apply trivial-result filter to cloned rows only
    cloned = filter_trivial(cloned_raw, baseline)
    print(f"  Cloned rows before filter: {len(cloned_raw):,}")
    print(f"  Cloned rows after filter:  {len(cloned):,} "
          f"({len(cloned_raw) - len(cloned):,} trivial rows removed)")

    # Re-attach baselines after filtering (filter_trivial adds them, so already there)
    # Rebuild a combined df for tie analysis (baseline + filtered cloned)
    df = pd.concat([baseline, cloned], ignore_index=True)

    print_report(df, cloned)
    save_outputs(df, cloned, OUTPUT_DIR)