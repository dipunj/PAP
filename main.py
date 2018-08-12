import pandas as pd
import numpy as np

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



# def phase2(matrix,rows):


def hung_method(df: pd.DataFrame) -> list:
    """Applies hungarian method to minimize the overall cost
    
    Args:
        df (pd.DataFrame): cells contain the cost at cell(r,c), lower the cost, higher the preference for the pair(r,c)
    
    Returns:
        list: a list of tuples (pairs) of (man,woman)
    """

    # phase 1: row reduction
    df = df.subtract(df.min(axis=1),axis=0)
    matrix = df.values    

    # now df has atleast one zero per row


    marked_zeros = 0
    marked_cols = set()
    # row scanning
    for row_num,row in enumerate(matrix):
        zero_cols = np.where(np.delete(row,list(marked_cols)) == 0)[0]
        # print(row_num,np.delete(row,marked_cols))
        if len(zero_cols) == 1:
            original_row_zeros = np.where(row == 0)[0]
            marked_cols.update(original_row_zeros)
            
            marked_zeros += 1

    if len(marked_cols) == num_rows:
        return matrix


    # column reduction
    df = df.subtract(df.min(axis=0),axis=1)


    # phase 2: optimisation
    num_rows = len(df.index)

    # iterations,result_matrix,pairs = phase2(matrix,num_rows)

    iteration_count = 0
    marked_zeros = 0

    while marked_zeros != num_rows:

        marked_zeros = 0
        marked_cols = set()
        marked_rows = set()

        # row scanning
        for row_num,row in enumerate(matrix):
            zero_cols = np.where(np.delete(row,list(marked_cols)) == 0)[0]
            # print(row_num,np.delete(row,marked_cols))
            if len(zero_cols) == 1:

                original_row_zeros = np.where(row == 0)[0]
                marked_cols.update(original_row_zeros)
                
                marked_zeros += 1

        unassigned_cols = [x for x in list(range(num_rows)) if x not in marked_cols]
        
        if np.sum(matrix[unassigned_cols] == 0) != 0:
        
        # every man doesn't get atleast one woman
        # if len(marked_cols) != num_rows:

            # attempt col scanning
            for col_num,col in enumerate(matrix.transpose()):
            
                if col_num not in marked_cols:
                    zero_rows = np.where(np.delete(col,list(marked_rows)) == 0)[0]

                    if len(zero_rows) == 1:

                        original_col_zeros = np.where(col == 0)[0]
                        marked_rows.update(original_col_zeros)
                
                        marked_zeros += 1


        
        unassigned_rows = [x for x in list(range(num_rows)) if x not in marked_rows]
        
        unmarked_matrix = matrix[unassigned_rows].T[unassigned_cols].T

        # print("\n\n==========")
        # print(marked_rows,marked_cols)
        # print(iteration_count,marked_zeros)
        # print(unmarked_matrix)
        # print("\n\n---------")
        # print(matrix)
        # print("\n\n==========")
        # assert(np.sum(unmarked_matrix == 0) == 0)
        # diagonal rule
        # if np.sum(unmarked_matrix == 0) != 0:
            

        # optimality not reached
        if marked_zeros < num_rows:
            unmarked_min = unmarked_matrix.min()

            # increase the value of intersections by min
            for r in marked_rows:
                matrix[r] += unmarked_min
            
            matrix = matrix.T
            for c in marked_cols:
                matrix[c] += unmarked_min

            matrix = matrix.T
            matrix -= unmarked_min
        
        iteration_count += 1
