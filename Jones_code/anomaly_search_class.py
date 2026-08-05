########################################
##### Anomaly search class
########################################

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

from election_class import *
from ballot_modifications_class import *

##### TODO
## 



def remove_zero_values(input_dict): #written by Gemini
  """
  Removes key-value pairs from a dictionary where the value is 0.
  Args:
    input_dict: A dictionary with letter keys and numerical values.
  Returns:
    A new dictionary with key-value pairs where the value is not 0.
  """
  return {key: value for key, value in input_dict.items() if value != 0}




def find_killer_subsets(profile, num_cands, diagnostic=False): 
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    killer_subsets = []
    winners, foo1, foo2 =IRV(profile, cands) #get election data from IRV
    if len(winners)>1:
        print('##### Multiple initial winners #####')
        return []
    winner = winners[0]
    if diagnostic:
        print(winners)
        
    ##### search for killer subsets
    losers = cands.copy()
    losers.remove(winner)
    
    ## only eliminate in round of five through two
    cand_subsets = list(combinations(losers, 2))
    cand_subsets += list(combinations(losers, 3))
    cand_subsets += list(combinations(losers, 4))
    for loser in losers:
        cand_subsets.append((loser))
    
    ## try all possible rounds
    # cand_subsets = []
    # for i in range(2, num_cands-1):
    #     cand_subsets+=list(combinations(losers,i))
    
    ## test if each subset could eliminate winner
    for cand_tuple in cand_subsets:
        subset = list(cand_tuple)
        subset.append(winner)
        
        scores = {cand: 0 for cand in subset}
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
            for c in ballot: 
                if c in subset:
                    scores[c]+=profile.at[k, 'Count']
                    break
            
        # if scores[winner] == min(scores.values()) and min(scores.values())!=max(scores.values()):
        if scores[winner] == min(scores.values()) and list(scores.values()).count(scores[winner])==1:
            # print(lxn + ' : ', winner, subset)
            # print(subset)
            # killer_subset_count += 1
            # break
            killer_subsets.append([subset, scores])
            
    return killer_subsets
            

###############################################################################
##### Anomaly search algorithms
##### general_search works with all election methods
##### more targeted searches are for specific election methods
##### all methods take in parameter that adjusts certain percent of votes
###############################################################################

def frac_general_search(profile, num_cands, voteMethod, mod_ballot_method, vote_frac, first_only=False, diagnostic=False):
    
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
    
    losers = cands.copy()
    losers.remove(W)
    if diagnostic:
        print(losers)

    if mod_ballot_method.__name__ == 'strat_bury_deep':
        scores = {cand: 0.0 for cand in cands}
        
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
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
            # if new_profile.at[k,'ballot']!='':
            ## change the ballot in some way
            curBal = new_profile.at[k,'ballot']
            if (not first_only) or (curBal[0] == L): 
                count = int(new_profile.at[k, 'Count']*vote_frac)
                modBal, modified = mod_ballot_method(curBal, W, L, cands_ranked)
                # new_profile.at[k,'ballot'] = modBal
                # if modified:
                if curBal!=modBal:
                    modified_ballot_list.append([curBal, modBal, count])
                    new_profile.at[k, 'Count'] -= count
                    new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [modBal], 'Count': [count]})], ignore_index=True)
            
        newWinners = voteMethod(new_profile, cands, diagnostic = diagnostic)[0]
        if len(newWinners)!=1:
            print('##### WARNING: MULTIPLE WINNERS DETECTED ######')
            continue
        newWinner = newWinners[0]
        
        if L == newWinner:
            return [W, L, modified_ballot_list]
    
    return []






###############################################################################
###############################################################################

def frac_noShowBucklin(profile, num_cands, vote_frac, diagnostic=False):
    # search through the election. If at any stage a loser is beating the winner, 
    # see if ballots that rank loser above winner but are not yet being counted
    # can be thrown out to lower the quota so that loser wins without having to 
    # advance to next round of counts
    
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    winners = bucklin(profile, cands)[0]
    if len(winners)>1:
        # hard to define an anomaly if there is not a single winner
        return []
    winner = winners[0]
    losers = cands.copy()
    losers.remove(winner)
    
    if diagnostic:
        print(winner)
        print(losers)
    
    ## Initialize scores for candidates to 0
    scores = {cand: 0.0 for cand in cands}
    threshold = profile['Count'].sum() / 2  # Majority threshold
    
    if diagnostic:
        print(scores)
        print(threshold)
    for round_indx in range(num_cands):
        ## update scores for the current round
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
            if len(ballot) > round_indx:
                cand = ballot[round_indx]
                scores[cand] += profile.at[k, 'Count']

        if diagnostic:
            print(scores)
        if scores[winner]>=threshold:
            return []
        
        ## check if any candidate has higher score than winner
        for loser in losers:
            if scores[loser] > scores[winner]:
                new_profile = profile.copy(deep=True)
                remove_ballots = []
                remove_ballot_count = 2*(threshold - scores[loser]) + 1
                for k in range(len(profile)):
                    ballot = profile.at[k, 'ballot']
                    count = int(profile.at[k, 'Count']*vote_frac)
                    if ballot.find(loser)>round_indx:
                        if (winner not in ballot) or (ballot.find(winner) > ballot.find(loser)):
                            if count <= remove_ballot_count:
                                remove_ballots.append([ballot, count])
                                new_profile.at[k, 'Count'] -= count
                                remove_ballot_count -= count
                            elif count > remove_ballot_count:
                                remove_ballots.append([ballot, remove_ballot_count])
                                new_profile.at[k, 'Count'] -= remove_ballot_count
                                remove_ballot_count = 0
                if remove_ballot_count == 0:
                    new_wins = bucklin(new_profile, cands)[0]
                    if diagnostic:
                        print(new_wins)
                        print(remove_ballots)
                    if new_wins == [loser]:
                        return [winner, loser, remove_ballots]
                    # else:
                    #     print('maybe a bucklin error')
                    #     bucklin(new_profile, cands, diagnostic=True)
        
        
        
        # ## check if any candidate has higher score than winner
        # for loser in losers:
        #     if scores[loser] > scores[winner]:
        #     # if scores[loser] == max(scores.values()):
        #         new_profile = profile.copy(deep=True)
        #         remove_ballots = []
        #         remove_ballot_total = 0
        #         for k in range(len(profile)):
        #             ballot = profile.at[k, 'ballot']
        #             count = int(profile.at[k, 'Count']*vote_frac)
        #             if ballot.find(loser)>round_indx:
        #                 if (winner not in ballot) or (ballot.find(winner) > ballot.find(loser)):
        #                     remove_ballots.append([ballot, count])
        #                     remove_ballot_total += count
        #                     new_profile.at[k, 'Count'] -= count
        #         if threshold - remove_ballot_total/2 < scores[loser]:
        #             new_wins = bucklin(new_profile, cands)[0]
        #             if diagnostic:
        #                 print(new_wins)
        #                 print(remove_ballots)
        #             if new_wins != [loser]:
        #                 print('##### WARNING: ERROR WITH BUCKLIN NO SHOW SEARCH #####')
        #                 print(breakhere)
        #             return [winner, loser, remove_ballots]

    return []

###############################################################################
###############################################################################

def frac_upMonoPR(profile, num_cands, vote_frac, diagnostic=False):
    # run original election to get winner and contender
    # see if any upstart candidates defeat winner in h2h
    # check if winner can be moved above contender in enough ballots so that
    # upstart advances to second round instead of contender
    # confirm that upstart defeats winner
    
    if num_cands>2:
        cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                      'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                      'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                      'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        cands = cand_names[:num_cands]
        
        # Initialize scores for candidates to 0
        scores = {cand: 0.0 for cand in cands}
        
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
            scores[ballot[0]] += profile.at[k, 'Count']
        
        if diagnostic:
            print(scores)
    
    
        # keep two candidates with highest scores
        second_round_cands = cands.copy()
        second_round_cands.sort(key=lambda cand: scores[cand], reverse = True)
        second_round_cands = second_round_cands[:2]
        
        c1, c2 = second_round_cands
        scores2 = {cand: 0.0 for cand in second_round_cands}
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
            if c1 in ballot and c2 in ballot:
                if ballot.find(c1)<ballot.find(c2):
                    scores2[c1] += profile.at[k, 'Count']
                else:
                    scores2[c2] += profile.at[k, 'Count']
            elif c1 in ballot:
                scores2[c1] += profile.at[k, 'Count']
            elif c2 in ballot:
                scores2[c2] += profile.at[k, 'Count']
        
        # Winner has most first place votes
        max_score = max(scores2.values())
        winners = [cand for cand, score in scores2.items() if score == max_score]
        if len(winners)>1:
            print('##### Multiple winners #####')
            return []
        
        if diagnostic:
            print(scores2)
            print(winners)
            
        ranked_cands = sorted(list(scores.keys()), key = lambda cand: scores[cand], reverse = True)
        if diagnostic:
            print(ranked_cands)
        
        if scores[ranked_cands[2]]==scores[ranked_cands[1]]:
            print('##### multiple contenders #####')
            return []
        
        winner = winners[0]
        
        ## find candidates that could beat winner in H2H
        margins = np.zeros((num_cands, num_cands))
        
        for c1 in range(num_cands):
            for c2 in range(c1+1, num_cands):
                c1_let = cand_names[c1]
                c2_let = cand_names[c2]
                # number of votes c1 gets over c2 in H2H
                margin = 0
                
                for k in range(len(profile)):
                    ballot = profile.at[k, 'ballot']
                    count = profile.at[k, 'Count']
                    ## ballot ranks both c1 and c2
                    if c1_let in ballot and c2_let in ballot:
                        if ballot.find(c1_let) < ballot.find(c2_let):
                            margin += count
                        else:
                            margin -= count
                    ## ballot only ranks c1       
                    elif c1_let in ballot:
                        margin += count
                    ## ballot only ranks c2
                    elif c2_let in ballot:
                        margin -= count
                
                margins[c1, c2] = margin
                margins[c2, c1] = -1*margin
        
        
        upstarts = [cand_names[c1] for c1 in range(num_cands) if margins[c1, cands.index(winner)]>0]
        if diagnostic:
            print(margins)
            print(cands)
            print(upstarts)
        
        for upstart in upstarts:
            if diagnostic:
                print(upstart)
            ## check if upstart can make it to second round and defeat winner
            upstart_win_margin = margins[cand_names.index(upstart), cand_names.index(winner)]
            
            need_to_lose = ranked_cands[:ranked_cands.index(upstart)]
            need_to_lose.remove(winner)
            gaps = {cand: scores[cand] - scores[upstart] for cand in need_to_lose}
            risky_ballots = {cand: 0 for cand in need_to_lose}
            if diagnostic:
                print(gaps)
            
            new_profile = profile.copy(deep = True)
            modified_ballot_list = []
            for k in range(len(profile)):
                oldBal = new_profile.at[k, 'ballot']
                cur_lead = oldBal[0]
                if cur_lead in need_to_lose:
                    if (upstart not in oldBal and winner in oldBal) or (upstart in oldBal and winner in oldBal and oldBal.find(winner)<oldBal.find(upstart)):
                        ## move winner to top
                        newBal = modifyUp(oldBal, winner)
                        count = int(new_profile.at[k, 'Count']*vote_frac)
                        # new_profile.at[k, 'ballot'] = newBal
                        new_profile.at[k, 'Count'] -= count
                        new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [newBal], 'Count': [count]})], ignore_index=True)
                        modified_ballot_list.append([oldBal, newBal, count])
                        gaps[cur_lead] -= count
                    elif (upstart in oldBal and winner in oldBal and oldBal.find(upstart)<oldBal.find(winner)) or (winner not in oldBal):
                        risky_ballots[cur_lead] += new_profile.at[k, 'Count']
            
            if diagnostic:
                print(gaps)
                print(modified_ballot_list)
                print(risky_ballots)
            if max(gaps.values()) < 0:
                ## upstart should advance to second round and beat winner
                ## check election
                new_win = plurality_runoff(new_profile, cands)[0]
                if new_win[0] == upstart:
                    return [winner, upstart, modified_ballot_list]
                else:
                    print(new_win[0])
                    print('##### Error with safe ballots #####')
            else:
                ## try removing risky ballots
                
                ballots_to_change = {}
                for cand in need_to_lose:
                    if gaps[cand] >= 0:
                        ballots_to_change[cand] = gaps[cand]
                
                if diagnostic:
                    print(ballots_to_change)
                    print(upstart_win_margin)
                    
                ## first change ballots that don't rank upstart
                for k in range(len(profile)):
                    oldBal = new_profile.at[k, 'ballot']
                    cur_lead = oldBal[0]
                    if cur_lead in ballots_to_change.keys():
                        if winner not in oldBal and upstart not in oldBal:
                            if ballots_to_change[cur_lead] < 0:
                                ## already removed enough ballots, no need to remove more
                                pass
                            elif ballots_to_change[cur_lead] >= (int(new_profile.at[k, 'Count']*vote_frac)+1):
                                ## change all ballots
                                newBal = modifyUp(oldBal, winner)
                                count = int(new_profile.at[k, 'Count']*vote_frac)
                                # new_profile.at[k, 'ballot'] = newBal
                                new_profile.at[k, 'Count'] -= count
                                new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [newBal], 'Count': [count]})], ignore_index=True)
                                modified_ballot_list.append([oldBal, newBal, count])
                                ballots_to_change[cur_lead] -= count
                                # new_profile.at[k, 'Count'] = 0
                            else:
                                ## only change enough ballots
                                ## add new row to new_profile
                                newBal = modifyUp(oldBal, winner)
                                new_profile.at[k, 'Count'] -= (ballots_to_change[cur_lead] + 1)
                                modified_ballot_list.append([oldBal, newBal, ballots_to_change[cur_lead]+1])
                                row={'Count':[ballots_to_change[cur_lead]+1], 'ballot':[newBal]}
                                df2=pd.DataFrame(row)
                                new_profile = pd.concat([new_profile, df2], ignore_index=True)
                                ballots_to_change[cur_lead] = -1
                                
                ## test election having removed the less risky ballots
                new_win = plurality_runoff(new_profile, cands)[0]
                if diagnostic:
                    print(new_win)
                    print(new_profile)
                if new_win[0] == upstart:   
                    return [winner, upstart, modified_ballot_list]
                
                else:
                    
                    ## now change ballots that rank upstart above winner
                    for k in range(len(profile)):
                        oldBal = new_profile.at[k, 'ballot']
                        cur_lead = oldBal[0]
                        if cur_lead in ballots_to_change.keys():
                            if (upstart in oldBal and winner in oldBal and oldBal.find(upstart)<oldBal.find(winner)) or (upstart in oldBal and winner not in oldBal):
                                if ballots_to_change[cur_lead] < 0:
                                    ## already removed enough ballots, no need to remove more
                                    pass
                                elif ballots_to_change[cur_lead] >= (int(new_profile.at[k, 'Count']*vote_frac)+1):
                                    ## change all ballots
                                    newBal = modifyUp(oldBal, winner)
                                    count = int(new_profile.at[k, 'Count']*vote_frac)
                                    # new_profile.at[k, 'ballot'] = newBal
                                    new_profile.at[k, 'Count'] -= count
                                    new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [newBal], 'Count': [count]})], ignore_index=True)
                                    modified_ballot_list.append([oldBal, newBal, count])
                                    ballots_to_change[cur_lead] -= count
                                    # new_profile.at[k, 'Count'] = 0
                                else:
                                    ## only change enough ballots
                                    ## add new row to new_profile
                                    newBal = modifyUp(oldBal, winner)
                                    new_profile.at[k, 'Count'] -= (ballots_to_change[cur_lead] + 1)
                                    modified_ballot_list.append([oldBal, newBal, ballots_to_change[cur_lead]+1])
                                    row={'Count':[ballots_to_change[cur_lead]+1], 'ballot':[newBal]}
                                    df2=pd.DataFrame(row)
                                    new_profile = pd.concat([new_profile, df2], ignore_index=True)
                                    ballots_to_change[cur_lead] = -1
                                    
                    ## test election having removed the less risky ballots
                    new_win = plurality_runoff(new_profile, cands)[0]
                    if diagnostic:
                        print(new_win)
                        print(new_profile)
                    if new_win[0] == upstart:   
                        return [winner, upstart, modified_ballot_list]
                    
                    
                    if diagnostic:
                        print(modified_ballot_list)
                    # print('##### Error with risky ballots #####')
                
    return []

###############################################################################
###############################################################################

def frac_noShowPR(profile, num_cands, vote_frac, diagnostic=False):
    ## check if any upstart can beat winner in h2h
    ## see if any contender supporters could no show and let upstart advance
    ## to second round
    
    if num_cands>2:
        cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                      'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                      'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                      'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        cands = cand_names[:num_cands]
        
        ## Initialize scores for candidates to 0
        scores = {cand: 0.0 for cand in cands}
        
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
            scores[ballot[0]] += profile.at[k, 'Count']
            
        if diagnostic:
            print(scores)
        
        ## keep two candidates with highest scores
        second_round_cands = cands.copy()
        second_round_cands.sort(key=lambda cand: scores[cand], reverse = True)
        second_round_cands = second_round_cands[:2]
        
        c1, c2 = second_round_cands
        scores2 = {cand: 0.0 for cand in second_round_cands}
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
            if c1 in ballot and c2 in ballot:
                if ballot.find(c1)<ballot.find(c2):
                    scores2[c1] += profile.at[k, 'Count']
                else:
                    scores2[c2] += profile.at[k, 'Count']
            elif c1 in ballot:
                scores2[c1] += profile.at[k, 'Count']
            elif c2 in ballot:
                scores2[c2] += profile.at[k, 'Count']
        
        # Winner has most first place votes
        max_score = max(scores2.values())
        winners = [cand for cand, score in scores2.items() if score == max_score]
        if len(winners)>1:
            print('##### Multiple winners #####')
            return []
        
        ranked_cands = sorted(list(scores.keys()), key = lambda cand: scores[cand], reverse = True)
        if diagnostic:
            print(winners)
            print(scores2)
            print(ranked_cands)
        
        if scores[ranked_cands[2]]==scores[ranked_cands[1]]:
            print('##### multiple contenders #####')
            return []
        
        winner = winners[0]
        
        ## find candidates that could beat winner in H2H
        margins = np.zeros((num_cands, num_cands))
        
        for c1 in range(num_cands):
            for c2 in range(c1+1, num_cands):
                c1_let = cand_names[c1]
                c2_let = cand_names[c2]
                ## number of votes c1 gets over c2 in H2H
                margin = 0
                
                for k in range(len(profile)):
                    ballot = profile.at[k, 'ballot']
                    count = profile.at[k, 'Count']
                    ## ballot ranks both c1 and c2
                    if c1_let in ballot and c2_let in ballot:
                        if ballot.find(c1_let) < ballot.find(c2_let):
                            margin += count
                        else:
                            margin -= count
                    ## ballot only ranks c1       
                    elif c1_let in ballot:
                        margin += count
                    ## ballot only ranks c2
                    elif c2_let in ballot:
                        margin -= count
                
                margins[c1, c2] = margin
                margins[c2, c1] = -1*margin
        
        upstarts = [cand_names[c1] for c1 in range(num_cands) if margins[c1, cands.index(winner)]>0]
        if diagnostic:
            print(margins)
            print(cands)
            print(upstarts)
        
        for upstart in upstarts:
            remove_ballots = []
            if diagnostic:
                print(upstart)
            ## check if upstart can make it to second round and defeat winner
            need_to_lose = ranked_cands[:ranked_cands.index(upstart)]
            ballots_to_change = {}
            for cand in need_to_lose:
                ballots_to_change[cand] = scores[cand]-scores[upstart]
            if diagnostic:
                print(ballots_to_change)
            
            
            new_profile = profile.copy(deep = True)
            for k in range(len(profile)):
                ballot = new_profile.at[k, 'ballot']
                cur_lead = ballot[0]
                if cur_lead in need_to_lose:
                    if (upstart in ballot and winner not in ballot) or (upstart in ballot and winner in ballot and ballot.find(upstart)<ballot.find(winner)):
                        count = int(new_profile.at[k, 'Count']*vote_frac)
                        
                        
                        if ballots_to_change[cur_lead] < 0:
                            ## already removed enough ballots, no need to remove more
                            pass
                        elif ballots_to_change[cur_lead] >= (int(new_profile.at[k, 'Count']*vote_frac)+1):
                            ## remove all ballots
                            remove_ballots.append([ballot, count])
                            ballots_to_change[cur_lead] -= count
                            new_profile.at[k, 'Count'] = 0
                        else:
                            ## only remove enough ballots
                            new_profile.at[k, 'Count'] -= (ballots_to_change[cur_lead] + 1)
                            remove_ballots.append([ballot, ballots_to_change[cur_lead]+1])
                            ballots_to_change[cur_lead] = -1
                        
                        
            
            new_win = plurality_runoff(new_profile, cands)[0]
            if new_win[0] == upstart:
                return [winner, upstart, remove_ballots]
        
    return []

###############################################################################
###############################################################################

def frac_downMonoPR(profile, num_cands, vote_frac, diagnostic=False): # (for Plurality Runoff)
    """inputs: name of election, dataframe of election, voting method
    runs election to find winners/hopefuls/losers, then identifies and makes vote swaps to find 
    downward monotonicity anomalies connected to change in dropout order.  
    Returns if an anomaly exists, and how anomaly happens"""
    
    # profileX, cands = prefProfileInput1(filename)
    
    if vote_frac != 1:
        print('##########################')
        print('WARNING:')
        print('downMonoPR only works for vote_frac of 1 right now')
        print('##########################')
    
    n = num_cands 
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    profile1 = profile.copy(deep=True)
    
    winners = plurality_runoff(profile1, cands, diagnostic=False) [0]
    
    W = winners[0]
    
    r1scores = {cand: 0.0 for cand in cands}
    
    for k in range(len(profile)):
        ballot = profile.at[k, 'ballot']
        if (len(ballot)>0) and (ballot[0] in cands):
            r1scores[ballot[0]] += profile.at[k, 'Count']
    
    ## keep two candidates with highest scores
    cands.sort(key=lambda cand: r1scores[cand], reverse = True)
    top_three_cands = cands[:3]
    #print("top three cands are " + str(top_three_cands))
    if (n == 2) or (n == 1) or (W not in top_three_cands):
        if diagnostic:
            print(n)
            print(W)
            print(top_three_cands)
            print("Not enough candidates or Winner not in top three, something went wrong in election ")
    else:
        C = cands[2]
        for x in top_three_cands:
            if (x != W) and (x != C):
                B = x
        if (r1scores[W]-r1scores[C])>=(r1scores[B]-r1scores[W]):
            if diagnostic:
                print(" No downward anomaly because W-C >= B-W." )
        else:
            gap = r1scores[W]-r1scores[C]
            profile2 = profile.copy(deep=True)
            newFrameThird = downwardIndivCheck(profile2, gap, B, C)
            newWins = plurality_runoff(newFrameThird, cands, diagnostic=False)[0]
            if B in newWins:
                if diagnostic:
                    print("")
                    print(" DOWNWARD MONOTONICITY ANOMALY for " + B +". "  + 
                          "Change " + str(gap +1) + B+ C + "__ and maybe bullet votes to " + 
                          C + B + "__ and " + B + " becomes a winner." )
                    print("Original winner was " + str(W))
                    print("New winner is " + str(B))
                    print("")
                    print("")
                
                return [W, B, []]

            else:
                if diagnostic:
                    print("No anomaly for " + B+" after modifying "+ str(gap +1) + " votes from "+ 
                          B+ C + "__ to " + C + B+"__. ")
                if len(cands)>3:
                    if diagnostic:
                        print("trying 4th")
                    D = cands[3]
                    if (r1scores[W]-r1scores[D])>=(r1scores[B]-r1scores[W]):
                        if diagnostic:
                            print(" No downward anomaly because W-D > B-W." )
                    else:
                        gap = r1scores[W]-r1scores[D]
                        newFrameFourth = downwardIndivCheck(profile, gap, B, D)
                        newWins = plurality_runoff(newFrameFourth, cands, diagnostic=False)[0] 
                        if B in newWins:
                            if diagnostic:
                                print("")
                                print(" DOWNWARD MONOTONICITY ANOMALY for " + B +". "  + 
                                      "Change " + str(gap +1) + B+ D + "__ and maybe bullet votes to " + 
                                      D + B + "__ and " + B + " becomes a winner." )
                                print("Original winner was " + str(W))
                                print("New winner is " + str(B))
                                print("")
                                print("")
                            return [W, B, []]
                        else:
                            if len(cands)>4:
                                if diagnostic:
                                    print("trying 5th")
                                E = cands[4]
                                if (r1scores[W]-r1scores[E])<=(r1scores[B]-r1scores[W]):
                                    if diagnostic:
                                        print(" No downward anomaly because W-E > B-W." )
                                else:
                                    gap = r1scores[W]-r1scores[E]
                                    profile4 = profile.copy(deep=True)
                                    newFrameFifth = downwardIndivCheck(profile4, gap, B, E)
                                    newWins = plurality_runoff(newFrameFifth, cands, diagnostic=False)[0]
                                    if B in newWins:
                                        if diagnostic:
                                            print("")
                                            print(" DOWNWARD MONOTONICITY ANOMALY for " + B +". "  + 
                                                  "Change " + str(gap +1) + B+ E + "__ and maybe bullet votes to " + 
                                                  E + B + "__ and " + B + " becomes a winner." )
                                            print("Original winner was " + str(W))
                                            print("New winner is " + str(B))
                                            print("")
                                            print("")
                                        return [W, B, []]
                                    else:
                                        if len(cands)>5:
                                            F = cands[5]
                                            if (r1scores[W]-r1scores[F])<(r1scores[B]-r1scores[W]):
                                                if diagnostic:
                                                    print(" No downward anomaly because W-F > B-W." )
                                            else:
                                                if diagnostic:
                                                    print("")
                                                    print("")
                                                    print("")
                                                    print(" OMG I never thought that this would happen.  ")
                                                    print("We are on the 6th candidate!!!!!")
                                                    print("")
                                                    print("")
                                                gap = r1scores[W]-r1scores[F]
                                                newFrameSixth = downwardIndivCheck(profile, gap, B, F)
                                                newWins = plurality_runoff(newFrameSixth, cands, diagnostic=False)[0]
                                                if B in newWins:
                                                    if diagnostic:
                                                        print("")
                                                        print(" DOWNWARD MONOTONICITY ANOMALY for " + B +". "  + 
                                                              "Change " + str(gap +1) + B+ F + "__ and maybe bullet votes to " + 
                                                              F + B + "__ and " + B + " becomes a winner." )
                                                        print("Original winner was " + str(W))
                                                        print("New winner is " + str(B))
                                                        print("")
                                                        print("")
                                                    return [W, B, []]
                        
    return []
    

#### helper function for downMonoPR
def downwardIndivCheck(frame1, gap, winnerB, loser): 
    """Inputs preference profile, vote gap, 2nd-place winnerB, 
    and loser.  Program makes ballot modifications to move winnerB below loser, returns modified profile"""

    tempFrame1 = frame1.copy(deep=True)
    modifiableVotes1 = 0 #modifiableVotes= sum of all ballots that start with C_k L
    for z in range(len(tempFrame1)):
        currentBallot = tempFrame1.at[z,'ballot']
        try:
            currentBallot[1]
        except: 
            continue
        else:
            if currentBallot[0]==winnerB and currentBallot[1]==loser:
                modifiableVotes1 += tempFrame1.at[z,'Count']
    #print("Modifiable votes are " + str(modifiableVotes1) + " and gap is " + str(gap))
    if modifiableVotes1 > gap:
        check = copy.deepcopy(gap)
        for z in range(len(tempFrame1)):
            if check>=0:
                currentBallot = tempFrame1.at[z,'ballot']
                try:
                    currentBallot[1]
                except: 
                    continue
                else:
                    if currentBallot[0]==winnerB and currentBallot[1]==loser:
                        if check - tempFrame1.at[z,'Count']>=0: #modify all such ballots
                            tempFrame1.at[z,'ballot'] = swapOneTwo(tempFrame1.at[z,'ballot'])
                            check = check - tempFrame1.at[z,'Count']
                        else: #modify only check+1 such ballots
                            tempFrame1.at[z,'Count'] = tempFrame1.at[z,'Count']-(check+1)
                            #now add new line to frame with modified ballot
                            tempFrame1.loc[len(tempFrame1)] = [swapOneTwo(tempFrame1.at[z,'ballot']), check+1]
                            check = -1
                    else:
                        pass
        return tempFrame1
    else: # modify all modifiableVotes C_k L votes in reduced_df to become L C_k 
        for z in range(len(tempFrame1)):
            currentBallot = tempFrame1.at[z,'ballot']
            try:
                currentBallot[1]
            except: 
                continue
            else:
                if currentBallot[0]== winnerB and currentBallot[1]== loser:
                    tempFrame1.at[z,'ballot'] = swapOneTwo(tempFrame1.at[z,'ballot'])
                    gap = gap - tempFrame1.at[z,'Count']

        #CHECK THE BULLET VOTES
        modifiableVotesBullet1 = 0 # = sum of all bullet votes w/ length 1
        for z in range(len(tempFrame1)):
            currentBallot = tempFrame1.at[z,'ballot']
            if len(currentBallot) == 1:
                if currentBallot[0]==winnerB:
                    modifiableVotesBullet1 += tempFrame1.at[z,'Count']  

        if modifiableVotesBullet1 > gap: 
            check = copy.deepcopy(gap)
            for z in range(len(tempFrame1)):
                if check>=0:
                    currentBallot = tempFrame1.at[z,'ballot']
                    if len(currentBallot) == 1:
                        if currentBallot[0]==winnerB:
                            if check - tempFrame1.at[z,'Count']>=0: #modify all such ballots
                                tempFrame1.at[z,'ballot'] = swapOneLoser(tempFrame1.at[z,'ballot'], loser)
                                check = check - tempFrame1.at[z,'Count']

                            else: #modify only check+1 such ballots
                                #take check+1 ballots from current ballot
                                tempFrame1.at[z,'Count'] = tempFrame1.at[z,'Count']-(check+1)  
                                #make new ballot with winner moved up, add line to election frame with check+1 as count
                                tempFrame1.loc[len(tempFrame1)] = [swapOneLoser(tempFrame1.at[z,'ballot'], loser), check+1]
                                check = -1
                        else:
                            pass
            return tempFrame1
        else: 
            print("No downward anomaly because not enough votes to modify.")
            return tempFrame1


###############################################################################
###############################################################################

##### new downward monotonicity IRV code
##### modifies killer subset idea into demikiller subsets

def frac_downMonoIRV(profile, num_cands, vote_frac, diagnostic=False):
# def killerSubsetSearchDownward_all(election, diagnostic = False):
    # profile, cands = prefProfileInput1(election)
    #maybe do a vote count here, and remove from profile anyone with 0 first-place votes? NEED for civs

    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    winners, foo1, foo2 = IRV(profile, cands)
    W = winners[0][0]
    
    if diagnostic:
        print("Winner is " + W)
    demi_killer_subs = findDemiKillerSubsets(profile, num_cands, diagnostic=False) 
    #this is a list of lists.  killer_subs[0][0]=first ks, [1][0]=2nd ks, etc
    #print(demi_killer_subs)
    if len(demi_killer_subs)!=0:
        
        for dks2 in demi_killer_subs:
            dks = dks2[0]
            #ks_dict = ks2[1]
            #maxNSremovable = calcMaxRemove(ks_dict, W)
#             print(" ")
#             print(" ")
#             print(dks)
            if W not in dks:
                print("Error: DemiKiller subset without winner, something is wrong.")
            else:
                dksnw = copy.deepcopy(dks)
                dksnw.remove(W) #because W wins IRV, they will never be in last place
#                 print("DKSNW is " + str(dksnw))
                modifiedVotesList = []
                modifiedVotesDict = {}
                #Make new profile with only ks, run IRV to find winner
                #ks_winners = findKSwinner(profile, cands, ks)
                
                for DK in dksnw:
                    profile1 = profile.copy(deep=True)
                    go = True
                    while go == True:
                        profile1, modifiedVotesList, modifiedVotesDict, go, anomFound = runAroundDown_all(profile1, dksnw, W, DK, modifiedVotesList, modifiedVotesDict, go)
                        if anomFound:
                            return [W, DK, modifiedVotesList]
                        #print("1. Now go is " + str(go))
                        
    else:
        if diagnostic:
            print("No demikiller subsets in " + str(election))

    return []
   
    

def runAroundDown_all(profile, dksnw, W, DK, modifiedVotesList, modifiedVotesDict, go, diagnostic=False):
    """ takes in profile, list of killers without winner, winner, killer, and modified votes.
    Runs a round of Killer Subset code, returns updated profile, mod votes, whether or not to go on"""
    #vote_counts={cand:0 for cand in hopefuls}
    if go == False:
        return profile, modifiedVotesList, modifiedVotesDict, False, False
    quota=math.floor(sum(profile['Count'])/(2))+1
    vote_counts = {} #may need to fix for CIVS elections...input candidate list and do like above.
    for j in range(len(profile)):
        if profile.at[j,'ballot']!='':
            if profile.at[j,'ballot'][0] in vote_counts.keys():
                vote_counts[profile.at[j,'ballot'][0]]+=profile.iloc[j]['Count']
            else:
                vote_counts[profile.at[j,'ballot'][0]]=profile.iloc[j]['Count']
    cands1 = vote_counts.keys()
    cands1Set = set(cands1)
    cands1SetNoW = cands1Set -{W}
    
    max_count=max(vote_counts.values())
    min_count=min(vote_counts.values())
    
    if W in cands1: #this should always happen
        if (vote_counts[W] == max_count) and (max_count > quota): #if W wins, no anomaly
            #print("No anomaly because Winner has majority.")
            return profile, modifiedVotesList, modifiedVotesDict, False, False #go on to next demikiller subset
        if (vote_counts[W] == min_count): #W has lowest, run election to check for new winner
            win1, foo1, foo2 = IRV(profile, cands1)
            if win1[0]== W:
                #print("No anomaly: This should be impossible.")
                return profile, modifiedVotesList, modifiedVotesDict, False, False
            elif win1[0]== DK:
                # data1.write("\n")
                # data1.write("\n")
                # data1.write(str(filename) + "\n" + " : Downward anomaly!!! Modified votes are " +
                #     str(modifiedVotesList)+ str(modifiedVotesDict) + " and now " + DK + " is the winner.")
                if diagnostic:
                    print("Downward anomaly!!! Modified votes are " + str(modifiedVotesList)+
                          str(modifiedVotesDict) + " and now " + DK + " is the winner.")
                return profile, modifiedVotesList, modifiedVotesDict, False, True
            else:
                #print("No anomaly, but different winner: wanted " + DK + "to win but " + win1[0]+ " won.")
                return profile, modifiedVotesList, modifiedVotesDict, False, False
        else: #winner not in last place
            for key, value in vote_counts.items(): #find last-place cand
                if value == min_count:
                    eliminated_cand = key
            if eliminated_cand not in dksnw: #run round, return
                frame2 = profile.copy(deep = True)
                for k in range(len(frame2)):
                    if eliminated_cand in frame2.iloc[k]['ballot']:
                        frame2.at[k,'ballot']=frame2.at[k,'ballot'].replace(eliminated_cand,'')
                for k in range(len(frame2)):
                    if frame2.at[k,'ballot']=='':
                        frame2.drop(k)
                #print("Eliminated candidate " + eliminated_cand)
                return frame2, modifiedVotesList, modifiedVotesDict, True, False
            else: #modify ballots, return
                frame2 = profile.copy(deep = True)
                return downMods_all(frame2, DK, W, dksnw, modifiedVotesList, modifiedVotesDict, go)
                 
        
    else:
        if diagnostic:
            print("Winner not in round. This should maybe not ever happen")
        win1, foo1, foo2 = IRV(profile, cands1)
        if win1[0]== W:
            #print("No anomaly: This should be REALLY impossible.")
            return profile, modifiedVotesList, modifiedVotesDict, False, False
        elif win1[0]== DK:
            # data1.write("\n")
            # data1.write("\n")
            # data1.write(str(filename) + "\n" + " : Downward anomaly!!! Modified votes are " +
            #     str(modifiedVotesList)+ str(modifiedVotesDict) + " and now " + DK + " is the winner.")
            if diagnostic:
                print("Downward anomaly!!! Modified votes are " + str(modifiedVotesList)+
                      str(modifiedVotesDict) + " and now " + DK + " is the winner.")
            return profile, modifiedVotesList, modifiedVotesDict, False, True
        else:
            #print("No anomaly, but different winner: wanted " + DK + "to win but " + win1[0]+ " won.")
            return profile, modifiedVotesList, modifiedVotesDict, False, False
        
    return profile, modifiedVotesList, modifiedVotesDict, False, False
    

def downMods_all(frame, DK, W, dksnw, modifiedVotesList, modifiedVotesDict, go): #don't need maxRemovable
    """given profile, killer K, winner W, ksnw, and list, modifies just enough 
    Kk2 or K ballots to make L drop out next, returns modified frame, removedVotesList, go"""
    dks1 = copy.deepcopy(dksnw)
    dks1.append(W)  #full killer subset, as a list
    dksSet = set(dks1) #full killer subset, as a set
    #print("Killer subset in Run modifications is " + str(ksSet))
    vote_counts = {} #may need to fix for CIVS elections...input candidate list and do like above.
    for j in range(len(frame)):
        if frame.at[j,'ballot']!='':
            if frame.at[j,'ballot'][0] in vote_counts.keys():
                vote_counts[frame.at[j,'ballot'][0]]+=frame.iloc[j]['Count']
            else:
                vote_counts[frame.at[j,'ballot'][0]]=frame.iloc[j]['Count']
    sorted_items = sorted(vote_counts.items(), key=lambda item: item[1]) #sorted lowest votes to highest
    sorted_cands = [item[0] for item in sorted_items] #K should be first
    nCands = len(vote_counts)
    
    DK2 = sorted_cands[0] #killer with lowest points, cannot be DK
    L = sorted_cands[1] #L could be in the killer subset
    
    #######new code to add in
    if (L in dksnw) and (DK2 in dksnw): #and (L != W)
        print("Bottom two candidates are both non-winner demiKillers, don't do anomaly check")
        return frame, modifiedVotesList, modifiedVotesDict, False, False
    #######
    
    if L == DK2:
        #print("No Downward anomaly, DemiKiller K is second-to-last place")
        return frame, modifiedVotesList, modifiedVotesDict, False, False
    if DK2 == DK:
        #print("Something weird, DemiKiller K is in last place")
        return frame, modifiedVotesList, modifiedVotesDict, False, False
    tempframe = frame.copy(deep=True)
    go = True
    gap = vote_counts[L]-vote_counts[DK2]
    downwardableVotes = 0
    for k in range(len(tempframe)):
        ballot = tempframe.at[k,'ballot']
        if (tempframe.at[k,'Count'] != 0) and (len(ballot)!=0) and (ballot[0]==DK) and (len(ballot)==1 or ballot[1]==DK2):
            downwardableVotes += tempframe.at[k,'Count']
    if downwardableVotes <= gap:
        #print("Not enough Downwardable votes to make the next dropout be " + L)
        return tempframe, modifiedVotesList, modifiedVotesDict, False, False
    else:
        check = copy.deepcopy(gap) #change all DK L ballots to L DK
        for z in range(len(tempframe)):
            if check >= 0:
                ballot = tempframe.at[z,'ballot']
                if (tempframe.at[z,'Count'] != 0) and (len(ballot) > 1) and (ballot[0]==DK) and (ballot[1]==DK2):
                    if check - tempframe.at[z,'Count']>=-1: #modify all such ballots
                        modifiedVotesList.append(str(tempframe.at[z,'Count'])+ " " + ballot)
                        if ballot in modifiedVotesDict.keys():
                            modifiedVotesDict[ballot]+=tempframe.iloc[z]['Count']
                        else:
                            modifiedVotesDict[ballot]=tempframe.iloc[z]['Count']
                        tempframe.at[z,'ballot'] = swapOneTwo(tempframe.at[z,'ballot'])
                        check = check - tempframe.at[z,'Count']
                    else: #modify only check+1 such ballots
                        modifiedVotesList.append(str(check+1)+ " " + ballot)
                        if ballot in modifiedVotesDict.keys():
                            modifiedVotesDict[ballot]+=(check+1)
                        else:
                            modifiedVotesDict[ballot]=(check+1)
                        tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                        #now add new line to frame with modified ballot
                        tempframe.loc[len(tempframe)] = [swapOneTwo(tempframe.at[z,'ballot']), check+1]
                        check = -1
                        
        if check >= 0: #if need to change bullet votes, do here
            check2 = copy.deepcopy(check)
            for z in range(len(tempframe)):
                if check2 >= 0:
                    ballot = tempframe.at[z,'ballot']
                    if (tempframe.at[z,'Count'] != 0) and (len(ballot) == 1) and (ballot[0]==DK):
                        if check2 - tempframe.at[z,'Count']>=-1: #modify all such ballots
                            modifiedVotesList.append(str(tempframe.at[z,'Count'])+ " " + ballot)
                            if ballot in modifiedVotesDict.keys():
                                modifiedVotesDict[ballot]+=tempframe.iloc[z]['Count']
                            else:
                                modifiedVotesDict[ballot]=tempframe.iloc[z]['Count']
                            tempframe.at[z,'ballot'] = swapOneLoser(tempframe.at[z,'ballot'], DK2)
                            check2 = check2 - tempframe.at[z,'Count']
                        else: #modify only check+1 such ballots
                            modifiedVotesList.append(str(check2+1)+ " " + ballot)
                            if ballot in modifiedVotesDict.keys():
                                modifiedVotesDict[ballot]+=(check2+1)
                            else:
                                modifiedVotesDict[ballot]=(check2+1)
                            tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check2+1)
                            #now add new line to frame with modified ballot
                            tempframe.loc[len(tempframe)] = [swapOneLoser(tempframe.at[z,'ballot'], DK2), check2+1]
                            check2 = -1

        while go == True:
            tempframe, modifiedVotesList, modifiedVotesDict, go, anomFound = runAroundDown_all(tempframe, dksnw, W, DK, modifiedVotesList, modifiedVotesDict, go)
            if anomFound:
                return tempframe, modifiedVotesList, modifiedVotesDict, go, True

    return tempframe, modifiedVotesList, modifiedVotesDict, False, False





def findDemiKillerSubsets(profile, num_cands, diagnostic=False): 
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    demi_killer_subsets = []
    winners, foo1, foo2 =IRV(profile, cands) #get election data from IRV
    if len(winners)>1:
        print('##### Multiple initial winners #####')
        return []
    winner = winners[0]
    if diagnostic:
        print(winners)
        
    ##### search for killer subsets
    losers = cands.copy()
    losers.remove(winner)
    
    ## only eliminate in round of three or two
    cand_subsets = list(combinations(losers, 2))
    cand_subsets3 = list(combinations(losers, 3))
    #for loser in losers:   #don't need these because they become two cand subset
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
        
        scores = {cand: 0 for cand in subset}
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
            for c in ballot: 
                if c in subset:
                    scores[c]+=profile.at[k, 'Count']
                    break
        
        S = get_secondLow(scores)
        # if scores[winner] == min(scores.values()) and min(scores.values())!=max(scores.values()):
        if S == winner:
            # print(lxn + ' : ', winner, subset)
            # print(subset)
            # killer_subset_count += 1
            # break
            demi_killer_subsets.append([subset, scores])
    return demi_killer_subsets






###############################################################################
###############################################################################

##### new upward monotonicity IRV code
##### uses killer subset idea

def frac_upMonoIRV(profile, num_cands, vote_frac, diagnostic=False): 
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    killer_subsets = []
    winners, foo1, foo2 =IRV(profile, cands) #get election data from IRV
    if len(winners)>1:
        print('##### Multiple initial winners #####')
        return []
    winner = winners[0]
    if diagnostic:
        print(winners)
        
    ##### search for killer subsets
    losers = cands.copy()
    losers.remove(winner)
    
    ## only eliminate in round of three or two
    cand_subsets = list(combinations(losers, 2))
    for loser in losers:
        cand_subsets.append((loser))
    
    ## try all possible rounds
    # cand_subsets = []
    # for i in range(2, num_cands-1):
    #     cand_subsets+=list(combinations(losers,i))
    
    ## test if each subset could eliminate winner
    for cand_tuple in cand_subsets:
        subset = list(cand_tuple)
        subset.append(winner)
        
        scores = {cand: 0 for cand in subset}
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
            for c in ballot: 
                if c in subset:
                    scores[c]+=profile.at[k, 'Count']
                    break
            
        # if scores[winner] == min(scores.values()) and min(scores.values())!=max(scores.values()):
        if scores[winner] == min(scores.values()) and list(scores.values()).count(scores[winner])==1:
            # print(lxn + ' : ', winner, subset)
            # print(subset)
            # killer_subset_count += 1
            # break
            killer_subsets.append([subset, scores])


    ##### try to manipulate votes so everyone not in killer subset is removed first
    for ks in killer_subsets:
        subset, scores = ks
        if diagnostic:
            print(f'##### {subset}')
        killers = subset.copy()
        killers.remove(winner)
        win_gap = min([scores[cand]-scores[winner] for cand in killers])-1
        
        new_profile = profile.copy(deep = True)
        for k in range(len(new_profile)):
            ballot = new_profile.at[k, 'ballot']
            ## if winner is not ranked, don't move up
            if winner not in ballot:
                pass
                # killer = ''
                # for cand in reversed(ballot):
                #     if cand in killers:
                #         killer = cand
                #         break
                # if killer:
                #     prekiller, postkiller = ballot.split(killer)
                #     mod_ballot = prekiller + killer + winner+ postkiller
                #     # print(winner, killers, ballot, mod_ballot)
                #     new_profile.at[k, 'ballot'] = mod_ballot
                # else:
                #     mod_ballot = winner + ballot
                #     # print(winner, killers, ballot, mod_ballot)
                #     new_profile.at[k, 'ballot'] = mod_ballot
            
            ## if winner is ranked, move them up until they are right behind someone in the killer subset
            else:
                cands_ahead, cands_behind = ballot.split(winner)
                killer = ''
                winner_indx = 0
                for cand in reversed(cands_ahead):
                    if cand in killers:
                        winner_indx = ballot.index(cand)+1
                        killer = cand
                        break
                if killer:
                    prekiller, postkiller = cands_ahead.split(killer)
                    mod_ballot = prekiller + killer + winner+ postkiller + cands_behind
                    # print(winner, killers, ballot, mod_ballot)
                    new_profile.at[k, 'ballot'] = mod_ballot
                else:
                    mod_ballot = winner + cands_ahead + cands_behind
                    # print(winner, killers, ballot, mod_ballot)
                    new_profile.at[k, 'ballot'] = mod_ballot
    
        ## run new election, see if winner loses
        new_winners, foo1, foo2 = IRV(new_profile, cands)
        if len(new_winners)>1:
            print('##### Multiple new winners #####')
            # return []
        new_win = new_winners[0]
        
        if new_win != winner:
            return [winner, new_win, []]
            # anomaly_list.append(lxn)
            # print('Anomaly in ' + lxn)
            break
        
        
        # breakhere
        
        ##### try changing bullet votes
        quota=math.floor(sum(new_profile['Count'])/(2))+1
        hopefuls = cands.copy()
        
        vote_counts = {cand: 0 for cand in hopefuls}
        for k in range(len(new_profile)):
            vote_counts[new_profile.at[k, 'ballot'][0]] += new_profile.at[k, 'Count'] 
        
        if max(vote_counts.values())>quota:
            new_win = [cand for cand in hopefuls if vote_counts[cand] == max(vote_counts.values())][0]
            win_found = True
            if new_win != winner:
                return [winner, new_win, []]
                # anomaly_list.append(lxn)
                # print('Anomaly in ' + lxn)
        else:
            win_found = False
            
        while not win_found:
            if diagnostic:
                print(hopefuls)
                print(vote_counts, win_gap)
            
            if max(vote_counts.values())>quota:
                new_win = [cand for cand in hopefuls if vote_counts[cand] == max(vote_counts.values())][0]
                win_found = True
                if new_win != winner:
                    return [winner, new_win, []]
                    # anomaly_list.append(lxn)
                    # print('Anomaly in ' + lxn)
                break
            
            min_count=min(i for i in vote_counts.values() if i>=0)
            # min_count=min(i for i in vote_counts.values() if i>0)
            count=0
            for votes in vote_counts:
                if votes==min_count:
                    count+=1
            if count>1:
                print("Tie in candidate to remove")
                new_winners = ''
                win_found = True
                break

            elim_cand = list(vote_counts.keys())[list(vote_counts.values()).index(min_count)] #took str() away
            
            ## safe to remove candidate
            if elim_cand not in subset:
                # red_frame = new_profile.copy(deep = True)
                for k in range(len(new_profile)):
                    ballot = new_profile.at[k, 'ballot']
                    if elim_cand in ballot:
                        new_profile.at[k, 'ballot'] = new_profile.at[k, 'ballot'].replace(elim_cand, '')
                        
                for k in range(len(new_profile)):
                    if new_profile.at[k, 'ballot'] == '':
                        new_profile.drop(k)
                
                hopefuls.remove(elim_cand)
                if diagnostic:
                    print('Eliminated ' + elim_cand)
                
                
                        
            ## its over, old winner is eliminated
            elif elim_cand == winner:
                win_found = True
                new_winners, foo1, foo2 = IRV(new_profile, cands)
                new_win = new_winners[0]
                return [winner, new_win, []]
                # anomaly_list.append(lxn)
                # print('Anomaly in ' + lxn)
                break
                
            ## need to try changing outcome by changing bullet votes
            elif elim_cand in killers:
                need_lose_score = min([vote_counts[cand] for cand in hopefuls if cand not in subset])
                for need_lose in hopefuls:
                    if vote_counts[need_lose] == need_lose_score:
                        break
                
                if vote_counts[need_lose] - vote_counts[elim_cand] + 1 > win_gap:
                    ## cant change enough votes without ruining killer subset
                    win_found = True
                    break
                else:
                    need_to_change = vote_counts[need_lose] - vote_counts[elim_cand] + 1
                    for k in range(len(new_profile)):
                        if new_profile.at[k, 'ballot'] == need_lose:
                            if new_profile.at[k, 'Count'] <= need_to_change:
                                new_profile.at[k, 'ballot'] = winner + need_lose
                                need_to_change -= new_profile.at[k, 'Count']
                                win_gap -= new_profile.at[k, 'Count']
                            else:
                                new_profile.at[k, 'Count'] -= need_to_change
                                new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [winner+need_lose], 'Count': [need_to_change]})], ignore_index=True)
                                win_gap -= need_to_change
                                need_to_change = 0
                    
                    if need_to_change > 0:
                        ## not enough ballots to change
                        
                        ###Adam changes start here
                        if ((2*need_to_change) < win_gap): #modify enough NL...EC...W ballots
                            for k in range(len(new_profile)):
                                bal = new_profile.at[k, 'ballot']
                                if (new_profile.at[k, 'ballot'][0] == need_lose) and (((winner in bal) and (elim_cand in bal) and (bal.index(winner)>bal.index(elim_cand))) or ((winner not in bal) and (elim_cand in bal))): #new_profile.at[k, 'ballot'] == (need_lose + elim_cand + winner): #
                                    if new_profile.at[k, 'Count'] <= need_to_change:
                                        new_profile.at[k, 'ballot'] = modifyUp(winner, new_profile.at[k, 'ballot'])
                                        need_to_change -= new_profile.at[k, 'Count']
                                        win_gap -= (2 * new_profile.at[k, 'Count'])
                                        ### new change below
                                        new_profile.at[k, 'Count'] = 0
                                    else:
                                        new_profile.at[k, 'Count'] -= need_to_change
                                        new_profile = pd.concat([new_profile, pd.DataFrame({'ballot': [modifyUp(new_profile.at[k, 'ballot'], winner)], 'Count': [need_to_change]})], ignore_index=True)
                                        win_gap -= (2 * need_to_change)
                                        need_to_change = 0
                            new_winners2, foo1, foo2 = IRV(new_profile, cands)
                            if len(new_winners2)>1:
                                print('##### Multiple new winners #####')
                                # return []
                            new_win2 = new_winners2[0]

                            if new_win2 != winner:
                                if new_win2 != elim_cand:
                                    print("something weird happened")
                                if diagnostic:
                                    print("Upward Mono anomaly")
                                win_found = True
                                return [winner, new_win2, []]
                                # anomaly_list.append(lxn)
                                # print('Anomaly in ' + lxn)
                                #break
                        
                        else:
                            ###Adam changes end here

                            print('###########################################')
                            print('There were not enough ballots to change')
                            # print(lxn)
                            win_found = True
                            break
                    if diagnostic:  
                        print('Lowered score for ' + need_lose)
                                
            ##this should not happen
            else:
                print('ERROR!!!!!!!!!!!!!!!!!!')
        
            
            vote_counts={cand:0 for cand in hopefuls}
            for k in range(len(new_profile)):
                if new_profile.at[k,'ballot']!='':
                    if new_profile.at[k,'ballot'][0] in vote_counts.keys():
                        vote_counts[new_profile.at[k,'ballot'][0]]+=new_profile.iloc[k]['Count']
                    else:
                        vote_counts[new_profile.at[k,'ballot'][0]]=new_profile.iloc[k]['Count']
        
        


###############################################################################
###############################################################################

##### new no show IRV code that uses killer subset idea
##### currently does not work on some CIVS elections!!

def frac_noShowIRV(frame, num_cands, vote_frac, diagnostic=False): 
# def killerSubsetSearchNoShow_all(election, diagnostic = False): #multiple elections version

    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    profile = frame
    #maybe do a vote count here, and remove from profile anyone with 0 first-place votes? NEED for civs

    winners, foo1, foo2 = IRV(profile, cands)
    W = winners[0][0]
    # print("Winner is "+ str(W))
    numCands = len(cands)
    killer_subs = findKillerSubsets(profile, numCands, diagnostic=False) 
    #this is a list of lists.  killer_subs[0][0]=first ks, [1][0]=2nd ks, etc
    # print(killer_subs)
    if len(killer_subs)!=0:
        for ks2 in killer_subs:
            ks = ks2[0]
            ks_dict = ks2[1]
            maxNSremovable = calcMaxRemove(ks_dict, W)
            #print(ks)
            if W not in ks:
                print("Error: Killer subset without winner, something is wrong.")
            else:
                ksnw = copy.deepcopy(ks)
                ksnw2 = copy.deepcopy(ks)
                ksnw.remove(W) #because W wins IRV, they will never be in last place
                ksnw2.remove(W)
                #print("KSNW is " + str(ksnw))
                modifiedVotesList = []
                modifiedVotesDict = {}
                modifiedVotesList2 = []
                modifiedVotesDict2 = {}
                #Make new profile with only ks, run IRV to find winner
                ks_winners = findKSwinner(profile, cands, ks)
                K = ks_winners[0] #K wins the IRV election in the killer subset
                K2 = copy.deepcopy(K)
                # print(ks, W, K)
                profile1 = profile.copy(deep=True)
                profile2 = profile.copy(deep=True)
                go = True
                while go == True:
                    # print('running runAround')
                    profile1, modifiedVotesList, modifiedVotesDict, go, anomFound = runAround_all(profile1, ksnw, W, K, modifiedVotesList, modifiedVotesDict, maxNSremovable, go)
                    # print(profile1, modifiedVotesList, modifiedVotesDict, go, anomFound)
                    # print(f'anomFound = {anomFound}')
                    if anomFound:
                        # print('returning!')
                        return [W, K, modifiedVotesList]
                goFor = True
                while goFor == True:
                    # print('running runAroundFor')
                    profile2, modifiedVotesList2, modifiedVotesDict2, goFor, anomFound = runAroundFor_all(profile2, ksnw2, W, K2, modifiedVotesList2, modifiedVotesDict2, maxNSremovable, goFor)
                    # print(anomFound)
                    if anomFound:
                        # print('returning!!')
                        return [W, K, modifiedVotesList2]
    else:
        # if diagnostic:
        #     print("No killer subsets in " + str(election))
        return []

###############################################################################
###############################################################################
##### no show IRV helper functions

def findKSwinner(profile, cands, ks): #profile, cands are OG profile/cands
    """input original election and candidates, outputs the winner if reduced to killer subset ks"""
    ks_profile = profile.copy(deep = True)
    for k in range(len(ks_profile)):
        ballot = ks_profile.at[k, 'ballot']
        for c in ballot: 
            if c not in ks:
                ballot = ballot.replace(c, "")
        ks_profile.at[k, 'ballot'] = ballot
    win_ks, foo1, foo2 = IRV(ks_profile, cands, diagnostic=False)
    return win_ks



def checkForKS(string, set):
    """check to see if any element of the string is in the set, if so, returns true"""
    boo = False
    for j in range(0,len(string)):
        if string[j] in set:
            boo = True
    return boo
 

def calcMaxRemove(ksScoreDict, winner):
    """inputs killer subset scores dictionary (winner in last place)
    returns the maximum number of votes that can be removed for no-show anomaly"""
    maxRemove = 0
    lowScore = ksScoreDict[winner]
    for cand, value in ksScoreDict.items():  
        maxRemove += (ksScoreDict[cand]-lowScore)
    return maxRemove

def noShowable(ballot, killer, winner):
    """check to see if ballot is valid for no show, if so, returns true"""
    boo = False
    if ((killer in ballot) and (ballot.index(killer) > 0) and (winner not in ballot)) or ((killer in ballot) and (winner in ballot) and (ballot.index(killer) < ballot.index(winner))):
        boo = True
    return boo

def findKillerSubsets(profile, num_cands, diagnostic=False): 
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    killer_subsets = []
    winners, foo1, foo2 =IRV(profile, cands, diagnostic=False) #get election data from IRV
    if len(winners)>1:
        print('##### Multiple initial winners #####')
        return []
    winner = winners[0]
    if diagnostic:
        print(winners)
        
    ##### search for killer subsets
    losers = cands.copy()
    losers.remove(winner)
    
    ## only eliminate in round of three or two
    cand_subsets = list(combinations(losers, 2))
    for loser in losers:
        cand_subsets.append((loser))
    
    ## test if each subset could eliminate winner
    for cand_tuple in cand_subsets:
        subset = list(cand_tuple)
        subset.append(winner)
        
        scores = {cand: 0 for cand in subset}
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
            for c in ballot: 
                if c in subset:
                    scores[c]+=profile.at[k, 'Count']
                    break
            
        # if scores[winner] == min(scores.values()) and min(scores.values())!=max(scores.values()):
        if scores[winner] == min(scores.values()) and list(scores.values()).count(scores[winner])==1:
            # print(lxn + ' : ', winner, subset)
            # print(subset)
            # killer_subset_count += 1
            # break
            killer_subsets.append([subset, scores])
    return killer_subsets


def runAround_all(profile, ksnw, W, K, modifiedVotesList, modifiedVotesDict, maxNSremovable, go, diagnostic=False):
    """ takes in profile, list of killers without winner, winner, killer, and modified votes.
    Runs a round of Killer Subset code, returns updated profile, mod votes, whether or not to go on"""
    #vote_counts={cand:0 for cand in hopefuls}
    if go == False:
        # print('return 1')
        return profile, modifiedVotesList, modifiedVotesDict, False, False
    quota=math.floor(sum(profile['Count'])/(2))+1
    vote_counts = {} #may need to fix for CIVS elections...input candidate list and do like above.
    for j in range(len(profile)):
        if profile.at[j,'ballot']!='':
            if profile.at[j,'ballot'][0] in vote_counts.keys():
                vote_counts[profile.at[j,'ballot'][0]]+=profile.iloc[j]['Count']
            else:
                vote_counts[profile.at[j,'ballot'][0]]=profile.iloc[j]['Count']
    cands1 = vote_counts.keys()
    cands1Set = set(cands1)
    cands1SetNoW = cands1Set -{W}
    
    max_count=max(vote_counts.values())
    min_count=min(vote_counts.values())
    
    if W in cands1: #this should always happen
        
        if (vote_counts[W] == max_count) and (max_count > quota):
            #print("No anomaly because Winner has majority")
            # print('return 2')
            return profile, modifiedVotesList, modifiedVotesDict, False, False #go on to next killer subset
        
        if cands1SetNoW == set(ksnw):
            win1, foo1, foo2 = IRV(profile, cands1, diagnostic=False)
            if win1[0]== W:
                #print("No anomaly: reached Killer Subset but OG Winner wins IRV.")
                
                # print('return 3')
                return profile, modifiedVotesList, modifiedVotesDict, False, False
            elif win1[0]== K:
                # data1.write("\n")
                # data1.write("\n")
                # data1.write(str(filename) + "\n" + " : No-show anomaly!!! Removed votes are " + str(modifiedVotesList)+
                #       str(modifiedVotesDict) + " and now " + K + " is the winner.")
                if diagnostic:
                    print("No-show anomaly!!! Removed votes are " + str(modifiedVotesList)+
                          str(modifiedVotesDict) + " and now " + K + " is the winner.")
                # print('Anomaly Found 1')
                # print('Returning True')
                # print(profile, modifiedVotesList, modifiedVotesDict, False, True)
                # print('return 4')
                return profile, modifiedVotesList, modifiedVotesDict, False, True
            
            else:
                #print("No anomaly: reached Killer subset and non-killer candidate won")
                # print('return 5')
                return profile, modifiedVotesList, modifiedVotesDict, False, False
        elif vote_counts[W] == min_count: #this should not really happen
            win1, foo1, foo2 = IRV(profile, cands1, diagnostic=False)
            if win1[0]== W:
                #print("No anomaly: Not at Killer Subset but OG Winner wins IRV. Should never happen")
                return profile, modifiedVotesList, modifiedVotesDict, False, False
            elif win1[0]== K:
                # data1.write("\n")
                # data1.write("\n")
                # data1.write(str(filename) + "\n" + " : No-show anomaly in weird non-KS way!!! Removed votes are " + str(modifiedVotesList)+
                #       str(modifiedVotesDict) + " and now " + K + " is the winner.")
                if diagnostic:
                    print("No-show anomaly in a weird non-KS way!!! Removed votes are " + str(modifiedVotesList)+
                          str(modifiedVotesDict) + " and now " + K + " is the winner.")
                    
                # print('Anomaly Found 2')
                # print('return 6')
                return profile, modifiedVotesList, modifiedVotesDict, False, True
            else:
                #print("No anomaly: W eliminated but non-killer candidate won")
                # print('return 7')
                return profile, modifiedVotesList, modifiedVotesDict, False, False
        else:
            
            for key, value in vote_counts.items(): #find last-place cand
                if value == min_count:
                    eliminated_cand = key
            if eliminated_cand not in ksnw: #run round, return
                frame2 = profile.copy(deep = True)
                for k in range(len(frame2)):
                    if eliminated_cand in frame2.iloc[k]['ballot']:
                        frame2.at[k,'ballot']=frame2.at[k,'ballot'].replace(eliminated_cand,'')
                for k in range(len(frame2)):
                    if frame2.at[k,'ballot']=='':
                        frame2.drop(k)
                #print("Eliminated candidate " + eliminated_cand)
                # print('return 8')
                return frame2, modifiedVotesList, modifiedVotesDict, True, False
            else: #modify ballots, return
                frame2 = profile.copy(deep = True)
                # print('return 9')
                return runNoShowModificationsOrderedEasy_all(frame2, K, W, ksnw, modifiedVotesList, modifiedVotesDict, maxNSremovable, go)
                 
    else:
        print("ERROR: Winner not in round.")
        # print('return 10')
        return profile, modifiedVotesList, modifiedVotesDict, False, False
    
    
    
def runAroundFor_all(profile, ksnw, W, K, modifiedVotesList, modifiedVotesDict, maxNSremovable, goFor, diagnostic=False):
    """ takes in profile, list of killers without winner, winner, killer, and modified votes.
    Runs a round of Killer Subset code, returns updated profile, mod votes, whether or not to go on"""
    #vote_counts={cand:0 for cand in hopefuls}
    if goFor == False:
        return profile, modifiedVotesList, modifiedVotesDict, False, False
    quota=math.floor(sum(profile['Count'])/(2))+1
    vote_counts = {} #may need to fix for CIVS elections...input candidate list and do like above.
    for j in range(len(profile)):
        if profile.at[j,'ballot']!='':
            if profile.at[j,'ballot'][0] in vote_counts.keys():
                vote_counts[profile.at[j,'ballot'][0]]+=profile.iloc[j]['Count']
            else:
                vote_counts[profile.at[j,'ballot'][0]]=profile.iloc[j]['Count']
    #print(vote_counts)
    cands1 = vote_counts.keys()
    cands1Set = set(cands1)
    cands1SetNoW = cands1Set -{W}
    
    max_count=max(vote_counts.values())
    min_count=min(vote_counts.values())
    
    if W in cands1: #this should always happen
        
        if (vote_counts[W] == max_count) and (max_count > quota):
            #print("No anomaly because Winner has majority")
            return profile, modifiedVotesList, modifiedVotesDict, False, False #go on to next killer subset
        
        if cands1SetNoW == set(ksnw):
            win1, foo1, foo2 = IRV(profile, cands1, diagnostic=False)
            if win1[0]== W:
                #print("No anomaly: reached Killer Subset but OG Winner wins IRV.")
                
                return profile, modifiedVotesList, modifiedVotesDict, False, False
            elif win1[0]== K:
                # data1.write("\n")
                # data1.write("\n")
                # data1.write(str(filename) + "\n" + " : No-show anomaly!!! Removed votes are " + str(modifiedVotesList)+
                #       str(modifiedVotesDict) + " and now " + K + " is the winner.")
                if diagnostic:
                    print("No-show anomaly!!! Removed votes are " + str(modifiedVotesList)+
                          str(modifiedVotesDict) + " and now " + K + " is the winner.")
                      
                # print('Anomaly Found 3')
                return profile, modifiedVotesList, modifiedVotesDict, False, True
            else:
                #print("No anomaly: reached Killer subset and non-killer candidate won")
                return profile, modifiedVotesList, modifiedVotesDict, False, False
        elif vote_counts[W] == min_count: #this should not really happen
            win1, foo1, foo2 = IRV(profile, cands1, diagnostic=False)
            if win1[0]== W:
                #print("No anomaly: Not at Killer Subset but OG Winner wins IRV. Should never happen")
                return profile, modifiedVotesList, modifiedVotesDict, False, False
            elif win1[0]== K:
                # data1.write("\n")
                # data1.write("\n")
                # data1.write(str(filename) + "\n" + " : No-show anomaly in weird non-KS way!!! Removed votes are " + str(modifiedVotesList)+
                #       str(modifiedVotesDict) + " and now " + K + " is the winner.")
                if diagnostic:
                    print("No-show anomaly in a weird non-KS way!!! Removed votes are " + str(modifiedVotesList)+
                          str(modifiedVotesDict) + " and now " + K + " is the winner.")
                    
                # print('Anomaly Found 4')
                return profile, modifiedVotesList, modifiedVotesDict, False, True
            else:
                #print("No anomaly: W eliminated but non-killer candidate won")
                return profile, modifiedVotesList, modifiedVotesDict, False, False
        else:
            
            for key, value in vote_counts.items(): #find last-place cand
                if value == min_count:
                    eliminated_cand = key
            if eliminated_cand not in ksnw: #run round, return
                frame2 = profile.copy(deep = True)
                for k in range(len(frame2)):
                    if eliminated_cand in frame2.iloc[k]['ballot']:
                        frame2.at[k,'ballot']=frame2.at[k,'ballot'].replace(eliminated_cand,'')
                for k in range(len(frame2)):
                    if frame2.at[k,'ballot']=='':
                        frame2.drop(k)
                #print("Eliminated candidate " + eliminated_cand)
                return frame2, modifiedVotesList, modifiedVotesDict, True, False
            else: #modify ballots, return
                frame2 = profile.copy(deep = True)
                return runNoShowModificationsOrderedEasyFor_all(frame2, K, W, ksnw, modifiedVotesList, modifiedVotesDict, maxNSremovable, goFor)
                 
    else:
        print("ERROR: Winner not in round.")
        return profile, modifiedVotesList, modifiedVotesDict, False, False
    

def runNoShowModificationsOrderedEasy_all(frame, K, W, ksnw, modifiedVotesList, modifiedVotesDict, maxNSremovable, go):
    """given profile, killer K, winner W, ksnw, and list, removes just enough 
    L1..K ballots, in an ordered way (L1...k2...K, to make 
    L1 drop out next, returns modified frame, removedVotesList, go"""
    ks1 = copy.deepcopy(ksnw)
    ks1.append(W)
    ksSet = set(ks1)
    #print("Killer subset in Run modifications is " + str(ksSet))
    vote_counts = {} #may need to fix for CIVS elections...input candidate list and do like above.
    for j in range(len(frame)):
        if frame.at[j,'ballot']!='':
            if frame.at[j,'ballot'][0] in vote_counts.keys():
                vote_counts[frame.at[j,'ballot'][0]]+=frame.iloc[j]['Count']
            else:
                vote_counts[frame.at[j,'ballot'][0]]=frame.iloc[j]['Count']
    sorted_items = sorted(vote_counts.items(), key=lambda item: item[1]) #sorted lowest votes to highest
    sorted_cands = [item[0] for item in sorted_items] #K should be first
    nCands = len(vote_counts)
    
    K1 = sorted_cands[0] #killer with lowest points, might not be K
    removable_list = copy.deepcopy(sorted_cands)
    for cand in ksSet:
        if cand in removable_list:
            removable_list.remove(cand)
            #print("Removed " + cand + " from removable list")
    #print("New Removable list is "+str(removable_list))
    for i in range(0,len(removable_list)):
        tempframe = frame.copy(deep=True)
        go = True
        L = removable_list[i] 
        #print("Removing votes for " + L)
        gap = vote_counts[L]-vote_counts[K1]
        if maxNSremovable <= gap:
            #print("No no-show: Maximum removable is less than gap for " + L)
            continue
        noShowableVotes = 0
        for k in range(len(tempframe)):
            ballot = tempframe.at[k,'ballot']
            if (tempframe.at[k,'Count'] != 0) and (len(ballot)!=0) and (ballot[0]==L) and (K in ballot):
                res = noShowable(ballot, K, W)
                if res == True:
                    noShowableVotes += tempframe.at[k,'Count']
        #print("No showable = " +str(noShowableVotes))
        if noShowableVotes<=(gap):
            return tempframe, modifiedVotesList, modifiedVotesDict, False, False #means no anomaly
            #print("Not enough No showable votes to make the next dropout be " + L)
        else:
            check = copy.deepcopy(gap)
            #if nCands>1:
            for i in range(nCands-1):
                for z in range(len(tempframe)):
                    if check >= 0:
                        ballot = tempframe.at[z,'ballot']
                        if (len(ballot) > nCands-2-i) and (ballot[0]==L) and (noShowable(ballot, K, W)):
                            if ballot.index(K) == (nCands-1-i):
                                if check - tempframe.at[z,'Count']>=-1: #remove all such ballots
                                    modifiedVotesList.append(str(tempframe.at[z,'Count'])+ " " + ballot)
                                    if ballot in modifiedVotesDict.keys():
                                        modifiedVotesDict[ballot]+=tempframe.iloc[z]['Count']
                                    else:
                                        modifiedVotesDict[ballot]=tempframe.iloc[z]['Count']
                                    check = check - tempframe.at[z,'Count']
                                    tempframe.at[z,'Count'] = 0

                                else: #remove check+1 such ballots
                                    modifiedVotesList.append(str(check+1)+ " " + ballot)
                                    if ballot in modifiedVotesDict.keys():
                                        modifiedVotesDict[ballot]+=(check+1)
                                    else:
                                        modifiedVotesDict[ballot]=(check+1)
                                    tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                                    check = -1
            # print(len(modifiedVotesList))
            # print(modifiedVotesList)
            if len(modifiedVotesList)>sum(vote_counts.values()):
                somethingIsWrong
            while go == True:
                # print('running runAround inside NoShowMod')
                tempframe, modifiedVotesList, modifiedVotesDict, go, anomFound = runAround_all(tempframe, ksnw, W, K, modifiedVotesList, modifiedVotesDict, maxNSremovable, go)
                if anomFound:
                    return tempframe, modifiedVotesList, modifiedVotesDict, False, True

    return tempframe, modifiedVotesList, modifiedVotesDict, False, False


def runNoShowModificationsOrderedEasyFor_all(frame, K, W, ksnw, modifiedVotesList, modifiedVotesDict, maxNSremovable, goFor):
    """given profile, killer K, winner W, ksnw, and list, removes just enough 
    L1...K ballots, in the reverse ordered way (L1K...k2..., to make 
    L1 drop out next, returns modified frame, removedVotesList, go"""
    ks1 = copy.deepcopy(ksnw)
    ks1.append(W)
    ksSet = set(ks1)
    #print("Killer subset in Run modifications is " + str(ksSet))
    vote_counts = {} #may need to fix for CIVS elections...input candidate list and do like above.
    for j in range(len(frame)):
        if frame.at[j,'ballot']!='':
            if frame.at[j,'ballot'][0] in vote_counts.keys():
                vote_counts[frame.at[j,'ballot'][0]]+=frame.iloc[j]['Count']
            else:
                vote_counts[frame.at[j,'ballot'][0]]=frame.iloc[j]['Count']
    sorted_items = sorted(vote_counts.items(), key=lambda item: item[1]) #sorted lowest votes to highest
    sorted_cands = [item[0] for item in sorted_items] #K should be first
    nCands = len(vote_counts)
    
    K1 = sorted_cands[0] #killer with lowest points, might not be K
    removable_list = copy.deepcopy(sorted_cands)
    for cand in ksSet:
        if cand in removable_list:
            removable_list.remove(cand)
            #print("Removed " + cand + " from removable list")
    #print("New Removable list is "+str(removable_list))
    for i in range(0,len(removable_list)):
        tempframe = frame.copy(deep=True)
        goFor = True
        L = removable_list[i] 
        #print("Removing votes for " + L)
        gap = vote_counts[L]-vote_counts[K1]
        if maxNSremovable <= gap:
            #print("No no-show: Maximum removable is less than gap for " + L)
            continue
        noShowableVotes = 0
        for k in range(len(tempframe)):
            ballot = tempframe.at[k,'ballot']
            if (tempframe.at[k,'Count'] != 0) and (len(ballot)!=0) and (ballot[0]==L) and (K in ballot):
                res = noShowable(ballot, K, W)
                if res == True:
                    noShowableVotes += tempframe.at[k,'Count']
        #print("No showable = " +str(noShowableVotes))
        if noShowableVotes<=(gap):
            return tempframe, modifiedVotesList, modifiedVotesDict, False, False #means no anomaly
            #print("Not enough No showable votes to make the next dropout be " + L)
        else:
            check = copy.deepcopy(gap)
            #if nCands>1:
            for i in range(nCands-1):
                for z in range(len(tempframe)):
                    if check >= 0:
                        ballot = tempframe.at[z,'ballot']
                        if (len(ballot) > 0) and (ballot[0]==L) and (noShowable(ballot, K, W)):
                            if ballot.index(K) == (i+1):
                                if check - tempframe.at[z,'Count']>=-1: #remove all such ballots
                                    modifiedVotesList.append(str(tempframe.at[z,'Count'])+ " " + ballot)
                                    if ballot in modifiedVotesDict.keys():
                                        modifiedVotesDict[ballot]+=tempframe.iloc[z]['Count']
                                    else:
                                        modifiedVotesDict[ballot]=tempframe.iloc[z]['Count']
                                    check = check - tempframe.at[z,'Count']
                                    tempframe.at[z,'Count'] = 0

                                else: #remove check+1 such ballots
                                    modifiedVotesList.append(str(check+1)+ " " + ballot)
                                    if ballot in modifiedVotesDict.keys():
                                        modifiedVotesDict[ballot]+=(check+1)
                                    else:
                                        modifiedVotesDict[ballot]=(check+1)
                                    tempframe.at[z,'Count'] = tempframe.at[z,'Count']-(check+1)
                                    check = -1
                                    
            if len(modifiedVotesList)>sum(vote_counts.values()):
                somethingIsWrong
            while goFor == True:
                tempframe, modifiedVotesList, modifiedVotesDict, goFor, anomFound = runAroundFor_all(tempframe, ksnw, W, K, modifiedVotesList, modifiedVotesDict, maxNSremovable, goFor)
                if anomFound:
                    return tempframe, modifiedVotesList, modifiedVotesDict, False, True
                
    return tempframe, modifiedVotesList, modifiedVotesDict, False, False

###############################################################################
###############################################################################

def frac_noShowSmithPlur(profile, num_cands, vote_frac, diagnostic=False):
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    smith_set, new_profile = restrict_to_smith(profile, cands)
    if diagnostic:
        print(smith_set)
    
    margins = np.zeros((num_cands, num_cands))
    for c1 in range(num_cands):
        for c2 in range(c1+1, num_cands):
            c1_let = cands[c1]
            c2_let = cands[c2]
            ## number of votes c1 gets over c2 in H2H
            margin = 0
            for k in range(len(profile)):
                ballot = profile.at[k, 'ballot']
                count = profile.at[k, 'Count']
                ## ballot ranks both c1 and c2
                if c1_let in ballot and c2_let in ballot:
                    if ballot.find(c1_let) < ballot.find(c2_let):
                        margin += count
                    else:
                        margin -= count
                ## ballot only ranks c1       
                elif c1_let in ballot:
                    margin += count
                ## ballot only ranks c2
                elif c2_let in ballot:
                    margin -= count
            margins[c1, c2] = margin
            margins[c2, c1] = -1*margin
    if diagnostic:
        print(margins)
    
    ## if there is a top cycle, try to break it
    if len(smith_set)>1:
        if diagnostic:
            print('Top cycle')
        plur_wins = plurality(profile, cands)[0]
        if len(plur_wins)>1:
            print('##### Multiple winners #####')
            return []
        plur_win = plur_wins[0]
        if diagnostic:
            print(plur_win)
            
        cond_wins = [cand for cand in smith_set if margins[cands.index(cand), cands.index(plur_win)]>0]
        if diagnostic:
            print(cond_wins)
        for cond_win in cond_wins:
            need_to_lose = {cand: margins[cands.index(cand), cands.index(cond_win)]+1 for cand in smith_set if margins[cands.index(cand), cands.index(cond_win)]>0}
            # need_to_lose = [cand for cand in smith_set if margins[cands.index(cand), cands.index(cond_win)]>0]
            margin = margins[cands.index(cond_win), cands.index(plur_win)]
            
            if diagnostic:
                print(cond_win)
                print(need_to_lose)
                print(margin)
            ## remove ballots that prevent cond_win from being condorcet winner
            new_profile = profile.copy(deep=True)
            remove_ballots = []
            for k in range(len(new_profile)):
                ballot = new_profile.at[k, 'ballot']
                count = int(new_profile.at[k, 'Count']*vote_frac)
                ## ballot prefers cond_win to plur_win
                if (cond_win in ballot and plur_win not in ballot) or (cond_win in ballot and plur_win in ballot and ballot.find(cond_win)<ballot.find(plur_win)):
                    ## removing ballot will help break top cycle
                    relevant_cands = set(ballot.split(cond_win)[0]).intersection(need_to_lose)
                    if relevant_cands:
                        remove_count = min([count]+[need_to_lose[cand] for cand in relevant_cands])
                        remove_ballots.append([ballot, remove_count])
                        new_profile.at[k, 'Count'] -= remove_count
            
            if diagnostic:
                print(remove_ballots)
                print(new_profile)
            new_wins = smith_plurality(new_profile, cands)[0]
            # new_smith, foo = restrict_to_smith(new_profile, cands)
            if len(new_wins)>1:
                print('##### Multiple winners #####')
                continue
            if new_wins[0]==cond_win:
                return [plur_win, cond_win, remove_ballots]
                
        
    ## if there is a condorcet winner, try to make top cycle
    else:
        if diagnostic:
            print('Condorcet winner')
        cond_win = smith_set[0]
        
        plur_wins = plurality(profile, cands)[0]
        if len(plur_wins)>1:
            print('##### Multiple winners #####')
            return []
        plur_win = plur_wins[0]
        margin = margins[cands.index(cond_win), cands.index(plur_win)]
        
        if diagnostic:
            print(cond_win)
            print(plur_win)
        
        if plur_win != cond_win:
            threats = [cand for cand in cands if cand != plur_win and cand != cond_win]
            if diagnostic:
                print(threats)
            for threat in threats:
                threat_marg = margins[cands.index(cond_win), cands.index(threat)]
                if diagnostic:
                    print(threat)
                    print(threat_marg)
                risky_ballots = []
                new_profile = profile.copy(deep=True)
                remove_ballots = []
                for k in range(len(new_profile)):
                    ballot = new_profile.at[k, 'ballot']
                    count = int(new_profile.at[k, 'Count']*vote_frac)
                    ## prefers plur_win over cond_win over threat
                    if plur_win in ballot and cond_win in ballot and ballot.find(plur_win)<ballot.find(cond_win):
                        if threat not in ballot or (threat in ballot and ballot.find(cond_win)<ballot.find(threat)):
                            ## not a risky ballot to remove
                            if ballot[0]!=plur_win:
                                remove_ballots.append([ballot, count])
                                threat_marg -= count
                                new_profile.at[k, 'Count'] -= count
                
                if diagnostic:
                    print(remove_ballots)
                    print(new_profile)
                    print(threat_marg)
                
                new_wins = smith_plurality(new_profile, cands)[0]
                if diagnostic:
                    print(new_wins)
                    
                if new_wins != [plur_win]:
                    ## remove some risky ballots
                    for k in range(len(new_profile)):
                        ballot = new_profile.at[k, 'ballot']
                        count = new_profile.at[k, 'Count']
                        ## prefers plur_win over cond_win over threat
                        if plur_win in ballot and cond_win in ballot and ballot.find(plur_win)<ballot.find(cond_win):
                            if threat not in ballot or (threat in ballot and ballot.find(cond_win)<ballot.find(threat)):
                                ## is a risky ballot to remove
                                if ballot[0]==plur_win:
                                    if count < threat_marg + 1:
                                        remove_ballots.append([ballot, count])
                                        threat_marg -= count
                                        new_profile.at[k, 'Count'] -= count
                                    else:
                                        remove_ballots.append([ballot, threat_marg + 1])
                                        new_profile.at[k, 'Count'] -= (threat_marg+1)
                                        break
                    
                if diagnostic:
                    print(remove_ballots)
                    print(new_profile)
                new_wins = smith_plurality(new_profile, cands)[0]
                if diagnostic:
                    print(new_wins)
                if len(new_wins)>1:
                    print('##### Multiple winners #####')
                    continue
                new_win = new_wins[0]
                if new_win == plur_win:
                    return [cond_win, plur_win, remove_ballots]
    
    return []
            
###############################################################################
###############################################################################

def frac_noShowSmithIRV(profile, num_cands, vote_frac, diagnostic=False):
    cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                  'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                  'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    cands = cand_names[:num_cands]
    
    smith_set, new_profile = restrict_to_smith(profile, cands)
    if diagnostic:
        print(smith_set)
    
    margins = np.zeros((num_cands, num_cands))
    for c1 in range(num_cands):
        for c2 in range(c1+1, num_cands):
            c1_let = cands[c1]
            c2_let = cands[c2]
            ## number of votes c1 gets over c2 in H2H
            margin = 0
            for k in range(len(profile)):
                ballot = profile.at[k, 'ballot']
                count = profile.at[k, 'Count']
                ## ballot ranks both c1 and c2
                if c1_let in ballot and c2_let in ballot:
                    if ballot.find(c1_let) < ballot.find(c2_let):
                        margin += count
                    else:
                        margin -= count
                ## ballot only ranks c1       
                elif c1_let in ballot:
                    margin += count
                ## ballot only ranks c2
                elif c2_let in ballot:
                    margin -= count
            margins[c1, c2] = margin
            margins[c2, c1] = -1*margin
    if diagnostic:
        print(margins)
    
    ## if there is a top cycle, try to break it
    if len(smith_set)>1:
        if diagnostic:
            print('Top cycle')
        irv_wins = IRV(profile, cands)[0]
        if len(irv_wins)>1:
            print('##### Multiple winners #####')
            return []
        irv_win = irv_wins[0]
        if diagnostic:
            print(irv_win)
            
        cond_wins = [cand for cand in smith_set if margins[cands.index(cand), cands.index(irv_win)]>0]
        if diagnostic:
            print(cond_wins)
        for cond_win in cond_wins:
            need_to_lose = {cand: margins[cands.index(cand), cands.index(cond_win)]+1 for cand in smith_set if margins[cands.index(cand), cands.index(cond_win)]>0}
            # need_to_lose = [cand for cand in smith_set if margins[cands.index(cand), cands.index(cond_win)]>0]
            margin = margins[cands.index(cond_win), cands.index(irv_win)]
            
            if diagnostic:
                print(cond_win)
                print(need_to_lose)
                print(margin)
            ## remove ballots that prevent cond_win from being condorcet winner
            new_profile = profile.copy(deep=True)
            remove_ballots = []
            for k in range(len(new_profile)):
                ballot = new_profile.at[k, 'ballot']
                count = int(new_profile.at[k, 'Count']*vote_frac)
                ## ballot prefers cond_win to irv_win
                if (cond_win in ballot and irv_win not in ballot) or (cond_win in ballot and irv_win in ballot and ballot.find(cond_win)<ballot.find(irv_win)):
                    ## removing ballot will help break top cycle
                    relevant_cands = set(ballot.split(cond_win)[0]).intersection(need_to_lose)
                    if relevant_cands:
                        remove_count = min([count]+[need_to_lose[cand] for cand in relevant_cands])
                        remove_ballots.append([ballot, remove_count])
                        new_profile.at[k, 'Count'] -= remove_count
            
            if diagnostic:
                print(remove_ballots)
                print(new_profile)
            new_wins = smith_irv(new_profile, cands)[0]
            # new_smith, foo = restrict_to_smith(new_profile, cands)
            if len(new_wins)>1:
                print('##### Multiple winners #####')
                continue
            if new_wins[0]==cond_win:
                return [irv_win, cond_win, remove_ballots]
                
        
    ## if there is a condorcet winner, try to make top cycle
    else:
        if diagnostic:
            print('Condorcet winner')
        cond_win = smith_set[0]
        
        irv_wins = IRV(profile, cands)[0]
        if len(irv_wins)>1:
            print('##### Multiple winners #####')
            return []
        irv_win = irv_wins[0]
        margin = margins[cands.index(cond_win), cands.index(irv_win)]
        
        if diagnostic:
            print(cond_win)
            print(irv_win)
        
        if irv_win != cond_win:
            threats = [cand for cand in cands if cand != irv_win and cand != cond_win]
            if diagnostic:
                print(threats)
            for threat in threats:
                threat_marg = margins[cands.index(cond_win), cands.index(threat)]
                if diagnostic:
                    print(threat)
                    print(threat_marg)
                risky_ballots = []
                new_profile = profile.copy(deep=True)
                remove_ballots = []
                for k in range(len(new_profile)):
                    ballot = new_profile.at[k, 'ballot']
                    count = int(new_profile.at[k, 'Count']*vote_frac)
                    ## prefers irv_win over cond_win over threat
                    if irv_win in ballot and cond_win in ballot and ballot.find(irv_win)<ballot.find(cond_win):
                        if threat not in ballot or (threat in ballot and ballot.find(cond_win)<ballot.find(threat)):
                            ## not a risky ballot to remove
                            if ballot[0]!=irv_win:
                                remove_ballots.append([ballot, count])
                                threat_marg -= count
                                new_profile.at[k, 'Count'] -= count
                
                if diagnostic:
                    print(remove_ballots)
                    print(new_profile)
                    print(threat_marg)
                
                new_wins = smith_irv(new_profile, cands)[0]
                if diagnostic:
                    print(new_wins)
                    
                if new_wins != [irv_win]:
                    ## remove some risky ballots
                    for k in range(len(new_profile)):
                        ballot = new_profile.at[k, 'ballot']
                        count = new_profile.at[k, 'Count']
                        ## prefers irv_win over cond_win over threat
                        if irv_win in ballot and cond_win in ballot and ballot.find(irv_win)<ballot.find(cond_win):
                            if threat not in ballot or (threat in ballot and ballot.find(cond_win)<ballot.find(threat)):
                                ## is a risky ballot to remove
                                if ballot[0]==irv_win:
                                    if profile.at[k, 'Count'] < threat_marg + 1:
                                        remove_ballots.append([ballot, count])
                                        threat_marg -= count
                                        new_profile.at[k, 'Count'] -= count
                                    else:
                                        remove_ballots.append([ballot, threat_marg + 1])
                                        new_profile.at[k, 'Count'] -= (threat_marg+1)
                                        break
                    
                if diagnostic:
                    print(remove_ballots)
                    print(new_profile)
                new_wins = smith_irv(new_profile, cands)[0]
                if diagnostic:
                    print(new_wins)
                if len(new_wins)>1:
                    print('##### Multiple winners #####')
                    continue
                new_win = new_wins[0]
                if new_win == irv_win:
                    return [cond_win, irv_win, remove_ballots]
    
    return []
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    