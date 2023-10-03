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
    def __init__(self, chan_name, wm_channel, dac_port, frequency, stretched_label, display_pid_voltage=None,
                 parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.make_layout(chan_name, wm_channel, dac_port, frequency, stretched_label, display_pid_voltage)

    def make_layout(self, name, wm_channel, dac_port, frequency, stretched_label, display_pid_voltage):
        layout = QtGui.QGridLayout()

        shell_font = 'MS Shell Dlg 2'
        chan_name = QtGui.QLabel(name)
        chan_name.setFont(QtGui.QFont(shell_font, pointSize=16))
        chan_name.setAlignment(QtCore.Qt.AlignCenter)

        config_title = QtGui.QLabel('WLM Connections:')
        config_title.setAlignment(QtCore.Qt.AlignBottom)
        config_title.setFont(QtGui.QFont(shell_font, pointSize=13))

        config_label = QtGui.QLabel("Channel " + str(wm_channel) + '        ' + "DAC Port " + str(dac_port))
        config_label.setFont(QtGui.QFont(shell_font, pointSize=11))
        config_label.setAlignment(QtCore.Qt.AlignCenter)

        self.pid_voltage = QtGui.QLabel('DAC Voltage (mV)  -.-')
        self.pid_voltage.setFont(QtGui.QFont(shell_font, pointSize=12))

        if display_pid_voltage:
            self.pid_indicator = SlideIndicator([-10.0, 10.0])

        self.power_meter = MQProgressBar()
        self.power_meter.setOrientation(QtCore.Qt.Vertical)
        self.power_meter.setMeterColor("orange", "red")
        self.power_meter.setMeterBorder("orange")

        if display_pid_voltage is True:
            layout.addWidget(self.pid_voltage, 6, 6, 1, 5)
            layout.addWidget(self.pid_indicator, 5, 6, 1, 5)
        if stretched_label is True:
            self.current_frequency = StretchedLabel(frequency)
        else:
            self.current_frequency = QtGui.QLabel(frequency)

        self.current_frequency.setFont(QtGui.QFont(shell_font, pointSize=60))
        self.current_frequency.setAlignment(QtCore.Qt.AlignCenter)
        # for a 1080p monitor, change the MinimumWidth to 600 or smaller
        self.current_frequency.setMinimumWidth(800)

        frequency_label = QtGui.QLabel('Set Frequency')
        frequency_label.setAlignment(QtCore.Qt.AlignBottom)
        frequency_label.setFont(QtGui.QFont(shell_font, pointSize=13))

        exposure_label = QtGui.QLabel('Set Exposure (ms)')
        exposure_label.setAlignment(QtCore.Qt.AlignBottom)
        exposure_label.setFont(QtGui.QFont(shell_font, pointSize=13))

        self.setPID = QtGui.QPushButton('Set PID')
        self.setPID.setMaximumHeight(30)
        self.setPID.setFont(QtGui.QFont(shell_font, pointSize=10))

        self.measSwitch = TextChangingButton('WLM Measure')
        self.lockChannel = TextChangingButton('Lock Channel')
        self.zeroVoltage = QtGui.QPushButton('Zero Voltage')
        self.lockChannel.setMinimumWidth(180)

        # editable fields
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

        layout.addWidget(self.spinFreq, 6, 0, 1, 3)
        layout.addWidget(self.spinExp, 6, 3, 1, 3)
        layout.addWidget(self.measSwitch, 0, 6, 1, 5)
        layout.addWidget(self.lockChannel, 1, 6, 1, 5)
        layout.addWidget(self.setPID, 2, 6, 1, 5)
        layout.addWidget(chan_name, 0, 0, 1, 6)
        layout.addWidget(config_title, 3, 6, 1, 5)
        layout.addWidget(config_label, 4, 6, 1, 5)
        layout.addWidget(self.current_frequency, 1, 0, 4, 6)
        layout.addWidget(frequency_label, 5, 0, 1, 1)
        layout.addWidget(exposure_label, 5, 3, 1, 3)
        layout.addWidget(self.power_meter, 0, 11, 7, 1)

        layout.minimumSize()

        self.setLayout(layout)

    def set_exposure_range(self, exp_range):
        self.spinExp.setRange(exp_range)

    def set_freq_range(self, freq_range):
        self.spinFreq.setRange(freq_range)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    icon = QCustomWavemeterChannel('Repumpe', 1, 4, 'Under Exposed', False, True)
    icon.show()
    app.exec_()
