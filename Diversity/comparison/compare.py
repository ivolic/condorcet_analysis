import sys
import os
import json
import pandas as pd
from fractions import Fraction
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from tqdm.contrib.concurrent import process_map
from tqdm import tqdm
from run_tvr import run_tvr
from run_diversity import run_diversity
sys.path.append('/Users/belle/Desktop/build/rcv')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import main_methods as mm
from votekit import Ballot, PreferenceProfile
import logging

logging.basicConfig(
    filename='condorcet.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

# CHANGE FILE NAME HERE
DATA_FILE = '/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/data/condorcet_sampling_hits_Australia_STV.json'
WIDE_RESULTS_FILE = 'condorcet_simulations.csv'

# Each entry: (column_name, callable)
METHODS = [
    ('plurality',       lambda p: list(mm.Plurality(prof=p))),
    ('IRV',             lambda p: list(mm.IRV(prof=p))),
    ('top-two',         lambda p: list(mm.TopTwo(prof=p))),
    ('borda-pm',        lambda p: list(mm.Borda_PM(p, tiebreak="first_place"))),
    ('borda-om',        lambda p: list(mm.Borda_OM(p, tiebreak="first_place"))),
    ('borda-avg',       lambda p: list(mm.Borda_AVG(p, tiebreak="first_place"))),
    ('top-3-truncation',lambda p: list(mm.Top3Truncation(prof=p))),
    ('condorcet',       lambda p: list(mm.Condorcet(prof=p))),
    ('minimax',         lambda p: list(mm.Minimax(prof=p))),
    ('smith-plurality', lambda p: list(mm.Smith_Plurality(prof=p))),
    ('smith-irv',       lambda p: list(mm.Smith_IRV(prof=p))),
    ('smith-minimax',   lambda p: list(mm.Smith_Minimax(prof=p))),
    ('ranked-pairs',    lambda p: list(mm.Ranked_Pairs(prof=p))),
    ('bucklin',         lambda p: list(mm.Bucklin(prof=p))),
    ('smith',           lambda p: list(mm.Smith(prof=p))),
    ('tvr-om',          lambda p: (run_tvr(p, "OM", logger))),
    ('tvr-avg',         lambda p: (run_tvr(p, "AVG", logger))),
    ('tvr-pm',          lambda p: (run_tvr(p, "PM", logger))),
    ('diversity-0',     lambda p: (run_diversity(p, 0)[0])),
    ('diversity-1',     lambda p: (run_diversity(p, 0.01)[0])),
    ('diversity-2',     lambda p: (run_diversity(p, 0.02)[0])),
    ('diversity-3',     lambda p: (run_diversity(p, 0.03)[0])),
    ('diversity-4',     lambda p: (run_diversity(p, 0.04)[0])),
    ('diversity-5',     lambda p: (run_diversity(p, 0.05)[0])),
    ('diversity-6',     lambda p: (run_diversity(p, 0.06)[0])),
    ('diversity-7',     lambda p: (run_diversity(p, 0.07)[0])),
    ('diversity-8',     lambda p: (run_diversity(p, 0.08)[0])),
    ('diversity-9',     lambda p: (run_diversity(p, 0.09)[0])),
    ('diversity-10',    lambda p: (run_diversity(p, 0.1)[0])),
]

METHOD_NAMES = [name for name, _ in METHODS]


def load_profile_from_hit(hit: dict, candidate_map: dict) -> PreferenceProfile | None:
    """
    Convert a single hit's profile dict into a PreferenceProfile.
    Keys like "A>B>C" map to vote counts; candidate_map maps letter -> full name.
    """
    ballots = []
    profile = hit.get("profile", {})

    for ballot_str, count in profile.items():
        if not count or int(count) <= 0:
            continue
        ranking = tuple(frozenset({candidate_map[c.strip()]}) for c in ballot_str.split(">"))
        ballots.append(Ballot(ranking=ranking, weight=Fraction(int(count))))

    if not ballots:
        return None
    return PreferenceProfile(ballots=tuple(ballots))


def process_election_task(task_data, candidate_map):
    """
    task_data is a tuple: (election_name, hit_index, hit)
    """
    election_name, hit_index, hit = task_data
    election_id = f"{election_name}__hit{hit_index}"

    vprofile = load_profile_from_hit(hit, candidate_map)
    if not vprofile:
        return None

    candidates = [c for c in vprofile.candidates if c not in ('skipped', 'writein', 'Write-in')]
    if not candidates:
        return None

    results = []
    for method_name, method_fn in METHODS:
        try:
            winner = method_fn(vprofile)
            results.append("\"" + str(winner) + "\"")
        except Exception as e:
            results.append("TIED")

    return f"{election_id}," + ",".join(results) + "\n"


def build_tasks(data: list) -> list:
    """Flatten all elections x hits into a list of (election_name, hit_index, hit, candidate_map) tuples."""
    tasks = []
    for election in data:
        election_name = election.get("election_name", "unknown")
        candidate_map = election.get("candidate_map", {})
        for hit_index, hit in enumerate(election.get("hits", [])):
            tasks.append((election_name, hit_index, hit, candidate_map))
    return tasks


def process_election_task(task_data):
    """
    task_data is a tuple: (election_name, hit_index, hit, candidate_map)
    """
    election_name, hit_index, hit, candidate_map = task_data
    election_id = f"{election_name}__hit{hit_index}"

    vprofile = load_profile_from_hit(hit, candidate_map)
    if not vprofile:
        return None

    candidates = [c for c in vprofile.candidates if c not in ('skipped', 'writein', 'Write-in')]
    if not candidates:
        return None

    results = []
    for method_name, method_fn in METHODS:
        try:
            winner = method_fn(vprofile)
            results.append("\"" + str(winner) + "\"")
        except Exception as e:
            results.append("TIED")

    return f"{election_id}," + ",".join(results) + "\n"


def run_all_slow(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)

    tasks = build_tasks(data)

    header = "election_id," + ",".join(METHOD_NAMES) + "\n"
    with open(WIDE_RESULTS_FILE, 'w') as f:
        f.write(header)

    print(f"Running methods: {METHOD_NAMES}")

    results = []
    for task in tqdm(tasks, desc="Elections"):
        csv_row = process_election_task(task)
        if csv_row:
            with open(WIDE_RESULTS_FILE, 'a') as f:
                f.write(csv_row)
            results.append(csv_row)

    return len(results)


def run_all(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)

    tasks = build_tasks(data)

    header = "election_id," + ",".join(METHOD_NAMES) + "\n"
    with open(WIDE_RESULTS_FILE, 'w') as f:
        f.write(header)

    print(f"Running methods: {METHOD_NAMES}")
    results = process_map(process_election_task, tasks, chunksize=5, desc="Elections")

    with open(WIDE_RESULTS_FILE, 'a') as f:
        for csv_row in results:
            if csv_row:
                f.write(csv_row)

    return len([r for r in results if r is not None])


if __name__ == '__main__':
    if not os.path.exists(DATA_FILE):
        print(f"Error: '{DATA_FILE}' not found.")
        sys.exit(1)

    total = run_all(DATA_FILE)
    print(f"\nDone! {total} experiments run and saved to {WIDE_RESULTS_FILE}")

# import sys
# import os
# import pandas as pd
# from fractions import Fraction
# from concurrent.futures import ProcessPoolExecutor
# from functools import partial
# from tqdm.contrib.concurrent import process_map
# from tqdm import tqdm
# from run_tvr import run_tvr
# from run_diversity import run_diversity
# sys.path.append('/Users/belle/Desktop/build/rcv')
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# import main_methods as mm
# from votekit import Ballot, PreferenceProfile
# import logging

# logging.basicConfig(
#     filename='condorcet.log',
#     level=logging.INFO,
#     format='%(asctime)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# )
# logger = logging.getLogger()

# # CHANGE FILE NAME HERE
# DATA_FILE = '/Users/belle/Desktop/build/condorcet_analysis/Data/OtherData/cycle_ballot_type_counts.csv'
# WIDE_RESULTS_FILE = 'condorcet_simulations.csv'

# # Each entry: (column_name, callable)
# # Add or remove methods here as needed
# METHODS = [
#     ('plurality',       lambda p: list(mm.Plurality(prof=p))),
#     ('IRV',             lambda p: list(mm.IRV(prof=p))),
#     ('top-two',         lambda p: list(mm.TopTwo(prof=p))),
#     ('borda-pm',        lambda p: list(mm.Borda_PM(p, tiebreak="first_place"))),
#     ('borda-om',        lambda p: list(mm.Borda_OM(p, tiebreak="first_place"))),
#     ('borda-avg',       lambda p: list(mm.Borda_AVG(p, tiebreak="first_place"))),
#     ('top-3-truncation',lambda p: list(mm.Top3Truncation(prof=p))),
#     ('condorcet',       lambda p: list(mm.Condorcet(prof=p))),
#     ('minimax',         lambda p: list(mm.Minimax(prof=p))),
#     ('smith-plurality', lambda p: list(mm.Smith_Plurality(prof=p))),
#     ('smith-irv',       lambda p: list(mm.Smith_IRV(prof=p))),
#     ('smith-minimax',   lambda p: list(mm.Smith_Minimax(prof=p))),
#     ('ranked-pairs',    lambda p: list(mm.Ranked_Pairs(prof=p))),
#     ('bucklin',         lambda p: list(mm.Bucklin(prof=p))),
#     ('smith',           lambda p: list(mm.Smith(prof=p))),
#     ('tvr-om',       lambda p: list(run_tvr(p, "OM", logger))),
#     ('tvr-avg', lambda p: list(run_tvr(p, "AVG", logger))),
#     ('tvr-pm', lambda p: list(run_tvr(p, "PM", logger))),
#     ('diversity-0', lambda p: list(run_diversity(p, 0)[0])),
#     ('diversity-1', lambda p: list(run_diversity(p, 0.01)[0])),
#     ('diversity-2', lambda p: list(run_diversity(p, 0.02)[0])),
#     ('diversity-3', lambda p: list(run_diversity(p, 0.03)[0])),
#     ('diversity-4', lambda p: list(run_diversity(p, 0.04)[0])),
#     ('diversity-5', lambda p: list(run_diversity(p, 0.05)[0])),
#     ('diversity-6', lambda p: list(run_diversity(p, 0.06)[0])),
#     ('diversity-7', lambda p: list(run_diversity(p, 0.07)[0])),
#     ('diversity-8', lambda p: list(run_diversity(p, 0.08)[0])),
#     ('diversity-9', lambda p: list(run_diversity(p, 0.09)[0])),
#     ('diversity-10', lambda p: list(run_diversity(p, 0.1)[0])),
# ]

# METHOD_NAMES = [name for name, _ in METHODS]


# def _is_ballot_col(col: str) -> bool:
#     return col.isalpha() and col.isupper() and len(col) >= 2


# def load_profile_from_row(row, ballot_cols):
#     ballots = []
#     for col in ballot_cols:
#         count = row[col]
#         if pd.isna(count) or int(count) <= 0:
#             continue
#         ranking = tuple(frozenset({c}) for c in col)
#         ballots.append(Ballot(ranking=ranking, weight=Fraction(int(count))))

#     if not ballots:
#         return None
#     return PreferenceProfile(ballots=tuple(ballots))


# def process_election_task(row_data, ballot_cols):
#     index, row = row_data
#     election_id = row.get('election_id', f"row_{index}")

#     vprofile = load_profile_from_row(row, ballot_cols)
#     if not vprofile:
#         return None

#     candidates = [c for c in vprofile.candidates if c not in ('skipped', 'writein', 'Write-in')]
#     if not candidates:
#         return None

#     results = []
#     for method_name, method_fn in METHODS:
#         try:
#             winner = method_fn(vprofile)
#             results.append("\"" + str(winner) + "\"")
#         except Exception as e:
#             results.append(f"TIED")

#     return f"{election_id}," + ",".join(results) + "\n"


# def run_all_slow(filepath):
#     df = pd.read_csv(filepath)
#     ballot_cols = [c for c in df.columns if _is_ballot_col(c)]

#     header = "election_id," + ",".join(METHOD_NAMES) + "\n"
#     with open(WIDE_RESULTS_FILE, 'w') as f:
#         f.write(header)

#     print(f"Running methods: {METHOD_NAMES}")

#     results = []
#     for index_row_tuple in tqdm(list(df.iterrows()), total=len(df), desc="Elections"):
#         csv_row = process_election_task(index_row_tuple, ballot_cols=ballot_cols)
#         if csv_row:
#             with open(WIDE_RESULTS_FILE, 'a') as f:
#                 f.write(csv_row)
#             results.append(csv_row)

#     return len(results)


# def run_all(filepath):
#     df = pd.read_csv(filepath)
#     ballot_cols = [c for c in df.columns if _is_ballot_col(c)]

#     header = "election_id," + ",".join(METHOD_NAMES) + "\n"
#     with open(WIDE_RESULTS_FILE, 'w') as f:
#         f.write(header)

#     tasks = list(df.iterrows())

#     worker_func = partial(process_election_task, ballot_cols=ballot_cols)

#     print(f"Running methods: {METHOD_NAMES}")
#     results = process_map(worker_func, tasks, chunksize=5, desc="Elections")

#     with open(WIDE_RESULTS_FILE, 'a') as f:
#         for csv_row in results:
#             if csv_row:
#                 f.write(csv_row)

#     return len([r for r in results if r is not None])


# if __name__ == '__main__':
#     if not os.path.exists(DATA_FILE):
#         print(f"Error: '{DATA_FILE}' not found.")
#         sys.exit(1)

#     total = run_all_slow(DATA_FILE)
#     print(f"\nDone! {total} experiments run and saved to {WIDE_RESULTS_FILE}")