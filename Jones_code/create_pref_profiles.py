import json
import pandas as pd
import numpy as np
import csv
from collections import Counter, defaultdict
import time
import sys
import os



# Function to process each voter's rankings, ignoring "overvote"
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

# Function to convert rankings (in tuple format) to indices and create dictionaries as keys
def ranking_to_indices(ranking, candidate_to_index):
    ranking_dict = {}
    for rank, candidate in enumerate(ranking, start=1):
        ranking_dict[candidate_to_index.get(candidate, -1)] = rank
    return ranking_dict

def process_csv(file_path):
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
    if 'Count' not in election_data.columns:
        election_data['Count'] = 1
    # print(election_data)
    ranking_counts = Counter(election_data['processed_rankings'].apply(tuple))
    ranking_counts.pop((), None)
    
    # Create candidate list and set "Write-in" index last
    candidates = [c for c in set().union(*[r for r in ranking_counts])]
    # added to sort by first place votes
    first_place = {cand: 0 for cand in candidates}
    for k in range(len(election_data)):
        top_cand=election_data.at[k, 'rank1']
        if top_cand in candidates:
            first_place[election_data.at[k, 'rank1']] += election_data.at[k, 'Count']
    candidates.sort(key=lambda x:first_place[x], reverse=True)
    
    # Convert rankings to indices format
    candidate_to_index = {candidate: index for index, candidate in enumerate(candidates)}
    
    # Display the candidates and their indices for reference
    candidates_with_indices = {index: candidate for candidate, index in candidate_to_index.items()}
    # print(candidates_with_indices)

    rankings = {rank: 0 for rank in ranking_counts.keys()}
    for i in range(len(election_data)):
        ranking = tuple(election_data.at[i, 'processed_rankings'])
        if ranking:
            rankings[ranking] += election_data.at[i,'Count']
    
    rank_cands = [ranking_to_indices(x, candidate_to_index) for x in rankings.keys()]
    rank_counts = list(rankings.values())
    
    # # Creating rankings with indices, ignoring ballots with "overvote"
    # rankings = [ranking_to_indices(ranking, candidate_to_index) for ranking, count in ranking_counts.items()]
    # # rcounts = [count for ranking, count in ranking_counts.items()]
    
    # rcounts = [0 for _ in rankings]
    # for i in range(len(election_data)):
    #     ranking = tuple(election_data.at[i, 'processed_rankings'])
    #     indx = rankings.index(ranking_to_indices(ranking, candidate_to_index))
    #     rcounts[indx]+=election_data.at[i,'Count']
    
    return rank_cands, rank_counts, candidates_with_indices, seat_num  

def get_num_ranks(file_name):
    election_data = pd.read_csv(file_path, nrows=10)
    column_names_list = election_data.columns.tolist()
    num_ranks=0
    for item in column_names_list:
        if 'rank' in item:
            num_ranks+=1
    return num_ranks


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




lxn_names = []
dataset = 'Australia'
base_name = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_clean/fairvote_style_data/' + dataset
destination_base = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_clean/preference_profiles'

for folder_name in os.listdir(base_name):
    
    # destination_folder_name = destination_base + '/' + folder_name
    # if not os.path.exists(destination_folder_name):
    #     os.makedirs(destination_folder_name)
    
    for file_name in os.listdir(base_name+'/'+folder_name):
        
        file_path = base_name+'/'+folder_name+'/'+file_name
        lxn_names.append(file_path)
        destination_path = destination_base+'/'+folder_name+'/'+file_name    
    
        sys.stdout.write('\r')
        sys.stdout.write(f'Election {len(lxn_names)}'+'         ')
        sys.stdout.flush()
        
        # if file_name in os.listdir(destination_base+'/'+folder_name):
        #     continue

        num_ranks = get_num_ranks(file_path)
        rankings, rcounts, cands_with_inds, seat_num = process_csv(file_path)
        
        # breakhere
        
        rows = [[str(len(cands_with_inds))+' '+str(seat_num)]]
        
        ballot_list = []
        for i in range(len(rankings)):
            cand_list = [cand+1 for cand in rankings[i].keys()]
            # cand_list = list(rankings[i].keys())
            ballot_list.append([rcounts[i], cand_list])
        
        ballot_list.sort(key = lambda x: x[1])
        
        for ballot in ballot_list:
            string = str(ballot[0])
            for cand in ballot[1]:
                string += ' '+str(cand)
            string += ' 0'
            rows.append([string])
        
        rows.append(['0'])
        
        for name in cands_with_inds.values():
            rows.append([name])
            
        destination_path = destination_base + '/' + dataset +'/' + folder_name + '/' + file_name
        with open(destination_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows)

        
        
        # print('first done')
        
        ########
        ## filter to top 15
        ########
        
        #dont filter if 15 or fewer candidates
        if len(cands_with_inds) <= 15:
            destination_path = destination_base + '_top_15/' + dataset +'/' + folder_name + '/' + file_name
            with open(destination_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(rows)
                
        else:
            filtered_rankings = {}
            for i in range(len(rankings)):
                cand_list = tuple([cand+1 for cand in rankings[i].keys() if cand+1 <= 15])
                
                if cand_list:
                    if cand_list in filtered_rankings:
                        filtered_rankings[cand_list] += rcounts[i]
                    else:
                        filtered_rankings[cand_list] = rcounts[i]
                
            filtered_ballot_list = [[value, list(key)] for key, value in filtered_rankings.items()]
            filtered_ballot_list.sort(key = lambda x: x[1])
            
            filtered_rows = [[str(len(cands_with_inds))+' '+str(seat_num)]]
            for ballot in filtered_ballot_list:
                string = str(ballot[0])
                for cand in ballot[1]:
                    string += ' '+str(cand)
                string += ' 0'
                filtered_rows.append([string])
            
            filtered_rows.append(['0'])
            
            for name in list(cands_with_inds.values())[:15]:
                filtered_rows.append([name])
            
            dash_indxs = [i for i in range(len(file_name)) if file_name[i]=='-']
            new_file_name = file_name[:max(dash_indxs)+1] + '15.csv'
            destination_path = destination_base + '_top_15/' + dataset +'/' + folder_name + '/' + new_file_name
            with open(destination_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(filtered_rows)
        
        



# # find different names between scotland and scotland condensed
# base_name = 'C:/Users/mijones/Documents/Datasets/ranked_ballots/Scotland condensed'
# for folder_name in os.listdir(base_name):
#     for file_name in os.listdir(base_name+'/'+folder_name):
#         if file_name not in os.listdir('C:/Users/mijones/Documents/Datasets/ranked_ballots/Scotland data processed'+'/'+folder_name):
#             print(folder_name+'/'+file_name)









###########
## stats about noncompetitive elections
###########

# base_name = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data/preference_profiles/'

# for country in os.listdir(base_name):
#     for lxn_type in os.listdir(base_name+'/'+country):
#         lxn_count = 0
#         lxn_noncompetitive = 0
#         for file in os.listdir(base_name+'/'+country+'/'+lxn_type):
#             lxn_count += 1
#             dash_indxs = [i for i in range(len(file)) if file[i]=='-']
#             seat_num = file[dash_indxs[-2]+1:dash_indxs[-1]]
#             cand_num = file[dash_indxs[-1]+1:file.index('.')]
            
#             if int(seat_num)>=int(cand_num):
#                 print(file)
#                 lxn_noncompetitive += 1









