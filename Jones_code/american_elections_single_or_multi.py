import json
import pandas as pd
import numpy as np
import csv
from collections import Counter, defaultdict
import time
import sys
import os
import shutil


def process_rankings(row):
    seen_candidates = set()
    ranking = defaultdict(list)
    rank = 1
    
    for i in range(1, num_ranks+1):
        candidate = str(row[f'rank{i}'])
        if candidate != 'overvote' and candidate != 'skipped' and candidate not in seen_candidates:
            ranking[rank].append(candidate)
            seen_candidates.add(candidate)
            rank += 1
    
    return {c: r for r, cs in ranking.items() for c in cs}



def get_num_ranks(file_path):
    election_data = pd.read_csv(file_path)
    column_names_list = election_data.columns.tolist()
    num_ranks=0
    for item in column_names_list:
        if 'rank' in item:
            num_ranks+=1
    return num_ranks



def get_info(file_path):
    election_data = pd.read_csv(file_path)
    if 'numSeats' in election_data.keys():
        seat_num = election_data['numSeats'][0]
    if 'Num seats' in election_data.keys():
        seat_num = election_data['Num seats'][0]
    elif 'Num Seats' in election_data.keys():
        seat_num = election_data['Num Seats'][0]
    elif 'numSeats' in election_data.keys():
        seat_num = election_data['numSeats'][0]
    else:
        print('seat error!')
        seat_num = 0
        
    # Apply the function and count occurrences of each ranking
    election_data['processed_rankings'] = election_data.apply(process_rankings, axis=1)
    # print(election_data)
    ranking_counts = Counter(election_data['processed_rankings'].apply(tuple))
    ranking_counts.pop((), None)

    # Create candidate list and set "Write-in" index last
    candidates = [c for c in set().union(*[r for r in ranking_counts])]
    # added to sort by first place votes
    first_place = {cand:sum([ranking_counts[r] for r in ranking_counts if r[0]==cand]) for cand in candidates}
    candidates.sort(key=lambda x:first_place[x], reverse=True)
        
    return seat_num, len(candidates)





######################################################
###### America
######################################################

name_list = []

cand_list = []
seat_list = []

single_win_names = []
multi_win_names = []

base_name = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_old/American data'
# new_base = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_clean/America'

for folder_name in os.listdir(base_name):
    for file_name in os.listdir(base_name+'/'+folder_name):
        sys.stdout.write('\r')
        sys.stdout.write(f'Election {len(name_list)+1}'+'         ')
        sys.stdout.flush()
        
        file_path = base_name + '/' + folder_name + '/' + file_name
        name_list.append(folder_name + '/' + file_name)
        

        num_ranks = get_num_ranks(file_path)
        seats, cands = get_info(file_path)
        seat_num = str(int(seats))
        cand_num = str(int(cands))
        
        seat_list.append(seat_num)
        cand_list.append(cand_num)
        # print(seat_num, cand_num)

        if folder_name == 'APA':
            new_name = file_name.replace(' ', '-')
        
        elif folder_name == 'Alameda County':
            new_name = 'Alameda_County_'+file_name.replace('_', '-')
        elif folder_name == 'New Mexico':
            new_name = 'New_Mexico_'+file_name.replace('_', '-').replace('sC', 's_C').replace('aF', 'a_F')
        elif folder_name == 'Utah cities':
            new_name = 'Utah_Cities_'+file_name.replace('_', '-')

        elif ', ' in folder_name:
            new_name = folder_name.replace(', ', '_').replace(' ', '_') + '-' + file_name[file_name.index('_')+1:].replace('_', '-')

        elif folder_name == 'New York City':
            new_name = file_name.replace('_','-').replace('NewYorkCity', 'New_York_City')
        elif folder_name == 'San Francisco':
            new_name = file_name.replace('_','-').replace('SanFrancisco', 'San_Francisco')
        elif folder_name == 'St Louis Park':
            new_name = file_name.replace('_','-').replace('StLouisPark', 'St_Louis_Park')

        else:
            new_name = file_name.replace('_', '-')
        # print(new_name)
        
        new_name = new_name[:-4]
        new_name += '-'+seat_num+'-'+cand_num+'.csv'

        if seat_num == '1':
            single_win_names.append(file_name)
        else:
            multi_win_names.append(file_name)



lxn_methods = ['plurality','plurality_runoff','IRV','smith_irv','smith_plurality','minimax','smith_minimax','ranked_pairs','Borda_PM','Borda_OM','Borda_AVG','bucklin','TVR_PM','TVR_OM','TVR_AVG','diversity_score_threshold','friendly_fire_inst','friendly_fire_seq_smith','friendly_fire_inst_smith','friendly_fire_inst_smith_exp']




