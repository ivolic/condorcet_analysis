import random as rand
import numpy as np
from election_class import *
import pandas as pd
import os
import pickle
import math

from election_class import simplex_point

centrist_tied = []
centrist_eliminated = []


cand_names = ['A', 'B', 'C', 'D', 'E']
samples = pd.read_csv('C:/Users/mijones/Documents/Datasets/CES_results/Trimodal voter distributions.csv')
states = list(samples.columns)
base_name = 'C:/Users/mijones/Documents/Datasets/CES_results/CES_sim_results'
for file_name in os.listdir(base_name):
    if '3cands' not in file_name:
        continue
    df = pd.read_parquet(base_name + '/' + file_name, engine='pyarrow')
    
    print(file_name)
    
    # for lxn_indx in range(len(df)):
    for lxn_indx in range(8000):
        
        sys.stdout.write('\r')
        sys.stdout.write('\r')
        sys.stdout.write(f'Election {lxn_indx}' + '                                         ')
        sys.stdout.flush()
        
        cand_positions = df.at[lxn_indx, 'cand_positions']
        cand_num = len(cand_positions)
        lxn_df = pickle.loads(df.at[lxn_indx, 'profile'])

        ballot_list = []
        count_list = []
        for j in range(len(lxn_df)):
            count_list.append(lxn_df.at[j, 'Count'])
            ballot = ''
            for k in range(1,6):
                try:
                    if lxn_df.at[j, 'rank'+str(k)]=='skipped':
                        break
                    else:
                        ballot += cand_names[int(lxn_df.at[j, 'rank'+str(k)])]
                except:
                    break
            ballot_list.append(ballot)

        df_dict = {'ballot': ballot_list, 'Count': count_list}
        profile = pd.DataFrame(df_dict)
        
        hopefuls = cand_names[:cand_num]
        # ##### compute diversity score - simplex
        # simplex_points = {cand: np.zeros(math.factorial(len(hopefuls)-1)) for cand in hopefuls}
        # first_place_votes = {cand:0 for cand in hopefuls}
        # for k in range(len(profile)):
        #     first_place_votes[profile.at[k, 'ballot'][0]] += profile.at[k, 'Count']
        #     simplex_points[profile.at[k, 'ballot'][0]] += profile.at[k, 'Count']*simplex_point(profile.at[k, 'ballot'], hopefuls)
            
        # for cand in hopefuls:
        #     simplex_points[cand] /= first_place_votes[cand]
        
        # diversity_scores = {cand: -np.linalg.norm(simplex_points[cand] - np.ones(math.factorial(len(hopefuls)-1))/math.factorial(len(hopefuls)-1)) for cand in hopefuls}
        
        ##### compute diversity score - threshold
        diversity_scores = {cand:0 for cand in hopefuls}
        first_place_votes = {cand:0 for cand in hopefuls}
        total_votes = sum(profile['Count'])
        for k in range(len(profile)):
            if profile.at[k, 'Count'] >= 0.05*total_votes:
                diversity_scores[profile.at[k, 'ballot'][0]] += 1
            first_place_votes[profile.at[k, 'ballot'][0]] += profile.at[k, 'Count']
        
        
        
        if cand_num == 3:
            lr_spectrum = sorted([0,1,2],key = lambda x: cand_positions[str(x)])
            if diversity_scores[hopefuls[lr_spectrum[1]]] == min(diversity_scores.values()):
                # print(cand_positions)
                # print(diversity_scores)
                centrist_tied.append((lxn_indx,file_name))
                if list(diversity_scores.values()).count(min(diversity_scores.values())) == 1:
                    centrist_eliminated.append((lxn_indx, file_name))
        
        
        
        
        