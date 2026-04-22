###################################################
##### Code to search for anomalies
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
import json
import matplotlib.pyplot as plt

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
from anomaly_search_class import *


#####TODO
## 




###############################################################################
###############################################################################
##### parameters
election_group = 'scotland'
mp_pool_size = 6

frac_depth = 5
###############################################################################
###############################################################################



####################################################
##### Functions to run searches
####################################################

def createBallotDF(list_profile, diagnostic=False):
    cand_names=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    
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
    base_name = 'C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/' + election_location
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
            
            # if 'banchory' not in  file_path:
            #     continue
            
            # print(file_path)
            
            if specific_lxn > 0:
                if lxn_count!=specific_lxn:
                    continue
            
            if diagnostic:
                print(lxn_count, file_path)
        
            # sys.stdout.write('\r')
            # sys.stdout.write(f'Election {lxn_count}'+'         ')
            # sys.stdout.flush()
            
            File=open(file_path,'r', encoding='utf-8')
            lines=File.readlines()
    
            first_space=lines[0].find(' ')
            num_cands=int(lines[0][0:first_space])
            if num_cands>52:
                print("Cannot handle this many candidates in election " + str(file_path) + ".  Has " + 
                      str(num_cands) + " candidates.")
                continue
                
            data = createBallotDF(lines)
            
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

def frac_search(params):
    lxn_method, ballot_mod, file_path, profile, num_cands = params
    # print(file_path)
    voter_fracs = []
    data = frac_general_search(profile, num_cands, lxn_method, ballot_mod, 1)
    if data:
        # print('Full bloc successful')
        voter_fracs.append(1)
    else:
        # print('None Found')
        return [lxn_method.__name__, ballot_mod.__name__, file_path, 2]
    depth = 0
    vote_frac = 1
    while depth<frac_depth:
        depth += 1
        if data:
            vote_frac -= 1/(2**depth)
        else:
            vote_frac += 1/(2**depth)
        
        # print(vote_frac)
        
        data = frac_general_search(profile, num_cands, lxn_method, ballot_mod, vote_frac)
        if data:
            # print('successful')
            voter_fracs.append(vote_frac)
    
    # print(voter_fracs)
    return [lxn_method.__name__, ballot_mod.__name__, file_path, min(voter_fracs)]
    
###############################################################################
###############################################################################



###############################################################################
###############################################################################
##### Run this code
###############################################################################
###############################################################################

if __name__ == '__main__':  

    if not os.path.exists(election_group+'_frac_search'):
        os.makedirs(election_group+'_frac_search')
    
    # lxn_methods = [plurality, plurality_runoff, IRV, smith_irv, smith_plurality, 
    #                 minimax, smith_minimax, ranked_pairs, 
    #                 Borda_PM, Borda_OM, Borda_AVG, bucklin]
    # lxn_methods += [TVR_OM, TVR_PM, TVR_AVG, diversity_score_threshold]
    lxn_methods = [diversity_score_simplex]
    
    # lxn_methods = [plurality]
    lxn_names = [lxn_method.__name__ for lxn_method in lxn_methods]
    
    ballot_mod_methods = [laterNoHarm, strat_compromise, strat_truncate_L, strat_truncate_W, strat_bury_shallow, strat_bury_deep]
    # ballot_mod_methods = [strat_truncate_L]
    strategy_names = [ballot_mod.__name__ for ballot_mod in ballot_mod_methods]
    
    
    search_combos = {}
    for lxn_method in lxn_methods:
        for ballot_mod in ballot_mod_methods:
            combo_name = lxn_method.__name__ + '_' + ballot_mod.__name__
            ## list is file_names, num_cands, old_winner, new_winner, modified_ballots
            search_combos[combo_name] = [[], [], [], [], []]
    

    ## get data
    lxn_list = get_election_data(election_group)
    gen_lxn_list = []
    for lxn in lxn_list:
        for lxn_method in lxn_methods:
            
            if lxn_method == diversity_score_simplex and lxn[2]>5:
                lxn = [lxn[0], filter_weak_cands(lxn[1], lxn[2], 5), 5]
            
            for ballot_mod in ballot_mod_methods:
                gen_lxn_list.append([lxn_method, ballot_mod]+lxn)
                
    
    # for x in gen_lxn_list:
    #     # print(gen_lxn_list.index(x))
    #     frac_search(x)

    
    ## search for general anomalies
    pool = multiprocessing.Pool(processes=mp_pool_size)
    massive_results = pool.map(frac_search, gen_lxn_list)
    
    with open(election_group+"_frac_search/massive_results_data.json", "w") as f:
        json.dump(massive_results, f, cls=NpEncoder)
        
    
    for strategy in strategy_names:
        if not os.path.exists(election_group+'_frac_search/'+strategy):
            os.makedirs(election_group+'_frac_search/'+strategy)
    
        for lxn_method in lxn_names:
            
            strat_frac_list = [x[3] for x in massive_results if x[1]==strategy and x[0]==lxn_method]
            with open(election_group+'_frac_search/'+strategy+'/'+lxn_method+'_coalition_fracs.json', "w") as f:
                json.dump(strat_frac_list, f, cls=NpEncoder)
            
            vote_fracs = [i/(2**frac_depth) for i in range(2**frac_depth + 1)]
            y_vals = [len([x for x in strat_frac_list if x <= vote_frac])/len(strat_frac_list) for vote_frac in vote_fracs]
            plt.subplots()
            plt.plot(vote_fracs, y_vals)
            plt.title(strategy+'_'+lxn_method)
            plt.savefig(election_group+'_frac_search/'+strategy+'/'+lxn_method+'_coalition_sizes.png', dpi=300)
            plt.close()





