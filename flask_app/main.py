from utilities import *

def getStableRelations(men_file,women_file):
    
    mPref,wPref = getPreference(men_file,women_file)
    gale_Shapely_result = stable(mPref,wPref)

    return dict(gale_Shapely_result)



# for debugging purposes
if __name__ == '__main__':
    print(getStableRelations("men.json","women.json"))