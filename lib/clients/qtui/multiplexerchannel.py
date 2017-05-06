import sys
from PyQt4 import QtGui, QtCore
from common.lib.clients.qtui.QCustomPowerMeter import MQProgressBar
from common.lib.clients.qtui.QCustomSlideIndicator import SlideIndicator
from common.lib.clients.qtui.q_custom_text_changing_button import \
    TextChangingButton as _TextChangingButton


class StretchedLabel(QtGui.QLabel):
    def __init__(self, *args, **kwargs):
        QtGui.QLabel.__init__(self, *args, **kwargs)
        self.setMinimumSize(QtCore.QSize(350, 100))

    def resizeEvent(self, evt):

        font = self.font()
        font.setPixelSize(self.width() * 0.14 - 14)
        self.setFont(font)


class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)


class QCustomWavemeterChannel(QtGui.QFrame):
    def __init__(self, chanName, wmChannel, DACPort, frequency, stretchedlabel, displayPIDvoltage=None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(chanName, wmChannel, DACPort, frequency, stretchedlabel, displayPIDvoltage)

    def makeLayout(self, name, wmChannel, DACPort, frequency, stretchedlabel, displayPIDvoltage):
        layout = QtGui.QGridLayout()

        shell_font = 'MS Shell Dlg 2'
        chanName = QtGui.QLabel(name)
        chanName.setFont(QtGui.QFont(shell_font, pointSize=16))
        chanName.setAlignment(QtCore.Qt.AlignCenter)

        configtitle = QtGui.QLabel('WLM Connections:')
        configtitle.setAlignment(QtCore.Qt.AlignBottom)
        configtitle.setFont(QtGui.QFont(shell_font, pointSize=13))

        configLabel = QtGui.QLabel("Channel " + str(wmChannel) + '        ' + "DAC Port " + str(DACPort))
        configLabel.setFont(QtGui.QFont(shell_font, pointSize=8))
        configLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.PIDvoltage = QtGui.QLabel('DAC Voltage (mV)  -.-')
        self.PIDvoltage.setFont(QtGui.QFont(shell_font, pointSize=12))

        if displayPIDvoltage:
            self.PIDindicator = SlideIndicator([-10.0, 10.0])

        self.powermeter = MQProgressBar()
        self.powermeter.setOrientation(QtCore.Qt.Vertical)
        self.powermeter.setMeterColor("orange", "red")
        self.powermeter.setMeterBorder("orange")

        if displayPIDvoltage is True:
            layout.addWidget(self.PIDvoltage,   6,4,1,1)
            layout.addWidget(self.PIDindicator, 5,4,1,1)
        if stretchedlabel is True:
            self.currentfrequency = StretchedLabel(frequency)
        else:
            self.currentfrequency = QtGui.QLabel(frequency)


        self.currentfrequency.setFont(QtGui.QFont(shell_font, pointSize=40))
        self.currentfrequency.setAlignment(QtCore.Qt.AlignCenter)
        self.currentfrequency.setMinimumWidth(200)

        frequencylabel = QtGui.QLabel('Set Frequency')
        frequencylabel.setAlignment(QtCore.Qt.AlignCenter)
        frequencylabel.setFont(QtGui.QFont(shell_font, pointSize=13))

        self.current_exposure = QtGui.QLabel('0.0 ms')
        self.current_exposure.setFont(QtGui.QFont(shell_font, pointSize=16))
        self.current_exposure.setAlignment(QtCore.Qt.AlignCenter)
        #self.current_exposre.setMinimumWidth(50)


        exposurelabel = QtGui.QLabel('Exposure (ms)')
        exposurelabel.setAlignment(QtCore.Qt.AlignCenter)
        exposurelabel.setFont(QtGui.QFont(shell_font, pointSize=13))

        self.setPID = QtGui.QPushButton('Set PID')
        self.setPID.setMaximumHeight(30)
        self.setPID.setFont(QtGui.QFont(shell_font, pointSize=10))

        self.measSwitch = TextChangingButton('WLM Measure')

        self.lockChannel = TextChangingButton('Lock Channel')
        #self.lockChannel.setMinimumWidth(90)

        #editable fields
        self.spinFreq = QtGui.QDoubleSpinBox()
        self.spinFreq.setFont(QtGui.QFont(shell_font, pointSize=16))
        self.spinFreq.setDecimals(6)
        self.spinFreq.setSingleStep(0.000001)
        self.spinFreq.setRange(100.0, 1000.0)
        self.spinFreq.setKeyboardTracking(False)

        self.spinExp = QtGui.QDoubleSpinBox()
        self.spinExp.setFont(QtGui.QFont(shell_font, pointSize=16))
        self.spinExp.setDecimals(0)
        self.spinExp.setSingleStep(1)
        # 10 seconds is the max exposure time on the wavemeter.
        self.spinExp.setRange(0, 10000.0)
        self.spinExp.setKeyboardTracking(False)

        # Set Auto Exposure
        self.autoExpose = QtGui.QCheckBox('Auto Expose')
        self.autoExpose.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=13))

        layout.addWidget(self.spinFreq,         6, 0, 1, 1)
        layout.addWidget(self.spinExp,          6, 1, 1, 1)
        layout.addWidget(self.measSwitch,       0, 4, 1, 1)
        layout.addWidget(self.lockChannel,      1,4,1,1)
        layout.addWidget(self.setPID,           2,4,1,1)
        layout.addWidget(chanName,              0,0,1,4)
        layout.addWidget(configtitle,           3,4,1,1)
        layout.addWidget(configLabel,           4,4,1,1)
        layout.addWidget(self.currentfrequency, 1, 0, 4, 4)
        layout.addWidget(frequencylabel,        5, 0, 1, 1)
        layout.addWidget(exposurelabel,         5, 1, 1, 2)
        layout.addWidget(self.powermeter,       0,5,7,1)
        layout.addWidget(self.autoExpose,       5, 3, 1, 1)
        layout.addWidget(self.current_exposure, 6, 2, 1, 1)

        layout.minimumSize()

        self.setLayout(layout)

    def setExpRange(self, exprange):
        self.spinExp.setRange(exprange)

    def setFreqRange(self, freqrange):
        self.spinFreq.setRange(freqrange)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    icon = QCustomWavemeterChannel('Repumper', 1, 4, 'Under Exposed', False, True)
    icon.show()
    app.exec_()
