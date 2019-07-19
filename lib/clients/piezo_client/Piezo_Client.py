from common.lib.clients.qtui.switch import QCustomSwitchChannel
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui
#import the config so you can name the channels
try:
    from config.piezo_client_config import piezo_config
except:
    from common.lib.config.piezo_client_config import piezo_config

class Piezo_Client(QtGui.QWidget):
    
    def __init__(self, reactor, parent = None):      
        super(Piezo_Client, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name = "Piezo Client")
        self.server = self.cxn.piezo_server
        self.reg = self.cxn.registry
        yield self.reg.cd(['', 'settings'])
        from labrad.units import WithUnit as U
        self.U = U
        self.initializeGUI()

    @inlineCallbacks
    def initializeGUI(self):  
        layout = QtGui.QGridLayout()
        initial_remote_setting = yield self.server.remote_mode()
        remote_button = QCustomSwitchChannel('Remote Mode', ('On', 'Off'))
        remote_button.TTLswitch.setChecked(int(initial_remote_setting))
        remote_button.TTLswitch.toggled.connect(lambda state=remote_button.TTLswitch.isDown():
                                                self.on_remote_toggled(state))
        layout.addWidget(remote_button, 0, 0) #puts remote button at top left
        channel_info = piezo_config.info
                
        for key in channel_info:
            initial_channel_setting = yield self.server.output_channel(channel_info[key][0])
            initial_voltage_list = yield self.server.set_voltage(channel_info[key][0])
            initial_voltage = float(initial_voltage_list[1])
            chan_button = QCustomSwitchChannel(key, ('On', 'Off'))
            chan_button.TTLswitch.setChecked(int(initial_channel_setting[1]))
            chan_button.TTLswitch.toggled.connect(lambda state=chan_button.TTLswitch.isDown(),
                                                  chan= channel_info[key][0]: self.on_chan_toggled(chan, state))
            voltage_spin_box = QtGui.QDoubleSpinBox()
            voltage_spin_box.setRange(0.0, 150.0)
            voltage_spin_box.setSingleStep(0.1)
            voltage_spin_box.setDecimals(3)
            voltage_spin_box.setValue(initial_voltage)
            voltage_spin_box.setKeyboardTracking(False)
            voltage_spin_box.valueChanged.connect(lambda volt=voltage_spin_box.value(),
                                                  chan = channel_info[key][0]: self.voltage_changed(chan, volt))
            layout.addWidget(chan_button, channel_info[key][1][0], channel_info[key][1][1])
            #puts voltage box below it's channel button
            layout.addWidget(voltage_spin_box, channel_info[key][1][0]+1, channel_info[key][1][1])
        self.setLayout(layout)

    @inlineCallbacks
    def on_chan_toggled(self, chan, state):
        yield self.server.output_channel(chan, state)

    @inlineCallbacks
    def on_remote_toggled(self, state):
        yield self.server.remote_mode(state)

    @inlineCallbacks
    def voltage_changed(self, chan, volt):
        yield self.server.set_voltage(chan, self.U(volt, 'V'))
        
    def closeEvent(self, x):
        self.reactor.stop()

if __name__ == "__main__":
    a = QtGui.QApplication([]) 
    import qt4reactor 
    qt4reactor.install()
    from twisted.internet import reactor
    piezoWidget = Piezo_Client(reactor) 
    piezoWidget.show()
    reactor.run()
