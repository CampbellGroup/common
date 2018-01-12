import sys
from PyQt4 import QtGui, QtCore
from common.lib.clients.qtui.QCustomPowerMeter import MQProgressBar
from common.lib.clients.qtui.QCustomSlideIndicator import SlideIndicator
from common.lib.clients.qtui.q_custom_text_changing_button import \
    TextChangingButton as _TextChangingButton


class StretchedLabel(QtGui.QLabel):
    def __init__(self, *args, **kwargs):
        QtGui.QLabel.__init__(self, *args, **kwargs)
        self.setMinimumSize(QtCore.QSize(200, 80))

    def resizeEvent(self, evt):
        font = self.font()
        width_pixel_size = self.width() * 0.14 - 14
        height_pixel_size = self.height() * 1.3 - 14
        if width_pixel_size < height_pixel_size:
            font.setPixelSize(width_pixel_size)
        else:
            font.setPixelSize(height_pixel_size)
        self.setFont(font)


class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)


class QCustomWavemeterChannel(QtGui.QFrame):
    def __init__(self, chanName, wmChannel, frequency, stretchedlabel, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(chanName, wmChannel, frequency, stretchedlabel)

    def makeLayout(self, name, wmChannel, frequency, stretchedlabel):
        layout = QtGui.QGridLayout()

        shell_font = 'MS Shell Dlg 2'
        chanName = QtGui.QLabel(name)
        chanName.setFont(QtGui.QFont(shell_font, pointSize=16))
        chanName.setAlignment(QtCore.Qt.AlignCenter)

        configtitle = QtGui.QLabel("WLM Connections:\nChannel " + str(wmChannel))
        configtitle.setAlignment(QtCore.Qt.AlignCenter)
        configtitle.setFont(QtGui.QFont(shell_font, pointSize=13))

        self.powermeter = MQProgressBar()
        self.powermeter.setOrientation(QtCore.Qt.Vertical)
        self.powermeter.setMeterColor("orange", "red")
        self.powermeter.setMeterBorder("orange")
        if stretchedlabel is True:
            self.currentfrequency = StretchedLabel(frequency)
        else:
            self.currentfrequency = QtGui.QLabel(frequency)


        self.currentfrequency.setFont(QtGui.QFont(shell_font, pointSize=40))
        self.currentfrequency.setAlignment(QtCore.Qt.AlignCenter)
        self.currentfrequency.setMinimumWidth(500)

        exposurelabel = QtGui.QLabel('Set Exposure (ms): ')
        exposurelabel.setAlignment(QtCore.Qt.AlignLeft)
        exposurelabel.setFont(QtGui.QFont(shell_font, pointSize=13))

        self.measSwitch = TextChangingButton('WLM Measure')

        self.lockChannel = TextChangingButton('Lock Channel')
        self.lockChannel.setMinimumWidth(180)
        self.lockChannel.setMaximumWidth(500)

        self.spinExp = QtGui.QDoubleSpinBox()
        self.spinExp.setFont(QtGui.QFont(shell_font, pointSize=16))
        self.spinExp.setDecimals(0)
        self.spinExp.setSingleStep(1)
        # 10 seconds is the max exposure time on the wavemeter.
        self.spinExp.setRange(0, 10000.0)
        self.spinExp.setKeyboardTracking(False)

        layout.addWidget(self.spinExp,          4, 0)
        layout.addWidget(self.measSwitch,       0, 2)
        layout.addWidget(self.lockChannel,      1, 2)
        layout.addWidget(chanName,              0, 0)
        layout.addWidget(configtitle,           2, 2)
        layout.addWidget(self.currentfrequency, 1, 0, 2, 1)
        layout.addWidget(exposurelabel,         3, 0)
        layout.addWidget(self.powermeter,       0, 3, 5, 1)

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
