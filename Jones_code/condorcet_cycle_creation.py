###################################################
##### For every election, check if a voter bloc is 
##### able to create a condorcet cycle using
##### truncation or burying
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

from election_class import *
from ballot_modifications_class import *




###############################################################################
###############################################################################
##### parameters
## election_group should be of the form 'region/type'
## regions: Scotland, Australia, America
## types: single_winner, multi_winner, multi_winner_condensed
## if Australia/multi_winner (or multi_winner_condensed), end with ',no_Fed' or ',only_Fed' or ',all'
# election_group = 'Scotland/single_winner'
# election_group = 'Scotland/multi_winner'
# election_group = 'Scotland/multi_winner_condensed'
# election_group = 'Australia/single_winner'
# election_group = 'Australia/multi_winner,no_Fed'
# election_group = 'Australia/multi_winner,only_Fed'
election_group = 'Australia/multi_winner_condensed,no_Fed'
# election_group = 'Australia/multi_winner_condensed,only_Fed'
# election_group = 'America/single_winner'
# election_group = 'America/multi_winner'
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
        ballot = ''.join([cand_names[int(i)-1] for i in this_line_parts[1:-1]])
        if ballot!='':
            ballot_list.append(ballot)
            count_list.append(int(this_line_parts[0]))
        
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
        # if 'Argyll' not in file_name:
        #     continue
    
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
        # if num_cands>67:
        #     print("Cannot handle this many candidates in election " + str(file_path) + ".  Has " + 
        #           str(num_cands) + " candidates.")
        #     continue
            
        data = createBallotDF(lines)
        
        # if num_cands>max_election_size:
        #     data = filter_weak_cands(data, num_cands, max_election_size)
        #     num_cands = max_election_size
        
        lxns.append([file_path, data, num_cands])

    return lxns




#########################################################################
#########################################################################

def simple_strat(profile, cands, cond_winner, strat, diagnostic=False):
    
    losers = cands.copy()
    losers.remove(cond_winner)
    if diagnostic:
        print(losers)

    if strat.__name__ == 'strat_bury_deep':
        scores = {cand: 0.0 for cand in cands}
        
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
            if ballot=='':
                continue
            scores[ballot[0]] += profile.at[k, 'Count']
        
        cands_ranked = cands.copy()
        cands_ranked.sort(key = lambda x: scores[x])
    else:
        cands_ranked = []
    
    for L in losers:
        if diagnostic:
            print(L)
        ## Make a copy of original profile to modify
        new_profile = profile.copy(deep=True)
        modified_ballot_list = []
        
        for k in range(len(profile)):
            if new_profile.at[k,'ballot']=='':
                continue
            ## change the ballot in some way
            curBal = new_profile.at[k,'ballot']
            if (curBal[0] == L): 
                count = int(new_profile.at[k, 'Count'])
                modBal, modified = strat(curBal, cond_winner, L, cands_ranked)
                # new_profile.at[k,'ballot'] = modBal
                # if modified:
                if curBal!=modBal:
                    modified_ballot_list.append([curBal, modBal, count])
                    new_profile.at[k, 'Count'] -= count
                    new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [modBal], 'Count': [count]})], ignore_index=True)
            
        new_smith_set = restrict_to_smith(new_profile, cands)[0]
        if diagnostic:
            print(new_smith_set)
        if len(new_smith_set)>1 and L in new_smith_set:
            return [L, new_smith_set]

    return []

















cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
              'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
              'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
              'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

strats = [strat_truncate_L, strat_truncate_W, strat_bury_shallow, strat_bury_deep]

start_time = time.time()
print('##### Collecting election data #####')
print(f'Election group: {election_group}')
lxn_list = get_election_data(election_group)
print(time.time()-start_time)


## check condensed elections for empty ballots
# for i, lxn in enumerate(lxn_list):
#     profile = lxn[1]
#     if '' in list(profile['ballot']):
#         print(i, lxn[0], list(profile['ballot']).index(''))


cond_winner_count = 0
simple_strat_hits = {strat.__name__:0 for strat in strats}
# smart_strat_hits = {strat.__name__:0 for strat in strats}

print('##### Creating Top Cycles #####')
for i, lxn in enumerate(lxn_list):
    sys.stdout.write('\r')
    sys.stdout.write('\r')
    sys.stdout.write(f'Election {i+1}'+':' + lxn[0] + '                      ')
    sys.stdout.flush()
    
    profile = lxn[1]
    num_cands = min([15, lxn[2]])
    cands = cand_names[:num_cands]
    smith_set = restrict_to_smith(profile, cands)[0]
    
    if len(smith_set)!=1:
        continue
    
    cond_winner_count += 1
    CW = smith_set[0]
    
    
    ##### simple strats
    for strat in strats:
        if simple_strat(profile, cands, CW, strat):
            simple_strat_hits[strat.__name__] += 1
    
    
    # ##### smart strats
    # ## compute H2H margins
    # margins = np.zeros((num_cands, num_cands))
    
    # for c1 in range(num_cands):
    #     for c2 in range(c1+1, num_cands):
    #         c1_let = cands[c1]
    #         c2_let = cands[c2]
    #         ## number of votes c1 gets over c2 in H2H
    #         margin = 0
            
    #         for k in range(len(profile)):
    #             ballot = profile.at[k, 'ballot']
    #             count = profile.at[k, 'Count']
    #             ## ballot ranks both c1 and c2
    #             if c1_let in ballot and c2_let in ballot:
    #                 if ballot.find(c1_let) < ballot.find(c2_let):
    #                     margin += count
    #                 else:
    #                     margin -= count
    #             ## ballot only ranks c1       
    #             elif c1_let in ballot:
    #                 margin += count
    #             ## ballot only ranks c2
    #             elif c2_let in ballot:
    #                 margin -= count
            
    #         margins[c1, c2] = margin
    #         margins[c2, c1] = -1*margin
    
print()
print(simple_strat_hits)
        
    








