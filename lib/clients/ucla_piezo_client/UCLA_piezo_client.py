from common.lib.clients.qtui.switch import QCustomSwitchChannel
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui


class ucla_piezo_client(QtGui.QWidget):

    def __init__(self, reactor, parent=None):

        super(ucla_piezo_client, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.connect()

    @inlineCallbacks
    def connect(self):

        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name="UCLAPiezo client")
        self.server = yield self.cxn.piezo_server
        self.reg = yield self.cxn.registry
        yield self.reg.cd(['', 'settings'])
        from labrad.units import WithUnit as U
        self.U = U
        yield self.initializeGUI()

    @inlineCallbacks
    def initializeGUI(self):  

        layout = QtGui.QGridLayout()
        for i in range(4):
            setting = yield self.reg.get('ucla_piezo_chan_' + str(i + 1))
            print len(setting)
            init_volt = setting[0]
            init_pos = setting[1]
            chan_button = QCustomSwitchChannel(setting[2], ('On', 'Off'))
            chan_button.TTLswitch.setChecked(init_pos)
            chan_button.TTLswitch.toggled.connect(lambda state=chan_button.TTLswitch.isDown(),
                                                  chan= i + 1: self.on_chan_toggled(state, chan))
            voltage_spin_box = QtGui.QDoubleSpinBox()
            voltage_spin_box.setRange(0.0, 150.0)
            voltage_spin_box.setSingleStep(0.1)
            voltage_spin_box.setDecimals(3)
            voltage_spin_box.setValue(init_volt['V'])
            voltage_spin_box.setKeyboardTracking(False)
            voltage_spin_box.valueChanged.connect(lambda volt=voltage_spin_box.value(),
                                                  chan = i +1: self.voltage_changed(volt, chan))
            layout.addWidget(chan_button)
            layout.addWidget(voltage_spin_box)
        self.setLayout(layout)

    @inlineCallbacks
    def on_chan_toggled(self, state, chan):
        yield self.server.piezo_output(chan, state)

    @inlineCallbacks
    def voltage_changed(self, volt, chan):
        yield self.server.set_voltage(chan, self.U(volt, 'V'))
        
    def closeEvent(self, x):
        self.reactor.stop()

if __name__ == "__main__":

    a = QtGui.QApplication([]) 
    import qt4reactor 
    qt4reactor.install()
    from twisted.internet import reactor
    piezoWidget = ucla_piezo_client(reactor) 
    piezoWidget.show()
    reactor.run()
