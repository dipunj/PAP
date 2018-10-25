from utilities import *

def main(verbose):
    mPref,wPref = getPreference("men.txt","women.txt")
    hungarian = getHungarian(mPref,wPref)

    # now the problem is a balanced assignment problem
    # the value in the hungarian matrix represents the cost/preference for each other

    # lower the value, lower the cost of marriage

    hungarian_method_result = hung_method(hungarian)
    gale_Shapely_result = stable(mPref,wPref)

    if verbose == True:
        print("Original Preference for men:")
        for m,pref in mPref.items():
            print("{:>10} :: {}".format(m,",".join(pref)))

        print("Original Preference for women:")
        for w,pref in wPref.items():
            print("{:>10} :: {}".format(w,",".join(pref)))

        print("\nFrom hungarian                                From Gale-Shapely")
        for (m_h,w_h),(m_gs,w_gs) in zip(hungarian_method_result,gale_Shapely_result):
            print("{:>10} <-> {:<10}                {:>10} <-> {:<10}".format(m_h,w_h,m_gs,w_gs))

        # print("Matched results")
        # for m,w in [x for x in hungarian_method_result if x in gale_Shapely_result]:
        #     print("{:>30} <-> {:<30}".format(m,w))
    else:
        print("The result obtained from hungarian algorithm is ")
    
    if isStable(hungarian_method_result,mPref,wPref):
        print("STABLE")
    else:
        print("NOT STABLE")

    print("The cost is :")
    print("HUNGARIAN METHOD : ",getCost(hungarian,hungarian_method_result))
    print("GALE SHAPELY METHOD : ",getCost(hungarian,gale_Shapely_result))


if __name__ == '__main__':
    main(True)