###################################################
##### Code to measure strategic voting payoffs
###################################################

import random
import pandas as pd
import math
import operator
import numpy as np
import copy
import csv
import os
import statistics
import warnings
import sys
warnings.simplefilter(action='ignore', category=FutureWarning)
import multiprocessing
import time
import matplotlib.pyplot as plt
import traceback
import json

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        # if isinstance(obj, np.floating):
        #     return float(obj)
        # if isinstance(obj, np.ndarray):
        #     return obj.tolist()
        return super(NpEncoder, self).default(obj)

from election_class import *
from ballot_modifications_class import *
from strat_vote_class import *


#####TODO
## 





###############################################################################
###############################################################################
##### parameters
election_group = 'Scotland'
vote_frac = 1
mp_pool_size = 6
max_election_size = 15
###############################################################################
###############################################################################



####################################################
##### Functions to run searches
####################################################

def createBallotDF(list_profile, diagnostic=False):
    cand_names=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
                  '!', '@', '#', '$', '%']
    
    ballot_list = []
    count_list = []
    for k in range(1,len(list_profile)):
        if list_profile[k][0]=='0':
            break
        if diagnostic:
            print(k)
        
        this_line = list_profile[k]
        this_line_parts = this_line.split(' ')
        count_list.append(int(this_line_parts[0]))
        ballot = ''.join([cand_names[int(i)-1] for i in this_line_parts[1:-1]])
        ballot_list.append(ballot)
        
    df_dict = {'ballot': ballot_list, 'Count': count_list}
    data = pd.DataFrame(df_dict)
    return data

###############################################################################
###############################################################################

def get_election_data(election_location, specific_lxn=-1, diagnostic=False):
    lxns = []
    ## version for github repo
    base_name = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data/Preference Profiles/' + election_location
    # base_name = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data/Synthetic Preference Profiles/' + election_location
    ## version for HPC
    # base_name = './data/' + election_location

    lxn_count = 0
    for folder_name in os.listdir(base_name):
    ## test folder in scotland
    # for folder_name in ['s-lanarks17-ballots']:
    ## test folder in america
    # for folder_name in ['Portland, ME']:
        for file_name in os.listdir(base_name+'/'+folder_name):
            lxn_count += 1
            file_path = base_name+'/'+folder_name+'/'+file_name
            

            # if 'aberdeen2012/Ward1' not in file_path:
            #     continue
        
            # if lxn_count == 100:
            #     break
            
            # print(file_path)
            
            if specific_lxn > 0:
                if lxn_count!=specific_lxn:
                    continue
            
            if diagnostic:
                print(lxn_count, file_path)
        
            sys.stdout.write('\r')
            sys.stdout.write(f'Election {lxn_count}'+'         ')
            sys.stdout.flush()
            
            File=open(file_path,'r', encoding='utf-8')
            lines=File.readlines()
    
            first_space=lines[0].find(' ')
            num_cands=int(lines[0][0:first_space])
            if num_cands>67:
                print("Cannot handle this many candidates in election " + str(file_path) + ".  Has " + 
                      str(num_cands) + " candidates.")
                continue
                
            data = createBallotDF(lines)
            
            
            if num_cands>max_election_size:
                data = filter_weak_cands(data, num_cands, max_election_size)
                num_cands = max_election_size
            
            
            lxns.append([file_path, data, num_cands])

    return lxns


def filter_weak_cands(profile, old_cand_num, new_cand_num):
    
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                  '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
                  '!', '@', '#', '$', '%']
    cands = cand_names[:old_cand_num]
    
    plurality_scores = {cand:0 for cand in cands}
    for k in range(len(profile)):
        plurality_scores[profile.at[k,'ballot'][0]] += profile.at[k,'Count']
    
    cands.sort(key=lambda x: plurality_scores[x], reverse=True)
        
    # mention_scores = {}
    # for k in range(len(profile)):
    #     count = profile.at[k, 'Count']
    #     for cand in profile.at[k, 'ballot']:
    #         if cand not in mention_scores.keys():
    #             mention_scores[cand] = 0
    #         mention_scores[cand] += count
    # cands.sort(key=lambda x: mention_scores[x], reverse=True)
    
    keep_cands = cands[:new_cand_num]
    
    # print(plurality_scores)
    # print(keep_cands)
    
    new_ballot_list = []
    new_count_list = []
    
    for k in range(len(profile)):
        ballot = profile.at[k, 'ballot']
        new_ballot = ''
        for cand in ballot:
            if cand in keep_cands:
                new_ballot += cand_names[keep_cands.index(cand)]
        # print(ballot, new_ballot)
                
        if new_ballot:            
            if new_ballot in new_ballot_list:
                indx = new_ballot_list.index(new_ballot)
                new_count_list[indx] += profile.at[k, 'Count']
            else:
                new_ballot_list.append(new_ballot)
                new_count_list.append(profile.at[k, 'Count'])
     
    df_dict = {'ballot': new_ballot_list, 'Count': new_count_list}
    new_profile = pd.DataFrame(df_dict)
    
    return new_profile

###############################################################################
###############################################################################

def anom_search_strats_shell(params):
    lxn_method, ballot_mod, file_path, profile, num_cands = params
    
    try:
        return [lxn_method.__name__, ballot_mod.__name__, file_path, num_cands] + anom_search_strats(profile, num_cands, lxn_method, ballot_mod, vote_frac)
    except:
        print('###############################################')
        print('###############################################')
        print('Error in election:', params[2])
        print('Election method:', params[0])
        print('Running search:', params[1])
        print(traceback.format_exc())
        print('###############################################')
        print('###############################################')
        return [params[0], params[1], params[2], params[4], [], 0]







###############################################################################
###############################################################################
###############################################################################


if not os.path.exists(election_group+'_stratvoting'):
    os.makedirs(election_group+'_stratvoting')


# lxn_methods = [plurality, plurality_runoff, IRV, smith_irv, smith_plurality, 
               # minimax, smith_minimax, ranked_pairs, 
               # Borda_PM, Borda_OM, Borda_AVG, bucklin]
lxn_methods = [TVR_PM, TVR_OM, TVR_AVG, diversity_score_threshold]
# lxn_methods += [diversity_score_simplex]
lxn_methods += [friendly_fire_inst, friendly_fire_seq_smith, friendly_fire_inst_smith]
lxn_methods += [friendly_fire_inst_smith_exp]

# ballot_mod_methods = [LtoTop, truncBalAtL, truncBalAtW, buryWinBal, boostLinBal, deepBuryW]
# ballot_mod_methods = [LtoTop, truncBalAtL, truncBalAtW, buryWinBal, deepBuryW]
ballot_mod_methods = [strat_compromise, strat_truncate_L, strat_truncate_W, strat_bury_shallow, strat_bury_deep]


if __name__ == '__main__':  
    ## get data
    lxn_list = get_election_data(election_group)
    # lxn_list = [lxn_list_full[0]]
    
    gen_lxn_list = []
    for lxn in lxn_list:
        for lxn_method in lxn_methods:
            for ballot_mod in ballot_mod_methods:
                gen_lxn_list.append([lxn_method, ballot_mod]+lxn)
    
    ## search for general anomalies
    pool = multiprocessing.Pool(processes=mp_pool_size)
    massive_results = pool.map(anom_search_strats_shell, gen_lxn_list)
    
    with open(election_group+"_stratvoting/massive_results_data.json", "w") as f:
        json.dump(massive_results, f, cls=NpEncoder)
    
    ## data frame for top line results 
    exp_val_table = pd.DataFrame(0, index = [ballot_mod.__name__ for ballot_mod in ballot_mod_methods], 
                                    columns = [lxn_method.__name__ for lxn_method in lxn_methods])
    prob_change_table = pd.DataFrame(0, index = [ballot_mod.__name__ for ballot_mod in ballot_mod_methods], 
                                    columns = [lxn_method.__name__ for lxn_method in lxn_methods])
    
    for lxn in massive_results:
        lxn_method = lxn[0]
        ballot_mod = lxn[1]
        if lxn[4]:
            exp_val_table.at[ballot_mod, lxn_method] += np.mean(lxn[4])/len(lxn_list)
        prob_change_table.at[ballot_mod, lxn_method] += lxn[5]/len(lxn_list)
    
    

    exp_val_table.to_csv(election_group+'_stratvoting/expected_values.csv')
    prob_change_table.to_csv(election_group+'_stratvoting/prob_change_winner.csv')
    



















###############################################################################

# start_time = time.time()

# print('##### Collecting election data #####')
# lxn_list = get_election_data('scotland')

# print(time.time()-start_time)




# print('##### Measuring strategic voting outcomes #####')
# print('###################################')
# full_exp_vals = []
# full_change_probs = []

# for i in range(len(lxn_list)):
    
#     sys.stdout.write('\r')
#     sys.stdout.write('\r')
#     sys.stdout.write(f'Election {i+1}'+':' + lxn_list[i][0] + '                      ')
#     sys.stdout.flush()
    
#     lxn, profile, num_cands = lxn_list[i]
    
#     data, change_prob = anom_search_strats(profile, num_cands, IRV, strat_bury_deep, 1)
    
#     full_exp_vals.append(data)
#     full_change_probs.append(change_prob)
        
# print(time.time()-start_time)  
# print('###################################')


# flat_exp_vals = []
# for x in full_exp_vals:
#     flat_exp_vals+=x
    
# plt.hist(flat_exp_vals)












# def vv_borda_avg(ballot, cand, num_cands):
#     max_score = num_cands - 1
#     if cand in ballot:
#         return max_score - ballot.index(cand)
#     else:
#         missing_num = num_cands-len(ballot)
#         return (missing_num-1)/2




# lxn, profile, num_cands = lxn_list[1]

# cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
#               'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
#               'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
#               'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
# cands = cand_names[:num_cands]


# scores = {cand: 0.0 for cand in cands}

# for k in range(len(profile)):
#     ballot = profile.at[k, 'ballot']
#     scores[ballot[0]] += profile.at[k, 'Count']

# cands_ranked = cands.copy()
# cands_ranked.sort(key = lambda x: scores[x])


# W = 'A'
# L = 'C'
# new_profile = profile.copy(deep=True)
# modified_ballot_list = []

# for k in range(len(new_profile)):
#     ## change the ballot in some way
#     curBal = new_profile.at[k,'ballot']
#     count = int(new_profile.at[k, 'Count']*vote_frac)
#     modBal, modified = strat_bury_deep(curBal, W, L, cands_ranked)
#     # new_profile.at[k,'ballot'] = modBal
#     # if modified:
#     if curBal!=modBal:
#         modified_ballot_list.append([curBal, modBal, count])
#         new_profile.at[k, 'Count'] -= count
#         new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [modBal], 'Count': [count]})], ignore_index=True)

# newWinners = IRV(new_profile, cands)[0]
# nW = newWinners[0]

# if nW != W:
#     total_value_change = 0
#     ## compute change in value for all voters that modified ballots
#     for group in modified_ballot_list:
#         ogBal = group[0]
#         count = group[2]
#         score_change = vv_borda_avg(ogBal, nW, num_cands) - vv_borda_avg(ogBal, W, num_cands)
#         print(group, score_change)
#         total_value_change += score_change*count
#     print(total_value_change/sum([g[2] for g in modified_ballot_list]))


