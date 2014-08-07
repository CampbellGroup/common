from common.lib.clients.qtui.switch import QCustomSwitchChannel
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui
#from common.lib.configuration_files.switch_client_config import switch_config
try:
    from config.switch_client_config import switch_config
except:
    from common.lib.config.switch_client_config import switch_config

class switchclient(QtGui.QWidget):
    


    def __init__(self, reactor, parent = None):
        """initializels the GUI creates the reactor 
            and empty dictionary for channel widgets to 
            be stored for iteration. also grabs chan info
            from wlm_client_config file 
        """ 
            
        super(switchclient, self).__init__()
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
        self.cxn = yield connectAsync(name = "switch client")
        self.server = yield self.cxn.arduinottl   
        self.reg = yield self.cxn.registry
        try:
            yield self.reg.cd('settings')
            self.settings = yield self.reg.dir()
            self.settings = self.settings[1]
        except:
            self.settings = []
  
        self.chaninfo = switch_config.info       
        self.initializeGUI()
        
    @inlineCallbacks
    def initializeGUI(self):  
    
        layout = QtGui.QGridLayout()
        
        qBox = QtGui.QGroupBox('Laser Shutters')
        subLayout = QtGui.QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)
        
        for chan in self.chaninfo:
            port     = self.chaninfo[chan][0]
            position = self.chaninfo[chan][1]
            inverted = self.chaninfo[chan][2]
            
            widget = QCustomSwitchChannel(chan)  
            if chan + 'shutter' in self.settings:
                value = yield self.reg.get(chan + 'shutter')
                widget.TTLswitch.setChecked(value)
            else:
                widget.TTLswitch.setChecked(False)
                
            widget.TTLswitch.toggled.connect(lambda state = widget.TTLswitch.isDown(), port = port, chan = chan  : self.changeState(state, port, chan))            
            self.d[port] = widget
            subLayout.addWidget(self.d[port])
        
        self.setLayout(layout)
        yield None
        
    @inlineCallbacks
    def changeState(self, state, port, chan):
        yield self.server.ttl_output(port, state)
        if chan + 'shutter' in self.settings:
            yield self.reg.set(chan + 'shutter', state)

    def closeEvent(self, x):
        self.reactor.stop()
        
        
        
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    from common.lib.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    switchWidget = switchclient(reactor)
    switchWidget.show()
    reactor.run()
        
        