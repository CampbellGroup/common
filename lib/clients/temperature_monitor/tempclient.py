#!/usr/bin/python
from PyQt4 import QtGui
import sys
import os
import time
import urllib2
from matplotlib import pyplot as plt
from matplotlib import dates, ticker
import numpy as np

class TemperatureMonitor(QtGui.QWidget):
    
    def __init__(self):
        super(TemperatureMonitor, self).__init__()
        self.initializeGUI()
    
    def initializeGUI(self):
        '''Initializes GUI
        '''
        self.setGeometry(400, 150, 350, 550)
        self.setWindowTitle('Temperature Monitor')
        layout = QtGui.QGridLayout()
        from matplotlib import pyplot as plt
        onehourbutton = QtGui.QPushButton('Show Last Hour')
        twohourbutton = QtGui.QPushButton('Show Last Two Hours')
        lastdaybutton = QtGui.QPushButton('Show Last 24 Hours')
        lasttwodaybutton   = QtGui.QPushButton('Show Last 48 Hours')
        lastmonthbutton = QtGui.QPushButton('Show Last Month')
        alldatabutton = QtGui.QPushButton('Show All')
        
        onehourbutton.clicked.connect(self.onehour)
        twohourbutton.clicked.connect(self.twohour)
        lastdaybutton.clicked.connect(self.lastday)
        lasttwodaybutton.clicked.connect(self.lasttwoday)
        lastmonthbutton.clicked.connect(self.lastmonth)
        alldatabutton.clicked.connect(self.alltime)
        
        layout.addWidget(onehourbutton    ,0,0)
        layout.addWidget(twohourbutton    ,1,0)
        layout.addWidget(lastdaybutton    ,2,0)
        layout.addWidget(lasttwodaybutton,3,0)
        layout.addWidget(lastmonthbutton  ,4,0)
        layout.addWidget(alldatabutton    ,5,0)
        
        self.setLayout(layout)
        
        
        
    '''
    The following functions grab the epoch time that occured the respective amounts of time ago...
    '''   
    def onehour(self):
        currenttime = time.time()
        starttime = currenttime - 3600
        self.sendData(starttime)
        
    def twohour(self):
        currenttime = time.time()
        starttime = currenttime - 2*3600
        self.sendData(starttime)
        
    def lastday(self):
        currenttime = time.time()
        starttime = currenttime - 24*3600
        self.sendData(starttime)
        
    def lasttwoday(self):
        currenttime = time.time()
        starttime = currenttime - 2*24*3600
        self.sendData(starttime)

    def lastmonth(self):
        currenttime = time.time()
        starttime = currenttime - 30*24*3600
        self.sendData(starttime)
        
    def alltime(self):
        currenttime = time.time()
        starttime = 1406403721
        self.sendData(starttime)
        
    def sendData(self, starttime):
        #for some reason webpage gives 500 error but still calls python script
        try:
            urllib2.urlopen("http://10.97.112.13/temp/temperaturewebsite.py/?startTime=" + str(starttime))
            print "got data"
            self.plot()
        except:
            self.plot(starttime)
            print "except"
                
    def plot(self, starttime):
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
        plt.ion()
        fig, ax = plt.subplots()
        data3 = np.array(data3)
        linewidth = 3
        ax.plot(data3[:,4], data3[:,0], lw = linewidth, label = "Duckberg")
        ax.plot(data3[:,4], data3[:,1], lw = linewidth,label = "Ion Table")
        ax.plot(data3[:,4], data3[:,2], lw = linewidth,label = "AC Inlet")
        ax.plot(data3[:,4], data3[:,3], lw = linewidth,label = "Molecule Table")
        a = ax.get_xticks().tolist()
        for i, tick in enumerate(a):
            a[i] = time.strftime("%a, %d %b %Y %H:%M", time.localtime(a[i]))
        ax.set_xticklabels(a)
        ax.set_ylabel(r"Temperature ( $^\circ F$ )")
        ax.set_title("Campbell Lab Temperature")
        ticker.FixedLocator(5)
        plt.xticks(rotation=30)
        ax.legend()
#        plt.show()
    
if __name__ == "__main__":
    a = QtGui.QApplication([])
    tempWidget = TemperatureMonitor()
    tempWidget.show()
    sys.exit(a.exec_())
    
    
