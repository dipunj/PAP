from utilities import *


def main():
    mPref,wPref = getPreference("men.txt","women.txt")
    hungarian = getHungarian(mPref,wPref)

    # now the problem is a balanced assignment problem
    # the value in the hungarian matrix represents the cost/preference for each other

    # lower the value, lower the cost of marriage

    print("Original Preference for men:")
    for m,pref in mPref.items():
        print("{:>10} :: {}".format(m,",".join(pref)))
    
    print("Original Preference for women:")
    for w,pref in wPref.items():
        print("{:>10} :: {}".format(w,",".join(pref)))
    

    print("From hungarian")
    hungarian_method_result = hung_method(hungarian)
    for m,w in hungarian_method_result:
        print("{:>30} <-> {:<30}".format(m,w))

    print("From Gale-Shapely")
    gale_Shapely_result = stable(mPref,wPref)
    for m,w in gale_Shapely_result:
        print("{:>30} <-> {:<30}".format(m,w))

    print("Matched results")
    for m,w in [x for x in hungarian_method_result if x in gale_Shapely_result]:
        print("{:>30} <-> {:<30}".format(m,w))
if __name__ == '__main__':
    main()