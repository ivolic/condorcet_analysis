import sys
sys.path.append('/Users/belle/Desktop/build/rcv')
import main_methods as mm
from votekit.cleaning import remove_and_condense_rank_profile
import os
from preflibtools.instances import OrdinalInstance
from votekit.pref_profile import PreferenceProfile
from preflibtools.properties.subdomains.ordinal import is_single_peaked_pq_tree
import multiprocessing


def votekit_to_preflib(profile: PreferenceProfile) -> OrdinalInstance:
    """
    Convert a VoteKit PreferenceProfile to a preflib OrdinalInstance.
    Preserves ballot multiplicities (weights).
    """
    instance = OrdinalInstance()

    # Collect all candidates to build a consistent candidate index
    candidates = list(profile.candidates)
    cand_to_idx = {c: i + 1 for i, c in enumerate(candidates)}  # preflib is 1-indexed

    orders = []
    multiplicities = []

    for ballot in profile.ballots:
        # VoteKit ballot.ranking is a tuple of frozensets (each tier is a set of tied candidates)
        # Flatten each tier into a tuple — preflib supports ties via tuples within the order
        order = tuple(
            tuple(cand_to_idx[c] for c in tier)
            for tier in ballot.ranking
        )
        orders.append(order)
        multiplicities.append(int(ballot.weight))  # weight is a Fraction, convert to int

    instance.orders = orders
    instance.multiplicity = multiplicities

    # Attach candidate names so preflib knows the alternatives
    instance.alternatives_name = {i + 1: c for i, c in enumerate(candidates)}
    print(instance.data_type) 
    return instance


import csv

def ballot_completion_stats(profile: PreferenceProfile, election: str, filepath: str) -> None:
    rows = []
    n_candidates = len(profile.candidates)
    
    total_voters = 0
    complete_voters = 0
    
    for ballot in profile.ballots:
        weight = int(ballot.weight)
        ranked = sum(len(tier) for tier in ballot.ranking)
        total_voters += weight
        if ranked == n_candidates:
            complete_voters += weight
    
    pct_complete = 100 * complete_voters / total_voters if total_voters > 0 else 0
    pct_incomplete = 100 - pct_complete
    cand = len(profile.candidates)
    rows.append([election, cand, f"{pct_complete:.1f}", f"{pct_incomplete:.1f}"])

    with open(filepath, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def run_ballot(full_path,filename, outputfile):
    profile = mm.v_profile(full_path)
    profile = remove_and_condense_rank_profile(profile=profile, removed=['skipped', 'writein', 'Write-in'])
    ballot_completion_stats(profile, filename, outputfile)

error_file = 'error.txt'

def main(country):
    root_dir = f'/Users/belle/Desktop/build/rcv_proposal/raw_data/{country}/processed_data'
    outputfile = f"{country}.csv"

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.blt') or filename.endswith('.csv') or filename.endswith('.txt'):
                full_path = os.path.join(dirpath, filename)

                if __name__ == '__main__':
                    p = multiprocessing.Process(target=run_ballot, args=(full_path,filename,outputfile,))
                    p.start()
                    p.join(180)

                    if p.is_alive():
                        print("running... let's kill it...")
                        with open(error_file, "a") as ef:
                            ef.write(f"{filename}, ")
                        p.terminate()
                        p.join()
                        print("\n")

if __name__ == "__main__":
    country = sys.argv[1]
    main(country)

# profile = mm.v_profile("/Users/belle/Desktop/build/condorcet_analysis/Data/JedburghandDistrictWard_sc-borders12-09.csv")
# profile = remove_and_condense_rank_profile(profile=profile, removed=['skipped', 'writein', 'Write-in'])
# ballot_completion_stats(profile)






# instance = votekit_to_preflib(profile)
# sp, axis = is_single_peaked_pq_tree(instance)

# print("Single-peaked:", sp)
# if sp:
#     print("Axis:", [instance.alternatives_name[i] for i in axis])