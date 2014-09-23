from common.lib.clients.qtui.multiplexerchannel import QCustomWavemeterChannel
from twisted.internet.defer import inlineCallbacks, returnValue
from PyQt4 import QtGui, QtCore
try:
    from config.multiplexerclient_config import multiplexer_config
except:
    from common.lib.config.multiplexerclient_config import multiplexer_config
#from wlm_client_config import multiplexer_config
import socket



SIGNALID1 = 445566
SIGNALID2 = 143533
SIGNALID3 = 111221
SIGNALID4 = 549210
SIGNALID5 = 190909

#this is the signal for the updated frequencys

class TextChangingButton(QtGui.QPushButton):
    """Button that changes its text to ON or OFF and colors when it's pressed"""
    def __init__(self, addtext = None, parent = None):
        super(TextChangingButton, self).__init__(parent)
        self.setCheckable(True)
        self.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=10))
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        #connect signal for appearance changing
        self.addtext = addtext
        if self.addtext == None:
            self.addtext = ''
        else:
            self.addtext = self.addtext + '   '
        self.toggled.connect(self.setAppearance)
        self.setAppearance(self.isDown())

    def setAppearance(self, down, addtext = None):
        if down:
            self.setText(self.addtext + 'On')
            self.setPalette(QtGui.QPalette(QtCore.Qt.darkGreen))
        else:
            self.setText(self.addtext + 'Off')
            self.setPalette(QtGui.QPalette(QtCore.Qt.black))
    def sizeHint(self):
        return QtCore.QSize(37, 26)


class wavemeterclient(QtGui.QWidget):

    def __init__(self, reactor, parent = None):
        """initializels the GUI creates the reactor
            and empty dictionary for channel widgets to
            be stored for iteration. also grabs chan info
            from wlm_client_config file
        """
        super(wavemeterclient, self).__init__()
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
        self.cxn = yield connectAsync('10.97.112.2', name = socket.gethostname() + ' Wave Meter Client')

        self.server = yield self.cxn.multiplexerserver
        self.chaninfo = multiplexer_config.info

        yield self.server.signal__frequency_changed(SIGNALID1)
        yield self.server.signal__selected_channels_changed(SIGNALID2)
        yield self.server.signal__update_exp(SIGNALID3)
        yield self.server.signal__lock_changed(SIGNALID4)
        yield self.server.signal__output_changed(SIGNALID5)

        yield self.server.addListener(listener = self.updateFrequency, source = None, ID = SIGNALID1)
        yield self.server.addListener(listener = self.toggleMeas, source = None, ID = SIGNALID2)
        yield self.server.addListener(listener = self.updateexp, source = None, ID = SIGNALID3)
        yield self.server.addListener(listener = self.toggleLock, source = None, ID = SIGNALID4)
        yield self.server.addListener(listener = self.updateWLMOutput, source = None, ID = SIGNALID5)

        self.initializeGUI()

    @inlineCallbacks
    def initializeGUI(self):

        layout = QtGui.QGridLayout()

        self.setWindowTitle('Multiplexed Wavemeter')

        qBox = QtGui.QGroupBox('Wave Length and Lock settings')
        subLayout = QtGui.QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)

        self.lockSwitch = TextChangingButton('Lock Wave Meter')
        self.startSwitch = TextChangingButton('Wavemeter')
        initstartvalue = yield self.server.get_wlm_output()
        initlockvalue = yield self.server.get_lock_state()
        self.lockSwitch.setChecked(initlockvalue)
        self.startSwitch.setChecked(initstartvalue)

        self.lockSwitch.toggled.connect(self.setLock)
        self.startSwitch.toggled.connect(self.setOutput)

        subLayout.addWidget(self.lockSwitch, 0, 3)
        subLayout.addWidget(self.startSwitch, 0, 1)

        for chan in self.chaninfo:
            port = self.chaninfo[chan][0]
            hint = self.chaninfo[chan][1]
            position = self.chaninfo[chan][2]
            stretched = self.chaninfo[chan][3]

            widget = QCustomWavemeterChannel(chan, hint, stretched)
            import RGBconverter as RGB
            RGB = RGB.RGBconverter()
            color = int(2.998e8/(float(hint)*1e3))
            color = RGB.wav2RGB(color)
            color = tuple(color)

            initcourse = yield self.getPIDCourse(port, hint)
            widget.spinFreq.setValue(initcourse)

            widget.currentfrequency.setStyleSheet('color: rgb' + str(color))

            widget.spinExp.valueChanged.connect(lambda exp = widget.spinExp.value(), port = port : self.expChanged(exp, port))
            initvalue = yield self.server.get_exposure(port)
            widget.spinExp.setValue(initvalue)
            initmeas = yield self.server.get_switcher_signal_state(port)
            initmeas = initmeas
            widget.measSwitch.setChecked(bool(initmeas))
            widget.measSwitch.toggled.connect(lambda state = widget.measSwitch.isDown(), port = port  : self.changeState(state, port))
            widget.spinFreq.valueChanged.connect(lambda freq = widget.spinFreq.value(), port = port : self.freqChanged(freq, port))

            self.d[port] = widget
            subLayout.addWidget(self.d[port], position[1], position[0], 1, 3)

        self.setLayout(layout)

    @inlineCallbacks
    def expChanged(self, exp, chan):
        #these are switched, dont know why
        exp = int(exp)
        yield self.server.set_exposure_time(chan,exp)


    def updateFrequency(self , c , signal):
        chan = signal[0]
        if chan in self.d :
            freq = signal[1]

            if not self.d[chan].measSwitch.isChecked():
                self.d[chan].currentfrequency.setText('Not Measured')
            elif freq == -3.0:
                self.d[chan].currentfrequency.setText('Under Exposed')
            elif freq == -4.0:
                self.d[chan].currentfrequency.setText('Over Exposed')
            else:
                self.d[chan].currentfrequency.setText(str(freq)[0:10])

    def toggleMeas(self, c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d :
            self.d[chan].measSwitch.setChecked(value)

    def toggleLock(self, c, signal):
        self.lockSwitch.setChecked(signal)

    def updateexp(self,c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d :
            self.d[chan].spinExp.setValue(value)

    def updateWLMOutput(self, c, signal):
        self.startSwitch.setChecked(signal)

    @inlineCallbacks
    def changeState(self, state, chan):
        yield self.server.set_switcher_signal_state(chan, state)

    @inlineCallbacks
    def freqChanged(self,freq, port):
        yield self.server.set_pid_course(port, freq)

    @inlineCallbacks
    def setLock(self, state):
        yield self.server.set_lock_state(state)

    @inlineCallbacks
    def setOutput(self, state):
        yield self.server.set_wlm_output(state)

    @inlineCallbacks
    def getPIDCourse(self, chan, hint):
        course = yield self.server.get_pid_course(chan)
        try:
            course = float(course)
        except:
            try:
                course = float(hint)
            except:
                course = 600
        returnValue(course)

    def closeEvent(self, x):
        self.reactor.stop()



if __name__=="__main__":
    a = QtGui.QApplication( [] )
    from common.lib.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    wavemeterWidget = wavemeterclient(reactor)
    wavemeterWidget.show()
    reactor.run()
