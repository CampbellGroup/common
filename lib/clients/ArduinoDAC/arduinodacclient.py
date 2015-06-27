from common.lib.clients.qtui.QCustomSpinBox import QCustomSpinBox
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui
try:
    from config.arduino_dac_config import arduino_dac_config
except:
    from common.lib.config.arduino_dac_config import arduino_dac_config

class dacclient(QtGui.QWidget):
    
    def __init__(self, reactor, parent = None):
        """initializels the GUI creates the reactor 
            and empty dictionary for channel widgets to 
            be stored for iteration. 
        """ 
            
        super(dacclient, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor     
        self.d = {}     
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection 
        
        """
        from labrad.wrappers import connectAsync
	from labrad.units import WithUnit as U
	self.U = U
        self.cxn = yield connectAsync(name = "dac client")
        self.server = yield self.cxn.arduinodac   
        self.reg = yield self.cxn.registry
        try:
            yield self.reg.cd('settings')
            self.settings = yield self.reg.dir()
            self.settings = self.settings[1]
        except:
            self.settings = []
  
        self.dacinfo = arduino_dac_config.info       
        self.initializeGUI()
        
    @inlineCallbacks
    def initializeGUI(self):  
    
        layout = QtGui.QGridLayout()
        
        qBox = QtGui.QGroupBox('DAC Channels')
        subLayout = QtGui.QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)
        
        for dac in self.dacinfo:
            name     = self.dacinfo[dac][0]
            dacchan  = self.dacinfo[dac][1]
            
            widget = QCustomSpinBox(name, (-15, 15))  
            if name + 'dac' in self.settings:
                value = yield self.reg.get(name + 'dac')
                widget.spinLevel.setValue(value)
            else:
                widget.spinLevel.setValue(0.0)    
            widget.spinLevel.valueChanged.connect(lambda value = widget.spinLevel.value(), ident=[name,dacchan] :self.setvalue(value, ident))            
            self.d[dacchan] = widget
            subLayout.addWidget(self.d[dacchan])
        
        self.setLayout(layout)
        yield None
        
    @inlineCallbacks
    def setvalue(self, value, ident):
	chan = ident[1]
	name = ident[0]
	value = value/5.0
	yield self.server.dacoutput(chan, self.U(value, 'V'))    
	#yield self.reg.set(name + 'dac', value)

    def closeEvent(self, x):
        self.reactor.stop()
        
        
        
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    from common.lib.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    dacWidget = dacclient(reactor)
    dacWidget.show()
    reactor.run()
        
        
