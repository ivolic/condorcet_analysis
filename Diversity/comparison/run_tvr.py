import sys
sys.path.append('/Users/belle/Desktop/build/rcv')
import main_methods as mm
import logging
import os
# logging.basicConfig(
#     filename=os.path.join(os.path.dirname(__file__), 'tvr.log'),
#     level=logging.INFO,
#     format='%(asctime)s - %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S',
#     force=True    
# )
# logger = logging.getLogger()
# logger.info("Logger initialized")
# RESULTS_FILE = 'tvr.csv'

def drop_candidate(vprofile, candidates, method, logger):
    lowest_score = {"candidates": [], "score": None}
    
    if method == "PM":
        scores = mm.Borda_PM_Return_Full(vprofile, candidates, tiebreak="random")
    elif method == "OM":
        scores = mm.Borda_OM_Return_Full(vprofile, candidates, tiebreak="random")
    elif method == "AVG":
        scores = mm.Borda_AVG_Return_Full(vprofile, candidates, tiebreak="random")
        
    logger.info(scores)
    for (key, val) in scores.items():
        if lowest_score["score"] == None or val < lowest_score["score"]:
            lowest_score["candidates"] = [key]
            lowest_score["score"] = val
        elif val == lowest_score["score"]:
            lowest_score["candidates"].append(key)
    logger.info(f"Candidates with lowest diversity score: {lowest_score}")      
    return lowest_score["candidates"]

def main_helper(vprofile, candidates, method, logger, round_num=1):
    logger.info(f"Round {round_num}: Remaining candidates: {candidates}")
    if len(candidates) == 1:
        return candidates[0]
    else:
        cand = drop_candidate(vprofile, candidates, method, logger)
        cand_to_drop = ""
        if len(cand) == 1:
            cand_to_drop = cand[0]
        else:
            logger.info("TIED")
            return "TIED"
    
        c = candidates.copy()
        c.remove(cand_to_drop)
        logger.info(f"Dropping candidate: {cand_to_drop}")
        logger.info("--------------------------------------------------")
        
        return main_helper(vprofile, c, method, logger, round_num + 1)

        
def run_tvr(vprofile, type, logger):
    # logger.info(f"\n{'='*60}")
    # logger.info(f"Processing file: {full_path}")
    # logger.info(f"{'='*60}")
    
    # vprofile = mm.v_profile(full_path)

    candidates = list(vprofile.candidates)
    candidates = [cand for cand in candidates if cand != 'skipped' and cand != 'writein' and cand != 'Write-in']
    
    # for m in ["OM", "PM", "AVG"]:
    # logger.info(f"running {m}")
    candidate_new = candidates.copy()
    winner = main_helper(vprofile, candidate_new, type, logger)
        # filename = os.path.basename(full_path)
        # with open(RESULTS_FILE, 'a') as f:
        #     f.write(f'{filename},{m},{winner}\n')
    
        # logger.info(f"RESULT for {m}: {winner}")
    return winner
    
# def main():
#     for filename in os.listdir('../../Data'):
#         if filename.endswith('.csv'):
#             full_path = os.path.join('../../Data', filename)
#             logger.info(f"Processing file: {filename}")
#             vprofile = mm.v_profile(full_path)
#             run_tvr(vprofile, "OM")

# root_dir = '/Users/belle/Desktop/build/rcv_proposal/raw_data/america/processed_data'
# error_file = 'error.txt'
# def main():
#     for dirpath, dirnames, filenames in os.walk(root_dir):
#         for filename in filenames:
#             if filename.endswith('.blt') or filename.endswith('.csv') or filename.endswith('.txt'):
#                 full_path = os.path.join(dirpath, filename)

#                 if __name__ == '__main__':
#                     p = multiprocessing.Process(target=run_tvr, args=(full_path,))
#                     p.start()
#                     p.join(180)

#                     if p.is_alive():
#                         print("running... let's kill it...")
#                         with open(error_file, "a") as ef:
#                             ef.write(f"{filename}, ")
#                         p.terminate()
#                         p.join()
#                         print("\n")

# main()