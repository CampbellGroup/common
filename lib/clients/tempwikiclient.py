#!/usr/bin/python
from PyQt4 import QtGui
import sys
import os
import time
import urllib2
from matplotlib import pyplot as plt
from matplotlib import dates, ticker
import numpy as np

        
currenttime = time.time()
starttime = currenttime - 24*3600
try:
    urllib2.urlopen("http://10.97.112.13/temp/temperaturewebsite.py/?startTime=" + str(starttime))
except:
    pass
data = urllib2.urlopen("http://10.97.112.13/tempdata/")
data = data.read()
data = data.split()
data2 = []
for kk in  xrange(len(data)):
    a = data[kk].split(',')
    data2.append( [float(a[0]), float(a[1]),float(a[2]),float(a[3]),float(a[4])] )

data2 = np.array(data2)
data2 = data2[data2[:,4].argsort()]
data3 = []
for kk in xrange(len(data2)):
    if data2[kk, 4] >= starttime:
        for i in range(4):
            if data2[kk,i] >= 150:
                data2[kk,i] = 150
            elif data2[kk, i] <= 40:
                data2[kk, i] = 40
        data3.append(data2[kk])
fig, ax = plt.subplots()
data3 = np.array(data3)
linewidth = 3
ax.plot(data3[:,4], data3[:,0], lw = linewidth, label = "Duckberg")
ax.plot(data3[:,4], data3[:,1], lw = linewidth,label = "Ion Table")
ax.plot(data3[:,4], data3[:,2], lw = linewidth,label = "AC Inlet")
ax.plot(data3[:,4], data3[:,3], lw = linewidth,label = "Molecule Table")
a = ax.get_xticks().tolist()
for i, tick in enumerate(a):
    a[i] = time.strftime("%a, %H:%M", time.localtime(a[i]))
ax.set_xticklabels(a, fontsize = 10)
ax.set_ylabel(r"Temperature ( $^\circ F$ )")
ax.set_title("Campbell Lab Temperature")
ticker.FixedLocator(5)
plt.xticks(rotation=30)
#ax.legend(loc=0,  fancybox=True, shadow=True)
plt.savefig('last24temp.jpg')
plt.show()
    
    
