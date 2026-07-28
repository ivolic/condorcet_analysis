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
import time

##### STAR scoring methods #####

def STAR_low(ballot, cands, pos_scores):
    ballot_scores = {}
    for i in range(len(ballot)):
        ballot_scores[ballot[i]] = max(5-i,0)
    return ballot_scores


def STAR_mid(ballot, cands, pos_scores):
    ballot_scores = {}
    for i in range(len(ballot)):
        ballot_scores[ballot[i]] = pos_scores[i]
    return ballot_scores


def STAR_high(ballot, cands, pos_scores):
    ballot_scores = {}
    for i in range(len(ballot)):
        ballot_scores[ballot[i]] = min(5, len(cands)-i-1)
    return ballot_scores





###############################################################################
###############################################################################
##### parameters
election_group = 'Scotland'
frac = 1
mp_pool_size = 10
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





#############################################################
##### STAR voting methods
#############################################################

def star_voting(profile, cands, star_strat, diagnostic=False):
    mid_score_positions = [max(5-int(i/len(cands)*6),0) for i in range(len(cands))]
    scores = {cand: 0 for cand in cands}
    
    ## compute STAR scores
    for k in range(len(profile)):
        ballot = profile.at[k, 'ballot']
        count = profile.at[k, 'Count']
        ballot_scores = star_strat(ballot, cands, mid_score_positions)
        for cand in ballot_scores.keys():
            scores[cand] += count*ballot_scores[cand]       
    top_two = sorted(scores, key=scores.get, reverse=True)[:2]
    
    ## head-to-head
    c1 = top_two[0]
    c1_votes = 0
    c2 = top_two[1]
    c2_votes = 0
    for k in range(len(profile)):
        ballot = profile.at[k, 'ballot']
        count = profile.at[k, 'Count']
        if (c1 in ballot and c2 not in ballot) or (c1 in ballot and c2 in ballot and ballot.index(c1)<ballot.index(c2)):
            c1_votes += count
        elif (c2 in ballot and c1 not in ballot) or (c2 in ballot and c1 in ballot and ballot.index(c2)<ballot.index(c1)):
            c2_votes += count
    
    if c1_votes > c2_votes:
        return c1
    elif c2_votes > c1_votes:
        return c2
    else:
        print('WARNING: TIE')
        return [c1, c2]
    
    
    
def strategic_star_voting(profile, cands, special_cand, base_strat, special_strat, diagnostic=False):
    mid_score_positions = [max(5-int(i/len(cands)*6),0) for i in range(len(cands))]
    scores = {cand: 0 for cand in cands}
    
    ## compute STAR scores
    for k in range(len(profile)):
        ballot = profile.at[k, 'ballot']
        count = profile.at[k, 'Count']
        if ballot[0]==special_cand:
            ballot_scores = special_strat(ballot, cands, mid_score_positions)
        else:
            ballot_scores = base_strat(ballot, cands, mid_score_positions)
        for cand in ballot_scores.keys():
            scores[cand] += count*ballot_scores[cand] 
    if diagnostic:
        print(scores)
        
    top_two = sorted(scores, key=scores.get, reverse=True)[:2]
    
    ## head-to-head
    c1 = top_two[0]
    c1_votes = 0
    c2 = top_two[1]
    c2_votes = 0
    for k in range(len(profile)):
        ballot = profile.at[k, 'ballot']
        count = profile.at[k, 'Count']
        if (c1 in ballot and c2 not in ballot) or (c1 in ballot and c2 in ballot and ballot.index(c1)<ballot.index(c2)):
            c1_votes += count
        elif (c2 in ballot and c1 not in ballot) or (c2 in ballot and c1 in ballot and ballot.index(c2)<ballot.index(c1)):
            c2_votes += count
    if diagnostic:
        print(top_two, c1_votes, c2_votes)
    
    if c1_votes > c2_votes:
        return c1
    elif c2_votes > c1_votes:
        return c2
    else:
        print('WARNING: TIE')
        return [c1, c2]





#############################################################
##### Run this code
#############################################################

cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
              'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
              'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
              'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
              '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
              '!', '@', '#', '$', '%']

print('##### Collecting election data #####')
lxn_list = get_election_data(election_group)


print('##### Running elections #####')
print('###################################')

victory_counts = np.zeros((3,3))
for i in range(len(lxn_list)):
    
    # start_time = time.time()
    sys.stdout.write('\r')
    sys.stdout.write('\r')
    sys.stdout.write(f'Election {i+1}'+':' + lxn_list[i][0] + '                      ')
    sys.stdout.flush()
    
    lxn, profile, num_cands = lxn_list[i]
    cands = cand_names[:num_cands]
    
    star_strats = [STAR_low, STAR_mid, STAR_high]
    for strat_i, base_strat in enumerate(star_strats):
        for strat_j, special_strat in enumerate(star_strats):
            for special_cand in cands:
                # print(base_strat.__name__, special_strat.__name__, special_cand)
                winner = strategic_star_voting(profile, cands, special_cand, base_strat, special_strat)
                if winner == special_cand:
                    victory_counts[[strat_i, strat_j]]+=1




















