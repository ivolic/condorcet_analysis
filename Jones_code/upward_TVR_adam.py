#upward_TVR_adam

### helper programs, generic ####

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
from itertools import combinations

def Borda_PM(profile, cands, diagnostic=False):
    
    num_cands = len(cands)
    max_score = num_cands - 1
    
    ## compute candidate scores
    cand_scores = {cand: 0 for cand in cands}
    for k in range(len(profile)):
        count = profile.at[k, 'Count']
        curBal= profile.at[k, 'ballot']
        for i in range(0,len(curBal)):
            candidate = curBal[i]
            if candidate in cands:
                cand_scores[candidate] += (max_score - (i )) * count
            # else:
            #     print("Candidate in ballot that is not in candidate list")
    
    
        
    max_score = max(cand_scores.values())
    winners = [cand for cand, score in cand_scores.items() if score == max_score]

    if diagnostic:
        print(cand_scores)
        print("Winner is " + str(winners))
        
    return [winners]

def BordaScores_PM(profile, cands, diagnostic=False):
    '''takes in voting data, returns all Borda scores'''
    
    num_cands = len(cands)
    max_score = num_cands - 1
    
    ## compute candidate scores
    cand_scores = {cand: 0 for cand in cands}
    for k in range(len(profile)):
        count = profile.at[k, 'Count']
        curBal= profile.at[k, 'ballot']
        for i in range(0,len(curBal)):
            candidate = curBal[i]
            if candidate in cands:
                cand_scores[candidate] += (max_score - (i )) * count
            # else:
            #     print("Candidate in ballot that is not in candidate list")
    
    return cand_scores
        

def BordaLoser_PM(profile, cands, diagnostic=False):
    cand_scores = BordaScores_PM(profile, cands, diagnostic=False)
    min_score = min(cand_scores.values())
    losers = [cand for cand, score in cand_scores.items() if score == min_score]

    if diagnostic:
        print(cand_scores)
        print("Loser is " + str(losers))
        
    return [losers]



###############################################################################
###############################################################################

def Borda_OM(profile, cands, diagnostic=False):
    
    num_cands = len(cands)
    max_score = num_cands - 1
    
    ## compute candidate scores
    cand_scores = {cand: 0 for cand in cands}
    for k in range(len(profile)):
        count = profile.at[k, 'Count']
        curBal= profile.at[k, 'ballot']
        for i in range(0,len(curBal)):
            candidate = curBal[i]
            if candidate in cands:
                cand_scores[candidate] += (max_score - (i )) * count
            # else:
            #     print("Candidate in ballot that is not in candidate list")
        
        ## add score for all candidates not on ballot
        for cand in cands:
            if cand not in curBal:
                cand_scores[cand] += (max_score - len(curBal)) * count
       
    max_score = max(cand_scores.values())
    winners = [cand for cand, score in cand_scores.items() if score == max_score]
    if diagnostic:
        print(cand_scores)
        print("Winner is " + str(winners))
        
    return [winners]


def BordaScores_OM(profile, cands, diagnostic=False):
    '''takes in voting data, returns all Borda scores'''
    
    num_cands = len(cands)
    max_score = num_cands - 1
    
    ## compute candidate scores
    cand_scores = {cand: 0 for cand in cands}
    for k in range(len(profile)):
        count = profile.at[k, 'Count']
        curBal= profile.at[k, 'ballot']
        for i in range(0,len(curBal)):
            candidate = curBal[i]
            if candidate in cands:
                cand_scores[candidate] += (max_score - (i )) * count
            # else:
            #     print("Candidate in ballot that is not in candidate list")
        
        ## add score for all candidates not on ballot
        for cand in cands:
            if cand not in curBal:
                cand_scores[cand] += (max_score - len(curBal)) * count
    
    return cand_scores
        

def BordaLoser_OM(profile, cands, diagnostic=False):
    cand_scores = BordaScores_OM(profile, cands, diagnostic=False)
    min_score = min(cand_scores.values())
    losers = [cand for cand, score in cand_scores.items() if score == min_score]

    if diagnostic:
        print(cand_scores)
        print("Loser is " + str(losers))
        
    return [losers]



###############################################################################
###############################################################################

def Borda_AVG(profile, cands, diagnostic=False):
    
    num_cands = len(cands)
    max_score = num_cands - 1
    
    ## compute candidate scores
    cand_scores = {cand: 0 for cand in cands}
    for k in range(len(profile)):
        count = profile.at[k, 'Count']
        curBal= profile.at[k, 'ballot']
        for i in range(0,len(curBal)):
            candidate = curBal[i]
            if candidate in cands:
                cand_scores[candidate] += (max_score - (i )) * count
            # else:
            #     print("Candidate in ballot that is not in candidate list")
        
        ## add score for all candidates not on ballot
        missing_cand_num = num_cands - len(curBal) 
        avg_points = (missing_cand_num - 1)/2
        for cand in cands:
            if cand not in curBal:
                cand_scores[cand] += avg_points * count
        
    max_score = max(cand_scores.values())
    winners = [cand for cand, score in cand_scores.items() if score == max_score]
    if diagnostic:
        print(cand_scores)
        print("Winner is " + str(winners))
        
    return [winners]


def BordaScores_AVG(profile, cands, diagnostic=False):
    '''takes in voting data, returns all Borda scores'''
    
    num_cands = len(cands)
    max_score = num_cands - 1
    
    ## compute candidate scores
    cand_scores = {cand: 0 for cand in cands}
    for k in range(len(profile)):
        count = profile.at[k, 'Count']
        curBal= profile.at[k, 'ballot']
        for i in range(0,len(curBal)):
            candidate = curBal[i]
            if candidate in cands:
                cand_scores[candidate] += (max_score - (i )) * count
        
        ## add score for all candidates not on ballot
        missing_cand_num = num_cands - len(curBal) 
        avg_points = (missing_cand_num - 1)/2
        for cand in cands:
            if cand not in curBal:
                cand_scores[cand] += avg_points * count
        
    
    return cand_scores
        

def BordaLoser_AVG(profile, cands, diagnostic=False):
    cand_scores = BordaScores_AVG(profile, cands, diagnostic=False)
    min_score = min(cand_scores.values())
    losers = [cand for cand, score in cand_scores.items() if score == min_score]

    if diagnostic:
        print(cand_scores)
        print("Loser is " + str(losers))
        
    return [losers]

###############################################################################
###############################################################################




def TVR_OM(profile, cands, diagnostic=False): #with majority check
    hopefuls = cands.copy()
    new_profile = profile.copy(deep=True)
    if diagnostic:
        print(new_profile)
        
    while len(hopefuls)>1:
        maj, winner = majorityCheck(new_profile, hopefuls)
        if maj == True:
            return [name for name in hopefuls if name == winner]
        
        max_score = len(hopefuls)-1
        scores = {cand: 0 for cand in hopefuls}
        
        for k in range(len(new_profile)):
            count = new_profile.at[k, 'Count']
            curBal= new_profile.at[k, 'ballot']
            if curBal == '':
                continue
            for i in range(0,len(curBal)):
                candidate = curBal[i]
                if candidate in hopefuls:
                    scores[candidate] += (max_score - (i )) * count
                # else:
                #     print("Candidate in ballot that is not in candidate list")
            
            ## add score for all candidates not on ballot
            for cand in hopefuls:
                if cand not in curBal:
                    scores[cand] += (max_score - len(curBal)) * count

        ## remove loser from election
        remove_cand = [cand for cand in hopefuls if scores[cand]==min(scores.values())]
        if len(remove_cand)>1:
            print('#####Tie in Borda score!#####')
            
        if diagnostic:
            print(scores)
            print(remove_cand)
        
        remove_cand = remove_cand[0]
        hopefuls.remove(remove_cand)
        
        for k in range(len(new_profile)):
            if remove_cand in new_profile.iloc[k]['ballot']:
                new_profile.at[k,'ballot']=new_profile.at[k,'ballot'].replace(remove_cand,'')
        
        if diagnostic:
            print(new_profile)
        
    return hopefuls


def TVR_OM_NoMajCheck(profile, cands, diagnostic=False): #with majority check
    hopefuls = cands.copy()
    new_profile = profile.copy(deep=True)
    if diagnostic:
        print(new_profile)
        
    while len(hopefuls)>1:
#         maj, winner = majorityCheck(new_profile, hopefuls)
#         if maj == True:
#             return [name for name in hopefuls if name == winner]
        
        max_score = len(hopefuls)-1
        scores = {cand: 0 for cand in hopefuls}
        
        for k in range(len(new_profile)):
            count = new_profile.at[k, 'Count']
            curBal= new_profile.at[k, 'ballot']
            if curBal == '':
                continue
            for i in range(0,len(curBal)):
                candidate = curBal[i]
                if candidate in hopefuls:
                    scores[candidate] += (max_score - (i )) * count
                # else:
                #     print("Candidate in ballot that is not in candidate list")
            
            ## add score for all candidates not on ballot
            for cand in hopefuls:
                if cand not in curBal:
                    scores[cand] += (max_score - len(curBal)) * count

        ## remove loser from election
        remove_cand = [cand for cand in hopefuls if scores[cand]==min(scores.values())]
        if len(remove_cand)>1:
            print('#####Tie in Borda score!#####')
            
        if diagnostic:
            print(scores)
            print(remove_cand)
        
        remove_cand = remove_cand[0]
        hopefuls.remove(remove_cand)
        
        for k in range(len(new_profile)):
            if remove_cand in new_profile.iloc[k]['ballot']:
                new_profile.at[k,'ballot']=new_profile.at[k,'ballot'].replace(remove_cand,'')
        
        if diagnostic:
            print(new_profile)
        
    return hopefuls






def TVR_PM(profile, cands, diagnostic=False):
    hopefuls = cands.copy()
    new_profile = profile.copy(deep=True)
    if diagnostic:
        print(new_profile)
        
    while len(hopefuls)>1:
        max_score = len(hopefuls)-1
        scores = {cand: 0 for cand in hopefuls}
        
        maj, winner = majorityCheck(new_profile, hopefuls)
        if maj == True:
            return [name for name in hopefuls if name == winner]
        
        for k in range(len(new_profile)):
            count = new_profile.at[k, 'Count']
            curBal= new_profile.at[k, 'ballot']
            if curBal == '':
                continue
            for i in range(0,len(curBal)):
                candidate = curBal[i]
                if candidate in hopefuls:
                    scores[candidate] += (max_score - (i )) * count
        
        ## remove loser from election
        remove_cand = [cand for cand in hopefuls if scores[cand]==min(scores.values())]
        if len(remove_cand)>1:
            print('#####Tie in Borda score!#####')
            
        if diagnostic:
            print("now printing scores")
            print(scores)
            #print(remove_cand)
        
        remove_cand = remove_cand[0]
        hopefuls.remove(remove_cand)
        
        for k in range(len(new_profile)):
            if remove_cand in new_profile.iloc[k]['ballot']:
                new_profile.at[k,'ballot']=new_profile.at[k,'ballot'].replace(remove_cand,'')
        
        if diagnostic:
            print(new_profile)
        
    return hopefuls

def TVR_PM_withMods(profile, cands, diagnostic=False):
    hopefuls = cands.copy()
    new_profile = profile.copy(deep=True)
#     if diagnostic:
#         print(new_profile)
        
    while len(hopefuls)>1:
        max_score = len(hopefuls)-1
        scores = {cand: 0 for cand in hopefuls}
        
        maj, winner = majorityCheck(new_profile, hopefuls)
        if maj == True:
            return [name for name in hopefuls if name == winner]
        
        for k in range(len(new_profile)):
            count = new_profile.at[k, 'Count']
            curBal= new_profile.at[k, 'ballot_modified']
            if curBal == '':
                continue
            for i in range(0,len(curBal)):
                candidate = curBal[i]
                if candidate in hopefuls:
                    scores[candidate] += (max_score - (i )) * count
        
        ## remove loser from election
        remove_cand = [cand for cand in hopefuls if scores[cand]==min(scores.values())]
        if len(remove_cand)>1:
            print('#####Tie in Borda score!#####')
            
        if diagnostic:
            print("now printing scores")
            print(scores)
            #print(remove_cand)
        
        remove_cand = remove_cand[0]
        hopefuls.remove(remove_cand)
        
        for k in range(len(new_profile)):
            if remove_cand in new_profile.iloc[k]['ballot_modified']:
                new_profile.at[k,'ballot_modified']=new_profile.at[k,'ballot_modified'].replace(remove_cand,'')
        
#         if diagnostic:
#             print(new_profile)
        
    return hopefuls

def TVR_PM_NoMajCheck(profile, cands, diagnostic=False):
    hopefuls = cands.copy()
    new_profile = profile.copy(deep=True)
    if diagnostic:
        print(new_profile)
        
    while len(hopefuls)>1:
        max_score = len(hopefuls)-1
        scores = {cand: 0 for cand in hopefuls}
        
#         maj, winner = majorityCheck(new_profile, hopefuls)
#         if maj == True:
#             return [name for name in hopefuls if name == winner]
        
        for k in range(len(new_profile)):
            count = new_profile.at[k, 'Count']
            curBal= new_profile.at[k, 'ballot']
            if curBal == '':
                continue
            for i in range(0,len(curBal)):
                candidate = curBal[i]
                if candidate in hopefuls:
                    scores[candidate] += (max_score - (i )) * count
        
        ## remove loser from election
        remove_cand = [cand for cand in hopefuls if scores[cand]==min(scores.values())]
        if len(remove_cand)>1:
            print('#####Tie in Borda score!#####')
            
        if diagnostic:
            print(scores)
            print(remove_cand)
        
        remove_cand = remove_cand[0]
        hopefuls.remove(remove_cand)
        
        for k in range(len(new_profile)):
            if remove_cand in new_profile.iloc[k]['ballot']:
                new_profile.at[k,'ballot']=new_profile.at[k,'ballot'].replace(remove_cand,'')
        
        if diagnostic:
            print(new_profile)
        
    return hopefuls



def TVR_AVG(profile, cands, diagnostic=False):
    hopefuls = cands.copy()
    new_profile = profile.copy(deep=True)
    if diagnostic:
        print(new_profile)
        
    while len(hopefuls)>1:
        maj, winner = majorityCheck(new_profile, hopefuls)
        if maj == True:
            return [name for name in hopefuls if name == winner]
        
        max_score = len(hopefuls)-1
        scores = {cand: 0 for cand in hopefuls}

        for k in range(len(new_profile)):
            count = new_profile.at[k, 'Count']
            curBal= new_profile.at[k, 'ballot']
            if curBal == '':
                continue
            for i in range(0,len(curBal)):
                candidate = curBal[i]
                if candidate in hopefuls:
                    scores[candidate] += (max_score - (i )) * count
                # else:
                #     print("Candidate in ballot that is not in candidate list")
            
            ## add score for all candidates not on ballot
            missing_cand_num = len(hopefuls) - len(curBal) 
            avg_points = (missing_cand_num - 1)/2
            for cand in hopefuls:
                if cand not in curBal:
                    scores[cand] += avg_points * count
        
        ## remove loser from election
        remove_cand = [cand for cand in hopefuls if scores[cand]==min(scores.values())]
        if len(remove_cand)>1:
            print('#####Tie in Borda score!#####')
            
        if diagnostic:
            print(scores)
            print(remove_cand)
        
        remove_cand = remove_cand[0]
        hopefuls.remove(remove_cand)
        
        for k in range(len(new_profile)):
            if remove_cand in new_profile.iloc[k]['ballot']:
                new_profile.at[k,'ballot']=new_profile.at[k,'ballot'].replace(remove_cand,'')
        
        if diagnostic:
            print(new_profile)
        
    return hopefuls
    
def TVR_AVG_NoMajCheck(profile, cands, diagnostic=False):
    hopefuls = cands.copy()
    new_profile = profile.copy(deep=True)
    if diagnostic:
        print(new_profile)
        
    while len(hopefuls)>1:
#         maj, winner = majorityCheck(new_profile, hopefuls)
#         if maj == True:
#             return [name for name in hopefuls if name == winner]
        
        max_score = len(hopefuls)-1
        scores = {cand: 0 for cand in hopefuls}

        for k in range(len(new_profile)):
            count = new_profile.at[k, 'Count']
            curBal= new_profile.at[k, 'ballot']
            if curBal == '':
                continue
            for i in range(0,len(curBal)):
                candidate = curBal[i]
                if candidate in hopefuls:
                    scores[candidate] += (max_score - (i )) * count
                # else:
                #     print("Candidate in ballot that is not in candidate list")
            
            ## add score for all candidates not on ballot
            missing_cand_num = len(hopefuls) - len(curBal) 
            avg_points = (missing_cand_num - 1)/2
            for cand in hopefuls:
                if cand not in curBal:
                    scores[cand] += avg_points * count
        
        ## remove loser from election
        remove_cand = [cand for cand in hopefuls if scores[cand]==min(scores.values())]
        if len(remove_cand)>1:
            print('#####Tie in Borda score!#####')
            
        if diagnostic:
            print(scores)
            print(remove_cand)
        
        remove_cand = remove_cand[0]
        hopefuls.remove(remove_cand)
        
        for k in range(len(new_profile)):
            if remove_cand in new_profile.iloc[k]['ballot']:
                new_profile.at[k,'ballot']=new_profile.at[k,'ballot'].replace(remove_cand,'')
        
        if diagnostic:
            print(new_profile)
        
    return hopefuls

def majorityCheck (profile, hopefuls): #hopefuls are candidates
    quota=math.floor(sum(profile['Count'])/(2))+1
    vote_counts={cand:0 for cand in hopefuls}
    # vote_counts = {}
    
    for k in range(len(profile)):
            if profile.at[k,'ballot']!='':
                if profile.at[k,'ballot'][0] in vote_counts.keys():
                    vote_counts[profile.at[k,'ballot'][0]]+=profile.iloc[k]['Count']
                else:
                    vote_counts[profile.at[k,'ballot'][0]]=profile.iloc[k]['Count']

        
    max_count=max(vote_counts.values())
    if max_count>=quota: 
        winner = max(vote_counts, key=vote_counts.get)
        return True, winner
    else:
        return False, 'foo'


#code for reducing profile to just a subset (Written by Gemini)
import pandas as pd

def reduceProfile(df, keep_list):
    # Create a deep copy to avoid modifying the original dataframe
    new_df = df.copy(deep=True)
    
    # Create a translation table or a set for faster lookup
    # This removes any character found in 'remove_list'
    to_keep = set(keep_list)
    
    def filter_ballot(ballot_str):
        # Keep the character only if it IS in our keep list
        return "".join([char for char in ballot_str if char in to_keep])
    
    # Apply the filtering to the 'ballot' column
    new_df['ballot'] = new_df['ballot'].apply(filter_ballot)
    
    # Optional: If removing candidates results in an empty string (e.g. ballot was 'BC'),
    # you might want to remove those rows. If not, keep this as is.
    
    return new_df

# code to get list of candidates from a profile (dataframe) (Written by Gemini)
def getCands(df):
    # 1. Use a set to store unique characters (candidates)
    candidates = set()
    
    # 2. Iterate through the 'ballot' column
    for ballot in df['ballot']:
        # Adding a string to a set adds each unique character individually
        candidates.update(ballot)
    
    # 3. Return as a sorted list for consistency
    return sorted(list(candidates))

# code to get list of candidates from a profile (dataframe) (Written by Gemini)
def getCands_OG(df):
    # 1. Use a set to store unique characters (candidates)
    candidates = set()
    
    # 2. Iterate through the 'ballot' column
    for ballot in df['ballot_OG']:
        # Adding a string to a set adds each unique character individually
        candidates.update(ballot)
    
    # 3. Return as a sorted list for consistency
    return sorted(list(candidates))



#code to get next-lowest
def get_lowest_remaining(results_dict, excluded_list): #(Written by Gemini)
    # 1. Filter the dictionary to only include keys NOT in the excluded_list
    remaining = {k: v for k, v in results_dict.items() if k not in excluded_list}
    
    # 2. If there are no candidates left, handle the empty case
    if not remaining:
        return None
    
    # 3. Find the key with the minimum value
    # min() will look at the values but return the corresponding key
    lowest_key = min(remaining, key=remaining.get)
    
    return lowest_key

def shift_candidate(ballot, L, W): #(thanks Gemini!)
    #This will work for modifying OG ballots
    # Ensure both characters are in the ballot
    if L not in ballot or W not in ballot:
        return ballot
    
    # Check if W is currently ranked lower (higher index) than L
    l_idx = ballot.find(L)
    w_idx = ballot.find(W)
    
    if w_idx > l_idx:
        # Convert to list to allow modification
        temp_list = list(ballot)
        
        # 1. Remove W from its current position
        temp_list.pop(w_idx)
        
        # 2. Insert W at the index where L currently is
        # This pushes L to the right
        temp_list.insert(l_idx, W)
        
        return "".join(temp_list)
    
    # If W is already before L, return original ballot
    return ballot

def filter_weak_cands(profile, old_cand_num, new_cand_num):
    cands = getCands(profile)
   
    plurality_scores = {cand:0 for cand in cands}
    for k in range(len(profile)):
        plurality_scores[profile.at[k,'ballot'][0]] += profile.at[k,'Count']
   
    cands.sort(key=lambda x: plurality_scores[x], reverse=True)
       
    keep_cands = cands[:new_cand_num]
   
    new_ballot_list = []
    new_count_list = []
   
    for k in range(len(profile)):
        ballot = profile.at[k, 'ballot']
        new_ballot = ''
        for cand in ballot:
            if cand in keep_cands:
                new_ballot += cand#_names[keep_cands.index(cand)]
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

def reduceToTopN(df, keep_num):
    #Note: this reduces profile to new number of candidates, keeps their letters same as original
    
    # Create a deep copy to avoid modifying the original dataframe
    new_df = df.copy(deep=True)
    
    #run plurality to find top keep_num cands, call that the keep_list
    cands = getCands(new_df)
   
    plurality_scores = {cand:0 for cand in cands}
    for k in range(len(new_df)):
        
        ballot = new_df.at[k, 'ballot']
        if len(ballot)>0:
            first_choice = ballot[0]
        else:
            continue
        if ballot and first_choice in plurality_scores:
            plurality_scores[first_choice] += new_df.at[k,'Count']
        else:
            print("Skipping invalid ballot at row", k, ":", ballot)

    cands.sort(key=lambda x: plurality_scores[x], reverse=True)
       
   
    keep_list = cands[:keep_num]
    
    # Create a translation table or a set for faster lookup
    # This removes any character found in 'remove_list'
    to_keep = set(keep_list)
    
    def filter_ballot(ballot_str):
        # Keep the character only if it IS in our keep list
        return "".join([char for char in ballot_str if char in to_keep])
    
    # Apply the filtering to the 'ballot' column
    new_df['ballot'] = new_df['ballot'].apply(filter_ballot)
    
    # Optional: If removing candidates results in an empty string (e.g. ballot was 'BC'),
    # you might want to remove those rows. If not, keep this as is.
    
    return new_df

def bufferCheck1(ballot, L, W, ksnw):
    if len(ballot) < 3:
        return False
    # Convert ballot to a list for easier slicing/replacement
    temp_list = list(ballot)
    
    # Iterate through the string to find the L_W pattern
    # We stop at len - 2 because we are looking for a 3-character window
    for i in range(len(temp_list) - 2):
        char_1 = temp_list[i]     # Potential L
        char_2 = temp_list[i + 1] # Potential buffer (_)
        char_3 = temp_list[i + 2] # Potential W
        
        # Check the conditions: First char is L, Third char is W, Middle char is in the ksnw set
        if char_1 == L and char_3 == W and char_2 in ksnw:
            return True

        
def shift_with_buffer1(ballot, L, W, ksnw):
    # We need at least 3 characters for the pattern L_W to exist
    if len(ballot) < 3:
        return ballot
    
    # Convert ballot to a list for easier slicing/replacement
    temp_list = list(ballot)
    
    # Iterate through the string to find the L_W pattern
    # We stop at len - 2 because we are looking for a 3-character window
    for i in range(len(temp_list) - 2):
        char_1 = temp_list[i]     # Potential L
        char_2 = temp_list[i + 1] # Potential buffer (_)
        char_3 = temp_list[i + 2] # Potential W
        
        # Check the conditions:
        # 1. First char is L
        # 2. Third char is W
        # 3. Middle char is in the ksnw set
        if char_1 == L and char_3 == W and char_2 in ksnw:
            # Modify the pattern: L _ W  ->  W L _
            temp_list[i] = W
            temp_list[i + 1] = L
            temp_list[i + 2] = char_2
            
            # If you only want to change the FIRST occurrence, 
            # you can return here. Otherwise, it will keep looking.
            return "".join(temp_list)    
        
    return ballot

def shift_with_buffer(ballot, L, W, ksnw): #written by Gemini
    # We need at least 3 characters for the pattern L_W to exist
    if len(ballot) < 3:
        return ballot
    
    # Convert ballot to a list for easier slicing/replacement
    temp_list = list(ballot)
    
    # Iterate through the string to find the L_W pattern
    # We stop at len - 2 because we are looking for a 3-character window
    for i in range(len(temp_list) - 2):
        char_1 = temp_list[i]     # Potential L
        char_2 = temp_list[i + 1] # Potential buffer (_)
        char_3 = temp_list[i + 2] # Potential W
        
        # Check the conditions:
        # 1. First char is L
        # 2. Third char is W
        # 3. Middle char is in the ksnw set
        if char_1 == L and char_3 == W and char_2 in ksnw:
            # Modify the pattern: L _ W  ->  W L _
            temp_list[i] = W
            temp_list[i + 1] = L
            temp_list[i + 2] = char_2
            
            # If you only want to change the FIRST occurrence, 
            # you can return here. Otherwise, it will keep looking.
            return "".join(temp_list)
            
    return ballot



def prefProfileInput5(rawData): 
    """Inputs raw preference profile (in standard Scottish form) and returns pandas
    dataframe with ballot, count, OG ballot/count and modified columns, ballots converted letters from numbers, 
    as well as list of candidates"""
    File=open(rawData,'r') #'moray17-03.blt'    NoShowAnomalyElections/edinburgh17-04.blt
    lines=File.readlines()

    first_space=lines[0].find(' ')

    num_cands=int(lines[0][0:first_space])
    #num_seats=int(lines[0][first_space+1])
    foo = ['X']
    
    column_names=['ballot','Count', 'ballot_OG', 'Count_OG', 'ballot_modified']
    data=pd.DataFrame(columns = column_names)
    if num_cands > 67:
        print('election greater than 67 candidates')
        return data, foo, num_cands
    list1=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z', '0', '1','2','3','4','5','6','7','8','9','!','@','#','$','%' ]
    cands=[list1[i] for i in range(num_cands)]
    
    candidates = []
    for k in range(1,len(lines)):
        if lines[k][0]=='0':
            break
        first_space=lines[k].find(' ')
        count=int(lines[k][0:first_space])
        end=lines[k].find(' 0')
        ballot=lines[k][first_space+1:end+1]
        if '10 ' in ballot:
            ballot=ballot.replace('10 ','J ')
        if '11 ' in ballot:
            ballot=ballot.replace('11 ','K ')
        if '12 ' in ballot:
            ballot=ballot.replace('12 ','L ')
        if '13 ' in ballot:
            ballot=ballot.replace('13 ', 'M ')
        if '14 ' in ballot:
            ballot=ballot.replace('14 ', 'N ')
        if '15 ' in ballot:
            ballot=ballot.replace('15 ','O ')
        if '16 ' in ballot:
            ballot=ballot.replace('16 ','P ')
        if '17 ' in ballot:
            ballot=ballot.replace('17 ','Q ')
        if '18 ' in ballot:
            ballot=ballot.replace('18 ','R ')
        if '19 ' in ballot:
            ballot=ballot.replace('19 ','S ')
        if '20 ' in ballot:
            ballot=ballot.replace('20 ','T ')
        if '21 ' in ballot:
            ballot=ballot.replace('21 ','U ')
        if '22 ' in ballot:
            ballot=ballot.replace('22 ','V ')
        if '23 ' in ballot:
            ballot=ballot.replace('23 ','W ')
        if '24 ' in ballot:
            ballot=ballot.replace('24 ','X ')
        if '25 ' in ballot:
            ballot=ballot.replace('25 ','Y ')
        if '26 ' in ballot:
            ballot=ballot.replace('26 ','Z ')
        if '27 ' in ballot:
            ballot=ballot.replace('27 ','a ')
        if '28 ' in ballot:
            ballot=ballot.replace('28 ','b ')
        if '29 ' in ballot:
            ballot=ballot.replace('29 ','c ')
        if '30 ' in ballot:
            ballot=ballot.replace('30 ','d ')
        if '31 ' in ballot:
            ballot=ballot.replace('31 ','e ')
        if '32 ' in ballot:
            ballot=ballot.replace('32 ','f ')
        if '33 ' in ballot:
            ballot=ballot.replace('33 ', 'g ')
        if '34 ' in ballot:
            ballot=ballot.replace('34 ', 'h ')
        if '35 ' in ballot:
            ballot=ballot.replace('35 ','i ')
        if '36 ' in ballot:
            ballot=ballot.replace('36 ','j ')
        if '37 ' in ballot:
            ballot=ballot.replace('37 ','k ')
        if '38 ' in ballot:
            ballot=ballot.replace('38 ','l ')
        if '39 ' in ballot:
            ballot=ballot.replace('39 ','m ')
        if '40 ' in ballot:
            ballot=ballot.replace('40 ','n ')
        if '41 ' in ballot:
            ballot=ballot.replace('41 ','o ')
        if '42 ' in ballot:
            ballot=ballot.replace('42 ','p ')
        if '43 ' in ballot:
            ballot=ballot.replace('43 ', 'q ')
        if '44 ' in ballot:
            ballot=ballot.replace('44 ', 'r ')
        if '45 ' in ballot:
            ballot=ballot.replace('45 ','s ')
        if '46 ' in ballot:
            ballot=ballot.replace('46 ','t ')
        if '47 ' in ballot:
            ballot=ballot.replace('47 ','u ')
        if '48 ' in ballot:
            ballot=ballot.replace('48 ','v ')
        if '49 ' in ballot:
            ballot=ballot.replace('49 ','w ')
        if '50 ' in ballot:
            ballot=ballot.replace('50 ','x ')
        if '51 ' in ballot:
            ballot=ballot.replace('51 ','y ')
        if '52 ' in ballot:
            ballot=ballot.replace('52 ','z ')
        if '53 ' in ballot:
            ballot=ballot.replace('53 ','0 ')
        if '54 ' in ballot:
            ballot=ballot.replace('54 ','1 ')
        if '55 ' in ballot:
            ballot=ballot.replace('55 ','2 ')
        if '56 ' in ballot:
            ballot=ballot.replace('56 ','3 ')
        if '57 ' in ballot:
            ballot=ballot.replace('57 ','4 ')
        if '58 ' in ballot:
            ballot=ballot.replace('58 ','5 ')
        if '59 ' in ballot:
            ballot=ballot.replace('59 ','6 ')    
        if '60 ' in ballot:
            ballot=ballot.replace('60 ','7 ')
        if '61 ' in ballot:
            ballot=ballot.replace('61 ','8 ')
        if '62 ' in ballot:
            ballot=ballot.replace('62 ','9 ')
        if '63 ' in ballot:
            ballot=ballot.replace('63 ','! ')    
        if '64 ' in ballot:
            ballot=ballot.replace('64 ','@ ')
        if '65 ' in ballot:
            ballot=ballot.replace('65 ','# ')
        if '66 ' in ballot:
            ballot=ballot.replace('66 ','$ ')
        if '67 ' in ballot:
            ballot=ballot.replace('67 ','% ')
        if '1 ' in ballot:
            ballot=ballot.replace('1 ','A ')
        if '2 ' in ballot:
            ballot=ballot.replace('2 ','B ')
        if '3 ' in ballot:
            ballot=ballot.replace('3 ','C ')
        if '4 ' in ballot:
            ballot=ballot.replace('4 ','D ')
        if '5 ' in ballot:
            ballot=ballot.replace('5 ','E ')
        if '6 ' in ballot:
            ballot=ballot.replace('6 ','F ')
        if '7 ' in ballot:
            ballot=ballot.replace('7 ','G ')
        if '8 ' in ballot:
            ballot=ballot.replace('8 ','H ')
        if '9 ' in ballot:
            ballot=ballot.replace('9 ','I ')

        while ' ' in ballot:
            ballot=ballot.replace(' ','')
        for i in range(len(ballot)):
            if ballot[i] not in candidates:
                candidates.append(ballot[i])
        row={'ballot':[ballot], 'Count':[float(count)], 'ballot_OG':[ballot], 'Count_OG':[float(count)], 'ballot_modified':[ballot]}
        df2=pd.DataFrame(row)
        data = pd.concat([data, df2], ignore_index=True)
    
    return data, candidates, num_cands

#Note: count and ballot are used/modified during program, count and ballot_modified are used to double-check result
# count_og and ballot_og are used to check original election




### helper programs, generic ####

################################################

### helper programs, for each main program ####

## PM ##

def findKillerSubsets_TVR_PM(profile, num_cands, diagnostic=False): 
    cands = getCands(profile)
    
    killer_subsets = []
    winners = TVR_PM(profile, cands) #get election data from TVR, need foo1, foo2?
    if len(winners)>1:
        print('##### Multiple initial winners #####')
        return []
    winner = winners[0]
    if diagnostic:
        print(winners)
        
    ##### search for killer subsets
    losers = cands.copy()
    losers.remove(winner)
    
    ## Create subsets of up to 5 losers 
    cand_subsets = list(combinations(losers, 2))
    cand_subsets3 = list(combinations(losers, 3))
    for loser in losers:
        cand_subsets.append((loser))
    for thing in cand_subsets3:
        cand_subsets.append(thing)
    if len(losers)>= 4:
        cand_subsets4 = list(combinations(losers, 4))
        for thing in cand_subsets4:
            cand_subsets.append(thing)
    if len(losers)>= 5:
        cand_subsets5 = list(combinations(losers, 5))
        for thing in cand_subsets5:
            cand_subsets.append(thing)
    
    ## test if each subset could eliminate winner
    
    ##add winner to each subset to make it a potential killer subset
    for cand_tuple in cand_subsets:
        subset = list(cand_tuple)
        subset.append(winner)
        
        
        profile_temp = profile.copy(deep=True)
        reduced_prof = reduceProfile(profile_temp, subset)
        bottoms = BordaLoser_PM(reduced_prof, subset, diagnostic=False)
        if (winner in bottoms[0]) and (len(bottoms[0]) == 1):
            scores = BordaScores_PM(reduced_prof, subset, diagnostic=False)
            killer_subsets.append([subset, scores])
#     if len(killer_subsets)>0:
#         print(killer_subsets)
    return killer_subsets

def runAround_TVR_PM(profile, ksnw, W, go, anomFound):
    """ takes in profile, list of killers without winner, winner, killer, and modified votes.
    Runs a round of Killer Subset code, returns updated profile, mod votes, whether or not to go on"""
    if go == False:
        return profile, False, anomFound 
    
    ## use profile to get list of candidates
    cands1 = getCands(profile)
    
    vote_counts = BordaScores_PM(profile, cands1, diagnostic=False)
    cands1noW = copy.deepcopy(cands1)
    cands1noW.remove(W)
    
    max_count=max(vote_counts.values())
    min_count=min(vote_counts.values())
    
    if W in cands1: #this should always happen
        
        if set(cands1noW) == set(ksnw):
            win1 = TVR_PM(profile, cands1, diagnostic=False)
            if win1[0] == W:
                print("No anomaly: reached Killer Subset but OG Winner wins TVR_PM.")
                return profile, False, False
            else:
                #create list of modified votes
                dfModsList = []
                dfModsList.append(W)
                dfModsList.append(win1[0])
                totalVotesChanged = 0
                for x in range(len(profile)):
                    if profile.at[x,'ballot_OG'] != profile.at[x,'ballot_modified']:
                        dfModsList.append([profile.at[x,'Count'], profile.at[x,'ballot_OG'], profile.at[x,'ballot_modified']])
                        totalVotesChanged += profile.at[x,'Count']
                dfModsList.append(totalVotesChanged)
                #make modified OG profile, check if same modified winner
                profile_modified = (profile[['Count', 'ballot_modified']] #thanks Copilot!
                    .rename(columns={'ballot_modified': 'ballot'}).copy() )
                cands_OG = getCands_OG(profile)
                winner_modified = TVR_PM(profile_modified, cands_OG, diagnostic=False)
                if winner_modified[0] != win1[0]:
                    print(f"MAJOR PROBLEM!!!! Program thinks {win1[0]} should be the new winner, but the modified election actually gives {winner_modified[0]}")
                    print(f"New data collection says: {dfModsList}.  Modified data winner is {winner_modified}")
                    
                print("\n")
                print("\n")
                print("Upward TVR ANOMALY!!! Changed votes are " + str(dfModsList)+
                       " and now " + str(win1[0]) + " is the winner.")
#                 data1.write("Upward TVR_OM ANOMALY!!! Changed votes are " +
#                       str(dfModsList) + " and now " + str(win1[0]) + " is the winner.")
#                 data1.write("\n")
                return profile, False, True 
            
       
            
        elif vote_counts[W] == min_count: #this should not really happen
            win1 = TVR_PM(profile, cands1, diagnostic=False)
            if win1[0] == W:
                print("No anomaly: Winner was ranked last but somehow OG Winner wins TVR_PM.")
                return profile, False, False 
            else:
                #create list of modified votes
                dfModsList = []
                dfModsList.append(W)
                dfModsList.append(win1[0])
                totalVotesChanged = 0
                for x in range(len(profile)):
                    if profile.at[x,'ballot_OG'] != profile.at[x,'ballot_modified']:
                        dfModsList.append([profile.at[x,'Count'], profile.at[x,'ballot_OG'], profile.at[x,'ballot_modified']])
                        totalVotesChanged += profile.at[x,'Count']
                dfModsList.append(totalVotesChanged)
                #make modified OG profile, check if same modified winner
                profile_modified = (profile[['Count', 'ballot_modified']] #thanks Copilot!
                    .rename(columns={'ballot_modified': 'ballot'}).copy() )
                cands_OG = getCands_OG(profile)
                winner_modified = TVR_PM(profile_modified, cands_OG, diagnostic=False)
                if winner_modified[0] != win1[0]:
                    print(f"MAJOR PROBLEM!!!! Program thinks {win1[0]} should be the new winner, but the modified election actually gives {winner_modified[0]}")
                    print(f"New data collection says: {dfModsList}.  Modified data winner is {winner_modified}")
                    
                print("\n")
                print("\n")
                print("Upward TVR ANOMALY!!! Changed votes are " + str(dfModsList)+
                      " and now " + str(win1[0]) + 
                      " is the winner. This should not really happen")
#                 data1.write("Upward TVR_OM ANOMALY!!! Changed votes are " +
#                       str(modifiedVotesDict) + " and now " + str(win1[0]) + 
#                             " is the winner.  This should not really happen")
#                 data1.write("\n")
                return profile, False, True 
        else:
            
            for key, value in vote_counts.items(): #find last-place cand
                if value == min_count:
                    eliminated_cand = key
            if eliminated_cand not in ksnw: #eliminate non KS cand
                frame2 = profile.copy(deep = True)
                for k in range(len(frame2)):
                    if eliminated_cand in frame2.iloc[k]['ballot']:
                        frame2.at[k,'ballot']=frame2.at[k,'ballot'].replace(eliminated_cand,'')
                for k in range(len(frame2)):
                    if frame2.at[k,'ballot']=='':
                        frame2.drop(k)
                return runAround_TVR_PM(frame2, ksnw, W, True, anomFound)
            else:
                frame2 = profile.copy(deep = True)
                return runMods_upwardTVR_PM(frame2, ksnw, W, go, anomFound)
    else:
        print("Error: Winner not in round.")
        return profile, False, anomFound   

def runMods_upwardTVR_PM(frame2, ksnw, W, go, anomFound):
    """given profile, winner W, ksnw, and list, modifies just enough ...K_W... ballots to make 
    K drop out next, returns modified frame, removedVotesList, go"""
    
    cands1 = getCands(frame2)
    vote_counts = BordaScores_PM(frame2, cands1, diagnostic=False)
    sorted_items = sorted(vote_counts.items(), key=lambda item: item[1]) #sorted lowest votes to highest
    sorted_cands = [item[0] for item in sorted_items] #K should be first
    
    K1 = sorted_cands[0] #killer with lowest points
    if K1 not in ksnw:
        print("Something strange happened, last-place is not in killer subset.")
        return frame2, False, anomFound 
    
    tempframe = frame2.copy(deep=True)
    go = True
    ksnw_set = set(ksnw)
    ksnw_set.add(W)
    killsubs = list(ksnw_set)
    L = get_lowest_remaining(vote_counts, killsubs) #find lowest candidate NOT in ksnw
    gap = vote_counts[L]-vote_counts[K1] #need to modify gap+1 votes
    
    #modify ballots of form ...LW... to be ...WL...
    
    #shift_candidate(ballot, L, W)
    check = copy.deepcopy(gap)
    for z in range(len(tempframe)):
        if check >= 0:
            ballot = tempframe.at[z,'ballot']
            if (len(ballot)!=0) and (W in ballot) and (L in ballot) and (ballot.find(W)-ballot.find(L)==1):
                if check - tempframe.at[z,'Count']>=-1: #change all such ballots
                    check = check - tempframe.at[z,'Count']
                    tempframe.at[z,'ballot'] = shift_candidate(ballot, L, W)
                    tempframe.at[z,'ballot_modified'] = shift_candidate(tempframe.at[z,'ballot_modified'], L, W)

                else: #change check+1 such ballots
                    tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                    #now add new line to frame with modified ballot
                    tempframe.loc[len(tempframe)] = [shift_candidate(ballot, L, W), check+1, tempframe.at[z,'ballot_OG'], 0, shift_candidate(tempframe.at[z,'ballot_OG'], L, W)]
                    check = -1
    if check < 0:
        #print(check)
        #print(tempframe)
        tempframe, go, anomFound = runAround_TVR_PM(tempframe, ksnw, W, go, anomFound)     
    
    
  
    
    else: #make another pass at tempframe, changing ...L_W... to ...WL_... if _ not in ksnw
        #print("first pass did not change enough votes")
        for z in range(len(tempframe)):
            if check >= 0:
                ballot = tempframe.at[z,'ballot']
                if bufferCheck1(ballot, L, W, ksnw):
                    if check - tempframe.at[z,'Count']>=-1: #change all such ballots
                        
                        check = check - tempframe.at[z,'Count']
                        tempframe.at[z,'ballot'] = shift_with_buffer1(ballot, L, W, ksnw)
                        tempframe.at[z,'ballot_modified'] = shift_candidate(tempframe.at[z,'ballot_modified'], L, W)
                        #print(f"changed ballot {tempframe.iloc[z]}")

                    else: #change check+1 such ballots
                        tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                        #now add new line to frame with modified ballot
                        tempframe.loc[len(tempframe)] = [shift_candidate(ballot, L, W), check+1, tempframe.at[z,'ballot_OG'], 0, shift_candidate(tempframe.at[z,'ballot_OG'], L, W)]
                        #print(f"changed ballot {tempframe.iloc[len(tempframe)-1]}")
                        check = -1
        if check < 0:
            #print(check)
            #print(tempframe)
            tempframe, go, anomFound = runAround_TVR_PM(tempframe, ksnw, W, go, anomFound)  

        else:
            #print("second pass did not change enough votes")
            pass
    
    #anomFound = False
    return tempframe, False, anomFound

## PM ##

## OM ##

def findKillerSubsets_TVR_OM(profile, num_cands, diagnostic=False): 
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    killer_subsets = []
    winners = TVR_OM(profile, cands) #get election data from TVR, need foo1, foo2?
    if len(winners)>1:
        print('##### Multiple initial winners #####')
        return []
    winner = winners[0]
    if diagnostic:
        print(winners)
        
    ##### search for killer subsets
    losers = cands.copy()
    losers.remove(winner)
    
    ## Create subsets of up to 5 losers 
    cand_subsets = list(combinations(losers, 2))
    cand_subsets3 = list(combinations(losers, 3))
    for loser in losers:
        cand_subsets.append((loser))
    for thing in cand_subsets3:
        cand_subsets.append(thing)
    if len(losers)>= 4:
        cand_subsets4 = list(combinations(losers, 4))
        for thing in cand_subsets4:
            cand_subsets.append(thing)
    if len(losers)>= 5:
        cand_subsets5 = list(combinations(losers, 5))
        for thing in cand_subsets5:
            cand_subsets.append(thing)
    #print('candidate subsets are ')
    #print(cand_subsets)
    
    
    ## test if each subset could eliminate winner
    
    ##add winner to each subset to make it a potential killer subset
    for cand_tuple in cand_subsets:
        subset = list(cand_tuple)
        subset.append(winner)
        
        ####Need to change this to get Borda scores
        profile_temp = profile.copy(deep=True)
        reduced_prof = reduceProfile(profile_temp, subset)
        bottoms = BordaLoser_OM(reduced_prof, subset, diagnostic=False)
        if (winner in bottoms[0]) and (len(bottoms[0]) == 1):
            scores = BordaScores_OM(reduced_prof, subset, diagnostic=False)
            killer_subsets.append([subset, scores])
    return killer_subsets





def runAround_TVR_OM(profile, ksnw, W, go, anomFound):
    """ takes in profile, list of killers without winner, winner, killer, and modified votes.
    Runs a round of Killer Subset code, returns updated profile, mod votes, whether or not to go on"""
    
    if go == False:
        return profile, False, anomFound
    
    ## use profile to get list of candidates
    cands1 = getCands(profile)
    
    vote_counts = BordaScores_OM(profile, cands1, diagnostic=False)
    cands1noW = copy.deepcopy(cands1)
    cands1noW.remove(W)
    
    max_count=max(vote_counts.values())
    min_count=min(vote_counts.values())
    
    if W in cands1: #this should always happen
        
        if set(cands1noW) == set(ksnw):
            win1 = TVR_OM(profile, cands1, diagnostic=False)
            if win1[0] == W:
                print("No anomaly: reached Killer Subset but OG Winner wins TVR_PM.")
                return profile, False, anomFound
            else:
                #create list of modified votes
                dfModsList = []
                dfModsList.append(W)
                dfModsList.append(win1[0])
                totalVotesChanged = 0
                for x in range(len(profile)):
                    if profile.at[x,'ballot_OG'] != profile.at[x,'ballot_modified']:
                        dfModsList.append([profile.at[x,'Count'], profile.at[x,'ballot_OG'], profile.at[x,'ballot_modified']])
                        totalVotesChanged += profile.at[x,'Count']
                dfModsList.append(totalVotesChanged)
                #make modified OG profile, check if same modified winner
                profile_modified = (profile[['Count', 'ballot_modified']] #thanks Copilot!
                    .rename(columns={'ballot_modified': 'ballot'}).copy() )
                cands_OG = getCands_OG(profile)
                winner_modified = TVR_OM(profile_modified, cands_OG, diagnostic=False)
                if winner_modified[0] != win1[0]:
                    print(f"MAJOR PROBLEM!!!! Program thinks {win1[0]} should be the new winner, but the modified election actually gives {winner_modified[0]}")
                    print(f"New data collection says: {dfModsList}.  Modified data winner is {winner_modified}")
                    
                print("\n")
                print("\n")
                print("Upward TVR ANOMALY!!! Changed votes are " + 
                      str(dfModsList) + " and now " + str(win1[0]) + " is the winner.")
                anomFound = True
#                 data1.write("Upward TVR_OM ANOMALY!!! Changed votes are " +
#                       str(dfModsList) + " and now " + str(win1[0]) + " is the winner.")
#                 data1.write("\n")
                
                return profile, False, anomFound
            
        elif vote_counts[W] == min_count: #this should not really happen unless a tie?
            win1 = TVR_OM(profile, cands1, diagnostic=False)
            if win1[0] == W:
                print("No anomaly: Winner was ranked last but somehow OG Winner wins TVR_PM. This should not be happening.")
                return profile, False, anomFound
            else:
                #create list of modified votes
                dfModsList = []
                dfModsList.append(W)
                dfModsList.append(win1[0])
                totalVotesChanged = 0
                for x in range(len(profile)):
                    if profile.at[x,'ballot_OG'] != profile.at[x,'ballot_modified']:
                        dfModsList.append([profile.at[x,'Count'], profile.at[x,'ballot_OG'], profile.at[x,'ballot_modified']])
                        totalVotesChanged += profile.at[x,'Count']
                dfModsList.append(totalVotesChanged)
                #make modified OG profile, check if same modified winner
                profile_modified = (profile[['Count', 'ballot_modified']] #thanks Copilot!
                    .rename(columns={'ballot_modified': 'ballot'}).copy() )
                cands_OG = getCands_OG(profile)
                winner_modified = TVR_OM(profile_modified, cands_OG, diagnostic=False)
                if winner_modified[0] != win1[0]:
                    print(f"MAJOR PROBLEM!!!! Program thinks {win1[0]} should be the new winner, but the modified election actually gives {winner_modified[0]}")
                    print(f"New data collection says: {dfModsList}.  Modified data winner is {winner_modified}")
                    
                print("\n")
                print("\n")
                print("Upward TVR ANOMALY!!! Removed votes are " + 
                      str(dfModsList) + " and now " + str(win1[0]) + " is the winner.")
                anomFound = True
#                 data1.write("Upward TVR ANOMALY!!! Changed votes are " +
#                       str(dfModsList) + " and now " + str(win1[0]) + " is the winner. This should not really happen.")
                return profile, False, anomFound
        else:
            
            for key, value in vote_counts.items(): #find last-place cand
                if value == min_count:
                    eliminated_cand = key
            if eliminated_cand not in ksnw: #eliminate non KS cand
                frame2 = profile.copy(deep = True)
                for k in range(len(frame2)):
                    if eliminated_cand in frame2.iloc[k]['ballot']:
                        frame2.at[k,'ballot']=frame2.at[k,'ballot'].replace(eliminated_cand,'')
                for k in range(len(frame2)):
                    if frame2.at[k,'ballot']=='':
                        frame2.drop(k)
                return runAround_TVR_OM(frame2, ksnw, W, True, anomFound)
            else:
                frame2 = profile.copy(deep = True)
                return runMods_upwardTVR_OM(frame2, ksnw, W, go, anomFound)
    else:
        print("Error: Winner not in round.")
        return profile, False, anomFound  

def runMods_upwardTVR_OM(frame2, ksnw, W, go, anomFound):
    """given profile, winner W, ksnw, and list, modifies just enough ...K_W... ballots to make 
    K drop out next, returns modified frame, removedVotesList, go"""
    cands1 = getCands(frame2)
    vote_counts = BordaScores_OM(frame2, cands1, diagnostic=False)
    sorted_items = sorted(vote_counts.items(), key=lambda item: item[1]) #sorted lowest votes to highest
    sorted_cands = [item[0] for item in sorted_items] #K should be first
    
    K1 = sorted_cands[0] #killer with lowest points
    if K1 not in ksnw:
        print("Something strange happened, last-place is not in killer subset.")
        print("last place is " + str(K1))
        print("ksnw is " + str(ksnw))
        print("winner is " + str(W))
        print(vote_counts)
        return frame2, False, anomFound 
    
    tempframe = frame2.copy(deep=True)
    go = True
    ksnw_set = set(ksnw)
    ksnw_set.add(W)
    killsubs = list(ksnw_set)
    L = get_lowest_remaining(vote_counts, killsubs) #find lowest candidate NOT in ksnw
    gap = vote_counts[L]-vote_counts[K1] #need to modify gap+1 votes
    
    #modify ballots of form ...LW... to be ...WL...
    
    #shift_candidate(ballot, L, W)
    check = copy.deepcopy(gap)
    for z in range(len(tempframe)):
        if check >= 0:
            ballot = tempframe.at[z,'ballot']
            if (len(ballot)!=0) and (W in ballot) and (L in ballot) and (ballot.find(W)-ballot.find(L)==1):
                if check - tempframe.at[z,'Count']>=-1: #change all such ballots
                    check = check - tempframe.at[z,'Count']
                    tempframe.at[z,'ballot'] = shift_candidate(ballot, L, W)
                    tempframe.at[z,'ballot_modified'] = shift_candidate(tempframe.at[z,'ballot_modified'], L, W)

                else: #change check+1 such ballots
                    
                    tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                    #now add new line to frame with modified ballot
                    tempframe.loc[len(tempframe)] = [shift_candidate(ballot, L, W), check+1, tempframe.at[z,'ballot_OG'], 0, shift_candidate(tempframe.at[z,'ballot_OG'], L, W)]
                    check = -1
    if check < 0:
        tempframe, go, anomFound = runAround_TVR_OM(tempframe, ksnw, W, go, anomFound)     
            
    else: #make another pass at tempframe, changing ...L_W... to ...WL_... if _ not in ksnw
        for z in range(len(tempframe)):
            if check >= 0:
                ballot = tempframe.at[z,'ballot']
                if bufferCheck1(ballot, L, W, ksnw):
                    if check - tempframe.at[z,'Count']>=-1: #change all such ballots
                        check = check - tempframe.at[z,'Count']
                        tempframe.at[z,'ballot'] = shift_with_buffer1(ballot, L, W, ksnw)
                        tempframe.at[z,'ballot_modified'] = shift_candidate(tempframe.at[z,'ballot_modified'], L, W)
                    else: #change check+1 such ballots
                        tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                        #now add new line to frame with modified ballot
                        tempframe.loc[len(tempframe)] = [shift_candidate(ballot, L, W), check+1, tempframe.at[z,'ballot_OG'], 0, shift_candidate(tempframe.at[z,'ballot_OG'], L, W)]
                        check = -1
        if check < 0:
            tempframe, go, anomFound = runAround_TVR_OM(tempframe, ksnw, W, go, anomFound)  

        else:
            pass
    
    return tempframe, False, anomFound




## OM ##

## AVG ##

def findKillerSubsets_TVR_AVG(profile, num_cands, diagnostic=False): 
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    killer_subsets = []
    winners = TVR_AVG(profile, cands) #get election data from TVR, need foo1, foo2?
    if len(winners)>1:
        print('##### Multiple initial winners #####')
        return []
    winner = winners[0]
    if diagnostic:
        print(winners)
        
    ##### search for killer subsets
    losers = cands.copy()
    losers.remove(winner)
    
    ## Create subsets of up to 5 losers 
    cand_subsets = list(combinations(losers, 2))
    cand_subsets3 = list(combinations(losers, 3))
    for loser in losers:
        cand_subsets.append((loser))
    for thing in cand_subsets3:
        cand_subsets.append(thing)
    if len(losers)>= 4:
        cand_subsets4 = list(combinations(losers, 4))
        for thing in cand_subsets4:
            cand_subsets.append(thing)
    if len(losers)>= 5:
        cand_subsets5 = list(combinations(losers, 5))
        for thing in cand_subsets5:
            cand_subsets.append(thing)
    #print('candidate subsets are ')
    #print(cand_subsets)
    
    
    ## test if each subset could eliminate winner
    
    ##add winner to each subset to make it a potential killer subset
    for cand_tuple in cand_subsets:
        subset = list(cand_tuple)
        subset.append(winner)
        
        ####Need to change this to get Borda scores
        profile_temp = profile.copy(deep=True)
        reduced_prof = reduceProfile(profile_temp, subset)
        bottoms = BordaLoser_AVG(reduced_prof, subset, diagnostic=False)
        if (winner in bottoms[0]) and (len(bottoms[0]) == 1):
            scores = BordaScores_AVG(reduced_prof, subset, diagnostic=False)
            killer_subsets.append([subset, scores])
    return killer_subsets



    
def runAround_TVR_AVG(profile, ksnw, W, go, anomFound):
    """ takes in profile, list of killers without winner, winner, killer, and modified votes.
    Runs a round of Killer Subset code, returns updated profile, mod votes, whether or not to go on"""
    
    if go == False:
        return profile, False, anomFound
    
    ## use profile to get list of candidates
    cands1 = getCands(profile)
    vote_counts = BordaScores_AVG(profile, cands1, diagnostic=False)
    cands1noW = copy.deepcopy(cands1)
    cands1noW.remove(W)
    
    max_count=max(vote_counts.values())
    min_count=min(vote_counts.values())
    
    if W in cands1: #this should always happen
        
        if set(cands1noW) == set(ksnw):
            win1 = TVR_AVG(profile, cands1, diagnostic=False)
            if win1[0] == W:
                #print("No anomaly: reached Killer Subset but OG Winner wins TVR_PM.")
                return profile, False, anomFound
            else:
                #create list of modified votes
                dfModsList = []
                dfModsList.append(W)
                dfModsList.append(win1[0])
                totalVotesChanged = 0
                for x in range(len(profile)):
                    if profile.at[x,'ballot_OG'] != profile.at[x,'ballot_modified']:
                        dfModsList.append([profile.at[x,'Count'], profile.at[x,'ballot_OG'], profile.at[x,'ballot_modified']])
                        totalVotesChanged += profile.at[x,'Count']
                dfModsList.append(totalVotesChanged)
                #make modified OG profile, check if same modified winner
                profile_modified = (profile[['Count', 'ballot_modified']] #thanks Copilot!
                    .rename(columns={'ballot_modified': 'ballot'}).copy() )
                cands_OG = getCands_OG(profile)
                winner_modified = TVR_AVG(profile_modified, cands_OG, diagnostic=False)
                if winner_modified[0] != win1[0]:
                    print(f"MAJOR PROBLEM!!!! Program thinks {win1[0]} should be the new winner, but the modified election actually gives {winner_modified[0]}")
                    print(f"New data collection says: {dfModsList}.  Modified data winner is {winner_modified}")
                    
                print("\n")
                print("\n")
                print("Upward TVR ANOMALY!!! Changed votes are " + 
                      str(dfModsList) + " and now " + str(win1[0]) + " is the winner.")
                anomFound = True
#                 data1.write("\n")
#                 data1.write("\n")
#                 data1.write("Upward TVR_AVG ANOMALY!!! Changed votes are " +
#                       str(dfModsList) + " and now " + str(win1[0]) + " is the winner.")
#                 data1.write("\n")
                return profile, False, anomFound
            
        elif vote_counts[W] == min_count: #this should not really happen unless a tie?
            win1 = TVR_AVG(profile, cands1, diagnostic=False)
            if win1[0] == W:
                print("No anomaly: Winner was ranked last but somehow OG Winner wins TVR_PM. This should not be happening.")
                return profile, False, anomFound
            else:
                #create list of modified votes
                dfModsList = []
                dfModsList.append(W)
                dfModsList.append(win1[0])
                totalVotesChanged = 0
                for x in range(len(profile)):
                    if profile.at[x,'ballot_OG'] != profile.at[x,'ballot_modified']:
                        dfModsList.append([profile.at[x,'Count'], profile.at[x,'ballot_OG'], profile.at[x,'ballot_modified']])
                        totalVotesChanged += profile.at[x,'Count']
                dfModsList.append(totalVotesChanged)
                #make modified OG profile, check if same modified winner
                profile_modified = (profile[['Count', 'ballot_modified']] #thanks Copilot!
                    .rename(columns={'ballot_modified': 'ballot'}).copy() )
                cands_OG = getCands_OG(profile)
                winner_modified = TVR_AVG(profile_modified, cands_OG, diagnostic=False)
                if winner_modified[0] != win1[0]:
                    print(f"MAJOR PROBLEM!!!! Program thinks {win1[0]} should be the new winner, but the modified election actually gives {winner_modified[0]}")
                    print(f"New data collection says: {dfModsList}.  Modified data winner is {winner_modified}")
                    
                print("\n")
                print("\n")
                print("Upward TVR ANOMALY!!! Removed votes are " + 
                      str(dfModsList) + " and now " + str(win1[0]) + " is the winner.")
                anomFound = True
#                 data1.write("Upward TVR ANOMALY!!! Changed votes are " +
#                       str(dfModsList) + " and now " + str(win1[0]) + " is the winner. This should not really happen.")
                return profile, False, anomFound
        else:
            
            for key, value in vote_counts.items(): #find last-place cand
                if value == min_count:
                    eliminated_cand = key
            if eliminated_cand not in ksnw: #eliminate non KS cand
                frame2 = profile.copy(deep = True)
                for k in range(len(frame2)):
                    if eliminated_cand in frame2.iloc[k]['ballot']:
                        frame2.at[k,'ballot']=frame2.at[k,'ballot'].replace(eliminated_cand,'')
                for k in range(len(frame2)):
                    if frame2.at[k,'ballot']=='':
                        frame2.drop(k)
                return runAround_TVR_AVG(frame2, ksnw, W, True, anomFound)
            else:
                frame2 = profile.copy(deep = True)
                return runMods_upwardTVR_AVG(frame2, ksnw, W, go, anomFound)
    else:
        print("Error: Winner not in round.")
        return profile, False, anomFound  

def runMods_upwardTVR_AVG(frame2, ksnw, W, go, anomFound):
    """given profile, winner W, ksnw, and list, modifies just enough ...K_W... ballots to make 
    K drop out next, returns modified frame, removedVotesList, go"""
    cands1 = getCands(frame2)
    vote_counts = BordaScores_AVG(frame2, cands1, diagnostic=False)
    sorted_items = sorted(vote_counts.items(), key=lambda item: item[1]) #sorted lowest votes to highest
    sorted_cands = [item[0] for item in sorted_items] #K should be first
    
    K1 = sorted_cands[0] #killer with lowest points
    if K1 not in ksnw:
        print("Something strange happened, last-place is not in killer subset.")
        return frame2, False, anomFound 
    
    tempframe = frame2.copy(deep=True)
    go = True
    ksnw_set = set(ksnw)
    ksnw_set.add(W)
    killsubs = list(ksnw_set)
    L = get_lowest_remaining(vote_counts, killsubs) #find lowest candidate NOT in ksnw
    gap = vote_counts[L]-vote_counts[K1] #need to modify gap+1 votes
    
    #modify ballots of form ...LW... to be ...WL...
    
    #shift_candidate(ballot, L, W)
    check = copy.deepcopy(gap)
    for z in range(len(tempframe)):
        if check >= 0:
            ballot = tempframe.at[z,'ballot']
            if (len(ballot)!=0) and (W in ballot) and (L in ballot) and (ballot.find(W)-ballot.find(L)==1):
                if check - tempframe.at[z,'Count']>=-1: #change all such ballots
                    check = check - tempframe.at[z,'Count']
                    tempframe.at[z,'ballot'] = shift_candidate(ballot, L, W)
                    tempframe.at[z,'ballot_modified'] = shift_candidate(tempframe.at[z,'ballot_modified'], L, W)

                else: #change check+1 such ballots
                    
                    tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                    #now add new line to frame with modified ballot
                    tempframe.loc[len(tempframe)] = [shift_candidate(ballot, L, W), check+1, tempframe.at[z,'ballot_OG'], 0, shift_candidate(tempframe.at[z,'ballot_OG'], L, W)]
                    check = -1
    if check < 0:
        #print(check)
        #print(tempframe)
        tempframe, go, anomFound = runAround_TVR_AVG(tempframe, ksnw, W, go, anomFound)     
            
    else: #make another pass at tempframe, changing ...L_W... to ...WL_... if _ not in ksnw
        for z in range(len(tempframe)):
            if check >= 0:
                ballot = tempframe.at[z,'ballot']
                if bufferCheck1(ballot, L, W, ksnw):
                    if check - tempframe.at[z,'Count']>=-1: #change all such ballots
                        check = check - tempframe.at[z,'Count']
                        tempframe.at[z,'ballot'] = shift_with_buffer1(ballot, L, W, ksnw)
                        tempframe.at[z,'ballot_modified'] = shift_candidate(tempframe.at[z,'ballot_modified'], L, W)
                    else: #change check+1 such ballots
                        tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                        #now add new line to frame with modified ballot
                        tempframe.loc[len(tempframe)] = [shift_candidate(ballot, L, W), check+1, tempframe.at[z,'ballot_OG'], 0, shift_candidate(tempframe.at[z,'ballot_OG'], L, W)]
                        check = -1
        if check < 0:
            tempframe, go, anomFound = runAround_TVR_AVG(tempframe, ksnw, W, go, anomFound)  

        else:
            pass
    
    return tempframe, False, anomFound


## AVG ##



### helper programs, for each main program ####

################################################

### main programs ####

def killerSubs_upwardMono_TVR_PM(election, anomFound, diagnostic = False):

    profile, cands, num_Cands = prefProfileInput5(election)
    if num_Cands > 15: #could remove this if we already have reduced elections to 15 cands
        print("more than 15 candidates, now filtering")
        profile = reduceToTopN(profile, 15)
        cands = getCands(profile)
        num_Cands = 15
    
    winners = TVR_PM(profile, cands, diagnostic=False)
    if len(winners)<1:
        print("TVR_PM found no winners, which is super duper weird")
        return False
    W = winners[0]
    numCands = len(cands) #should remove this
    killer_subs = findKillerSubsets_TVR_PM(profile, num_Cands, diagnostic=False) 
    #this is a list of lists.  killer_subs[0][0]=first ks, [1][0]=2nd ks, etc

    if len(killer_subs)!=0:
        for ks2 in killer_subs:
            ks = ks2[0]
            ks_dict = ks2[1]
            if W not in ks:
                print("Error: Killer subset without winner, something is wrong.")
            else:
                ksnw = copy.deepcopy(ks)
                ksnw.remove(W) #because W wins IRV, they will never be in last place

                profile1 = profile.copy(deep=True)

                go = True
                while (go == True) and (anomFound == False): 
                    profile1, go, anomFound  = runAround_TVR_PM(profile1, ksnw, W, go, anomFound)
                    if go == False or anomFound == True:
                        break
            if anomFound:
                return True
    else:
        if diagnostic:
            print("No killer subsets in " + str(election))
        return False
    
       

def killerSubs_upwardMono_TVR_OM(election, anomFound, diagnostic = False):

    profile, cands, num_Cands = prefProfileInput5(election) #process pref sched into pandas data
    if num_Cands > 15:
        print("more than 10 candidates, now filtering")
        profile = filter_weak_cands(profile, num_Cands, 15)
        cands = getCands(profile)
        num_Cands = 15
    
    winners = TVR_OM(profile, cands, diagnostic=False)
    W = winners[0]

    numCands = len(cands)
    killer_subs = findKillerSubsets_TVR_OM(profile, numCands, diagnostic=False) 
    #this is a list of lists.  killer_subs[0][0]=first ks, [1][0]=2nd ks, etc

    if len(killer_subs)!=0:
        for ks2 in killer_subs:
            ks = ks2[0]
            ks_dict = ks2[1]
            if W not in ks:
                print("Error: Killer subset without winner, something is wrong.")
            else:
                ksnw = copy.deepcopy(ks)
                ksnw.remove(W) #because W wins IRV, they will never be in last place
                profile1 = profile.copy(deep=True)
                go = True
                while go == True: 
                    profile1, go, anomFound = runAround_TVR_OM(profile1, ksnw, W,  go, anomFound)
                    if go == False or anomFound == True:
                        break
        if anomFound:
            return True
    else:
        return False
        if diagnostic:
            print("No killer subsets in " + str(election))



#note: election is raw data
def killerSubs_upwardMono_TVR_AVG(election, anomFound, diagnostic = False):

    profile, cands, num_Cands = prefProfileInput5(election)
    if num_Cands > 15:
        print("more than 15 candidates, now filtering")
        profile = filter_weak_cands(profile, num_Cands, 15)
        cands = getCands(profile)
        num_Cands = 15
        
    winners = TVR_AVG(profile, cands, diagnostic=False)
    W = winners[0]

    numCands = len(cands)
    
    killer_subs = findKillerSubsets_TVR_AVG(profile, numCands, diagnostic=False) 
    #this is a list of lists.  killer_subs[0][0]=first ks, [1][0]=2nd ks, etc

    if len(killer_subs)!=0:
        for ks2 in killer_subs:
            ks = ks2[0]
            ks_dict = ks2[1]
            if W not in ks:
                print("Error: Killer subset without winner, something is wrong.")
            else:
                ksnw = copy.deepcopy(ks)
                ksnw.remove(W) #because W wins IRV, they will never be in last place
                profile1 = profile.copy(deep=True)

                go = True
                while go == True: #Need K, maxNSremovable? old was (profile1, ksnw, W, K, modifiedVotesList, modifiedVotesDict, maxNSremovable, go)

                    profile1, go, anomFound = runAround_TVR_AVG(profile1, ksnw, W, go, anomFound)
                    if go == False or anomFound == True:
                        break
        if anomFound:
            return True
    else:
        return False
        if diagnostic:
            print("No killer subsets in " + str(election))



### main programs ####

################################################

### run over single election:

# election = 'Preference Profiles/scotland/dumgal22/Ward8-Lochar_ward8.csv'
# anomFound = False
# killerSubs_upwardMono_TVR_AVG(election, anomFound, diagnostic = False)


### run over a dataset

#Run  code for all
import os
import statistics
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

tvr_type = "PM" #also change below at weasel
dataset_name = "scotland" #NontrivialSmith #convex_combinations_andy #sampled_top_cycles_david

start1 = time.process_time()
#data1 = open(f"TVRnew_{tvr_type}_Upward_{dataset_name}.txt", "w")

directory="C:/Users/mijones/Documents/Datasets/ranked_ballot_data/preference_profiles_top_15/Scotland" #'Scotland data, LEAP'
r=[]
subdirs = [x[0] for x in os.walk(directory)]
subdirs=subdirs[1:]
counter=0
num_elections=0

for subdir in subdirs:
    files=os.listdir(subdir)
    for file in files:
        filename=subdir+'/'+file   
        election=file
        num_elections+=1
        if (num_elections % 50 == 0):
            print("\n")
            print(f"Number of elections so far is {num_elections}. Number of anomalies is {counter}.")
            print("\n" )
            #print(filename)
        anomFound = False
        weasel = killerSubs_upwardMono_TVR_OM(filename, anomFound, diagnostic = False) #change type here too!!!!
        if weasel:
            counter += 1
            print("\n")
            print(f"{counter}) {filename}")
            print("\n")
#             data1.write("\n")
#             data1.write("(" + str(counter) + ") " + str(filename))
#             data1.write("\n"+ "\n" )
            
print("Total number of elections with anomaly is " + str(counter))     
# data1.close()
print("total time was ")
print(time.process_time() - start1)