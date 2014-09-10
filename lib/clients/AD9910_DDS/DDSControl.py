from common.lib.clients.qtui.QCustomFreqPower import QCustomFreqPower
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui
#from common.lib.configuration_files.switch_client_config import switch_config
try:
    from config.DDS_client_config import DDS_config
except:
    from common.lib.config.DDS_client_config import DDS_config
    
class DDSclient(QtGui.QWidget):

    def __init__(self, reactor, parent = None):
        """initializels the GUI creates the reactor 
            and empty dictionary for channel widgets to 
            be stored for iteration. also grabs chan info
            from wlm_client_config file 
        """     
        super(DDSclient, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.d = {}
        self.connect()

    @inlineCallbacks    
    def connect(self):
        """Creates an Asynchronous connection to the wavemeter computer and
        connects incoming signals to relavent functions
        """
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name = "DDS client")
        self.server = yield self.cxn.ddsdeviceserver   
        self.chaninfo = DDS_config.info
        self.initializeGUI()
        
    @inlineCallbacks
    def initializeGUI(self):      
        layout = QtGui.QGridLayout()
        from labrad.units import WithUnit as U
        self.U = U
        qBox = QtGui.QGroupBox('DDS Control')
        subLayout = QtGui.QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)
        for chan in self.chaninfo:
            port = self.chaninfo[chan][0]
            position = self.chaninfo[chan][1]
            channel = self.chaninfo[chan][2]    
            widget = QCustomFreqPower(chan) 
            MinPower =  self.U(-63, 'dbm')
            MaxPower =  self.U(-1.17, 'dbm')
            MinFreq = self.U(0, 'MHz')
            MaxFreq = self.U(500, 'MHz')
            widget.setPowerRange((MinPower, MaxPower))
            widget.setFreqRange((MinFreq, MaxFreq))
            initpower = self.U(-63, 'dbm')
            initstate = False
            initfreq = self.U(161, 'MHz')
            widget.setStateNoSignal(initstate)
            widget.setPowerNoSignal(initpower)
            widget.setFreqNoSignal(initfreq)
            widget.spinPower.valueChanged.connect(lambda value =  widget.spinPower.value(), port = port, channel = channel: self.powerChanged(value, port, channel))
            widget.spinFreq.valueChanged.connect(lambda value = widget.spinFreq.value(), port = port, channel = channel : self.freqChanged(value, port, channel)) 
            widget.buttonSwitch.toggled.connect(lambda state = widget.buttonSwitch.isDown(), port = port, channel = channel : self.switchChanged(state, port, channel))
            
            self.d[port] = widget
            subLayout.addWidget(self.d[port], position[0], position[1])
        
        self.setLayout(layout)
        yield None
    
    @inlineCallbacks
    def powerChanged(self, value, port, chan):
        value = self.U(value, 'dbm')
        yield self.server.select_device(port)
        yield self.server.amplitude(chan, value)
        yield self.server.deselect_device()
        
    
    @inlineCallbacks
    def freqChanged(self, value, port, chan):
        value = self.U(value, 'MHz')
        yield self.server.select_device(port)
        yield self.server.frequency(chan, value)
        yield self.server.deselect_device()
        
    @inlineCallbacks
    def switchChanged(self, state, port, chan):
        yield self.server.select_device(port)
        yield self.server.output(chan, state)
        yield self.server.deselect_device()
        
    def closeEvent(self, x):
        self.reactor.stop()
        
        
        
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    from common.lib.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    DDSWidget = DDSclient(reactor)
    DDSWidget.show()
    reactor.run()
        
        
