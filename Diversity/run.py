import sys
sys.path.append('/Users/belle/Desktop/build/rcv')
import main_methods as mm
import os
import logging
from votekit.utils import first_place_votes
from votekit.cleaning import remove_noncands

logging.basicConfig(
    filename='condercet_analysis2.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

RESULTS_FILE = 'condercet_analysis2.csv'
with open(RESULTS_FILE, 'w') as f:
    f.write('file,threshold,winner,rounds\n')

def get_condorcet_winner(vprofile, candidates):
    condorcet_winner = mm.Condorcet(prof=vprofile, cands_to_keep=candidates)
    return condorcet_winner
      
def get_diversity_score(profile, candidate, threshold=0, showAll=False):
    total_weight = sum(ballot.weight for ballot in profile.ballots)
    min_weight = threshold * total_weight
    diversity_score = 0

    for ballot in profile.ballots:
        if ballot.weight >= min_weight and candidate in ballot.ranking[0]:
            diversity_score += 1

    return diversity_score

def drop_candidate(vprofile, candidates, threshold):
    lowest_score = {"candidates": [], "score": None}

    for c in candidates:
        score = get_diversity_score(vprofile, c, threshold)
        logger.info(f"Candidate: {c}, Diversity Score: {score}")

        if lowest_score["score"] == None or score < lowest_score["score"]:
            lowest_score["candidates"] = [c]
            lowest_score["score"] = score
        elif score == lowest_score["score"]:
            lowest_score["candidates"].append(c)
    logger.info(f"Candidates with lowest diversity score: {lowest_score}")      
    return lowest_score["candidates"]

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
        vprofile = remove_noncands(vprofile, [cand_to_drop])
        logger.info(f"Dropping candidate: {cand_to_drop}")
        logger.info("--------------------------------------------------")
        
        return main_helper(vprofile, candidates, threshold, round_num + 1)
        
def run_diversity(full_path, threshold=0):
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing file: {full_path}, threshold: {threshold}")
    logger.info(f"{'='*60}")
    
    vprofile = mm.v_profile(full_path)
    candidates = list(vprofile.candidates)
    candidates = [cand for cand in candidates if cand != 'skipped']

    winner, rounds = main_helper(vprofile, candidates, threshold)
    
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
            for i in range(0, 30): #set at 30 usually
                logger.info(f"\nRunning with diversity threshold: {i / 10}")
                threshold = i / 100
                run_diversity(full_path, threshold)

main()

# check on condorcet analysis
# [] graph on the x axis threshold, on the y axis, percentage of original diversity score??