#!/usr/bin/python
from PyQt4 import QtGui
import sys
import os
import time

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
        starttime = currenttime - 12*30*24*3600
        self.sendData(starttime)
        
    def sendData(self, starttime):
        print "send data"

                
    def getepochtime(self, date):
        '''
        takes date format YYYY-MM-DD
        '''
        eptime = time.mktime(time.strptime(date, "%Y-%m-%d"))
        return eptime
        
    
    
    
if __name__ == "__main__":
    a = QtGui.QApplication(sys.argv)
    tempWidget = TemperatureMonitor()
    tempWidget.show()
    sys.exit(a.exec_())