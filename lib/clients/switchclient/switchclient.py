from common.lib.clients.qtui.switch import QCustomSwitchChannel
from twisted.internet.defer import inlineCallbacks
from common.lib.clients.connection import connection
from pyqtgraph.Qt import QtGui
#from common.lib.configuration_files.switch_client_config import switch_config
try:
    from config.switch_client_config import switch_config
except:
    from common.lib.config.switch_client_config import switch_config


class switchclient(QtGui.QWidget):

    def __init__(self, reactor, cxn=None):
        """initializels the GUI creates the reactor
            and empty dictionary for channel widgets to
            be stored for iteration. also grabs chan info
            from wlm_client_config file
        """
        super(switchclient, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.cxn = cxn
        self.d = {}
        self.connect()

    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection to the wavemeter computer and
        connects incoming signals to relavent functions

        """
        from labrad.wrappers import connectAsync
        if self.cxn is None:
            self.cxn = connection(name="Switch Client")
            yield self.cxn.connect()
        self.server = yield self.cxn.get_server('arduinottl')
        self.reg = yield self.cxn.get_server('registry')

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

            widget = QCustomSwitchChannel(chan,('Closed','Open'))
            if chan + 'shutter' in self.settings:
                value = yield self.reg.get(chan + 'shutter')
                print(value)
                widget.TTLswitch.setChecked(bool(value))
            else:
                widget.TTLswitch.setChecked(False)

            widget.TTLswitch.toggled.connect(lambda state = widget.TTLswitch.isDown(), port = port, chan = chan, inverted = inverted
                                               : self.changeState(state, port, chan, inverted))
            self.d[port] = widget
            subLayout.addWidget(self.d[port])

        self.setLayout(layout)
        yield None

    @inlineCallbacks
    def changeState(self, state, port, chan, inverted):
        if chan + 'shutter' in self.settings:
            yield self.reg.set(chan + 'shutter', state)
        if inverted:
            state = not state
        yield self.server.ttl_output(port, state)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QtGui.QApplication([])
    try:
        import qt4reactor as qtreactor
    except ImportError:
        try:
            import qt5reactor as qtreactor
        except:
            msg = "Error loading qtreactor. Check either qt4reactor or "
            msg += "qt5reactor is in the python path."
            raise ImportError(msg)
    qtreactor.install()
    from twisted.internet import reactor
    switchWidget = switchclient(reactor)
    switchWidget.show()
    reactor.run()
