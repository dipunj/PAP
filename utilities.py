import pandas as pd
import numpy as np
from scipy.optimize import linear_sum_assignment
from itertools import product


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

def stable(mPref,wPref):
    """returns a stable set of marriages for given preference between men and women
    
    Args:
        mPref (dict): list of preferences of women for each man
        wPref (dict): list of preferences of men for each woman
    
    Returns:
        list: list of tuples, where each tuple represents a pair
    """

    men = mPref.keys()
    women = wPref.keys()
    n = len(men)
    
    rankings = dict( ((i, j+1), mPref[i][j]) for (i, j) in product(men, range(0,n)))
    rankings.update(dict( ((i, j+1), wPref[i][j]) for (i, j) in product(women, range(0,n))))
    partners = dict((m, (rankings[(m, 1)], 1)) for m in men)

    is_stable = False # whether the current pairing (given by `partners`) is stable
    while is_stable == False:
        is_stable = True
        for w in women:
            is_paired = False # whether w has m pair which w ranks <= to n
            for n in range(1, n + 1):
                m = rankings[(w, n)]
                a_partner, a_n = partners[m]
                if a_partner == w:
                    if is_paired:
                        is_stable = False
                        partners[m] = (rankings[(m, a_n + 1)], a_n + 1)
                    else:
                        is_paired = True
    return sorted((m, w) for (m, (w, n)) in partners.items())


def getPreference(men_file,women_file):
    
    mPref = {}
    wPref = {}

    with open(men_file) as f:
        for line in f:
           (key, val) = line.split(':')
           mPref[key.strip()] = [i.strip() for i in val.split(',')]


    with open(women_file) as f:
        for line in f:
           (key, val) = line.split(':')
           wPref[key.strip()] = [i.strip() for i in val.split(',')]
    
    return mPref,wPref

def getHungarian(mPref,wPref):

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

    return hungarian