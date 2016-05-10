from common.lib.clients.qtui.QCustomSpinBox import QCustomSpinBox
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui, QtCore

class TextChangingButton(QtGui.QPushButton):
    """Button that changes its text to ON or OFF and colors when it's pressed"""
    def __init__(self, labels = None, parent = None):
        super(TextChangingButton, self).__init__(parent)
        self.labels = labels
        self.setCheckable(True)
        self.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=10))
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        #connect signal for appearance changing
        self.toggled.connect(self.setAppearance)
        self.setAppearance(self.isDown())

    def setAppearance(self, down):
        if down:
            if self.labels == None:
                self.setText('On')
            else:
                self.setText(self.labels[0])
            self.setPalette(QtGui.QPalette(QtCore.Qt.darkGreen))
        else:
            if self.labels == None:
                self.setText('Off')
            else:
                self.setText(self.labels[1])
            self.setPalette(QtGui.QPalette(QtCore.Qt.black))

    def sizeHint(self):
        return QtCore.QSize(37, 26)

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
        self.server = self.cxn.rigol_dg1022_server
        self.devicelist = yield self.server.list_devices()
        if self.devicelist:
            yield self.server.select_device(0)
        self.initializeGUI()

    def initializeGUI(self):

        layout = QtGui.QGridLayout()

        self.setWindowTitle('Rigol DG1022 Control')

        qBox = QtGui.QGroupBox('Rigol DG1022')
        subLayout = QtGui.QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)

        self.deviceselect = QtGui.QComboBox(self)
        self.updatedevices()


        self.offsetwidget1 = QCustomSpinBox('Offset', (-5, 5))
        self.offsetwidget2 = QCustomSpinBox('Offset', (-5, 5))
        self.volt1widget = QCustomSpinBox('Amplitude (Vpp)', (-10, 10))
        self.freq1widget = QCustomSpinBox('Frequency (Hz)', (0, 40e6))
        self.volt2widget = QCustomSpinBox('Amplitude (Vpp)', (-10, 10))
        self.freq2widget = QCustomSpinBox('Frequency (Hz)', (0, 40e6))
        self.waveselect1 = QtGui.QComboBox(self)
        self.waveselect2 = QtGui.QComboBox(self)
        self.output1 = TextChangingButton(('On','Off'))
        self.output2 = TextChangingButton(('On','Off'))

        self.waveselect1.addItem("sine")
        self.waveselect1.addItem("square")
        self.waveselect1.addItem("ramp")
        self.waveselect1.addItem("pulse")
        self.waveselect1.addItem("noise")
        self.waveselect1.addItem("DC")
        self.waveselect1.addItem("USER")

        self.waveselect2.addItem("sine")
        self.waveselect2.addItem("square")
        self.waveselect2.addItem("ramp")
        self.waveselect2.addItem("pulse")
        self.waveselect2.addItem("noise")
        self.waveselect2.addItem("DC")
        self.waveselect2.addItem("USER")

        self.output1.toggled.connect(lambda state = self.output1.isDown(), chan = 1, : self.setoutput(chan, state))
        self.output2.toggled.connect(lambda state = self.output1.isDown(), chan = 2, : self.setoutput(chan, state))
        self.volt1widget.spinLevel.valueChanged.connect(lambda value = self.volt1widget.spinLevel.value(), chan = 1 : self.voltchanged(chan, value))
        self.volt2widget.spinLevel.valueChanged.connect(lambda value = self.volt2widget.spinLevel.value(), chan = 2 : self.voltchanged(chan, value))
        self.freq1widget.spinLevel.valueChanged.connect(lambda value = self.freq1widget.spinLevel.value(), chan = 1 : self.freqchanged(chan, value))
        self.freq2widget.spinLevel.valueChanged.connect(lambda value = self.freq2widget.spinLevel.value(), chan = 2 : self.freqchanged(chan, value))
        self.offsetwidget1.spinLevel.valueChanged.connect(lambda value = self.offsetwidget1.spinLevel.value(), chan = 1 : self.offsetchanged(chan, value))
        self.offsetwidget2.spinLevel.valueChanged.connect(lambda value = self.offsetwidget2.spinLevel.value(), chan = 2 : self.offsetchanged(chan, value))
        self.waveselect1.activated[str].connect(lambda wave = self.waveselect1.currentText(), chan = 1 : self.waveselect(chan, wave))
        self.waveselect2.activated[str].connect(lambda wave = self.waveselect2.currentText(), chan = 2 : self.waveselect(chan, wave))
        self.deviceselect.activated[str].connect(self.changedevice)
        subLayout.addWidget(self.freq1widget, 1,0)
        subLayout.addWidget(self.volt1widget, 1,1)
        subLayout.addWidget(self.freq2widget, 1,2)
        subLayout.addWidget(self.volt2widget, 1,3)
        subLayout.addWidget(self.waveselect1, 2,0, 1,2)
        subLayout.addWidget(self.waveselect2, 2,2, 1,2)
        subLayout.addWidget(self.offsetwidget1, 3,0)
        subLayout.addWidget(self.offsetwidget2, 3,2)
        subLayout.addWidget(self.output1,      3,1)
        subLayout.addWidget(self.output2,      3,3)
        subLayout.addWidget(self.deviceselect, 0,3)

        self.setLayout(layout)

    @inlineCallbacks
    def voltchanged(self, chan, value):
        value = self.U(value, 'V')
        yield self.server.amplitude(chan, value)

    @inlineCallbacks
    def freqchanged(self, chan, value):
        value = self.U(value, 'Hz')
        yield self.server.frequency(chan, value)

    @inlineCallbacks
    def offsetchanged(self, chan, value):
        value = self.U(value, 'V')
        yield self.server.offset(chan, value)

    @inlineCallbacks
    def setoutput(self, chan, state):
        yield self.server.output(chan, state)

    @inlineCallbacks
    def waveselect(self, chan, wave):
        if wave == 'DC':
            if chan == 1:
                self.freq1widget.setEnabled(False)
            else:
                self.freq2widget.setEnabled(False)
        else:
            self.freq1widget.setEnabled(True)
            self.freq2widget.setEnabled(True)
        yield self.server.wave_function(chan, str(wave))

    @inlineCallbacks
    def changedevice(self, deviceid):
        if deviceid == 'Refresh List':
            yield self.server.refresh()
            self.updatedevices()
        else:
            self.server.release_device()
            self.server.select_device(int(deviceid[1]))


    @inlineCallbacks
    def updatedevices(self):
        self.deviceselect.clear()
        self.devicelist = yield self.server.list_devices()
        for device in self.devicelist:
            self.deviceselect.addItem(str(device))
        self.deviceselect.addItem('Refresh List')


    def closeEvent(self, x):
        self.reactor.stop()

if __name__ == "__main__":
    a = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    rigolWidget = rigolclient(reactor)
    rigolWidget.show()
    reactor.run()
