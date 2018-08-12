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