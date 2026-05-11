import sys
import os
import json
import pandas as pd
from fractions import Fraction
from functools import partial
from tqdm.contrib.concurrent import process_map
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import run_diversity as rd
from votekit import Ballot, PreferenceProfile

# TODO: CHANGE THIS
DATA_FILE = '/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/data/condorcet_sampling_hits_USA.json'
RESULTS_FILE = 'diversity_simulations_usa.csv'


def load_profile_from_hit(hit: dict, candidate_map: dict) -> PreferenceProfile | None:
    """
    Convert a single hit's profile dict into a PreferenceProfile.
    Keys like "A>B>C" become ranked ballots; values are vote counts.
    candidate_map maps letter -> full name (unused in ranking, but available).
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


def process_election_task(task_data, thresholds):
    """
    task_data is a tuple: (election_name, hit_index, hit, candidate_map)
    Returns a CSV row string or None.
    """
    election_name, hit_index, hit, candidate_map = task_data
    election_id = f"{election_name}__hit{hit_index}"
    rd.logger.info(f"RUNNING election {election_id}")

    vprofile = load_profile_from_hit(hit, candidate_map)
    if not vprofile:
        return None

    candidates = [
        c for c in vprofile.candidates
        if c not in ('skipped', 'writein', 'Write-in')
    ]
    rd.logger.info(f"candidates: {candidates}")
    if not candidates:
        return None

    winners = []
    for t in thresholds:
        winner, _ = rd.main_helper(vprofile, candidates.copy(), t)
        winners.append(str(winner))

    return f"{election_id}," + ",".join(winners) + "\n"


def build_tasks(data: list) -> list:
    """Flatten all elections x hits into a list of task tuples."""
    tasks = []
    for election in data:
        election_name = election.get("election_name", "unknown")
        candidate_map = election.get("candidate_map", {})
        for hit_index, hit in enumerate(election.get("hits", [])):
            tasks.append((election_name, hit_index, hit, candidate_map))
    return tasks


def run_all_slow(filepath, thresholds):
    with open(filepath, 'r') as f:
        data = json.load(f)

    tasks = build_tasks(data)

    header = "election_id," + ",".join([str(t) for t in thresholds]) + "\n"
    with open(RESULTS_FILE, 'w') as f:
        f.write(header)

    print(f"Running diversity experiment ({len(tasks)} tasks)")
    results = []
    for task in tqdm(tasks, desc="Elections"):
        csv_row = process_election_task(task, thresholds=thresholds)
        if csv_row:
            with open(RESULTS_FILE, 'a') as f:
                f.write(csv_row)
            results.append(csv_row)

    return len(results)


def run_all(filepath, thresholds):
    with open(filepath, 'r') as f:
        data = json.load(f)

    tasks = build_tasks(data)

    header = "election_id," + ",".join([str(t) for t in thresholds]) + "\n"
    with open(RESULTS_FILE, 'w') as f:
        f.write(header)

    print(f"Running diversity experiment ({len(tasks)} tasks)")
    worker_func = partial(process_election_task, thresholds=thresholds)
    results = process_map(worker_func, tasks, chunksize=5, desc="Elections")

    with open(RESULTS_FILE, 'a') as f:
        for csv_row in results:
            if csv_row:
                f.write(csv_row)

    return len([r for r in results if r is not None])


if __name__ == '__main__':
    THRESHOLDS = [i / 100 for i in range(10)]  # 0.00 to 0.09

    if not os.path.exists(DATA_FILE):
        print(f"Error: '{DATA_FILE}' not found.")
        sys.exit(1)

    total = run_all(DATA_FILE, thresholds=THRESHOLDS)
    print(f"\nDone! {total} experiments run and saved to {RESULTS_FILE}")