import sys
import os
import pandas as pd
from fractions import Fraction
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from tqdm.contrib.concurrent import process_map
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import Diversity.comparison.run_diversity as rd
from votekit import Ballot, PreferenceProfile

#CHANGE FILE NAME HERE
DATA_FILE  = '/Users/belle/Desktop/build/condorcet_analysis/Data/cycle_ballot_type_counts.csv'
WIDE_RESULTS_FILE = 'condorcet_simulations.csv'

def _is_ballot_col(col: str) -> bool:
    return col.isalpha() and col.isupper() and len(col) >= 2

# process ballot into preference profile
def load_profile_from_row(row, ballot_cols):
    ballots = []
    for col in ballot_cols:
        count = row[col]
        if pd.isna(count) or int(count) <= 0:
            continue

        ranking = tuple(frozenset({c}) for c in col)
        ballots.append(Ballot(ranking=ranking, weight=Fraction(int(count))))

    if not ballots:
        return None
    return PreferenceProfile(ballots=tuple(ballots))

def process_election_task(row_data, thresholds, ballot_cols):
    index, row = row_data
    election_id = row.get('election_id', f"row_{index}")
    rd.logger.info(f"RUNNING election {election_id}")
        
    vprofile = load_profile_from_row(row, ballot_cols)
    if not vprofile: return None

    candidates = [c for c in vprofile.candidates if c not in ('skipped', 'writein', 'Write-in')]
    rd.logger.info(f"candidates: {candidates}")
    if not candidates: return None

    winners = []
    for t in thresholds:
        winner, _ = rd.main_helper(vprofile, candidates.copy(), t)
        winners.append(str(winner))
    
    return f"{election_id}," + ",".join(winners) + "\n"

def run_all_slow(filepath, thresholds):
    df = pd.read_csv(filepath)
    ballot_cols = [c for c in df.columns if _is_ballot_col(c)]
    
    header = "election_id," + ",".join([str(t) for t in thresholds]) + "\n"
    with open(WIDE_RESULTS_FILE, 'w') as f:
        f.write(header)

    print(f"Running diversity experiment")
    
    results = []
    for index_row_tuple in tqdm(list(df.iterrows()), total=len(df), desc="Elections"):
        csv_row = process_election_task(index_row_tuple, thresholds=thresholds, ballot_cols=ballot_cols)
        if csv_row:
            with open(WIDE_RESULTS_FILE, 'a') as f:
                f.write(csv_row)

    return len(results)

def run_all(filepath, thresholds):
    df = pd.read_csv(filepath)
    ballot_cols = [c for c in df.columns if _is_ballot_col(c)]
    
    header = "election_id," + ",".join([str(t) for t in thresholds]) + "\n"
    with open(WIDE_RESULTS_FILE, 'w') as f:
        f.write(header)

    tasks = list(df.iterrows())
    
    worker_func = partial(process_election_task, thresholds=thresholds, ballot_cols=ballot_cols)

    print(f"Running diversity experiment")
    results = process_map(worker_func, tasks, chunksize=5, desc="Elections")

    with open(WIDE_RESULTS_FILE, 'a') as f:
        for csv_row in results:
            if csv_row:
                f.write(csv_row)

    return len([r for r in results if r is not None])

if __name__ == '__main__':
    # 0.000 to 0.099
    THRESHOLDS = [i / 100 for i in range(10)] 

    if not os.path.exists(DATA_FILE):
        print(f"Error: '{DATA_FILE}' not found.")
        sys.exit(1)

    total = run_all_slow(DATA_FILE, thresholds=THRESHOLDS)
    print(f"\nDone! {total} experiments run and saved to {WIDE_RESULTS_FILE}")