###################################################
##### For every election, check if a voter bloc is 
##### able to create a condorcet cycle using
##### truncation or burying
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
import ast

from election_class import *
from ballot_modifications_class import *