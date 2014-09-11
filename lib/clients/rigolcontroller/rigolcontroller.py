from common.lib.clients.qtui.QCustomFreqVoltage import QCustomFreqVoltage
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui

class rigolclient(QtGui.QWidget):
    


    def __init__(self, reactor, parent = None):
        """initializels the GUI creates the reactor  
        """   
        super(rigolclient, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor          
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection 
        """
        from labrad.wrappers import connectAsync
        from labrad.units import WithUnit as U
        self.U = U
        self.cxn = yield connectAsync(name = "rigol client")
        self.server = yield self.cxn.rigol_dg1022_server
        self.server.select_device(0)        
        self.initializeGUI()
        
    @inlineCallbacks
    def initializeGUI(self):  
    
        layout = QtGui.QGridLayout()
        
        qBox = QtGui.QGroupBox('Rigol DG1022')
        subLayout = QtGui.QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)         
        widget = QCustomFreqVoltage('Rep Rate Rigol') 
        widget.setVoltageRange((-5, 5))
        widget.setFreqRange((0, 40e6)) 
        widget.setVoltageNoSignal(0)
        widget.setFreqNoSignal(0)      
        widget.spinVoltage.valueChanged.connect(self.voltchanged)
        widget.spinFreq.valueChanged.connect(self.freqchanged)             
        subLayout.addWidget(widget) 
        self.setLayout(layout)
        yield None
        
    def voltchanged(self, value):
        value = self.U(value, 'V')
        self.server.amplitude(1, value)
        
    def freqchanged(self, value):
        value = self.U(value, 'Hz')
        self.server.frequency(1, value)
    
    def closeEvent(self, x):
        self.reactor.stop()
        
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    from common.lib.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    rigolWidget = rigolclient(reactor)
    rigolWidget.show()
    reactor.run()
