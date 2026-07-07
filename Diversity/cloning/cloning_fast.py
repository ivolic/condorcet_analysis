import sys
import os
import json
import math
import csv
import logging
import statistics
import argparse
from fractions import Fraction
from collections import defaultdict

from tqdm.contrib.concurrent import process_map

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from votekit import Ballot, PreferenceProfile
from run_diversity_fast import condense_ballots, prepare_context, run_diversity_from_context

logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'diversity_cloning.log'),
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)
logger = logging.getLogger()

# TODO: CHANGE THIS
DATA_FILE = '/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/data/condorcet_sampling_hits_Scotland.json'
RESULTS_FILE = 'diversity_cloning_simulations_scotland.csv'

# Clone percentages to sweep: fraction of a target candidate's ballot weight
# that ranks the Clone candidate ABOVE the original; remainder ranks below.
CLONE_PERCENTS = [Fraction(p, 10) for p in range(1, 10)]  # 0.1, 0.2, ..., 0.9

# Diversity metric thresholds (passed into run_diversity), 0.00 through 0.09.
DIVERSITY_THRESHOLDS = [i / 100 for i in range(10)]


def load_profile_from_hit(hit: dict, candidate_map: dict) -> PreferenceProfile | None:
    """
    Convert a single hit's profile dict into a PreferenceProfile.
    Keys like "A>B>C" become ranked ballots; values are vote counts.
    """
    ballots = []
    profile = hit.get("profile", {})

    for ballot_str, count in profile.items():
        if not count or int(count) <= 0:
            continue

        try:
            ranking = tuple(
                frozenset({candidate_map[c.strip()]}) for c in ballot_str.split(">")
            )
        except KeyError as e:
            logger.warning(f"Unknown candidate code {e} in ballot '{ballot_str}', skipping ballot")
            continue

        ballots.append(Ballot(ranking=ranking, weight=Fraction(int(count))))

    if not ballots:
        return None
    return PreferenceProfile(ballots=tuple(ballots))


def insert_clone_into_profile(condensed_profile: PreferenceProfile, target_candidate, percent) -> PreferenceProfile:
    """
    percent must be Fraction-convertible to keep ballot-weight arithmetic exact.
    condensed_profile must already have gone through condense_ballots -- callers
    that run this for many (candidate, percent) pairs against the same base
    profile should condense once up front rather than per call.
    """
    percent = Fraction(percent)

    weight_map = defaultdict(Fraction)
    for ballot in condensed_profile.ballots:
        ranking = list(ballot.ranking)
        weight = ballot.weight

        idx = next(
            (i for i, s in enumerate(ranking) if target_candidate in s),
            None
        )

        if idx is None:
            weight_map[tuple(frozenset(s) for s in ranking)] += weight
            continue

        before_weight = math.ceil(weight * percent)
        after_weight = weight - before_weight

        before = tuple(frozenset(s) for s in ranking[:idx] + [{'Clone'}] + ranking[idx:])
        after = tuple(frozenset(s) for s in ranking[:idx + 1] + [{'Clone'}] + ranking[idx + 1:])

        if before_weight > 0:
            weight_map[before] += before_weight
        if after_weight > 0:
            weight_map[after] += after_weight

    return PreferenceProfile(ballots=tuple(
        Ballot(ranking=list(ranking), weight=weight)
        for ranking, weight in weight_map.items()
    ))


def diversity_row(vprofile: PreferenceProfile, election_id: str, candidate_cloned: str, percent) -> dict:
    row = {
        'election_id': election_id,
        'candidate_cloned': candidate_cloned,
        'percent': str(percent),
    }
    row['numCands'] = len([c for c in vprofile.candidates if c != "skipped"])

    # Build the plain-ballot representation + pairwise matrix ONCE for this
    # profile, then reuse it across every threshold -- avoids repeating the
    # votekit conversion and matrix precomputation 10 times over.
    context = prepare_context(vprofile)
    for t in DIVERSITY_THRESHOLDS:
        winner, _rounds = run_diversity_from_context(context, t)
        row[str(t)] = winner
    return row


def process_election_task(task_data):
    """
    task_data is a tuple: (election_name, hit_index, hit, candidate_map)
    Returns a list of row dicts (baseline + every candidate x every clone percent),
    or [] if the hit couldn't be turned into a profile.
    """
    election_name, hit_index, hit, candidate_map = task_data
    election_id = f"{election_name}__hit{hit_index}"
    logger.info(f"RUNNING election {election_id}")

    vprofile = load_profile_from_hit(hit, candidate_map)
    if not vprofile:
        return []

    candidates = [
        c for c in vprofile.candidates
        if c not in ('skipped', 'writein', 'Write-in')
    ]
    if not candidates:
        return []

    rows = [diversity_row(vprofile, election_id, 'none', 0)]

    condensed = condense_ballots(vprofile)
    for candidate in candidates:
        for percent in CLONE_PERCENTS:
            cloned_profile = insert_clone_into_profile(condensed, candidate, percent)
            rows.append(diversity_row(cloned_profile, election_id, candidate, percent))

    return rows


def build_tasks(data: list) -> list:
    """Flatten all elections x hits into a list of task tuples."""
    tasks = []
    for election in data:
        election_name = election.get("election_name", "unknown")
        candidate_map = election.get("candidate_map", {})
        for hit_index, hit in enumerate(election.get("hits", [])):
            tasks.append((election_name, hit_index, hit, candidate_map))
    return tasks


def get_task_metadata(task_data: tuple) -> dict:
    """
    Cheap, read-only pass over one (election, hit) task: loads the profile
    and reports its candidate count, total ballot weight, and how many CSV
    rows it will contribute to the full run -- without doing any cloning.
    Useful for sizing a run before committing to it, and for spotting
    elections whose candidate count is unusually large (those tasks will
    take roughly num_candidates x len(CLONE_PERCENTS) times longer than a
    small election, which matters for how work gets balanced across workers).
    """
    election_name, hit_index, hit, candidate_map = task_data
    election_id = f"{election_name}__hit{hit_index}"

    vprofile = load_profile_from_hit(hit, candidate_map)
    if not vprofile:
        return {
            'election_id': election_id,
            'num_candidates': 0,
            'total_ballot_weight': 0,
            'expected_rows': 0,
        }

    candidates = [
        c for c in vprofile.candidates
        if c not in ('skipped', 'writein', 'Write-in')
    ]
    total_weight = sum(b.weight for b in vprofile.ballots)

    return {
        'election_id': election_id,
        'num_candidates': len(candidates),
        'total_ballot_weight': total_weight,
        'expected_rows': 1 + len(candidates) * len(CLONE_PERCENTS),
    }


def summarize_candidate_metadata(filepath: str, out_path: str = 'election_metadata.csv') -> tuple:
    """
    Computes and writes per-election candidate-count metadata for the whole
    dataset, then prints a summary (min/max/mean/median candidates, and the
    total number of rows the full cloning run would produce). Returns
    (records, summary) for programmatic use.
    """
    with open(filepath, 'r') as f:
        data = json.load(f)

    tasks = build_tasks(data)
    print(f"Computing candidate-count metadata for {len(tasks)} election/hit profiles...")

    records = process_map(get_task_metadata, tasks, chunksize=1, desc="Metadata")

    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    candidate_counts = [r['num_candidates'] for r in records if r['num_candidates'] > 0]
    total_expected_rows = sum(r['expected_rows'] for r in records)

    summary = {
        'num_tasks': len(records),
        'num_tasks_with_candidates': len(candidate_counts),
        'min_candidates': min(candidate_counts) if candidate_counts else 0,
        'max_candidates': max(candidate_counts) if candidate_counts else 0,
        'mean_candidates': round(statistics.mean(candidate_counts), 2) if candidate_counts else 0,
        'median_candidates': statistics.median(candidate_counts) if candidate_counts else 0,
        'total_expected_output_rows': total_expected_rows,
    }

    print("\nCandidate-count metadata summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print(f"\nPer-election detail written to {out_path}")

    return records, summary


def run_all(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)

    tasks = build_tasks(data)
    print(f"Running diversity-cloning experiment ({len(tasks)} tasks)")

    # Workers only compute and return rows -- no file I/O happens inside a
    # worker, so there's no risk of concurrent processes corrupting a shared
    # CSV. Everything is written once, here, after process_map finishes.
    all_row_lists = process_map(process_election_task, tasks, chunksize=1, desc="Elections")

    total = 0
    writer = None
    with open(RESULTS_FILE, 'w', newline='') as f:
        for rows in all_row_lists:
            for row in rows:
                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=list(row.keys()))
                    writer.writeheader()
                writer.writerow(row)
                total += 1

    return total


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--metadata-only', action='store_true',
        help='Only compute per-election candidate-count metadata and exit, skipping the full cloning experiment.'
    )
    args = parser.parse_args()

    if not os.path.exists(DATA_FILE):
        print(f"Error: '{DATA_FILE}' not found.")
        sys.exit(1)

    if args.metadata_only:
        summarize_candidate_metadata(DATA_FILE)
        sys.exit(0)

    total = run_all(DATA_FILE)
    print(f"\nDone! {total} rows written to {RESULTS_FILE}")