from common.lib.clients_py3.qtui.switch import QCustomSwitchChannel
from common.lib.clients_py3.connection import connection
from twisted.internet.defer import inlineCallbacks
from PyQt5 import QtGui, QtWidgets
try:
    from config.shutter_client_config import ShutterClientConfig
except:
    from common.lib.config.shutter_client_config import ShutterClientConfig


class ShutterClient(QtWidgets.QWidget):
    SIGNALID = 219749

    def __init__(self, reactor, cxn=None):
        super(ShutterClient, self).__init__()
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.reactor = reactor
        self.cxn = cxn
        self.d = {}
        self.chan_from_port = {}
        self.connect()

    @inlineCallbacks
    def connect(self):
        if self.cxn is None:
            self.cxn = connection(name="Shutter Client")
            yield self.cxn.connect()
        self.server = yield self.cxn.cxn.shutter_server

        yield self.server.signal__on_shutter_changed(self.SIGNALID)
        yield self.server.addListener(listener=self.signal_shutter_changed,
                                      source=None, ID=self.SIGNALID)

        self.chaninfo = ShutterClientConfig.info
        self.initialize_gui()

    def initialize_gui(self):
        layout = QtWidgets.QGridLayout()
        qBox = QtWidgets.QGroupBox('Laser Shutters')
        subLayout = QtWidgets.QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)

        for chan in self.chaninfo:
            port = self.chaninfo[chan][0]
            position = self.chaninfo[chan][1]

            widget = QCustomSwitchChannel(chan, ('Closed', 'Open'))

            widget.TTLswitch.toggled.connect(lambda state=widget.TTLswitch.isDown(),
                                             port=port, chan=chan:
                                             self.change_state(state, port, chan))
            self.d[port] = widget
            self.chan_from_port[port] = chan
            subLayout.addWidget(self.d[port], position[0], position[1])

        self.setLayout(layout)

    @inlineCallbacks
    def change_state(self, state, port, chan):
        yield self.server.set_channel_state(port, state)

    def signal_shutter_changed(self, c, signal):
        port = signal[0]
        state = signal[1]
        chan = self.chan_from_port[port]
        if port in self.d:
            self.d[port].TTLswitch.blockSignals(True)
            self.d[port].TTLswitch.setAppearance(state)
            self.d[port].TTLswitch.setChecked(state)
            self.d[port].TTLswitch.blockSignals(False)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QtWidgets.QApplication([])
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    client = ShutterClient(reactor)
    client.show()
    reactor.run()
