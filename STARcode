###### Helper programs ######

def reduceToTopN(df, keep_num): #written with AI
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
            plurality_scores[first_choice] += profile.at[k,'Count']
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


###### Helper programs above ######

###### STAR programs below #######

def STAR_hi(profile, cands, diagnostic=False): 
    if len(cands)>6:
        profile = reduceToTopN(profile, 6)
        cands = getCands(profile)
        num_Cands = 6
    
    scores = STAR_Scores_hi(profile, cands, diagnostic=False)
    top_two = sorted(scores, key=scores.get, reverse=True)[:2]
    top2_profile = reduceProfile(profile, top_two)
    
    winner = Borda_PM(top2_profile, top_two, diagnostic=False) #Can be any Borda, just want winner of top 2
    return winner

def STAR_Scores_hi(profile, cands, diagnostic=False):
    '''takes in voting data, returns all STAR hi scores'''
    
    max_score = 5
    
    ## compute candidate scores
    cand_scores = {cand: 0 for cand in cands}
    for k in range(len(profile)):
        count = profile.at[k, 'Count']
        curBal= profile.at[k, 'ballot']
        for i in range(0,len(curBal)):
            candidate = curBal[i]
            if candidate in cands:
                cand_scores[candidate] += (max_score - (i )) * count
                
    return cand_scores

############################################
############################################

def STAR_mid(profile, cands, diagnostic=False): 
    if len(cands)>6:
        profile = reduceToTopN(profile, 6)
        cands = getCands(profile)
        num_Cands = 6
    
    scores = scores_STAR_mid(profile, cands, diagnostic=False)
    top_two = sorted(scores, key=scores.get, reverse=True)[:2]
    top2_profile = reduceProfile(profile, top_two)
    
    winner = Borda_PM(top2_profile, top_two, diagnostic=False)
    return winner

def scores_STAR_mid(profile, cands, diagnostic=False):
    max_score = 5
    
    ## compute candidate scores
    cand_scores = {cand: 0 for cand in cands}
    
    if len(cands)==6: 
        for k in range(len(profile)):
            count = profile.at[k, 'Count']
            curBal= profile.at[k, 'ballot']
            if len(curBal)==6: #Calc as Borda PM
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        cand_scores[candidate] += (max_score - (i )) * count
            elif len(curBal)==5: #Calc as Borda PM
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        cand_scores[candidate] += (max_score - (i )) * count
            elif len(curBal)==4: #Calc as 5-4-2-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0) or (i==1):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==2):
                            cand_scores[candidate] += 2 * count
                        if (i==3):
                            cand_scores[candidate] += count
            elif len(curBal)==3: #Calc as 5-3-2
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 3 * count
                        if (i==2):
                            cand_scores[candidate] += 2 * count
            elif len(curBal)==2: #Calc as 5-2.5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 2.5 * count
            elif len(curBal)==1: #Calc as 5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
            else:
                pass #ballot is blank
        return cand_scores
    
    elif len(cands)==5:
        for k in range(len(profile)):
            count = profile.at[k, 'Count']
            curBal= profile.at[k, 'ballot']
            
            if len(curBal)==5: #Calc as 5-4-2-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0) or (i==1):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==2):
                            cand_scores[candidate] += 2 * count
                        if (i==3):
                            cand_scores[candidate] += count
            elif len(curBal)==4: #Calc as 5-4-2-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0) or (i==1):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==2):
                            cand_scores[candidate] += 2 * count
                        if (i==3):
                            cand_scores[candidate] += count
            elif len(curBal)==3: #Calc as 5-3-2
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 3 * count
                        if (i==2):
                            cand_scores[candidate] += 2 * count
            elif len(curBal)==2: #Calc as 5-2.5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 2.5 * count
            elif len(curBal)==1: #Calc as 5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
            else:
                pass #ballot is blank
        return cand_scores
    elif len(cands)==4:
        for k in range(len(profile)):
            count = profile.at[k, 'Count']
            curBal= profile.at[k, 'ballot']
            
            if len(curBal)==4: #Calc as 5-3-2
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 3 * count
                        if (i==2):
                            cand_scores[candidate] += 2 * count
            elif len(curBal)==3: #Calc as 5-3-2
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 3 * count
                        if (i==2):
                            cand_scores[candidate] += 2 * count
            elif len(curBal)==2: #Calc as 5-2.5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 2.5 * count
            elif len(curBal)==1: #Calc as 5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
            else:
                pass #ballot is blank
        return cand_scores
    elif len(cands)==3:
        for k in range(len(profile)):
            count = profile.at[k, 'Count']
            curBal= profile.at[k, 'ballot']
            
            if len(curBal)==3: #Calc as 5-2.5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 2.5 * count
            elif len(curBal)==2: #Calc as 5-2.5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 2.5 * count
            elif len(curBal)==1: #Calc as 5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
            else:
                pass #ballot is blank
        return cand_scores
    else:
        print("More than 6 or less than three candidates: SOMETHING WEIRD!")
        cand_scores = BordaScores_PM(profile, cands, diagnostic=False)
        return cand_scores
    
############################################
############################################

def STAR_lo(profile, cands, diagnostic=False): 
    if len(cands)>6:
        profile = reduceToTopN(profile, 6)
        cands = getCands(profile)
        num_Cands = 6
    
    scores = scores_STAR_lo(profile, cands, diagnostic=False)
    top_two = sorted(scores, key=scores.get, reverse=True)[:2]
    top2_profile = reduceProfile(profile, top_two)
    
    winner = Borda_PM(top2_profile, top_two, diagnostic=False)
    return winner

def scores_STAR_lo(profile, cands, diagnostic=False):
    max_score = 5
    
    ## compute candidate scores
    cand_scores = {cand: 0 for cand in cands}
    
    if len(cands)==6: 
        for k in range(len(profile)):
            count = profile.at[k, 'Count']
            curBal= profile.at[k, 'ballot']
            if len(curBal)==6: #Calc as Borda PM
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        cand_scores[candidate] += (max_score - (i )) * count
            elif len(curBal)==5: #Calc as Borda PM
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        cand_scores[candidate] += (max_score - (i )) * count
            elif len(curBal)==4: #Calc as 5-3-2-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 3 * count
                        if (i==2):
                            cand_scores[candidate] += 2 * count
                        if (i==3):
                            cand_scores[candidate] += count
            elif len(curBal)==3: #Calc as 5-2-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 2 * count
                        if (i==2):
                            cand_scores[candidate] += 1 * count
            elif len(curBal)==2: #Calc as 5-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += count
            elif len(curBal)==1: #Calc as 5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
            else:
                pass #ballot is blank
        return cand_scores
    
    elif len(cands)==5:
        for k in range(len(profile)):
            count = profile.at[k, 'Count']
            curBal= profile.at[k, 'ballot']
            
            if (len(curBal)==5) or (len(curBal)==4): #Calc as 5-3-2-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 3 * count
                        if (i==2):
                            cand_scores[candidate] += 2 * count
                        if (i==3):
                            cand_scores[candidate] += count
            
            elif len(curBal)==3: #Calc as 5-2-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 2 * count
                        if (i==2):
                            cand_scores[candidate] += 1 * count
            elif len(curBal)==2: #Calc as 5-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 1 * count
            elif len(curBal)==1: #Calc as 5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
            else:
                pass #ballot is blank
        return cand_scores
    elif len(cands)==4:
        for k in range(len(profile)):
            count = profile.at[k, 'Count']
            curBal= profile.at[k, 'ballot']
            
            if (len(curBal)==4) or (len(curBal)==3): #Calc as 5-2-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += 2 * count
                        if (i==2):
                            cand_scores[candidate] += 1 * count
            
            elif len(curBal)==2: #Calc as 5-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] +=  count
            elif len(curBal)==1: #Calc as 5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
            else:
                pass #ballot is blank
        return cand_scores
    elif len(cands)==3:
        for k in range(len(profile)):
            count = profile.at[k, 'Count']
            curBal= profile.at[k, 'ballot']
            
            if (len(curBal)==3) or (len(curBal)==2): #Calc as 5-1
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
                        if (i==1):
                            cand_scores[candidate] += count
            
            elif len(curBal)==1: #Calc as 5
                for i in range(0,len(curBal)):
                    candidate = curBal[i]
                    if candidate in cands:
                        if (i==0):
                            cand_scores[candidate] += (max_score - (i )) * count
            else:
                pass #ballot is blank
        return cand_scores
    else:
        print("More than 6 or less than three candidates: SOMETHING WEIRD!")
        cand_scores = BordaScores_PM(profile, cands, diagnostic=False)
        return cand_scores
