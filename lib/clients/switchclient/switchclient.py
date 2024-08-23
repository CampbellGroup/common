from common.lib.clients.qtui.switch import QCustomSwitchChannel
from twisted.internet.defer import inlineCallbacks
from common.lib.clients.connection import connection
from PyQt5.QtWidgets import *
import logging
logger = logging.getLogger(__name__)

try:
    from config.switch_client_config import switch_config
except ImportError:
    from common.lib.config.switch_client_config import switch_config


class SwitchClient(QFrame):
    SIGNALID = 219749

    def __init__(self, reactor, cxn=None):
        """initializes the GUI creates the reactor
            and empty dictionary for channel widgets to
            be stored for iteration. also grabs chan info
            from switch_config file
        """
        super(SwitchClient, self).__init__()
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.reactor = reactor
        self.cxn = cxn
        self.d = {}
        self.chan_from_port = {}
        self.connect()

    @inlineCallbacks
    def connect(self):
        """Creates a connection if no connection passed and
        checked for saved switch settings

        """
        if self.cxn is None:
            self.cxn = connection(name="Switch Client")
            yield self.cxn.connect()
        self.server = yield self.cxn.get_server('arduinottl')
        self.reg = yield self.cxn.get_server('registry')

        yield self.server.signal__on_switch_changed(self.SIGNALID)
        yield self.server.addListener(listener=self.signal_switch_changed,
                                      source=None, ID=self.SIGNALID)

        try:
            yield self.reg.cd(['', 'settings'])
            self.settings = yield self.reg.dir()
            self.settings = self.settings[1]
        except Exception as e:
            print(e)
            self.settings = []

        self.chaninfo = switch_config.info
        self.initialize_gui()

    @inlineCallbacks
    def initialize_gui(self):

        layout = QVBoxLayout()

        for chan in self.chaninfo:
            port = self.chaninfo[chan][0]
            position = self.chaninfo[chan][1]
            inverted = self.chaninfo[chan][2]

            widget = QCustomSwitchChannel(chan, ('Closed', 'Open'))
            if chan + 'shutter' in self.settings:
                value = yield self.reg.get(chan + 'shutter')
                widget.TTLswitch.setChecked(bool(value))
            else:
                widget.TTLswitch.setChecked(False)

            widget.TTLswitch.toggled.connect(lambda state=widget.TTLswitch.isDown(),
                                             p=port, c=chan, i=inverted:
                                             self.change_state(state, p, c, i))
            self.d[port] = widget
            self.chan_from_port[port] = chan
            layout.addWidget(self.d[port])

        self.setLayout(layout)

    @inlineCallbacks
    def change_state(self, state, port, chan, inverted):
        if chan + 'shutter' in self.settings:
            yield self.reg.set(chan + 'shutter', state)
        if inverted:
            state = not state
        yield self.server.ttl_output(port, state)

    @inlineCallbacks
    def signal_switch_changed(self, c, signal):
        port = signal[0]
        state = signal[1]
        chan = self.chan_from_port[port]
        if port in self.d.keys():
            if chan + 'shutter' in self.settings:
                yield self.reg.set(chan + 'shutter', state)
            inverted = self.chaninfo[chan][2]
            if inverted:
                state = not state
            self.d[port].TTLswitch.setChecked(state)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    switchWidget = SwitchClient(reactor)
    switchWidget.show()
    reactor.run()
