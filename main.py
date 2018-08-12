import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment

mPref = {}
wPref = {}

with open("men.txt") as f:
    for line in f:
       (key, val) = line.split(':')
       mPref[key.strip()] = [i.strip() for i in val.split(',')]


with open("women.txt") as f:
    for line in f:
       (key, val) = line.split(':')
       wPref[key.strip()] = [i.strip() for i in val.split(',')]


women = sorted(list(wPref.keys()))
men = sorted(list(mPref.keys()))


hungarian = pd.DataFrame(0,index=men,columns=women)
the_max = -float('inf')

for m in men:
    for w in women:
        men_rank = 10 - mPref[m].index(w)
        wom_rank = 10 - wPref[w].index(m)
        val = men_rank**2 + wom_rank**2
        the_max = max(the_max,val)
        hungarian.loc[m,w] = val

hungarian = the_max - hungarian

# now the problem is a balanced assignment problem
# the value in the hungarian matrix represents the cost/preference for each other



def hung_method(df: pd.DataFrame) -> list:
    """Applies hungarian method to minimize the overall cost
    
    Args:
        df (pd.DataFrame): cells contain the cost at cell(r,c), lower the cost, higher the preference for the pair(r,c)
    
    Returns:
        list: a list of tuples (pairs) of (man,woman)
    """

    # phase 1: row reduction

    matrix = df.values
    result = []
    m,w = linear_sum_assignment(matrix)
    for m_indx,w_indx in zip(m,w):
        man = df.index[m_indx]
        woman = df.columns[w_indx]
        result.append((man,woman))
    
    return result

print(hung_method(hungarian))