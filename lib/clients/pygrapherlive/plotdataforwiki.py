import matplotlib.pyplot as plt
from PyQt4 import QtGui, QtCore
import os
import datetime
#import labrad
from numpy import array
from twisted.internet.defer import inlineCallbacks

class plotwikidata(QtGui.QWidget):
            
    def __init__(self, data, datadir, parent=None):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle('Wiki Client')
        self.datadir = datadir
        self.data = data
        self.timetag = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.labels =['Title', 'X_scale_min','X_scale_max','Y_scale_min',
                       'Y_scale_max','X_label','Y_label']
        self.xlabel = ''
        self.ylabel = ''
        self.title  = ''
        self.connect()
               
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name='Plot Wiki Data Client')
        self.dv = yield self.cxn.data_vault
        self.ws = yield self.cxn.wikiserver
        yield self.cxn.registry.cd(['','Servers', 'wikiserver'])
        self.maindir = yield self.cxn.registry.get('wikipath')
#        self.maindir = self.maindir[0] + '/'
        print self.maindir
        yield os.chdir(self.maindir)
        self.setupWidget()
        
    def setupWidget(self):
        self.setGeometry(300, 300, 500, 150)
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(5)
        self.labeldict = {}
        for i, label in enumerate(self.labels):
            self.labeldict[label] = QtGui.QLabel(self)
            self.labeldict[label].setText(label)
            self.grid.addWidget(self.labeldict[label]     ,i,0)
        
        self.textdict = {}    
        for i, label in enumerate(self.labels):
            self.textdict[label] = QtGui.QLineEdit(self)
            self.grid.addWidget(self.textdict[label]      ,i,1)
        
        self.commentbox = QtGui.QPlainTextEdit(self)
        
        self.gobutton = QtGui.QPushButton('GO!',self) 
        self.gobutton.clicked.connect(self.onbuttonpress)
        
        self.grid.addWidget(self.gobutton      ,1,2)
        self.grid.addWidget(self.commentbox    ,0,2)
        self.setLayout(self.grid)
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.setWindowTitle("Plot data for Wiki")
        self.show()
        
    def onbuttonpress(self):
        
        self.title     = self.textdict['Title'].text()
        self.xscalemin = self.textdict['X_scale_min'].text() 
        self.xscalemax = self.textdict['X_scale_max'].text()
        try:
            self.xlims = [float(self.xscalemin),float(self.xscalemax)]
        except: self.xlims = None
        self.yscalemin = self.textdict['Y_scale_min'].text()
        self.yscalemax = self.textdict['Y_scale_max'].text()
        try:
            self.ylims = [float(self.yscalemin),float(self.yscalemax)]
        except:
            self.ylims = None
        self.xlabel= self.textdict['X_label'].text()
        self.ylabel= self.textdict['Y_label'].text()
        self.comments = self.commentbox.toPlainText().split('/n')
        self.comments = str(self.comments[0])
        self.get_data()
    
    @inlineCallbacks     
    def get_data(self):
        
        yield self.dv.cd(self.datadir)
        yield self.dv.open(self.data)
        self.dataarray = yield self.dv.get()
        self.dataarray = self.dataarray.asarray
        self.plotdata(self.dataarray)
    @inlineCallbacks
    def plotdata(self, dataarray):
        plt.plot(dataarray[:,0],dataarray[:,1])
        plt.title(self.title)
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        if self.xlims != None:
            plt.xlim(self.xlims)
        if self.ylims != None:
            plt.ylim(self.ylims)
        print os.getcwd()
        plt.savefig(self.timetag)
        plt.show()
        yield self.ws.add_line_to_file( self.comments)
        yield self.ws.add_line_to_file( "##" + self.timetag + '[[' + self.timetag + '.png]]')
        yield self.ws.update_wiki()
        self.close()
#         if dirofcurrentday does not exist:
#             self.ws.adddir('current time')
#             self.saveplotindir
#             self.ws.addline('include file')
#         else:
#             self.saveplotindir
#             self.ws.addline('include file')
#         self.
#         self.fig = plt.figure()
#         self.ax = self.fig.add_subplot(111)
#         self.ax.set_title(self.title)
#         self.ax.plot(dataarray)
 #       self.ax.set_xlabel(self.xlabel + ' (' + self.xunits +')')
 #       self.ax.set_ylabel(self.ylabel + ' (' + self.yunits +')')
 
    def closeEvent(self, x):
        self.cxn.disconnect()
#        self.reactor.stop()
        
        