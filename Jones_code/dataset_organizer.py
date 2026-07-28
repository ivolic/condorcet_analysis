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
##### Scotland
######################################################
# name_list = []

# council_list = []
# year_list = []
# ward_list = []
# cand_list = []
# seat_list = []

# council_names = {
#     'aberdeen': 'Aberdeen_City',
#     'aberdeenshire': 'Aberdeenshire',
#     'angus': 'Angus',
#     'argyll-bute': 'Argyll_and_Bute',
#     'clackmannanshire': 'Clackmannanshire',
#     'dumgal': 'Dumfries_and_Galloway',
#     'dundee': 'Dundee_City',
#     'e-ayrshire': 'East_Ayrshire',
#     'e-duns': 'East_Dunbartonshire',
#     'e-lothian': 'East_Lothian',
#     'e-renfs': 'East_Renfrewshire',
#     'edinburgh': 'City_of_Edinburgh',
#     'falkirk': 'Falkirk',
#     'fife': 'Fife',
#     'glasgow': 'Glasgow_City',
#     'highland': 'Highland',
#     'inverclyde': 'Inverclyde',
#     'midlothian': 'Midlothian',
#     'moray': 'Moray',
#     'eilean-siar': 'Eilean_Siar',
#     'n-ayrshire': 'North_Ayrshire',
#     'n-lanarks': 'North_Lanarkshire',
#     'orkney': 'Orkney Islands',
#     'perth-kinross': 'Perth_and_Kinross',
#     'renfs': 'Renfrewshire',
#     'sc-borders': 'Scottish_Borders',
#     'shetland': 'Shetland Islands',
#     's-ayrshire': 'South_Ayrshire',
#     's-lanarks': 'South_Lanarkshire',
#     'stirling': 'Stirling',
#     'w-duns': 'West_Dunbartonshire',
#     'w-lothian': 'West_Lothian'
#     }
# years = {
#     '07': '2007',
#     '12': '2012',
#     '17': '2017',
#     '22': '2022',
#     '24': '2024'
#     }

# base_name = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_clean/old_data_files/Scotland data'
# new_base = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_clean/Scotland'

# for folder_name in os.listdir(base_name):
#     for file_name in os.listdir(base_name+'/'+folder_name):
#         sys.stdout.write('\r')
#         sys.stdout.write(f'Election {len(name_list)+1}'+'         ')
#         sys.stdout.flush()
        
#         file_path = base_name + '/' + folder_name + '/' + file_name
#         name_list.append(folder_name + '/' + file_name)
        
#         if 'by-elections' not in folder_name:
#             council = council_names[folder_name[:folder_name.index('.')]]
#             year = years[folder_name[folder_name.index('.')+1:]]
#             if file_name[:4] == 'Ward':
#                 if file_name[5] in [str(x) for x in range(10)]:
#                     ward_num = file_name[4:6]
#                 else:
#                     ward_num = '0'+file_name[4]
#             else:
#                 if file_name[-6] not in ['d','-']:
#                     ward_num = file_name[-6:-4]
#                 else:
#                     ward_num = '0' + file_name[-5]
#         else:
#             council = council_names[file_name[file_name.index('_')+1:file_name.index(' ')]]
#             year = file_name[file_name.index('20'):file_name.index('20')+4]
#             if file_name[5] != '-':
#                 ward_num = file_name[4:6]
#             else:
#                 ward_num = '0'+file_name[4]
                
#         num_ranks = get_num_ranks(file_path)
#         seats, cands = get_info(file_path)
#         seat_num = str(seats)
#         cand_num = str(cands)
        
#         council_list.append(council)
#         year_list.append(year)
#         ward_list.append(ward_num)
#         seat_list.append(seat_num)
#         cand_list.append(cand_num)
    
#         new_name = council+'-Ward'+ward_num+'-'
#         if 'by-election' in file_path:
#             new_name += 'byelection-'
#         new_name += year+'-'+seat_num+'-'+cand_num+'.csv'
    
#         # print(new_name)
        
#         if seat_num == '1':
#             shutil.copy(file_path, new_base+'/single_winner/'+new_name)
#         else:
#             shutil.copy(file_path, new_base+'/multi_winner/'+new_name)




# ######################################################
# ###### America
# ######################################################

# name_list = []

# cand_list = []
# seat_list = []

# base_name = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_clean/old_data_files/American data'
# new_base = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_clean/America'

# for folder_name in os.listdir(base_name):
#     for file_name in os.listdir(base_name+'/'+folder_name):
#         sys.stdout.write('\r')
#         sys.stdout.write(f'Election {len(name_list)+1}'+'         ')
#         sys.stdout.flush()
        
#         file_path = base_name + '/' + folder_name + '/' + file_name
#         name_list.append(folder_name + '/' + file_name)
        

#         num_ranks = get_num_ranks(file_path)
#         seats, cands = get_info(file_path)
#         seat_num = str(int(seats))
#         cand_num = str(int(cands))
        
#         seat_list.append(seat_num)
#         cand_list.append(cand_num)
#         # print(seat_num, cand_num)

#         if folder_name == 'APA':
#             new_name = file_name.replace(' ', '-')
        
#         elif folder_name == 'Alameda County':
#             new_name = 'Alameda_County_'+file_name.replace('_', '-')
#         elif folder_name == 'New Mexico':
#             new_name = 'New_Mexico_'+file_name.replace('_', '-').replace('sC', 's_C').replace('aF', 'a_F')
#         elif folder_name == 'Utah cities':
#             new_name = 'Utah_Cities_'+file_name.replace('_', '-')

#         elif ', ' in folder_name:
#             new_name = folder_name.replace(', ', '_').replace(' ', '_') + '-' + file_name[file_name.index('_')+1:].replace('_', '-')

#         elif folder_name == 'New York City':
#             new_name = file_name.replace('_','-').replace('NewYorkCity', 'New_York_City')
#         elif folder_name == 'San Francisco':
#             new_name = file_name.replace('_','-').replace('SanFrancisco', 'San_Francisco')
#         elif folder_name == 'St Louis Park':
#             new_name = file_name.replace('_','-').replace('StLouisPark', 'St_Louis_Park')

#         else:
#             new_name = file_name.replace('_', '-')
#         # print(new_name)
        
#         new_name = new_name[:-4]
#         new_name += '-'+seat_num+'-'+cand_num+'.csv'

#         if seat_num == '1':
#             shutil.copy(file_path, new_base+'/single_winner/'+new_name)
#         else:
#             shutil.copy(file_path, new_base+'/multi_winner/'+new_name)







######################################################
###### Australia
######################################################

name_list = []

cand_list = []
seat_list = []


# ## Andrew Conway data
# base_name = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_clean/old_data_files/Australia STV full data'
# new_base = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_clean/Australia'

# for folder_name in os.listdir(base_name):
#     for file_name in os.listdir(base_name+'/'+folder_name):
#         sys.stdout.write('\r')
#         sys.stdout.write(f'Election {len(name_list)+1}'+'         ')
#         sys.stdout.flush()
        
#         file_path = base_name + '/' + folder_name + '/' + file_name
#         name_list.append(folder_name + '/' + file_name)
        

#         num_ranks = get_num_ranks(file_path)
#         seats, cands = get_info(file_path)
#         seat_num = str(int(seats))
#         cand_num = str(int(cands))
        
#         seat_list.append(seat_num)
#         cand_list.append(cand_num)
#         # print(seat_num, cand_num)
            
            
#         if 'Federal' in file_name:
#             new_name = 'Federal_Senate-' + file_name[15:19] + '-' + file_name[20:file_name.index(',')]
        
#         elif 'Legislative_Council' in file_name:
#             new_name = 'State_Leg_Council-' + file_name[24:28] + '-NSW'
            
#         elif 'Mayoral' in file_name:
#             new_name = 'Mayoral-' + file_name[21:25] + '-NSW-' + file_name[26:file_name.index('_Mayoral')]
            
#         else:
#             new_name = 'Local_Council-' + file_name[21:25] + '-NSW-' + file_name[26:file_name.index(',')].replace('_-','')
        
#         # print(new_name)
        
#         new_name += '-'+seat_num+'-'+cand_num+'.csv'

#         if seat_num == '1':
#             shutil.copy(file_path, new_base+'/single_winner/'+new_name)
#         else:
#             shutil.copy(file_path, new_base+'/multi_winner/'+new_name)


## David data
base_name = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_clean/old_data_files/Australia data'
new_base = 'C:/Users/mijones/Documents/Datasets/ranked_ballot_data_clean/Australia'

for folder_name in os.listdir(base_name):
    if 'Mayorals' in folder_name:
        continue
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
        
        if 'ByElections' in folder_name:
            year = '20'+file_name[2:4]
        else:
            year = folder_name[-4:]
            
        if 'Victoria' in folder_name:
            state = 'VIC'
        else:
            state = 'NSW'
            
        if '2015' in folder_name or 'ByElections' in folder_name:
            area = file_name[file_name.index('NA_')+3:-4].replace(' ','_')
        elif '2019' in folder_name or '2023' in folder_name:
            area = file_name[file_name.index('Data ')+5:-4].replace(' ','_')
        else:
            if '2018' in folder_name:
                area = 'Melbourne'
            else:
                area = file_name[file_name.index('-')+1:file_name.index(' with')].replace(' ','_')
        
        new_name = 'State_Leg_Assembly-'+year+'-'+state+'-'+area
        
        if 'ByElections' in folder_name:
            new_name += '-byelection'
        
        # print(new_name)
        
        new_name += '-'+seat_num+'-'+cand_num+'.csv'

        if seat_num == '1':
            shutil.copy(file_path, new_base+'/single_winner/'+new_name)
        else:
            shutil.copy(file_path, new_base+'/multi_winner/'+new_name)

