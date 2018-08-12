import utilities
import pandas as pd


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


print("Original Preference :")
for m,pref in mPref.items():
    print("{:>10} :: {}".format(m,",".join(pref)))


print("From hungarian")
for m,w in utilities.hung_method(hungarian):
    print("{:>30}<->{:<30}".format(m,w))

print("From Gale-Shapely")
for m,w in utilities.stable(mPref,wPref):
    print("{:>30}<->{:<30}".format(m,w))