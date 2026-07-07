# TVR Cloning Analysis

## Overview

This analysis examines how inserting a **Clone** candidate next to a real candidate affects who wins under three Borda-based TVR (Total Variation Ratio) voting methods: **OM**, **AVG**, and **PM**.

The core question is: does adding a near-identical candidate (Clone) change election outcomes, and if so, how?

---

## Filtering Rule

One class of results is automatically excluded before any analysis:

> Rows where **percent == 0.5** and the **original winner == candidate_cloned**.

At 50% clone placement, half the ballots rank the Clone *above* the original winner. When the original winner was going to win anyway, the Clone displacing them is a guaranteed mathematical artifact — not a meaningful sensitivity result. These rows are removed to avoid inflating flip counts.

---

## Input Data

`tvr_cloning_tests.csv` is produced by `run_tvr.py`. Each row represents one (election, cloned candidate, clone placement percent, fork branch) combination.

Key columns:

| Column | Meaning |
|---|---|
| `file` | Election filename — one unique election per filename |
| `candidate_cloned` | Which real candidate the Clone was inserted next to. `none` = baseline (no clone) |
| `percent` | Fraction of ballots where Clone is placed *before* the cloned candidate (0.0–0.5) |
| `numCands` | Number of candidates in the election (excluding skipped/writein) |
| `om` / `avg` / `pm` | Winner under each method for this row |
| `om_tie_path` etc. | Fork decisions taken when a bottom tie occurred (empty if no tie) |
| `om_tie_dropped` etc. | Just the sequence of candidates dropped to resolve ties |

**Baseline rows**: rows where `candidate_cloned == none`. These represent the original election with no Clone inserted, and are the reference point for all flip comparisons.

**Tie forks**: when two candidates tie for last place during elimination, the algorithm forks — it runs both possible eliminations and records each as a separate row. All rows from the same fork group share the same (file, candidate_cloned, percent) but differ in tie_path.

---

## Output Files

### `01_flip_summary.csv`
Per method: how many elections had at least one clone-induced flip (across any candidate or percent).

- `elections_w_flip`: count of unique elections where the winner changed
- `pct_elections`: what fraction of all elections this represents

### `02_threshold_effect.csv`
Per (method, percent): how many elections flip *at that specific percent level*.

Use this to understand whether cloning needs to be strong (high %) to matter, or whether even weak cloning (low %) changes outcomes.

### `03_first_flip_percent.csv`
Per (election, method): the **minimum percent** at which a flip first appeared in that election.

A low value (e.g. 0.1) means that election is highly sensitive — even a weak clone disrupts the outcome. A high value (e.g. 0.4) means the election is robust until clone placement is quite aggressive.

### `04_tie_divergence.csv`
For every group of tie-fork branches (same election, same clone, same percent, different tie resolution), records whether the branches produced different winners.

- `diverges = True`: the tie resolution mattered — different dropped candidates led to different winners
- `diverges = False`: the tie was inconsequential — all branches agreed on the winner

### `05_clone_outcome_split.csv`
Per (method, percent), among rows where a flip occurred:

- `clone_wins`: the Clone itself became the winner (the original winner was displaced *by the Clone*)
- `spoiler_wins`: a *different* real candidate won (Clone disrupted the original winner without winning itself — classic spoiler effect)
- `pct_clone_wins` / `pct_spoiler_wins`: breakdown of the two types as a percentage of all flips at that threshold

This is the main table for understanding the *nature* of clone influence. A high `pct_spoiler_wins` means cloning is primarily a spoiler mechanism rather than a direct path to winning.

### `06_method_agreement_per_election.csv`
Per (election, percent): pairwise and joint agreement rates between the three methods.

- `all_agree_pct`: % of rows in this group where OM, AVG, and PM all chose the same winner
- `om_avg_agree_pct`, `om_pm_agree_pct`, `avg_pm_agree_pct`: pairwise rates

### `07_method_agreement_overall.csv`
Same as above but collapsed to a single row across all elections and percents.

### `summary.json`
Machine-readable summary of all key statistics in one place. Useful for automated reporting or quick inspection without opening CSVs. Structure mirrors the five analysis sections.

---

## Interpreting Results

**"Is cloning a real threat?"**
→ Look at `01_flip_summary.csv`. If `pct_elections` is high across methods, clone insertion frequently changes outcomes.

**"Does it matter how aggressively the clone is placed?"**
→ Look at `02_threshold_effect.csv`. If flips are concentrated at high percents (0.4–0.5), outcomes are only sensitive to strong clones. If flips appear at 0.1–0.2, elections are fragile.

**"Are ties consequential or just noise?"**
→ Look at `04_tie_divergence.csv`. If most `diverges` values are False, tie-breaking order rarely changes who wins. If many are True, tie resolution is a meaningful source of ambiguity.

**"Does the Clone actually win, or does it just spoil?"**
→ Look at `05_clone_outcome_split.csv`. A high `pct_spoiler_wins` means cloning is primarily disruptive rather than a viable strategy to get the Clone elected.

**"Do the three methods agree?"**
→ Look at `07_method_agreement_overall.csv`. High agreement means the methods are largely interchangeable. Low agreement suggests the choice of method is itself consequential.