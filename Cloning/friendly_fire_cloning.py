import sys
sys.path.append('/Users/belle/Desktop/build/condorcet_analysis/Jones_code')
sys.path.append('/Users/belle/Desktop/build/rcv')
import string

import election_class as ec
import main_methods as mm
from votekit.cleaning import remove_and_condense_rank_profile
import pandas as pd
import csv
from fractions import Fraction
from collections import defaultdict
from votekit import PreferenceProfile, Ballot
import os
import re
import math
import json
import os
import logging
import multiprocessing

logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'ff.log'),
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True    
)
logger = logging.getLogger()
logger.disabled = True

def condense_ballots(profile):
    weights = defaultdict(Fraction)
    
    for ballot in profile.ballots:
        weights[ballot.ranking] += ballot.weight
        
    new_ballots = [
        Ballot(ranking=ranking, weight=weight)
        for ranking, weight in weights.items()
    ]

    return PreferenceProfile(ballots=tuple(new_ballots))

def debug_weight_map(weight_map, target_cand, path="weight_map_debug.json"):
    serializable = {
        str([list(s) for s in ranking]): str(weight)
        for ranking, weight in weight_map.items() if weight > 100
    }
    with open(path, 'a') as f:
        json.dump(serializable, f, indent=2)
        
def clean_path(path):
    return re.sub(r"/0\.[0-5]/", "/", path)

def profile_to_df(profile, name_to_letter=None):
    rows = []
    for ballot in profile.ballots:
        ranking = ''.join(name_to_letter[next(iter(s))] for s in ballot.ranking)
        rows.append({'Count': int(ballot.weight), 'ballot': ranking})
    return pd.DataFrame(rows)


def run_voting_methods(v_profile, file_label, candidate_cloned, output_folder, percent):
    logger.info(f"cloned: {candidate_cloned}, percent: {percent}")
    data = {
        'file': clean_path(file_label.replace(output_folder, '')),
        'candidate_cloned': candidate_cloned,
        'percent': percent,
    }

    candidates = [c for c in v_profile.candidates if c != "skipped"]
    data['numCands'] = len(candidates)
    
    if len(candidates) > 46:
        data['f'] = "Too many cand"
        return data

    # build bidirectional maps
    letters = list(string.ascii_lowercase + string.ascii_uppercase)
    name_to_letter = {name: ('Z' if name == 'Clone' else letters[i]) for i, name in enumerate(candidates)}
    letter_to_name = {v: k for k, v in name_to_letter.items()}
    # print("winner")
    # print(mm.Condorcet(v_profile))
    
    # logger.info(letter_to_name)

    new_profile = profile_to_df(profile=v_profile, name_to_letter=name_to_letter)
    letter_candidates = [name_to_letter[c] for c in candidates]

    # logger.info(new_profile.sort_values('Count', ascending=False).to_string())
    
    # print(letter_candidates)
    
    # low  = new_profile[new_profile['Count'] < 10]
    # high = new_profile[new_profile['Count'] >= 10]

    # print(f"Ballot types with count < 10:  {len(low)},  total votes: {low['Count'].sum()}")
    # print(f"Ballot types with count >= 10: {len(high)}, total votes: {high['Count'].sum()}")

    ff_result = ec.friendly_fire_inst_smith(new_profile, letter_candidates, True)
    # print(ff_result)
    # map winners back to full names
    data['ff'] = [letter_to_name[l] for l in ff_result] if isinstance(ff_result, list) else letter_to_name.get(ff_result, ff_result)

    return data

def insert_clone_into_profile(profile, target_candidate, percent):
    weight_map = defaultdict(Fraction)
    profile = condense_ballots(profile)
    for ballot in profile.ballots:
        ranking = list(ballot.ranking)
        weight = ballot.weight

        idx = next(
            (i for i, s in enumerate(ranking) if s == target_candidate),
            None
        )

        if idx is None:
            weight_map[tuple(frozenset(s) for s in ranking)] += weight
            continue
        
        before_weight = math.ceil(weight * percent)
        after_weight  = weight - before_weight
        
        if before_weight + after_weight != weight:
            print("WRONG")

        before = tuple(frozenset(s) for s in ranking[:idx] + [{'Clone'}] + ranking[idx:])
        after  = tuple(frozenset(s) for s in ranking[:idx+1] + [{'Clone'}] + ranking[idx+1:])
    
        
        if before_weight > 0:
            weight_map[before] += before_weight
        if after_weight > 0:
            weight_map[after] += after_weight
    
    
    return PreferenceProfile(ballots=tuple(
        Ballot(ranking=list(ranking), weight=weight)
        for ranking, weight in weight_map.items()
    ))

def process_data(profile, file_name, output_folder, results, percent):
    """
    Takes a votekit PreferenceProfile directly, injects a Clone candidate
    after each real candidate, runs voting methods, and writes results.
    """
    # extract candidates from ballot rankings
    all_candidates = set()
    for ballot in profile.ballots:
        for cand in ballot.ranking:
            all_candidates.add(cand)
    candidates = list(all_candidates)
    
    logger.info(f"RUNNING {file_name}")
    
    for candidate in candidates:
        # print(f"Total before ballots: {sum(b.weight for b in profile.ballots)}")
        cloned_profile = insert_clone_into_profile(profile, candidate, percent)
        # print(f"Total after ballots: {sum(b.weight for b in cloned_profile.ballots)}")
        d = run_voting_methods(cloned_profile, file_name, candidate, output_folder, percent)
        
        with open(results, mode='a', newline='') as f:
            writer = csv.writer(f)
            if os.stat(results).st_size == 0:
                writer.writerow(d.keys())
            writer.writerow([d.get(key, '') for key in d.keys()])

output_folder = "/Users/belle/Desktop/build/condorcet_analysis/Cloning/Res"
results = './ff_cloning.csv'

def process(full_path):
    profile = mm.v_profile(full_path)
    profile = remove_and_condense_rank_profile(profile=profile, removed=['skipped', 'writein', 'Write-in'])
    profile = condense_ballots(profile)
    d = run_voting_methods(profile, full_path.split('/')[-1], 'none', output_folder, 0)

    with open(results, mode='a', newline='') as f:
        writer = csv.writer(f)
        if os.stat(results).st_size == 0:
            writer.writerow(d.keys())
        writer.writerow([d.get(key, '') for key in d.keys()])
    
    for i in range(0, 6):
        process_data(profile, full_path.split('/')[-1], output_folder, results, i/10)
error_file = 'error.txt'

def log_error(filename):
    with open(error_file, "a") as ef:
        ef.write(f"{filename}, ")
        
# root_dir = "/Users/belle/Desktop/build/rcv/American data condensed"
# def main():
#     for dirpath, dirnames, filenames in os.walk(root_dir):
#         for filename in filenames:
#             if filename.endswith('.blt') or filename.endswith('.csv') or filename.endswith('.txt'):
#                 if filename not in files:
#                     full_path = os.path.join(dirpath, filename)
#                     p = multiprocessing.Process(target=process, args=(full_path,))
#                     p.start()
#                     p.join(200)  # 3 minutes — was this intentional vs the 20 min earlier?

#                     if p.is_alive():
#                         # timeout
#                         p.terminate()
#                         p.join()
#                         log_error(filename)
#                     elif p.exitcode != 0:
#                         # crashed
#                         log_error(filename)

if __name__ == '__main__':
#     main()

    for filename in os.listdir('/Users/belle/Desktop/build/condorcet_analysis/Data'):
        if filename.endswith('.csv'):
            full_path = os.path.join('/Users/belle/Desktop/build/condorcet_analysis/Data', filename)
            logger.info(f"Processing file: {filename}")
            process(full_path)



# process("test.csv")
# process("/Users/belle/Desktop/build/rcv/American data condensed/New York City/NewYorkCity_06222021_DEMCouncilMember9thCouncilDistrict.csv")