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


top_cycle_elections = [
#                        'C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/w-duns22/Ward2-Leven_west dunbartonshire,2022,ward 2.csv',
#                        'C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/glasgow2007 preflib/govan_govan.csv',
#                        'C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/fife12-ballots/GlenrothesCentralAndThorntonWard_fife12-16.csv',
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/renfs12-ballots/7.JohnstoneSouthElderslie&HowwoodWard_renfs12-07.csv",
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/dumgal22/Ward3-DeeandGlenkens_ward3.csv",
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/argyll22/Ward2-KintyreandtheIslands_ward2.csv",
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/n-lanarks17-ballots/Ward4-CumbernauldEast_n-lanarks17-004.csv",
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/glasgow17-ballots/Ward21NorthEast_glasgow17-021.csv",
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/aberdeenshire22/preferenceprofile_v0001_ward-10-west-garioch_06052022_172124.csv",
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/dumgal12-ballots/AnnandaleNorthWard_dumgal12-12.csv",
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/angus22/Ward3-ForfarandDistrict_ward3.csv",
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/n-ayrshire12-ballots/Ward03-Kilwinning_n-ayrshire12-03.csv",
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/sc-borders12-ballots/JedburghandDistrictWard_sc-borders12-09.csv",
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland/angus12-ballots/ForfarandDistrict_angus12-03.csv",
#                        "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/america/Alameda County/Oakland_11082022_Schoolboarddistrict4.csv",
                       "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/america/Minneapolis/Minneapolis_11022021_CityCouncilWard2.csv"]
                       


###############################################################################
###############################################################################
##### parameters
election_group = 'scotland'
frac = 1
mp_pool_size = 6
###############################################################################
###############################################################################


american_ban_list = ['Easthampton_11022021_Mayor.csv',
                     'Oakland_11042014_Mayor.csv',
                     'Cambridge_11032009_CityCouncil.csv',
                     'Cambridge_11032015_CityCouncil.csv',
                     'Cambridge_11042003_CityCouncil.csv',
                     'Cambridge_11052013_CityCouncil.csv',
                     'Cambridge_11062001_CityCouncil.csv',
                     'Cambridge_11062007_CityCouncil.csv',
                     'Cambridge_11072017_CityCouncil.csv',
                     'Cambridge_11072017_SchoolCommittee.csv',
                     'Cambridge_11072023_CityCouncil.csv',
                     'Cambridge_11082005_CityCouncil.csv',
                     'Cambridge_11082011_CityCouncil.csv',
                     'Cambridge_11152019_CityCouncil.csv',
                     'Minneapolis_11022021_Mayor.csv',
                     'Minneapolis_11052013_Mayor.csv',
                     'Minneapolis_11072017_Mayor.csv',
                     'NewYorkCity_06222021_DEMCouncilMember26thCouncilDistrict.csv',
                     'PortlandOR_110524_Mayor.csv',
                     'Portland_D1_2024.csv',
                     'Portland_D2_2024.csv',
                     'Portland_D3_2024.csv',
                     'Portland_D4_2024.csv',
                     'SanFrancisco_11022004_BoardofSupervisorsDistrict5.csv',
                     'SanFrancisco_11022010_BoardofSupervisorsDistrict10.csv',
                     'SanFrancisco_11062007_Mayor.csv',
                     'SanFrancisco_11082011_Mayor.csv',
                     'Berkeley_11042014_CityAuditor.csv',
                     'Oakland_11062018_SchoolDirectorDistrict2.csv',
                     'Oakland_11082016_CityAttorney.csv',
                     'SanLeandro_11082016_CountyCouncilDistrict4.csv',
                     'SanLeandro_11082016_CountyCouncilDistrict6.csv',
                     'SanFrancisco_11052024_Treasurer.csv',
                     'SanFrancisco_11062018_PublicDefender.csv',
                     'SanFrancisco_11082022_AssessorRecorder.csv',
                     'SanFrancisco_11082022_BoardofSupervisorsD2.csv']


civs_ban_list = ['1a3300430c.csv',
                 '6072b2cf65.csv',
                 '7abc80f697.csv',
                 'e1cae49c22.csv',
                 'e20d8aeccc.csv',
                 'e3794bad55.csv',
                 'feb82581e0.csv']
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
    base_name = "C:/Users/mijones/Documents/Datasets/Ranked_Ballots/preference_profiles/scotland"

    lxn_count = 0
    # for folder_name in os.listdir(base_name):
    ## test folder in scotland
    for folder_name in ['s-lanarks17-ballots']:
    ## test folder in america
    # for folder_name in ['Portland, ME']:
        for file_name in os.listdir(base_name+'/'+folder_name):
            lxn_count += 1
            file_path = base_name+'/'+folder_name+'/'+file_name
            
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




    ## Only the elections with top cycles        
    # lxn_count = 0
    # for file_path in top_cycle_elections:
    #     if diagnostic:
    #         print(lxn_count, file_path)
    
    #     # sys.stdout.write('\r')
    #     # sys.stdout.write(f'Election {lxn_count}'+'         ')
    #     # sys.stdout.flush()
        
    #     File=open(file_path,'r', encoding='utf-8')
    #     lines=File.readlines()

    #     first_space=lines[0].find(' ')
    #     num_cands=int(lines[0][0:first_space])
    #     if num_cands>52:
    #         print("Cannot handle this many candidates in election " + str(file_path) + ".  Has " + 
    #               str(num_cands) + " candidates.")
    #         continue
            
    #     data = createBallotDF(lines)
        
    #     lxns.append([file_path, data, num_cands])

    return lxns
    




###############################################################################
###############################################################################
##### Run this code
###############################################################################
###############################################################################



cand_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
              'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
              'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
              'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

start_time = time.time()

print('##### Collecting election data #####')
lxn_list = get_election_data(election_group)

print(time.time()-start_time)


print('##### Searching for anomalies #####')
print('###################################')
# vote_methods = [IRV, smith_irv, Borda_PM, Borda_OM, Borda_AVG, minimax, smith_minimax, ranked_pairs, plurality, condorcet_plurality, plurality_runoff, bucklin]
# vote_methods = [minimax, minimax_fast]
# vote_methods = [IRV]

# for method in vote_methods:
    
    
start_time = time.time()
# print(method.__name__)

nums_times = []

anomaly_data = []
for i in range(len(lxn_list)):
# for i in range(2190, len(lxn_list)):
    
    # start_time = time.time()
    sys.stdout.write('\r')
    sys.stdout.write('\r')
    sys.stdout.write(f'Election {i+1}'+':' + lxn_list[i][0] + '                      ')
    sys.stdout.flush()
    
    lxn, profile, num_cands = lxn_list[i]
    
    lxn_start = time.time()
    
    cands = cand_names[:num_cands]
    print(TVR(profile, cands, 'OM'))
    
    # cands = cand_names[:num_cands]
    # # threshold = 0.05
    # for threshold in [0.01 * i for i in range(30)]:
    #     print(threshold, diversity_score_threshold(profile, cands, threshold, diagnostic=False))

        
print(time.time()-start_time)    
print(len(anomaly_data))
print('###################################')









