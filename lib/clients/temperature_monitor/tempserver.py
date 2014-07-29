import os 
import time
import sys
def getepochtime(date):
    '''
    takes date format YYYY-MM-DD
    '''
    eptime = time.mktime(time.strptime(date, "%Y-%m-%d"))
    return float(eptime)

def getFiles(starttime):
    storefile = open("test_tempserver.dat2", 'a+')
    for dirpath, dirnames, filenames in os.walk("."):
        for filename in [f for f in filenames if (f.endswith(".dat") and (getepochtime(f[0:-9]) + 24*3600 >= float(starttime)))]:
            path = os.path.join(dirpath, filename) 
            storefile.write(path + "_")
#    for dirpath, dirnames, filedata in os.walk("."):
#        for fileset in filedata:
#            for filename in fileset:
#                if filename.endswith(".dat") and (getepochtime(filename[0:-9]) >= float(starttime)):
#                    path = os.path.join(dirpath, filename) 
#                    storefile.write(path + "_")

def main(starttime):
    starttime = starttime[1]
    getFiles(starttime)
    
if __name__ == "__main__":
    main(sys.argv)
    