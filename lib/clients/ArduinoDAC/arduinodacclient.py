from common.lib.clients.qtui.QCustomSpinBox import QCustomSpinBox
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui
from PyQt4.Qt import QPushButton

try:
    from config.arduino_dac_config import arduino_dac_config
except:
    from common.lib.config.arduino_dac_config import arduino_dac_config


class dacclient(QtGui.QWidget):

    def __init__(self, reactor, parent=None):
        """initializes the GUI creates the reactor
        and empty dictionary for channel widgets to
        be stored for iteration.
        """

        super(dacclient, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.d = {}
        self.e = {}
        self.topelectrodes = {"Black": 1, "Blue": 2, "White": 7, "Brown": 5}
        self.xminuselectrodes = {"White": 7, "Mustard Yellow": 2}
        self.xpluselectrodes = {"Black": 1, "Red": 4}
        self.yminuselectrodes = {}
        self.ypluselectrodes = {"Brown": 5, "Orange": 3}
        self.connect()

    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection"""
        from labrad.wrappers import connectAsync
        from labrad.units import WithUnit as U

        self.U = U
        self.cxn = yield connectAsync(name="dac client")
        self.server = yield self.cxn.arduinodac
        self.reg = yield self.cxn.registry

        try:
            yield self.reg.cd(["", "settings"])
            self.settings = yield self.reg.dir()
            self.settings = self.settings[1]
        except:
            self.settings = []

        self.dacinfo = arduino_dac_config.info
        self.initializeGUI()

    @inlineCallbacks
    def initializeGUI(self):

        layout = QtGui.QGridLayout()

        qBox = QtGui.QGroupBox("DAC Channels")
        subLayout = QtGui.QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)

        for v, dac in enumerate(self.dacinfo):
            name = self.dacinfo[dac][0]
            dacchan = self.dacinfo[dac][1]

            widget = QCustomSpinBox((0, 255), title=name)
            widget.title.setFixedWidth(120)
            label = QtGui.QLabel("0 V")
            if name + " dac" in self.settings:
                value = yield self.reg.get(name + " dac")
                widget.spin_level.setValue(value)
                self.setvalue(value, [name, dacchan])
            else:
                widget.spin_level.setValue(0.0)
            widget.set_step_size(1)
            widget.spin_level.set_decimals(0)
            widget.spin_level.valueChanged.connect(
                lambda value=widget.spin_level.value(), ident=[
                    name,
                    dacchan,
                ]: self.setvalue(value, ident)
            )
            self.d[dacchan] = widget
            self.e[dacchan] = label
            subLayout.addWidget(self.d[dacchan], v, 1)
            subLayout.addWidget(self.e[dacchan], v, 2)

        self.ezupwidget = QPushButton("Ez increase")
        self.ezdownwidget = QPushButton("Ez decrease")
        self.exupwidget = QPushButton("Ex increase")
        self.exdownwidget = QPushButton("Ex decrease")
        self.eyupwidget = QPushButton("Ey increase")
        self.eydownwidget = QPushButton("Ey decrease")

        self.ezupwidget.clicked.connect(self.ezup)
        self.ezdownwidget.clicked.connect(self.ezdown)
        self.exupwidget.clicked.connect(self.exup)
        self.exdownwidget.clicked.connect(self.exdown)
        self.eyupwidget.clicked.connect(self.eyup)
        self.eydownwidget.clicked.connect(self.eydown)

        subLayout.addWidget(self.ezupwidget, 0, 5)
        subLayout.addWidget(self.ezdownwidget, 1, 5)
        subLayout.addWidget(self.exupwidget, 3, 6)
        subLayout.addWidget(self.exdownwidget, 3, 3)
        subLayout.addWidget(self.eyupwidget, 2, 5)
        subLayout.addWidget(self.eydownwidget, 4, 5)

        self.setLayout(layout)

    @inlineCallbacks
    def ezup(self, isheld):
        for name, dacchan in self.topelectrodes.items():
            currentvalue = yield self.reg.get(name + " dac")
            if currentvalue >= 255:
                break
            self.setvalue(currentvalue + 1, [name, dacchan])
            self.d[dacchan].spin_level.setValue(currentvalue + 1)

    @inlineCallbacks
    def ezdown(self, isheld):
        for name, dacchan in self.topelectrodes.items():
            currentvalue = yield self.reg.get(name + " dac")
            if currentvalue <= 0:
                break
            self.setvalue(currentvalue - 1, [name, dacchan])
            self.d[dacchan].spin_level.setValue(currentvalue - 1)

    @inlineCallbacks
    def exup(self, isheld):
        for name, dacchan in self.xpluselectrodes.items():
            currentvalue = yield self.reg.get(name + " dac")
            if currentvalue <= 0:
                break
            self.setvalue(currentvalue - 1, [name, dacchan])
            self.d[dacchan].spin_level.setValue(currentvalue - 1)
        for name, dacchan in self.xminuselectrodes.items():
            currentvalue = yield self.reg.get(name + " dac")
            if currentvalue >= 255:
                break
            self.setvalue(currentvalue + 1, [name, dacchan])
            self.d[dacchan].spin_level.setValue(currentvalue + 1)

    @inlineCallbacks
    def exdown(self, isheld):
        for name, dacchan in self.xminuselectrodes.items():
            currentvalue = yield self.reg.get(name + " dac")
            if currentvalue <= 0:
                break
            self.setvalue(currentvalue - 1, [name, dacchan])
            self.d[dacchan].spin_level.setValue(currentvalue - 1)
        for name, dacchan in self.xpluselectrodes.items():
            currentvalue = yield self.reg.get(name + " dac")
            if currentvalue >= 255:
                break
            self.setvalue(currentvalue + 1, [name, dacchan])
            self.d[dacchan].spin_level.setValue(currentvalue + 1)

    @inlineCallbacks
    def eyup(self, isheld):
        for name, dacchan in self.ypluselectrodes.items():
            currentvalue = yield self.reg.get(name + " dac")
            if currentvalue <= 0:
                break
            self.setvalue(currentvalue - 1, [name, dacchan])
            self.d[dacchan].spin_level.setValue(currentvalue - 1)
        for name, dacchan in self.yminuselectrodes.items():
            currentvalue = yield self.reg.get(name + " dac")
            if currentvalue >= 255:
                break
            self.setvalue(currentvalue + 1, [name, dacchan])
            self.d[dacchan].spin_level.setValue(currentvalue + 1)

    @inlineCallbacks
    def eydown(self, isheld):
        for name, dacchan in self.yminuselectrodes.items():
            currentvalue = yield self.reg.get(name + " dac")
            if currentvalue <= 0:
                break
            self.setvalue(currentvalue - 1, [name, dacchan])
            self.d[dacchan].spin_level.setValue(currentvalue - 1)
        for name, dacchan in self.ypluselectrodes.items():
            currentvalue = yield self.reg.get(name + " dac")
            if currentvalue >= 255:
                break
            self.setvalue(currentvalue + 1, [name, dacchan])
            self.d[dacchan].spin_level.setValue(currentvalue + 1)

    @inlineCallbacks
    def setvalue(self, value, ident):
        name = ident[0]
        chan = ident[1]
        value = int(value)
        yield self.server.dacoutput(chan, value)
        voltage = 0.10896 * value - 13.89777
        self.e[chan].setText(str(voltage))
        yield self.reg.set(name + " dac", value)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QtGui.QApplication([])
    import qt4reactor

    qt4reactor.install()
    from twisted.internet import reactor

    dacWidget = dacclient(reactor)
    dacWidget.show()
    reactor.run()
