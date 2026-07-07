import sys
import os
import json
import math
import csv
import logging
from fractions import Fraction
from collections import defaultdict

from tqdm.contrib.concurrent import process_map

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from votekit import Ballot, PreferenceProfile
from run_diversity import run_diversity, condense_ballots

logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'diversity_cloning.log'),
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)
logger = logging.getLogger()

# TODO: CHANGE THIS
DATA_FILE = '/Users/belle/Desktop/build/condorcet_analysis/Diversity/andy/data/condorcet_sampling_hits_USA.json'
RESULTS_FILE = 'diversity_cloning_simulations_usa.csv'

# Clone percentages to sweep: fraction of a target candidate's ballot weight
# that ranks the Clone candidate ABOVE the original; remainder ranks below.
CLONE_PERCENTS = [Fraction(p, 10) for p in range(1, 5)]  # 0.1, 0.2, ..., 0.4

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
    for t in DIVERSITY_THRESHOLDS:
        row[str(t)] = run_diversity(vprofile, t)
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
    if not os.path.exists(DATA_FILE):
        print(f"Error: '{DATA_FILE}' not found.")
        sys.exit(1)

    total = run_all(DATA_FILE)
    print(f"\nDone! {total} rows written to {RESULTS_FILE}")
# import sys
# sys.path.append('/Users/belle/Desktop/build/rcv')
# import multiprocessing
# import main_methods as mm
# from votekit.cleaning import remove_and_condense_rank_profile
# import pandas as pd
# import csv
# import random
# from fractions import Fraction
# from collections import defaultdict
# from votekit import PreferenceProfile, Ballot
# import os
# import re
# from Diversity.comparison.run_diversity import run_diversity, condense_ballots
# from Diversity.comparison.run_tvr import run_tvr
# import math
# import json
# from datetime import datetime
# from tqdm.contrib.concurrent import process_map
# import os
# import functools
# import logging

# logging.basicConfig(
#     filename=os.path.join(os.path.dirname(__file__), 'tvr.log'),
#     level=logging.INFO,
#     format='%(asctime)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S',
#     force=True    
# )
# logger = logging.getLogger()

# def debug_weight_map(weight_map, target_cand, path="weight_map_debug.json"):
#     serializable = {
#         str([list(s) for s in ranking]): str(weight)
#         for ranking, weight in weight_map.items() if weight > 100
#     }
#     with open(path, 'a') as f:
#         json.dump(serializable, f, indent=2)
        
# def clean_path(path):
#     return re.sub(r"/0\.[0-5]/", "/", path)

# def run_voting_methods(v_profile, file_label, candidate_cloned, output_folder, percent):
#     logger. info(f"cloned: {candidate_cloned}, percent: {percent}")
#     # print(v_profile)
#     data = {
#         'file': clean_path(file_label.replace(output_folder, '')),
#         'candidate_cloned': candidate_cloned,
#         'percent': percent,
#     }
#     data['numCands'] = len([c for c in v_profile.candidates if c != "skipped"])
#     for i in range(10):
#         threshold = i / 100
#         data[str(threshold)] = run_diversity(v_profile, threshold)

#     return data

# def insert_clone_into_profile(profile, target_candidate, percent):
#     # print(target_candidate)
#     weight_map = defaultdict(Fraction)
#     profile = condense_ballots(profile)
#     for ballot in profile.ballots:
#         ranking = list(ballot.ranking)
#         # print(ranking)
#         weight = ballot.weight

#         idx = next(
#             (i for i, s in enumerate(ranking) if s == target_candidate),
#             None
#         )

#         if idx is None:
#             weight_map[tuple(frozenset(s) for s in ranking)] += weight
#             continue
        
#         # og = weight * percent
#         before_weight = math.ceil(weight * percent)
#         # if og != before_weight:
#         #     print(og, ";", before_weight)
#         after_weight  = weight - before_weight

#         before = tuple(frozenset(s) for s in ranking[:idx] + [{'Clone'}] + ranking[idx:])
#         after  = tuple(frozenset(s) for s in ranking[:idx+1] + [{'Clone'}] + ranking[idx+1:])
#         # print(before)
#         # print(after)
        
#         if before_weight > 0:
#             weight_map[before] += before_weight
#         if after_weight > 0:
#             weight_map[after] += after_weight
    
    
#     # debug_weight_map(weight_map, target_candidate)

#     return PreferenceProfile(ballots=tuple(
#         Ballot(ranking=list(ranking), weight=weight)
#         for ranking, weight in weight_map.items()
#     ))

# def process_data(profile, file_name, output_folder, results, percent):
#     """
#     Takes a votekit PreferenceProfile directly, injects a Clone candidate
#     after each real candidate, runs voting methods, and writes results.
#     """
#     # extract candidates from ballot rankings
#     all_candidates = set()
#     for ballot in profile.ballots:
#         for cand in ballot.ranking:
#             all_candidates.add(cand)
#     candidates = list(all_candidates)
    
#     logger.info(f"RUNNING {file_name}")
    
    

#     for candidate in candidates:
#         # print(candidate)
#         cloned_profile = insert_clone_into_profile(profile, candidate, percent)

#         d = run_voting_methods(cloned_profile, file_name, candidate, output_folder, percent)
#         with open(results, mode='a', newline='') as f:
#             writer = csv.writer(f)
#             if os.stat(results).st_size == 0:
#                 writer.writerow(d.keys())
#             writer.writerow([d.get(key, '') for key in d.keys()])


# # def main():
#     # for filename in os.listdir('../Data'):
#     #     if filename.endswith('.csv'):
#     #         full_path = os.path.join('../Data', filename)
#             # logger.info(f"Processing file: {filename}")
#     # full_path = "/Users/belle/Desktop/build/condorcet_analysis/Data/govan_govan.csv"
    
# output_folder = "/Users/belle/Desktop/build/condorcet_analysis/Cloning/Res"
# results = './tvr_cloning_tests.csv'

# def process(full_path):
#     ballots = [
#     Ballot(ranking=({"A"}), weight=Fraction(52)),
#     Ballot(ranking=({"B"}), weight=Fraction(48)),
#     ]

#     profile = PreferenceProfile(ballots=tuple(ballots))
    
#     print(profile)


#     # profile = mm.v_profile(full_path)
#     profile = remove_and_condense_rank_profile(profile=profile, removed=['skipped', 'writein', 'Write-in'])
#     d = run_voting_methods(profile, full_path.split('/')[-1], 'none', output_folder, 0)

#     with open(results, mode='a', newline='') as f:
#         writer = csv.writer(f)
#         if os.stat(results).st_size == 0:
#             writer.writerow(d.keys())
#         writer.writerow([d.get(key, '') for key in d.keys()])
    
#     # for p in range(1,10):
#     #     percent = p / 10
#     #     # print(percent)
#     process_data(profile, full_path.split('/')[-1], output_folder, results, 0.4)

# root_dir = '/Users/belle/Desktop/build/rcv_proposal/raw_data/america/processed_data'
# error_file = 'error.txt'

# def log_error(filename):
#     with open(error_file, "a") as ef:
#         ef.write(f"{filename}, ")
        
# if __name__ == '__main__':
#     process("/Users/belle/Downloads/American data condensed/San Francisco/SanFrancisco_11082016_BoardofSupervisorsDistrict1.csv")
    
# def main():
#     for dirpath, dirnames, filenames in os.walk(root_dir):
#         for filename in filenames:
#             if filename.endswith('.blt') or filename.endswith('.csv') or filename.endswith('.txt'):
#                 full_path = os.path.join(dirpath, filename)
#                 p = multiprocessing.Process(target=process, args=(full_path,))
#                 p.start()
#                 p.join(600)

#                 if p.is_alive():
#                     # timeout
#                     p.terminate()
#                     p.join()
#                     log_error(filename)
#                 elif p.exitcode != 0:
#                     # crashed
#                     log_error(filename)

# if __name__ == '__main__':
#     main()


# # def collect_files(folder):
# #     """Collect all valid file paths from the folder."""
# #     valid_extensions = ('.blt', '.csv', '.txt')
# #     file_paths = []
# #     for dirpath, dirnames, filenames in os.walk(folder):
# #         for filename in filenames:
# #             if filename.endswith(valid_extensions):
# #                 file_paths.append(os.path.join(dirpath, filename))
# #     return file_paths

# # def process_with_error_log(args):
# #     """Wrapper to call process() and return filename on failure."""
# #     full_path, country = args
# #     try:
# #         process(full_path)
# #         return None  # success
# #     except Exception as e:
# #         return os.path.basename(full_path)  # return filename to log as error

# # def main(country, folder):
# #     file_paths = collect_files(folder)
# #     args = [(fp, country) for fp in file_paths]

# #     results = process_map(process_with_error_log, args, timeout=20, max_workers=os.cpu_count(), chunksize=1,
# #     total=len(args))

# #     errors = [r for r in results if r is not None]
# #     if errors:
# #         with open(f'./error_{country}.txt', 'a') as ef:
# #             ef.write(', '.join(errors))

# # if __name__ == '__main__':
# #     main('america', '/Users/belle/Desktop/build/rcv_proposal/raw_data/america/processed_data')

