"""
Runs the raw-index Borda_PM(profile, cands) function against a wide-format
ballot CSV, using csv_to_profile.py to do the conversion.

Usage:
    python run_borda_pm_test.py <path_to_ballot_csv>
"""

import sys
import pandas as pd

def csv_to_borda_profile(filepath: str):
    """
    Read a wide-format ballot CSV and convert it into a profile DataFrame.
 
    Supports both:
      - Aggregated files (has a 'Count' column: one row = many identical ballots)
      - Per-voter files (no 'Count' column: one row = one ballot, weight = 1)
 
    Returns:
        profile    - DataFrame with columns ['Count', 'ballot'], where 'ballot'
                     is a list of rank-column values IN ORIGINAL ORDER,
                     'skipped' entries included and NOT removed.
        candidates - sorted list of all real (non-'skipped') candidate names
                     found anywhere in the file.
    """
    df = pd.read_csv(filepath)
    rank_cols = [c for c in df.columns if c.lower().startswith('rank')]
    count_col = next((c for c in df.columns if c.lower() == 'count'), None)
 
    if not rank_cols:
        raise ValueError(f"No rank columns found in {filepath}")
 
    # Collect every real candidate name that appears anywhere
    all_candidates = set()
    for col in rank_cols:
        for val in df[col].dropna():
            v = str(val).strip()
            if v.lower() != 'skipped':
                all_candidates.add(v)
 
    rows = []
    for _, row in df.iterrows():
        count = int(row[count_col]) if count_col and pd.notna(row[count_col]) else 1
        ballot = []
        for col in rank_cols:
            val = str(row[col]).strip() if pd.notna(row[col]) else 'skipped'
            ballot.append(val if val.lower() != 'skipped' else 'skipped')
        rows.append({'Count': count, 'ballot': ballot})
 
    profile = pd.DataFrame(rows)
    return profile, sorted(all_candidates)

def Borda_PM(profile, cands, diagnostic=False):
    num_cands = len(cands)
    max_score = num_cands - 1

    cand_scores = {cand: 0 for cand in cands}
    for k in range(len(profile)):
        count = profile.at[k, 'Count']
        curBal = profile.at[k, 'ballot']
        for i in range(0, len(curBal)):
            candidate = curBal[i]
            if candidate in cands:
                cand_scores[candidate] += (max_score - i) * count
            # else:
            #     print("Candidate in ballot that is not in candidate list")

    if diagnostic:
        print(cand_scores)

    max_score_val = max(cand_scores.values())
    winners = [cand for cand, score in cand_scores.items() if score == max_score_val]
    return cand_scores, [winners]


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_borda_pm_test.py <path_to_ballot_csv>")
        sys.exit(1)

    filepath = sys.argv[1]
    profile, candidates = csv_to_borda_profile(filepath)

    print(f"File: {filepath}")
    print(f"Candidates ({len(candidates)}): {candidates}")
    print(f"Total ballots: {profile['Count'].sum()}")
    print()

    scores, winners = Borda_PM(profile, candidates)

    print("Borda_PM scores:")
    for c, s in sorted(scores.items(), key=lambda x: -x[1]):
        print(f"  {c}: {s}")
    print()
    print("Winner(s):", winners[0])


if __name__ == '__main__':
    main()