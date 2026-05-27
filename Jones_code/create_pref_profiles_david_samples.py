import json
import pandas as pd
import numpy as np
import csv
from collections import Counter, defaultdict
import time
import sys
import os


folder_name = "C:/Users/mijones/Documents/Datasets/ranked_ballot_data/Synthetic Preference Profiles/sampled_top_cycles_david_data"
destination_folder = "C:/Users/mijones/Documents/Datasets/ranked_ballot_data/Synthetic Preference Profiles/sampled_top_cycles_david"

for file_name in os.listdir(folder_name):
    
    election_group = file_name[file_name.index('hits')+5:file_name.index('.json')]
    
    print('###############')
    print(election_group)
    print('###############')
    with open(folder_name+'/'+file_name, 'r') as file:
        data = json.load(file)
    
    print('Candidate numbers')
    print([len(x['candidate_map']) for x in data])
    
    print('Number of profiles')
    print([len(x['hits']) for x in data])
    
    cand_key = {'A':'1', 'B':'2', 'C':'3', 'D':'4', 'E':'5'}
    for lxn in data:
        lxn_name_full = lxn['election_name']
        lxn_name = lxn_name_full[:lxn_name_full.index('.csv')]
        
        if len(lxn['hits'])<200:
            continue
        
        for indx, hit in enumerate(lxn['hits']):
            profile = hit['profile']
            
            rows = [[str(len(lxn['candidate_map']))+' '+ '1']]
            for ballot_type in profile.items():
                cand_list = ballot_type[0].split('>')
                ballot = ' '.join([cand_key[cand] for cand in cand_list])
                string = str(ballot_type[1]) + ' ' + ballot + ' 0'
                rows.append([string])
            
            rows.append(['0'])
            
            for name in lxn['candidate_map'].values():
                rows.append([name])
            
            destination_path = destination_folder + '/' + election_group + '_' + lxn_name + '_' + str(indx) +'.csv'
            with open(destination_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(rows)