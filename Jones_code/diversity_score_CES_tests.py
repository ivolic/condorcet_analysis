import random as rand
import numpy as np
from election_class import *
import pandas as pd
import os
import pickle
import math

from election_class import simplex_point, restrict_to_smith

no_cond_winner_count = 0
strat_possible_list = []

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
    # for lxn_indx in range(8):
        
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
        hopefuls =cand_names[:cand_num]
        
        smith_set = restrict_to_smith(profile, hopefuls)
        
        if len(smith_set[0])>1:
            # print('No Condorcet winner!')
            no_cond_winner_count+=1
            continue
        
        CW = smith_set[0][0]
        
        new_ballot_list = []
        new_count_list = []
        for k in range(len(profile)):
            ballot = profile.at[k, 'ballot']
            if len(ballot) == len(hopefuls)-1:
                missing_cand = [cand for cand in hopefuls if cand not in ballot][0]
                ballot += missing_cand
                
            if ballot in new_ballot_list:
                indx = new_ballot_list.index(ballot)
                new_count_list[indx] += profile.at[k, 'Count']
            else:
                new_ballot_list.append(ballot)
                new_count_list.append(profile.at[k, 'Count'])
         
        df_dict = {'ballot': new_ballot_list, 'Count': new_count_list}
        profile = pd.DataFrame(df_dict)

        
        diversity_scores = {cand:0 for cand in hopefuls}
        first_place_votes = {cand:0 for cand in hopefuls}
        total_votes = sum(profile['Count'])
        for k in range(len(profile)):
            if profile.at[k, 'Count'] >= 0.05*total_votes:
                diversity_scores[profile.at[k, 'ballot'][0]] += 1
            first_place_votes[profile.at[k, 'ballot'][0]] += profile.at[k, 'Count']
            
        margins = np.zeros((cand_num, cand_num))
        for c1 in range(cand_num):
            for c2 in range(c1+1, cand_num):
                c1_let = hopefuls[c1]
                c2_let = hopefuls[c2]
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
        
        for cand in hopefuls:
            if cand==CW:
                continue
            cand_margins = margins[hopefuls.index(cand), :]
            if len([x for x in cand_margins if x<0]) == 1:
                thief = cand
                break
        stooge = [cand for cand in hopefuls if cand not in [CW, thief]][0]
             
        if diversity_scores[stooge]>diversity_scores[CW] or (diversity_scores[stooge]==diversity_scores[CW] and first_place_votes[stooge]>first_place_votes[CW]):
            # stooge wont be eliminated
            if first_place_votes[thief]>first_place_votes[CW]:
                # just tie diversity score
                types_needed = diversity_scores[CW]
            else:
                # need to win on diversity score
                types_needed = diversity_scores[CW]+1
            total_thief_votes = sum([profile.at[i,'Count'] for i in range(len(profile)) if profile.at[i, 'ballot'][0]==thief])
            
            gap = first_place_votes[CW]-first_place_votes[stooge]
            spare_thief_votes = total_thief_votes - types_needed*(int(0.05*total_votes)+1)
            
            if spare_thief_votes>=0:
                stooge_votes = first_place_votes[stooge]+(int(0.05*total_votes)+1)+spare_thief_votes
                CW_votes = first_place_votes[CW]
                if types_needed==3:
                    CW_votes += (int(0.05*total_votes)+1)
                
                if stooge_votes>CW_votes:
                    strat_possible_list.append(profile)
                    
        


        
        # ##### compute diversity score - simplex
        # simplex_points = {cand: np.zeros(math.factorial(len(hopefuls)-1)) for cand in hopefuls}
        # first_place_votes = {cand:0 for cand in hopefuls}
        # for k in range(len(profile)):
        #     first_place_votes[profile.at[k, 'ballot'][0]] += profile.at[k, 'Count']
        #     simplex_points[profile.at[k, 'ballot'][0]] += profile.at[k, 'Count']*simplex_point(profile.at[k, 'ballot'], hopefuls)
            
        # for cand in hopefuls:
        #     simplex_points[cand] /= first_place_votes[cand]
        
        # diversity_scores = {cand: -np.linalg.norm(simplex_points[cand] - np.ones(math.factorial(len(hopefuls)-1))/math.factorial(len(hopefuls)-1)) for cand in hopefuls}
        
        # ##### compute diversity score - threshold
        # diversity_scores = {cand:0 for cand in hopefuls}
        # first_place_votes = {cand:0 for cand in hopefuls}
        # total_votes = sum(profile['Count'])
        # for k in range(len(profile)):
        #     if profile.at[k, 'Count'] >= 0.05*total_votes:
        #         diversity_scores[profile.at[k, 'ballot'][0]] += 1
        #     first_place_votes[profile.at[k, 'ballot'][0]] += profile.at[k, 'Count']
        
        
        
        # if cand_num == 3:
        #     lr_spectrum = sorted([0,1,2],key = lambda x: cand_positions[str(x)])
        #     if diversity_scores[hopefuls[lr_spectrum[1]]] == min(diversity_scores.values()):
        #         # print(cand_positions)
        #         # print(diversity_scores)
        #         centrist_tied.append((lxn_indx,file_name))
        #         if list(diversity_scores.values()).count(min(diversity_scores.values())) == 1:
        #             centrist_eliminated.append((lxn_indx, file_name))
        
        
        
        
        