import sys
sys.path.append('/Users/belle/Desktop/build/rcv')
import main_methods as mm
import os
import logging
from votekit.utils import first_place_votes
from votekit.cleaning import remove_and_condense_rank_profile
from collections import defaultdict
from fractions import Fraction
from votekit import Ballot, PreferenceProfile

logging.basicConfig(
    filename='condorcet_highest.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

RESULTS_FILE = 'condorcet_highest.csv'
with open(RESULTS_FILE, 'w') as f:
    f.write('file,threshold,winner,rounds\n')

def condense_ballots(profile):
    weights = defaultdict(Fraction)
    
    for ballot in profile.ballots:
        weights[ballot.ranking] += ballot.weight
        
    new_ballots = [
        Ballot(ranking=ranking, weight=weight)
        for ranking, weight in weights.items()
    ]

    return PreferenceProfile(ballots=tuple(new_ballots))


def condense_ballots2(profile):
    weights = defaultdict(Fraction)

    all_candidates = set(profile.candidates)

    for ballot in profile.ballots:
        ranking = list(ballot.ranking)

        ranked_candidates = set()
        for rank in ranking:
            ranked_candidates.update(rank)

        missing = all_candidates - ranked_candidates

        if len(missing) == 1:
            missing_candidate = next(iter(missing))
            ranking.append(frozenset({missing_candidate}))

        weights[tuple(ranking)] += ballot.weight

    new_ballots = [
        Ballot(ranking=ranking, weight=weight)
        for ranking, weight in weights.items()
    ]

    return PreferenceProfile(ballots=tuple(new_ballots))

def get_condorcet_winner(vprofile, candidates):
    condorcet_winner = mm.Condorcet(prof=vprofile, cands_to_keep=candidates)
    return condorcet_winner
      
def get_diversity_score(profile, candidate, threshold=0, printMinWeight=False):
    total_weight = sum(ballot.weight for ballot in profile.ballots)
    min_weight = threshold * total_weight
    if printMinWeight:
        logger.info(f"min_weight {min_weight}")
    diversity_score = 0

    for ballot in profile.ballots:
        if candidate in ballot.ranking[0]:
            # logger.info(ballot.ranking)
            # logger.info(ballot.weight)
            # logger.info(ballot.voter_set)
            if ballot.weight >= min_weight:
                diversity_score += 1

    return diversity_score

def drop_candidate(vprofile, candidates, threshold):
    lowest_score = {"candidates": [], "score": None}

    print_min = True
    for c in candidates:
        score = get_diversity_score(vprofile, c, threshold, printMinWeight=print_min)
        logger.info(f"Candidate: {c}, Diversity Score: {score}")

        if lowest_score["score"] == None or score < lowest_score["score"]:
            lowest_score["candidates"] = [c]
            lowest_score["score"] = score
        elif score == lowest_score["score"]:
            lowest_score["candidates"].append(c)
        print_min = False
    logger.info(f"Candidates with lowest diversity score: {lowest_score}")      
    return lowest_score["candidates"]

def get_highest_diversity_score(vprofile, candidates, threshold):
    highest = {"candidates": [], "score": 0}

    for c in candidates:
        score = get_diversity_score(vprofile, c, threshold)
        logger.info(f"Candidate: {c}, Diversity Score: {score}")

        if score > highest["score"]:
            highest["candidates"] = [c]
            highest["score"] = score
        elif score == highest["score"]:
            highest["candidates"].append(c)
    logger.info(f"Candidates with highest diversity score: {highest}")      
    return highest["candidates"]

def first_place_count(vprofile, candidates_to_compare):
    logger.info("Running first place count...")
    result = {"cand": '', "score": None}
    fpv = first_place_votes(vprofile)
    fpv = {c: fpv[c] for c in candidates_to_compare if c in fpv}
    logger.info(f"First place votes: {fpv}")
    
    for c in candidates_to_compare:
        if result["score"] is None or (fpv[c] < result["score"]):
            result["cand"] = c
            result["score"] = fpv[c]
    return result["cand"]

def main_helper(vprofile, candidates, threshold, round_num=1):
    logger.info(f"Round {round_num}: Remaining candidates: {candidates}")
    winner = get_condorcet_winner(vprofile, candidates)
    if winner:
        logger.info(f"Condorcet winner found: {winner}")
        return list(winner)[0], round_num
    else:
        logger.info("No Condorcet winner found. Calculating diversity scores...")
        cand = drop_candidate(vprofile, candidates, threshold)
        cand_to_drop = ""
        if len(cand) == 1:
            cand_to_drop = cand[0]
        else:
            cand_to_drop = first_place_count(vprofile, cand)
        candidates.remove(cand_to_drop) #technically not needed anymore since we also update vprofile
        vprofile = remove_and_condense_rank_profile(profile=vprofile, removed=[cand_to_drop])
        vprofile = condense_ballots2(vprofile)
        logger.info(f"Dropping candidate: {cand_to_drop}")
        logger.info("--------------------------------------------------")
        
        return main_helper(vprofile, candidates, threshold, round_num + 1)
    
def main_helper2(vprofile, candidates, threshold, round_num=1):
    logger.info(f"Round {round_num}: Remaining candidates: {candidates}")
    winner = get_condorcet_winner(vprofile, candidates)
    if winner:
        logger.info(f"Condorcet winner found: {winner}")
        return list(winner)[0], round_num
    else:
        logger.info("No Condorcet winner found. Calculating diversity scores...")
        cand = get_highest_diversity_score(vprofile, candidates, threshold)
        return cand,0
        
def run_diversity(full_path, threshold=0):
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing file: {full_path}, threshold: {threshold}")
    logger.info(f"{'='*60}")
    
    vprofile = mm.v_profile(full_path)
    vprofile = remove_and_condense_rank_profile(profile=vprofile, removed=['skipped', 'writein', 'Write-in'])
    vprofile = condense_ballots2(vprofile)
    candidates = list(vprofile.candidates)
    candidates = [cand for cand in candidates if cand != 'skipped' and cand != 'writein' and cand != 'Write-in']
    
    winner, rounds = main_helper2(vprofile, candidates, threshold)
    
    filename = os.path.basename(full_path)
    with open(RESULTS_FILE, 'a') as f:
        f.write(f'{filename},{threshold},{winner},{rounds}\n')
    
    logger.info(f"RESULT: Winner: {winner}, Rounds: {rounds}")
    return winner, rounds
    
def main():
    for filename in os.listdir('../Data'):
        if filename.endswith('.csv'):
            full_path = os.path.join('../Data', filename)
            logger.info(f"Processing file: {filename}")
    # full_path = "/Users/belle/Desktop/build/condorcet_analysis/Data/Oakland_11082022_Schoolboarddistrict4.csv"
            for i in range(10):
                logger.info(f"\nRunning with diversity threshold: {i / 10}")
                threshold = i / 100
                run_diversity(full_path, threshold)

main()