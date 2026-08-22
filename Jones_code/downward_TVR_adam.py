
#### general helper programs ####

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

def BordaPM_score(ballot, cand, nCands):
    max_score = nCands - 1
    if cand in ballot:
        score = max_score - ballot.index(cand)
    else:
        score = 0
    return score

def BordaPMdiff(ballot, nCands, A, B):
    diff = BordaPM_score(ballot, A, nCands)-BordaPM_score(ballot, B, nCands)
    return max(diff,0)


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

def BordaOM_score(ballot, cand, nCands):
    max_score = nCands - 1
    if cand in ballot:
        score = max_score - ballot.index(cand)
    else:
        score = max_score - len(ballot)
    return score

def BordaOMdiff(ballot, nCands, A, B): #for A ranked higher than B
    diff = BordaOM_score(ballot, A, nCands)-BordaOM_score(ballot, B, nCands)
    return max(diff,0)

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

def BordaAVG_score(ballot, cand, nCands):
    max_score = nCands - 1
    missing_cand_num = nCands - len(ballot) 
    avg_points = (missing_cand_num - 1)/2
    if cand in ballot:
        score = max_score - ballot.index(cand)
    else:
        score = avg_points
    return score

def BordaAVGdiff(ballot, nCands, A, B): #for A ranked higher than B
    diff = BordaAVG_score(ballot, A, nCands)-BordaAVG_score(ballot, B, nCands)
    return max(diff,0)

###############################################################################
###############################################################################




def TVR_OM(profile, cands, diagnostic=False):
    hopefuls = cands.copy()
    new_profile = profile.copy(deep=True)
#     if diagnostic:
#         print(new_profile)
        
    while len(hopefuls)>1:
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
        
        remove_cand = remove_cand[0]
        hopefuls.remove(remove_cand)
        
        for k in range(len(new_profile)):
            if remove_cand in new_profile.iloc[k]['ballot']:
                new_profile.at[k,'ballot']=new_profile.at[k,'ballot'].replace(remove_cand,'')
        
#         if diagnostic:
#             print(new_profile)
        
    return hopefuls




def TVR_PM(profile, cands, diagnostic=False):
    hopefuls = cands.copy()
    new_profile = profile.copy(deep=True)
#     if diagnostic:
#         print(new_profile)
        
    while len(hopefuls)>1:
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
        
        ## remove loser from election
        remove_cand = [cand for cand in hopefuls if scores[cand]==min(scores.values())]
        if len(remove_cand)>1:
            print('#####Tie in Borda score!#####')
            
        if diagnostic:
            print(scores)
        
        remove_cand = remove_cand[0]
        hopefuls.remove(remove_cand)
        
        for k in range(len(new_profile)):
            if remove_cand in new_profile.iloc[k]['ballot']:
                new_profile.at[k,'ballot']=new_profile.at[k,'ballot'].replace(remove_cand,'')
        
#         if diagnostic:
#             print(new_profile)
        
    return hopefuls




def TVR_AVG(profile, cands, diagnostic=False):
    hopefuls = cands.copy()
    new_profile = profile.copy(deep=True)
#     if diagnostic:
#         print(new_profile)
        
    while len(hopefuls)>1:
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
        
        remove_cand = remove_cand[0]
        hopefuls.remove(remove_cand)
        
        for k in range(len(new_profile)):
            if remove_cand in new_profile.iloc[k]['ballot']:
                new_profile.at[k,'ballot']=new_profile.at[k,'ballot'].replace(remove_cand,'')
        
#         if diagnostic:
#             print(new_profile)
        
    return hopefuls
   

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


def get_secondLow(my_dict):
    """inputs dictionary, returns key for second-lowest value"""
    for key, value in my_dict.items():
         if value == sorted([*my_dict.values()])[1]:
             return key

def swapOneTwo(ballot):
    """inputs a ballot, and swaps position of first and second place"""
    
    if len(ballot) == 2:
        modified = ballot[1] + ballot[0]
    elif len(ballot) > 2:
        modified = ballot[1] + ballot[0] + ballot[2:]
    else:
        print("incorrect application of swapOneTwo function")
    return modified

def swapOneLoser(ballot, loser):
    """inputs a ballot with a bullet vote, puts loser above bullet vote"""
    modified = loser + ballot
    return modified


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
    """moves W above L in the ballot"""
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

def shift_candidateDown(ballot, L, W): #(thanks Gemini!)
    """moves L below W in the ballot"""
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
        temp_list.pop(l_idx)
        
        # 2. Insert W at the index where L currently is
        # This pushes L to the right
        temp_list.insert(w_idx, L)
        
        return "".join(temp_list)
    
    # If W is already before L, return original ballot
    return ballot

def insert_candidateAbove(ballot, L, new): #(thanks Gemini!)
    """inserts new above L in the ballot"""
    # Ensure both characters are in the ballot
    if L not in ballot or new in ballot:
        return ballot
    
    l_idx = ballot.find(L)
    temp_list = list(ballot)

    #  Insert new at the index where L currently is
    # This pushes L to the right
    temp_list.insert(l_idx, new)

    return "".join(temp_list)
    
    


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






#### general helper programs ####

############################################################

### helper programs for individual types ####


def findDemiKillerSubs_TVR_PM(profile, diagnostic=False): 
    cands = getCands(profile)
    
    demi_killer_subsets = []
    winners = TVR_PM(profile, cands)
    if len(winners)>1:
        print('##### Multiple initial winners #####')
        return []
    winner = winners[0]
    if diagnostic:
        print(winners)
        
    ##### search for demikiller subsets
    losers = cands.copy()
    losers.remove(winner)
    
    ## only eliminate in round of three or two
    cand_subsets = list(combinations(losers, 2))
    cand_subsets3 = list(combinations(losers, 3))
    #for loser in losers: #dont need these because 2 candidate DK subsets are no good
        #cand_subsets.append((loser))
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
    
    
    ## test if each subset has winner in second to last place
    for cand_tuple in cand_subsets:
        subset = list(cand_tuple)
        subset.append(winner)
        
        profile_temp = profile.copy(deep=True)
        reduced_prof = reduceProfile(profile_temp, subset)
        scores = BordaScores_PM(reduced_prof, subset, diagnostic=False)
        S = get_secondLow(scores)
        
        if (winner == S):
            demi_killer_subsets.append([subset, scores])
#     if len(demi_killer_subsets)>0:
#         print(demi_killer_subsets)
        #data2.write(demi_killer_subsets)
        
    return demi_killer_subsets


    
def runAroundDown_TVR_PM(profile, ksnw, W, K, go, anomFound):
    """ takes in profile, list of demikillers without winner, winner, killer, and modified votes.
    Runs a round of Demi Killer Subset code, returns updated profile, mod votes, whether or not to go on"""
    
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
        
        if vote_counts[W] == min_count: #this could happen after DK mods, winner in last place
            win1 = TVR_PM(profile, cands1, diagnostic=False)
            if win1[0] == W:
                print("No anomaly: Winner ranked last but somehow OG Winner wins TVR_PM. Should not happen")
                return profile, False, False 
            elif win1[0] == K:
                anomFound = True
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
                winner_modified = TVR_PM(profile_modified, cands_OG, diagnostic=True)
                if winner_modified[0] != win1[0]:
                    print(f"MAJOR PROBLEM!!!! Program thinks {win1[0]} should be the new winner, but the modified election actually gives {winner_modified[0]}")
                    print(f"New data collection says: {dfModsList}.  Modified data winner is {winner_modified}")
                print("\n")
                print("Downward TVR_PM ANOMALY!!! Modified votes are " + str(dfModsList)+
                      " and now " + str(win1[0]) + " is the winner.")
#                 data1.write("Downward TVR_PM ANOMALY!!! Removed votes are " +
#                       str(modifiedVotesDict) + " and now " + str(win1[0]) +
#                         " is the winner.")
#                 data1.write("\n")
                return profile, False, True 
            else:
                return profile, False, False
        elif set(cands1noW) == set(ksnw): #if at demiKiller subset, run DK mods
            frame2 = profile.copy(deep = True)
            return runMods_Down_TVR_PM(frame2, ksnw, W, K, go, anomFound)
                #DKMods: last-place is K1, remove enough K....W....K1 ballots so that W drops out
        else:
            #have NOT hit the demiKiller subset
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
                #print("Eliminated candidate " + eliminated_cand)
                #print(frame2)
                return runAroundDown_TVR_PM(frame2, ksnw, W, K, True, anomFound)
            else: #run non-DK modifications.  Someone in ksnw is in last place
                frame2 = profile.copy(deep = True)
                return runMods_Down_TVR_PM(frame2, ksnw, W, K, go, anomFound)
    else:
        print("Error: Winner not in round.")
        return profile, False, anomFound   
            
            
            
def runMods_Down_TVR_PM(frame2, ksnw, W, K, go, anomFound):
    #removing ballots when NOT in DK subset, hoping to get to DK subset
    """given profile, winner W, killer K, ksnw, and list, removes just enough ..L...K_W... ballots to make 
    L drop out next, returns modified frame, removedVotesList, go"""
    
    #find candidate with lowest Borda points, should be killer but NOT W
    cands1 = getCands(frame2)
    nCands = len(cands1)
    if nCands<=2:
        print("Something strange happened, nCands is less than 3, no mods possible.")
        return frame2, True, anomFound
    vote_counts = BordaScores_PM(frame2, cands1, diagnostic=False)
    sorted_items = sorted(vote_counts.items(), key=lambda item: item[1]) #sorted lowest votes to highest
    sorted_cands = [item[0] for item in sorted_items] #K should be first
    
    #anomFound = False
    
    K1 = sorted_cands[0] #killer with lowest points, may not be K
    if K1 not in ksnw:
        print("Something strange happened, last place is not in killer subset.")
        return frame2, False, False
    if K1 == K:
        print("DemiKiller K is in last place, Downward anomaly NOT possible")
        return frame2, False, False
    tempframe = frame2.copy(deep=True)
    go = True
    
    L = get_lowest_remaining(vote_counts, ksnw) #find lowest candidate NOT in ksnw
    
    gap = vote_counts[L]-vote_counts[K1] #need to modify gap+1 votes
    check = copy.deepcopy(gap)
    
        
    #now change bullet votes (do this first in OM and PM? Yes...maybe AVG too?)
    for z in range(len(tempframe)):
        if check >= 0:
            ballot = tempframe.at[z,'ballot'] #change all K to K1_K
            if (len(ballot)==1) and (K in ballot):
                if check - tempframe.at[z,'Count']*2>=-1: #modify all such ballots
                    check = check - tempframe.at[z,'Count']*2
                    tempframe.at[z,'ballot'] = insert_candidateAbove(ballot, K, K1) #makes K->K_1_K,
                    tempframe.at[z,'ballot_modified'] = insert_candidateAbove(tempframe.at[z,'ballot_modified'], K, K1)
                else: #modify check+1 such ballots such ballots
                    if tempframe.at[z,'Count']>0:
                        tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                        #now add new line to frame with modified ballot
                        tempframe.loc[len(tempframe)] = [insert_candidateAbove(ballot, K, K1), check+1, tempframe.at[z,'ballot_OG'], 0, insert_candidateAbove(tempframe.at[z,'ballot_OG'], K, K1)]
                        check = -1
                        
            if check < 0:
                #print(check)
                #print(tempframe)
                tempframe, go, anomFound = runAroundDown_TVR_PM(tempframe, ksnw, W, K, go, anomFound)     
        
    for z in range(len(tempframe)):
        if check >= 0:
            ballot = tempframe.at[z,'ballot'] #change all K_K1 to K1_K
            if (len(ballot)!=0) and (K in ballot) and (K1 in ballot) and (ballot.find(K1)-ballot.find(K)==1):
                if check - tempframe.at[z,'Count']>=-1: #modify all such ballots
                    check = check - tempframe.at[z,'Count']
                    tempframe.at[z,'ballot'] = shift_candidateDown(ballot, K, K1) #makes K_K1->K_1_K, rest stays
                    tempframe.at[z,'ballot_modified'] = shift_candidateDown(tempframe.at[z,'ballot_modified'], K, K1)

                else: #modify check+1 such ballots such ballots
                    if tempframe.at[z,'Count']>0:
                        tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                        #now add new line to frame with modified ballot
                        tempframe.loc[len(tempframe)] = [shift_candidateDown(ballot, K, K1), check+1, tempframe.at[z,'ballot_OG'], 0, shift_candidateDown(tempframe.at[z,'ballot_OG'], K, K1)]
                        check = -1
                        
            if check < 0:
                #print(check)
                #print(tempframe)
                tempframe, go, anomFound = runAroundDown_TVR_PM(tempframe, ksnw, W, K, go, anomFound)     
    
    
    #anomFound = False
    return tempframe, False, anomFound






def findDemiKillerSubs_TVR_OM(profile, diagnostic=False): 
    cands = getCands(profile)
    
    demi_killer_subsets = []
    winners = TVR_OM(profile, cands)
    if len(winners)>1:
        print('##### Multiple initial winners #####')
        return []
    winner = winners[0]
    if diagnostic:
        print(winners)
        
    ##### search for demikiller subsets
    losers = cands.copy()
    losers.remove(winner)
    
    ## only eliminate in round of three or two
    cand_subsets = list(combinations(losers, 2))
    cand_subsets3 = list(combinations(losers, 3))
    #for loser in losers: #dont need these because 2 candidate DK subsets are no good
        #cand_subsets.append((loser))
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
    
    
    ## test if each subset has winner in second to last place
    for cand_tuple in cand_subsets:
        subset = list(cand_tuple)
        subset.append(winner)
        
        profile_temp = profile.copy(deep=True)
        reduced_prof = reduceProfile(profile_temp, subset)
        scores = BordaScores_OM(reduced_prof, subset, diagnostic=False)
        S = get_secondLow(scores)
        
        if (winner == S):
            demi_killer_subsets.append([subset, scores])
    if len(demi_killer_subsets)>0:
        print(demi_killer_subsets)
        #data2.write(demi_killer_subsets)
        
    return demi_killer_subsets


    
def runAroundDown_TVR_OM(profile, ksnw, W, K, go, anomFound):
    """ takes in profile, list of demikillers without winner, winner, killer, and modified votes.
    Runs a round of Demi Killer Subset code, returns updated profile, mod votes, whether or not to go on"""
    
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
        
        if vote_counts[W] == min_count: #this could happen after DK mods, winner in last place
            win1 = TVR_OM(profile, cands1, diagnostic=False)
            if win1[0] == W:
                print("No anomaly: Winner ranked last but somehow OG Winner wins TVR_OM. Should not happen")
                return profile, False, False 
            elif win1[0] == K:
                anomFound = True
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
                winner_modified = TVR_OM(profile_modified, cands_OG, diagnostic=True)
                if winner_modified[0] != win1[0]:
                    print(f"MAJOR PROBLEM!!!! Program thinks {win1[0]} should be the new winner, but the modified election actually gives {winner_modified[0]}")
                    print(f"New data collection says: {dfModsList}.  Modified data winner is {winner_modified}")
                print("\n")
                print("Downward TVR_OM ANOMALY!!! Modified votes are " + 
                      str(dfModsList) + " and now " + str(win1[0]) + " is the winner.")
                      
#                 data1.write("Downward TVR_OM ANOMALY!!! Removed votes are " +
#                       str(modifiedVotesDict) + " and now " + str(win1[0]) +
#                         " is the winner.")
#                 data1.write("\n")
                return profile, False, True 
            else:
                return profile, False, False
        elif set(cands1noW) == set(ksnw): #if at demiKiller subset, run DK mods
            frame2 = profile.copy(deep = True)
            return runMods_Down_TVR_OM(frame2, ksnw, W, K, go, anomFound)
        else:
            #have NOT hit the demiKiller subset
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
                return runAroundDown_TVR_OM(frame2, ksnw, W, K, True, anomFound)
            else: #run non-DK modifications.  Someone in ksnw is in last place
                frame2 = profile.copy(deep = True)
                return runMods_Down_TVR_OM(frame2, ksnw, W, K, go, anomFound)
    else:
        print("Error: Winner not in round.")
        return profile, False, anomFound   
            
            
            
def runMods_Down_TVR_OM(frame2, ksnw, W, K, go, anomFound):
    #removing ballots when NOT in DK subset, hoping to get to DK subset
    """given profile, winner W, killer K, ksnw, and list, removes just enough ..L...K_W... ballots to make 
    L drop out next, returns modified frame, removedVotesList, go"""
    
    #find candidate with lowest Borda points, should be killer but NOT W
    cands1 = getCands(frame2)
    nCands = len(cands1)
    if nCands<=2:
        print("Something strange happened, nCands is less than 3, no mods possible.")
        return frame2, True, anomFound
    vote_counts = BordaScores_OM(frame2, cands1, diagnostic=False)
    sorted_items = sorted(vote_counts.items(), key=lambda item: item[1]) #sorted lowest votes to highest
    sorted_cands = [item[0] for item in sorted_items] #K should be first
    
    #anomFound = False
    
    K1 = sorted_cands[0] #killer with lowest points, may not be K
    if K1 not in ksnw:
        print("Something strange happened, last place is not in killer subset.")
        return frame2, False, False
    if K1 == K:
        print("DemiKiller K is in last place, Downward anomaly NOT possible")
        return frame2, False, False
    tempframe = frame2.copy(deep=True)
    go = True
    
    L = get_lowest_remaining(vote_counts, ksnw) #find lowest candidate NOT in ksnw
    
    gap = vote_counts[L]-vote_counts[K1] #need to modify gap+1 votes
    check = copy.deepcopy(gap)
    
#      #K1 is not same as K (need K before W, all other conditions same)
#     #Remove ballots of greatest depth
#     for j in range(nCands-2): #want to start with length n-2
#         space = nCands-2-j
        
    #now change bullet votes (do this first in OM? Yes)
    for z in range(len(tempframe)):
        if check >= 0:
            ballot = tempframe.at[z,'ballot'] #change all K to K1_K
            if (len(ballot)==1) and (K in ballot):
                if check - tempframe.at[z,'Count']*2>=-1: #modify all such ballots
                    check = check - tempframe.at[z,'Count']*2
                    tempframe.at[z,'ballot'] = insert_candidateAbove(ballot, K, K1) #makes K->K_1_K,
                    tempframe.at[z,'ballot_modified'] = insert_candidateAbove(tempframe.at[z,'ballot_modified'], K, K1)

                else: #modify check+1 such ballots such ballots
                    if tempframe.at[z,'Count']>0:
                        tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                        #now add new line to frame with modified ballot
                        tempframe.loc[len(tempframe)] = [insert_candidateAbove(ballot, K, K1), check+1, tempframe.at[z,'ballot_OG'], 0, insert_candidateAbove(tempframe.at[z,'ballot_OG'], K, K1)]
                        check = -1
                        
            if check < 0:
                tempframe,go, anomFound = runAroundDown_TVR_OM(tempframe, ksnw, W, K, go, anomFound)     
        
    for z in range(len(tempframe)):
        if check >= 0:
            ballot = tempframe.at[z,'ballot'] #change all K_K1 to K1_K
            if (len(ballot)!=0) and (K in ballot) and (K1 in ballot) and (ballot.find(K1)-ballot.find(K)==1):
                if check - tempframe.at[z,'Count']>=-1: #modify all such ballots
                    check = check - tempframe.at[z,'Count']
                    tempframe.at[z,'ballot'] = shift_candidateDown(ballot, K, K1) #makes K_K1->K_1_K, rest stays
                    tempframe.at[z,'ballot_modified'] = shift_candidateDown(tempframe.at[z,'ballot_modified'], K, K1)

                else: #modify check+1 such ballots such ballots
                    if tempframe.at[z,'Count']>0:
                        tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                        #now add new line to frame with modified ballot
                        tempframe.loc[len(tempframe)] = [shift_candidateDown(ballot, K, K1), check+1, tempframe.at[z,'ballot_OG'], 0, shift_candidateDown(tempframe.at[z,'ballot_OG'], K, K1)]
                        check = -1
                        
            if check < 0:
                #print(check)
                #print(tempframe)
                tempframe, go, anomFound = runAroundDown_TVR_OM(tempframe, ksnw, W, K, go, anomFound)     
    
    
    #anomFound = False
    return tempframe, False, anomFound





def findDemiKillerSubs_TVR_AVG(profile, diagnostic=False): 
    cands = getCands(profile)
    
    demi_killer_subsets = []
    winners = TVR_AVG(profile, cands)
    if len(winners)>1:
        print('##### Multiple initial winners #####')
        return []
    winner = winners[0]
    if diagnostic:
        print(winners)
        
    ##### search for demikiller subsets
    losers = cands.copy()
    losers.remove(winner)
    
    ## only eliminate in round of three or two
    cand_subsets = list(combinations(losers, 2))
    cand_subsets3 = list(combinations(losers, 3))
    #for loser in losers: #dont need these because 2 candidate DK subsets are no good
        #cand_subsets.append((loser))
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
    
    
    ## test if each subset has winner in second to last place
    for cand_tuple in cand_subsets:
        subset = list(cand_tuple)
        subset.append(winner)
        
        profile_temp = profile.copy(deep=True)
        reduced_prof = reduceProfile(profile_temp, subset)
        scores = BordaScores_AVG(reduced_prof, subset, diagnostic=False)
        S = get_secondLow(scores)
        
        if (winner == S):
            demi_killer_subsets.append([subset, scores])
    if len(demi_killer_subsets)>0:
        print(demi_killer_subsets)
        #data2.write(demi_killer_subsets)
        
    return demi_killer_subsets
        
       
    
def runAroundDown_TVR_AVG(profile, ksnw, W, K,go, anomFound):
    """ takes in profile, list of demikillers without winner, winner, killer, and modified votes.
    Runs a round of Demi Killer Subset code, returns updated profile, mod votes, whether or not to go on"""
    
    #vote_counts={cand:0 for cand in hopefuls}
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
        
        if vote_counts[W] == min_count: #this could happen after DK mods, winner in last place
            win1 = TVR_AVG(profile, cands1, diagnostic=False)
            if win1[0] == W:
                print("No anomaly: Winner ranked last but somehow OG Winner wins TVR_AVG. Should not happen")
                return profile, False, False 
            elif win1[0] == K:
                anomFound = True
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
                winner_modified = TVR_AVG(profile_modified, cands_OG, diagnostic=True)
                if winner_modified[0] != win1[0]:
                    print(f"MAJOR PROBLEM!!!! Program thinks {win1[0]} should be the new winner, but the modified election actually gives {winner_modified[0]}")
                    print(f"New data collection says: {dfModsList}.  Modified data winner is {winner_modified}")
                    
                print("\n")
                print("Downward TVR_AVG ANOMALY!!! Modified votes are " + str(dfModsList)+
                       " and now " + str(win1[0]) + " is the winner.")
                
#                 data1.write("Downward TVR_AVG ANOMALY!!! Removed votes are " +
#                       str(modifiedVotesDict) + " and now " + str(win1[0]) +
#                         " is the winner.")
#                 data1.write("\n")
                return profile,  False, True 
            else:
                return profile, False, False
        elif set(cands1noW) == set(ksnw): #if at demiKiller subset, run DK mods
            frame2 = profile.copy(deep = True)
            return runMods_Down_TVR_AVG(frame2, ksnw, W, K, go, anomFound)
                #DKMods: last-place is K1, remove enough K....W....K1 ballots so that W drops out
        else:
            #have NOT hit the demiKiller subset
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
                return runAroundDown_TVR_AVG(frame2, ksnw, W, K, True, anomFound)
            else: #run non-DK modifications.  Someone in ksnw is in last place
                frame2 = profile.copy(deep = True)
                return runMods_Down_TVR_AVG(frame2, ksnw, W, K, go, anomFound)
    else:
        print("Error: Winner not in round.")
        return profile, False, anomFound   
            
            
            
def runMods_Down_TVR_AVG(frame2, ksnw, W, K, go, anomFound):
    #removing ballots when NOT in DK subset, hoping to get to DK subset
    """given profile, winner W, killer K, ksnw, and list, removes just enough ..L...K_W... ballots to make 
    L drop out next, returns modified frame, removedVotesList, go"""
    
    #find candidate with lowest Borda points, should be killer but NOT W
    cands1 = getCands(frame2)
    nCands = len(cands1)
    if nCands<=2:
        print("Something strange happened, nCands is less than 3, no mods possible.")
        return frame2, True, anomFound
    vote_counts = BordaScores_AVG(frame2, cands1, diagnostic=False)
    sorted_items = sorted(vote_counts.items(), key=lambda item: item[1]) #sorted lowest votes to highest
    sorted_cands = [item[0] for item in sorted_items] #K should be first
    
    #anomFound = False
    
    K1 = sorted_cands[0] #killer with lowest points, may not be K
    if K1 not in ksnw:
        print("Something strange happened, last-place is not in killer subset. Check this election!")
        return frame2, False, False #runAroundDown_TVR_AVG(frame2, ksnw, W, K, modifiedVotesList, modifiedVotesDict, True, anomFound) 
    if K1 == K:
        print("DemiKiller K is in last place, Downward anomaly NOT possible")
        return frame2, False, False
    tempframe = frame2.copy(deep=True)
    go = True
    
    L = get_lowest_remaining(vote_counts, ksnw) #find lowest candidate NOT in ksnw
    
    gap = vote_counts[L]-vote_counts[K1] #need to modify gap+1 votes
    check = copy.deepcopy(gap)
    
        
    for z in range(len(tempframe)):
        if check >= 0:
            ballot = tempframe.at[z,'ballot'] #change all K_K1 to K1_K
            if (len(ballot)!=0) and (K in ballot) and (K1 in ballot) and (ballot.find(K1)-ballot.find(K)==1):
                if check - tempframe.at[z,'Count']>=-1: #modify all such ballots
                    check = check - tempframe.at[z,'Count']
                    tempframe.at[z,'ballot'] = shift_candidateDown(ballot, K, K1) #makes K_K1->K_1_K, rest stays
                    tempframe.at[z,'ballot_modified'] = shift_candidateDown(tempframe.at[z,'ballot_modified'], K, K1)

                else: #modify check+1 such ballots such ballots
                    if tempframe.at[z,'Count']>0:
                        tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                        #now add new line to frame with modified ballot
                        tempframe.loc[len(tempframe)] = [shift_candidateDown(ballot, K, K1), check+1, tempframe.at[z,'ballot_OG'], 0, shift_candidateDown(tempframe.at[z,'ballot_OG'], K, K1)]
                        check = -1
                        
            if check < 0:
                tempframe, go, anomFound = runAroundDown_TVR_AVG(tempframe, ksnw, W, K, go, anomFound)     
    
    #now change bullet votes (do this first in OM? Yes)
    for z in range(len(tempframe)):
        if check >= 0:
            ballot = tempframe.at[z,'ballot'] #change all K to K1_K
            if (len(ballot)==1) and (K in ballot):
                if check - tempframe.at[z,'Count']>=-1: #modify all such ballots
                    check = check - tempframe.at[z,'Count']
                    tempframe.at[z,'ballot'] = insert_candidateAbove(ballot, K, K1) #makes K->K_1_K,
                    tempframe.at[z,'ballot_modified'] = insert_candidateAbove(tempframe.at[z,'ballot_modified'], K, K1)

                else: #modify check+1 such ballots such ballots
                    if tempframe.at[z,'Count']>0:
                        
                        tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                        #now add new line to frame with modified ballot
                        tempframe.loc[len(tempframe)] = [insert_candidateAbove(ballot, K, K1), check+1, tempframe.at[z,'ballot_OG'], 0, insert_candidateAbove(tempframe.at[z,'ballot_OG'], K, K1)]
                        check = -1
            if check < 0:
                tempframe, go, anomFound = runAroundDown_TVR_AVG(tempframe, ksnw, W, K, go, anomFound)     
        
    #anomFound = False
    return tempframe, False, anomFound




    ### helper programs for individual types ####


############################################################

    ### main programs for individual types ####

#DemiKiller subset code for TVR AVG No show
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



#note: election is raw data
def demiKillerSubs_Down_TVR_PM(election, anomFound, diagnostic = False):
    if diagnostic:
        print("running Downward tvr PM ")
    
    profile, cands, num_Cands = prefProfileInput5(election)
    if num_Cands > 15:
        print("more than 15 candidates, now filtering")
        profile = reduceToTopN(profile, 15)
        cands = getCands(profile)
        num_Cands = 15
    
    
    winners = TVR_PM(profile, cands, diagnostic=False)
    W = winners[0]

    demikiller_subs = findDemiKillerSubs_TVR_PM(profile, diagnostic=False) 
    #this is a list of lists.  killer_subs[0][0]=first ks, [1][0]=2nd ks, etc

    if len(demikiller_subs)!=0:
        for ks2 in demikiller_subs: #should be dks2, but I am skipping that to make things easier
            ks = ks2[0]
            ksnw = copy.deepcopy(ks)
            if W not in ksnw:
                print("something weird.  W not in demikiller subset")
                continue
            ksnw.remove(W) #because W wins TVR, they will never be in last place
            profile_temp = profile.copy(deep=True)
            reduced_prof = reduceProfile(profile_temp, ksnw) #reduce to demiKillers w/o W
            killers = TVR_PM(reduced_prof, ksnw, diagnostic=False) #find winner of ksnw
            K = killers[0] #call that killer K: want to remove votes with K>W and have K win
            ks_dict = ks2[1]
            if W not in ks:
                print("Error: Killer subset without winner, something is wrong.")
            else:
                if anomFound:
                    return True
                profile1 = profile.copy(deep=True)
                go = True
                while (go == True) and (anomFound == False): 
                    if diagnostic:
                        print("starting runAround ")
                    profile1, go, anomFound  = runAroundDown_TVR_PM(profile1, ksnw, W, K, go, anomFound)
                    #print("1. Now go is " + str(go))
                    if go == False or anomFound == True:
                        break
        if anomFound:
            return True
    else:
        if diagnostic:
            print("No killer subsets in " + str(election))
        return False
        
       

#note: election is raw data
def demiKillerSubs_Down_TVR_OM(election, anomFound, diagnostic = False):
    if diagnostic:
        print("running Downward tvr OM ")
    
    profile, cands, num_Cands = prefProfileInput5(election)
    if num_Cands > 15:
        print("more than 15 candidates, now filtering")
        profile = reduceToTopN(profile, num_Cands, 15)
        cands = getCands(profile)
        num_Cands = 15
    
    winners = TVR_OM(profile, cands, diagnostic=False)
    W = winners[0]

    demikiller_subs = findDemiKillerSubs_TVR_OM(profile, diagnostic=False) 
    #this is a list of lists.  killer_subs[0][0]=first ks, [1][0]=2nd ks, etc

    if len(demikiller_subs)!=0:
        for ks2 in demikiller_subs: #should be dks2, but I am skipping that to make things easier
            ks = ks2[0]
            ksnw = copy.deepcopy(ks)
            if W not in ksnw:
                print("something weird.  W not in demikiller subset")
                continue
            ksnw.remove(W) #because W wins TVR, they will never be in last place
            profile_temp = profile.copy(deep=True)
            reduced_prof = reduceProfile(profile_temp, ksnw) #reduce to demiKillers w/o W
            killers = TVR_OM(reduced_prof, ksnw, diagnostic=False) #find winner of ksnw
            K = killers[0] #call that killer K: want to remove votes with K>W and have K win
            ks_dict = ks2[1]
            if W not in ks:
                print("Error: Killer subset without winner, something is wrong.")
            else:
                if anomFound:
                    return True
                profile1 = profile.copy(deep=True)
                go = True
                while (go == True) and (anomFound == False): 
                    if diagnostic:
                        print("starting runAround ")
                    profile1, go, anomFound  = runAroundDown_TVR_OM(profile1, ksnw, W, K, go, anomFound)
                    #print("1. Now go is " + str(go))
                    if go == False or anomFound == True:
                        break
        if anomFound:
            return True
    else:
        if diagnostic:
            print("No killer subsets in " + str(election))
        return False
        


#note: election is raw data
def demiKillerSubs_Down_TVR_AVG(election, anomFound, diagnostic = False):
    if diagnostic:
        print("running Downward tvr AVG ")
    
    profile, cands, num_Cands = prefProfileInput5(election)
    if num_Cands > 15:
        print("more than 15 candidates, now filtering")
        profile = filter_weak_cands(profile, num_Cands, 15)
        cands = getCands(profile)
        num_Cands = 15
    
    
    winners = TVR_AVG(profile, cands, diagnostic=False)
    W = winners[0]

    demikiller_subs = findDemiKillerSubs_TVR_AVG(profile, diagnostic=False) 
    #this is a list of lists.  killer_subs[0][0]=first ks, [1][0]=2nd ks, etc

    if len(demikiller_subs)!=0:
        for ks2 in demikiller_subs: #should be dks2, but I am skipping that to make things easier
            ks = ks2[0]
            ksnw = copy.deepcopy(ks)
            if W not in ksnw:
                print("something weird.  W not in demikiller subset")
                continue
            ksnw.remove(W) #because W wins TVR, they will never be in last place
            profile_temp = profile.copy(deep=True)
            reduced_prof = reduceProfile(profile_temp, ksnw) #reduce to demiKillers w/o W
            killers = TVR_AVG(reduced_prof, ksnw, diagnostic=False) #find winner of ksnw
            K = killers[0] #call that killer K: want to remove votes with K>W and have K win
            ks_dict = ks2[1]
            if W not in ks:
                print("Error: Killer subset without winner, something is wrong.")
            else:
                if anomFound:
                    return True
                profile1 = profile.copy(deep=True)
                go = True
                while (go == True) and (anomFound == False): 
                    if diagnostic:
                        print("starting runAround ")
                    profile1,  go, anomFound  = runAroundDown_TVR_AVG(profile1, ksnw, W, K, go, anomFound)
                    #print("1. Now go is " + str(go))
                    if go == False or anomFound == True:
                        break
        if anomFound:
            return True
    else:
        if diagnostic:
            print("No killer subsets in " + str(election))
        return False



    ### main programs for individual types ####


    #Run  code for all
import os
import statistics
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

start1 = time.process_time()
dataset_name = "scotland"
#data1 = open(f"TVR_AVG_Downward_{dataset_name}.txt", "w")
#data3 = open("CompromiseMore_IRV_Murky.txt", "w")

directory=f'Preference Profiles/{dataset_name}' #'Scotland data, LEAP'
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
            print("\n")
            print(num_elections)
            #print(filename)
        anomFound = False
        weasel = demiKillerSubs_Down_TVR_OM(filename, anomFound, diagnostic = False)
        if weasel:
            counter += 1
            print(str(counter) + ")" + str(filename))
#             data1.write("\n")
#             data1.write("(" + str(counter) + ") " + str(filename))
#             data1.write("\n")
#             data1.write("\n")
            
#print("Total number of elections with TVR_AVG killer subsets is " + str(counter))     
#data1.close()
#data2.close()
#data3.close()
print(f"Total anomalies were {counter} and total time was ")
print(time.process_time() - start1)

