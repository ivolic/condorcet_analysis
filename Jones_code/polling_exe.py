###################################################
##### Code to see if anomalies can be reversed
##### by reciprocal behavior
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
import traceback
import ast
import random as rand
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


#####TODO 
## 


###############################################################################
###############################################################################
##### parameters
##### parameters
## election_group should be of the form 'region/type'
## regions: Scotland, Australia, America
## types: single_winner, multi_winner, multi_winner_condensed
## if Australia/multi_winner (or multi_winner_condensed), end with ',no_Fed' or ',only_Fed' of ',all'
election_group = 'Scotland/single_winner'
# election_group = 'Scotland/multi_winner'
# election_group = 'Scotland/multi_winner_condensed'
# election_group = 'Australia/single_winner'
# election_group = 'Australia/multi_winner,no_Fed'
# election_group = 'Australia/multi_winner,only_Fed'
# election_group = 'Australia/multi_winner_condensed,no_Fed'
# election_group = 'Australia/multi_winner_condensed,only_Fed'
# election_group = 'America/single_winner'
# election_group = 'America/multi_winner'
mp_pool_size = 10


## don't mess with these, they are not important
frac = 1
mp_pool_size = 6
compromise_n = 4
bullet_n = 2
protect_n = 2
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

def get_election_data(election_location, diagnostic=False):
    lxns = []
    
    ## base_name should end at the preference_profiles_top_15 folder
    ## version for github repo
    base_name = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data/preference_profiles_top_15/'
    ## version for HPC
    # base_name = ?
    
    if ',' not in election_location:
        folder_name = base_name + election_location
        fed_keep = 'all'
    else:
        c_indx = election_location.index(',')
        folder_name = base_name + election_location[:c_indx]
        fed_keep = election_location[c_indx+1:]
        
    lxn_count = 0
    for file_name in os.listdir(folder_name):
        
        ## test code on few elections
        if 'Argyll' not in file_name:
            continue
    
        if fed_keep == 'no_Fed' and 'Federal' in file_name:
            continue
        if fed_keep == 'only_Fed' and 'Federal' not in file_name:
            continue
        
        file_path = folder_name+'/'+file_name
        
        lxn_count += 1
        # if lxn_count == 100:
        #     break
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
        
        # if num_cands>max_election_size:
        #     data = filter_weak_cands(data, num_cands, max_election_size)
        #     num_cands = max_election_size
        
        lxns.append([file_path, data, num_cands])

    return lxns



# def filter_weak_cands(profile, old_cand_num, new_cand_num):
    
#     cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
#                   'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
#                   'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
#                   'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
#                   '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
#                   '!', '@', '#', '$', '%']
#     cands = cand_names[:old_cand_num]
    
#     plurality_scores = {cand:0 for cand in cands}
#     for k in range(len(profile)):
#         plurality_scores[profile.at[k,'ballot'][0]] += profile.at[k,'Count']
    
#     cands.sort(key=lambda x: plurality_scores[x], reverse=True)
        
#     # mention_scores = {}
#     # for k in range(len(profile)):
#     #     count = profile.at[k, 'Count']
#     #     for cand in profile.at[k, 'ballot']:
#     #         if cand not in mention_scores.keys():
#     #             mention_scores[cand] = 0
#     #         mention_scores[cand] += count
#     # cands.sort(key=lambda x: mention_scores[x], reverse=True)
    
#     keep_cands = cands[:new_cand_num]
    
#     # print(plurality_scores)
#     # print(keep_cands)
    
#     new_ballot_list = []
#     new_count_list = []
    
#     for k in range(len(profile)):
#         ballot = profile.at[k, 'ballot']
#         new_ballot = ''
#         for cand in ballot:
#             if cand in keep_cands:
#                 new_ballot += cand_names[keep_cands.index(cand)]
#         # print(ballot, new_ballot)
                
#         if new_ballot:            
#             if new_ballot in new_ballot_list:
#                 indx = new_ballot_list.index(new_ballot)
#                 new_count_list[indx] += profile.at[k, 'Count']
#             else:
#                 new_ballot_list.append(new_ballot)
#                 new_count_list.append(profile.at[k, 'Count'])
     
#     df_dict = {'ballot': new_ballot_list, 'Count': new_count_list}
#     new_profile = pd.DataFrame(df_dict)
    
#     return new_profile



###############################################################################
##### Voter value functions
###############################################################################

def vv_borda_avg(ballot, cand, num_cands):
    max_score = num_cands - 1
    if cand in ballot:
        return max_score - ballot.index(cand)
    else:
        missing_num = num_cands-len(ballot)
        return (missing_num-1)/2


###############################################################################
##### Functions to modify profiles
###############################################################################

def voters_compromise(profile, voteMethod, num_cands, n, vote_frac=1, bury_deep=True, poll_noise=0, diagnostic=False):
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    winners = voteMethod(profile, cands, diagnostic=diagnostic)[0]
    if len(winners)!=1:
        print('##### WARNING: MULTIPLE WINNERS DETECTED ######')
        return []
    W=winners[0]
    if diagnostic:
        print(W)
        
    scores = {cand: 0.0 for cand in cands}
    for k in range(len(profile)):
        ballot = profile.at[k, 'ballot']
        scores[ballot[0]] += profile.at[k, 'Count']
    if poll_noise>0:
        for cand in cands:
            scores[cand] += rand.uniform(-poll_noise, poll_noise)
    poll_result = cands.copy()
    poll_result.sort(key = lambda x: scores[x], reverse=True)
    if diagnostic:
        print(scores)
        print(poll_result)
        
    new_profile = profile.copy(deep = True)
    modified_ballot_list = []
    
    for k in range(len(new_profile)):
        ## change the ballot in some way
        curBal = new_profile.at[k,'ballot']
        count = int(new_profile.at[k, 'Count']*vote_frac)
        modBal = compromise_top_n(curBal, poll_result, n, bury_deep=bury_deep)
        if curBal!=modBal:
            modified_ballot_list.append([curBal, modBal, count])
            new_profile.at[k, 'Count'] -= count
            new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [modBal], 'Count': [count]})], ignore_index=True)
    
    newWinners = voteMethod(new_profile, cands, diagnostic = diagnostic)[0]
    if len(newWinners)!=1:
        print('##### WARNING: MULTIPLE WINNERS DETECTED ######')
        return []
    nW = newWinners[0]
    
    if nW != W:
        total_value_change = 0
        total_change_count = 0
        for l in modified_ballot_list:
            curBal, modBal, count = l
            total_value_change += (vv_borda_avg(curBal, nW, num_cands) - vv_borda_avg(curBal, W, num_cands))*count
            total_change_count += count
        return [W, nW, total_value_change/total_change_count, poll_result.index(nW)]
    else:
        return []
        
###############################################################################
###############################################################################

def voters_bullet(profile, voteMethod, num_cands, n, vote_frac=1, poll_noise=0, diagnostic=False):
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    winners = voteMethod(profile, cands, diagnostic=diagnostic)[0]
    if len(winners)!=1:
        print('##### WARNING: MULTIPLE WINNERS DETECTED ######')
        return []
    W=winners[0]
    if diagnostic:
        print(W)
        
    scores = {cand: 0.0 for cand in cands}
    for k in range(len(profile)):
        ballot = profile.at[k, 'ballot']
        scores[ballot[0]] += profile.at[k, 'Count']
    if poll_noise>0:
        for cand in cands:
            scores[cand] += rand.uniform(-poll_noise, poll_noise)
    poll_result = cands.copy()
    poll_result.sort(key = lambda x: scores[x], reverse=True)
    if diagnostic:
        print(scores)
        print(poll_result)
        
    new_profile = profile.copy(deep = True)
    modified_ballot_list = []
    
    for k in range(len(new_profile)):
        ## change the ballot in some way
        curBal = new_profile.at[k,'ballot']
        count = int(new_profile.at[k, 'Count']*vote_frac)
        modBal = bullet_top_n(curBal, poll_result, n)
        if curBal!=modBal:
            modified_ballot_list.append([curBal, modBal, count])
            new_profile.at[k, 'Count'] -= count
            new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [modBal], 'Count': [count]})], ignore_index=True)
    
    newWinners = voteMethod(new_profile, cands, diagnostic = diagnostic)[0]
    if len(newWinners)!=1:
        print('##### WARNING: MULTIPLE WINNERS DETECTED ######')
        return []
    nW = newWinners[0]
    
    if nW != W:
        total_value_change = 0
        total_change_count = 0
        for l in modified_ballot_list:
            curBal, modBal, count = l
            total_value_change += (vv_borda_avg(curBal, nW, num_cands) - vv_borda_avg(curBal, W, num_cands))*count
            total_change_count += count
        return [W, nW, total_value_change/total_change_count, poll_result.index(nW)]
    else:
        return []

###############################################################################
###############################################################################

def voters_protect(profile, voteMethod, num_cands, n, vote_frac=1, bury_deep=True, poll_noise=0, diagnostic=False):
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    winners = voteMethod(profile, cands, diagnostic=diagnostic)[0]
    if len(winners)!=1:
        print('##### WARNING: MULTIPLE WINNERS DETECTED ######')
        return []
    W=winners[0]
    if diagnostic:
        print(W)
        
    scores = {cand: 0.0 for cand in cands}
    for k in range(len(profile)):
        ballot = profile.at[k, 'ballot']
        scores[ballot[0]] += profile.at[k, 'Count']
    if poll_noise>0:
        for cand in cands:
            scores[cand] += rand.uniform(-poll_noise, poll_noise)
    poll_result = cands.copy()
    poll_result.sort(key = lambda x: scores[x], reverse=True)
    if diagnostic:
        print(scores)
        print(poll_result)
        
    new_profile = profile.copy(deep = True)
    modified_ballot_list = []
    
    for k in range(len(new_profile)):
        ## change the ballot in some way
        curBal = new_profile.at[k,'ballot']
        count = int(new_profile.at[k, 'Count']*vote_frac)
        modBal = protect_top_n(curBal, poll_result, n, bury_deep=bury_deep)
        if curBal!=modBal:
            modified_ballot_list.append([curBal, modBal, count])
            new_profile.at[k, 'Count'] -= count
            new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [modBal], 'Count': [count]})], ignore_index=True)
    
    newWinners = voteMethod(new_profile, cands, diagnostic = diagnostic)[0]
    if len(newWinners)!=1:
        print('##### WARNING: MULTIPLE WINNERS DETECTED ######')
        return []
    nW = newWinners[0]
    
    if nW != W:
        total_value_change = 0
        total_change_count = 0
        for l in modified_ballot_list:
            curBal, modBal, count = l
            total_value_change += (vv_borda_avg(curBal, nW, num_cands) - vv_borda_avg(curBal, W, num_cands))*count
            total_change_count += count
        return [W, nW, total_value_change/total_change_count, poll_result.index(nW)]
    else:
        return []

###############################################################################
###############################################################################

def voters_score(profile, voteMethod, num_cands, poll_weight=1, vote_frac=1, bury_deep=True, poll_noise=0, diagnostic=False):
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    winners = voteMethod(profile, cands, diagnostic=diagnostic)[0]
    if len(winners)!=1:
        print('##### WARNING: MULTIPLE WINNERS DETECTED ######')
        return []
    W=winners[0]
    if diagnostic:
        print(W)
        
    scores = {cand: 0.0 for cand in cands}
    for k in range(len(profile)):
        ballot = profile.at[k, 'ballot']
        scores[ballot[0]] += profile.at[k, 'Count']
    if poll_noise>0:
        for cand in cands:
            scores[cand] += rand.uniform(-poll_noise, poll_noise)
    poll_result = cands.copy()
    poll_result.sort(key = lambda x: scores[x], reverse=True)
    if diagnostic:
        print(scores)
        print(poll_result)
        
    new_profile = profile.copy(deep = True)
    modified_ballot_list = []
    
    for k in range(len(new_profile)):
        ## change the ballot in some way
        curBal = new_profile.at[k,'ballot']
        count = int(new_profile.at[k, 'Count']*vote_frac)
        modBal = score_cands(curBal, poll_result, poll_weight=poll_weight)
        if curBal!=modBal:
            modified_ballot_list.append([curBal, modBal, count])
            new_profile.at[k, 'Count'] -= count
            new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [modBal], 'Count': [count]})], ignore_index=True)
    
    newWinners = voteMethod(new_profile, cands, diagnostic = diagnostic)[0]
    if len(newWinners)!=1:
        print('##### WARNING: MULTIPLE WINNERS DETECTED ######')
        return []
    nW = newWinners[0]
    
    if nW != W:
        total_value_change = 0
        total_change_count = 0
        for l in modified_ballot_list:
            curBal, modBal, count = l
            total_value_change += (vv_borda_avg(curBal, nW, num_cands) - vv_borda_avg(curBal, W, num_cands))*count
            total_change_count += count
        return [W, nW, total_value_change/total_change_count, poll_result.index(nW)]
    else:
        return []

###############################################################################
###############################################################################

def sort_search(params):
    lxn_method, strategy, file_path, profile, num_cands = params
    
    try:
        if strategy == voters_compromise:
            return [lxn_method.__name__, strategy.__name__, file_path, num_cands] + voters_compromise(profile, lxn_method, num_cands, compromise_n)
        elif strategy == voters_bullet:
            return [lxn_method.__name__, strategy.__name__, file_path, num_cands] + voters_bullet(profile, lxn_method, num_cands, bullet_n)
        elif strategy == voters_protect:
            return [lxn_method.__name__, strategy.__name__, file_path, num_cands] + voters_protect(profile, lxn_method, num_cands, protect_n)
        elif strategy == voters_score:
            return [lxn_method.__name__, strategy.__name__, file_path, num_cands] + voters_score(profile, lxn_method, num_cands)
        else:
            print('###############################')
            print('##### ERROR: STRATEGY BAD #####')
            print(strategy.__name__)
            print('###############################')
            return [strategy.__name__] 
    except:
        if callable(params[0]):
            method_name = params[0].__name__
        else:
            method_name = params[0]
        if callable(params[1]):
            mod_name = params[1].__name__
        else:
            mod_name = params[1]
        print('###############################################')
        print('###############################################')
        print('Error in election:', params[2])
        print('Election method:', method_name)
        print('Running search:', mod_name)
        print(traceback.format_exc())
        print('###############################################')
        print('###############################################')
        return [method_name, mod_name, params[2], params[4]]

###############################################################################
###############################################################################
##### Run this code
###############################################################################
###############################################################################

vote_fracs = [1 - i/frac for i in range(frac)]
if not os.path.exists(election_group.replace('/','_')+'_polling'):
    os.makedirs(election_group.replace('/','_')+'_polling')

# lxn_methods = [plurality, plurality_runoff, IRV, smith_irv, smith_plurality, 
               # minimax, smith_minimax, ranked_pairs, 
               # Borda_PM, Borda_OM, Borda_AVG, bucklin]
lxn_methods = [TVR_PM, TVR_OM, TVR_AVG, diversity_score_threshold]
# lxn_methods += [diversity_score_simplex]
lxn_methods += [friendly_fire_inst, friendly_fire_seq_smith, friendly_fire_inst_smith]
lxn_methods += [friendly_fire_inst_smith_exp]

voter_strategies = [voters_compromise, voters_bullet, voters_protect, voters_score]


if __name__ == '__main__':  
    ## get data
    lxn_list = get_election_data(election_group)
    
    gen_lxn_list = []
    for lxn in lxn_list:
        for lxn_method in lxn_methods:
            for strategy in voter_strategies:
                gen_lxn_list.append([lxn_method, strategy]+lxn)
    
    ## search for general anomalies
    pool = multiprocessing.Pool(processes=mp_pool_size)
    massive_results = pool.map(sort_search, gen_lxn_list)
    
    with open(election_group.replace('/','_')+"_polling/massive_results_data.json", "w") as f:
        json.dump(massive_results, f, cls=NpEncoder)
    
    
    prob_change_table = pd.DataFrame(0, index = [strategy.__name__ for strategy in voter_strategies], 
                                    columns = [lxn_method.__name__ for lxn_method in lxn_methods])
    exp_val_table = pd.DataFrame(0, index = [strategy.__name__ for strategy in voter_strategies], 
                                    columns = [lxn_method.__name__ for lxn_method in lxn_methods])
    new_win_pos_dict = {}
    
    for lxn in massive_results:
        lxn_method = lxn[0]
        strategy = lxn[1]
        combo = lxn_method+'_'+strategy
        if combo not in new_win_pos_dict.keys():
            new_win_pos_dict[combo] = []
        if len(lxn)>4:
            prob_change_table.at[strategy, lxn_method] += 1/len(lxn_list)
            exp_val_table.at[strategy, lxn_method] += np.mean(lxn[6])/len(lxn_list)
            new_win_pos_dict[combo].append(lxn[7])
            
            
    exp_val_table.to_csv(election_group.replace('/','_')+'_polling/expected_values.csv')
    prob_change_table.to_csv(election_group.replace('/','_')+'_polling/prob_change_winner.csv')
    
    new_win_exp_pos_table = pd.DataFrame(0, index = [strategy.__name__ for strategy in voter_strategies], 
                                    columns = [lxn_method.__name__ for lxn_method in lxn_methods])

    exp_val_table = pd.DataFrame(0, index = [strategy.__name__ for strategy in voter_strategies], 
                                    columns = [lxn_method.__name__ for lxn_method in lxn_methods])
    for lxn_method in [x.__name__ for x in lxn_methods]:
        for strategy in [y.__name__ for y in voter_strategies]:
            if new_win_pos_dict[lxn_method+'_'+strategy]:
                new_win_exp_pos_table.at[strategy, lxn_method] = np.mean(new_win_pos_dict[lxn_method+'_'+strategy])
            else:
                new_win_exp_pos_table.at[strategy, lxn_method] = -1
                
    new_win_exp_pos_table.to_csv(election_group.replace('/','_')+'_polling/winner_poll_positions.csv')
    
    
    
    




##############################################################
##### run searches, no multiprocessing
##############################################################



# print('##### Collecting election data #####')
# lxn_list = get_election_data('australia')

# print('##### Measuring outcomes #####')
# changed_elections = []
# for i in range(len(lxn_list)):
    
#     sys.stdout.write('\r')
#     sys.stdout.write('\r')
#     sys.stdout.write(f'Election {i+1}'+':' + lxn_list[i][0] + '                      ')
#     sys.stdout.flush()
    
#     lxn, profile, num_cands = lxn_list[i]
    
#     data = voters_compromise(profile, plurality_runoff, num_cands, 4)
    
#     if data:
#         changed_elections.append([lxn]+data)

