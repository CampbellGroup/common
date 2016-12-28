from twisted.internet.defer import inlineCallbacks
from common.lib.clients.connection import connection
from PyQt4 import QtGui
import os
from common.lib.clients.qtui import RGBconverter as RGB
SIGNALID1 = 125366
SIGNALID2 = 525466


class bristol_client(QtGui.QWidget):

    def __init__(self, reactor):
        super(bristol_client, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor
        self.RGB = RGB.RGBconverter()
        self.password = os.environ['LABRADPASSWORD']
        self.connect()
        self.initializeGUI()

    @inlineCallbacks
    def connect(self):
        """Creates an AsyncSIGNALID1 = 445566hronous connection to arduinottl and
        connects incoming signals to relavent functions

        """

        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(
                                      name='bristol client',
                                      password=self.password)
        self.server = yield self.cxn.bristol_521

        yield self.server.signal__frequency_changed(SIGNALID1)
        yield self.server.signal__amplitude_changed(SIGNALID2)
        yield self.server.addListener(listener=self.updateFrequency, source=None, ID=SIGNALID1)
        yield self.server.addListener(listener=self.updatePower, source=None, ID=SIGNALID2)

    def initializeGUI(self):
        layout = QtGui.QGridLayout()
        self.freqlabel = QtGui.QLabel('Frequency (THz)')
        self.powerlabel = QtGui.QLabel('Power (mW)')
        self.freqwidget = QtGui.QLabel('')
        self.powerwidget = QtGui.QLabel('')

        shell_font = 'MS Shell Dlg 2'
        self.freqlabel.setFont(QtGui.QFont(shell_font, pointSize=28))
        self.powerlabel.setFont(QtGui.QFont(shell_font, pointSize=28))
        self.freqwidget.setFont(QtGui.QFont(shell_font, pointSize=35))
        self.powerwidget.setFont(QtGui.QFont(shell_font, pointSize=35))
        layout.addWidget(self.freqlabel, 0,0)
        layout.addWidget(self.powerlabel, 0,1)
        layout.addWidget(self.freqwidget, 1,0)
        layout.addWidget(self.powerwidget, 1,1)
        self.setLayout(layout)

    def updateFrequency(self, c, signal):
        print signal
        color = int(2.998e8/(float(signal)))
        color = self.RGB.wav2RGB(color)
        color = tuple(color)
        self.freqwidget.setStyleSheet('color: rgb' + str(color))
        self.freqwidget.setText(str(signal*1e-3)[0:10])

    def updatePower(self, c, signal):
        self.powerwidget.setText(str(signal)[0:5])

    def closeEvent(self, x):
        self.reactor.stop()

if __name__ == "__main__":
    a = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    bristolclientWidget = bristol_client(reactor)
    bristolclientWidget.show()
    reactor.run()
