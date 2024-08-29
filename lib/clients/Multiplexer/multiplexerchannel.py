import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from common.lib.clients.qtui.QCustomPowerMeter import MQProgressBar
from common.lib.clients.qtui.QCustomSlideIndicator import SlideIndicator
from common.lib.clients.qtui.q_custom_text_changing_button import (
    TextChangingButton as _TextChangingButton,
)


class StretchedLabel(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args)
        self.setMinimumSize(QSize(350, 100))

    def resizeEvent(self, evt):
        font = self.font()
        font.setPixelSize(int(self.width() * 0.14 - 14))
        self.setFont(font)


class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)


# noinspection PyArgumentList
class QCustomWavemeterChannel(QFrame):
    def __init__(
        self,
        chan_name,
        wm_channel,
        dac_port,
        frequency,
        stretched_label,
        display_pid_voltage=None,
        display_channel_lock=None,
        parent=None,
    ):
        QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.make_layout(
            chan_name,
            wm_channel,
            dac_port,
            frequency,
            stretched_label,
            display_pid_voltage,
            display_channel_lock,
        )

    def make_layout(
        self,
        name,
        wm_channel,
        dac_port,
        frequency,
        stretched_label,
        display_pid_voltage,
        display_channel_lock,
    ):

        shell_font = "MS Shell Dlg 2"
        chan_name = QLabel(name)
        chan_name.setFont(QFont(shell_font, pointSize=16))
        chan_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        dac_label = QLabel("DAC Port " + str(dac_port))
        dac_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dac_label.setFont(QFont(shell_font, pointSize=13))

        wm_chan_label = QLabel("WM Channel " + str(wm_channel))
        wm_chan_label.setFont(QFont(shell_font, pointSize=13))
        wm_chan_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pid_voltage = QLabel("DAC Voltage (mV)  -.-")
        self.pid_voltage.setFont(QFont(shell_font, pointSize=12))

        if display_pid_voltage:
            self.pid_indicator = SlideIndicator([-10.0, 10.0])

        self.power_meter = MQProgressBar()
        self.power_meter.setOrientation(Qt.Orientation.Vertical)
        self.power_meter.setMeterColor("orange", "red")
        self.power_meter.setMeterBorder("orange")

        if stretched_label is True:
            self.current_frequency = StretchedLabel(frequency)
        else:
            self.current_frequency = QLabel(frequency)

        self.current_frequency.setFont(QFont(shell_font, pointSize=60))
        self.current_frequency.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_frequency.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding
        )

        frequency_label = QLabel("Set Frequency")
        frequency_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        frequency_label.setFont(QFont(shell_font, pointSize=13))

        exposure_label = QLabel("Set Exposure (ms)")
        exposure_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        exposure_label.setFont(QFont(shell_font, pointSize=13))

        self.set_pid_button = QPushButton("Set PID")
        self.set_pid_button.setMaximumHeight(30)
        self.set_pid_button.setFont(QFont(shell_font, pointSize=10))

        self.measure_button = TextChangingButton("WLM Measure")

        self.lock_channel_button = TextChangingButton("Lock Channel")

        self.zero_voltage_button = QPushButton("Zero Voltage")
        self.zero_voltage_button.setMaximumHeight(30)
        self.zero_voltage_button.setFont(QFont(shell_font, pointSize=10))

        # editable fields
        self.freq_spinbox = QDoubleSpinBox()
        self.freq_spinbox.setFont(QFont(shell_font, pointSize=16))
        self.freq_spinbox.setDecimals(6)
        self.freq_spinbox.setSingleStep(0.000001)
        self.freq_spinbox.setRange(100.0, 1000.0)
        self.freq_spinbox.setKeyboardTracking(False)

        self.exposure_spinbox = QDoubleSpinBox()
        self.exposure_spinbox.setFont(QFont(shell_font, pointSize=16))
        self.exposure_spinbox.setDecimals(0)
        self.exposure_spinbox.setSingleStep(1)
        self.exposure_spinbox.setRange(
            0, 10000.0
        )  # 10 seconds is the max exposure time
        self.exposure_spinbox.setKeyboardTracking(False)

        layout = QHBoxLayout()

        left_grid_widget = QWidget()
        left_grid_layout = QGridLayout()

        left_grid_layout.addWidget(self.freq_spinbox, 7, 0, 1, 3)
        left_grid_layout.addWidget(self.exposure_spinbox, 7, 3, 1, 3)
        left_grid_layout.addWidget(chan_name, 0, 0, 1, 6)
        left_grid_layout.addWidget(self.current_frequency, 1, 0, 5, 6)
        left_grid_layout.addWidget(frequency_label, 6, 0, 1, 1)
        left_grid_layout.addWidget(exposure_label, 6, 3, 1, 3)
        left_grid_widget.setLayout(left_grid_layout)
        layout.addWidget(left_grid_widget, 3)

        right_col_widget = QWidget()
        right_col = QVBoxLayout()

        right_col.addWidget(self.measure_button)
        if display_channel_lock:
            right_col.addWidget(self.lock_channel_button)
        right_col.addWidget(self.set_pid_button)
        right_col.addWidget(self.zero_voltage_button)
        right_col.addWidget(wm_chan_label)
        right_col.addWidget(dac_label)
        right_col.addStretch()
        if display_pid_voltage:
            right_col.addWidget(self.pid_indicator)
            right_col.addWidget(self.pid_voltage)

        right_col_widget.setLayout(right_col)
        right_col_widget.setMinimumSize(200, 200)
        right_col_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout.addWidget(right_col_widget, 1)

        layout.addWidget(self.power_meter, 0, Qt.AlignRight)

        layout.minimumSize()

        self.setLayout(layout)

    def set_exposure_range(self, exp_range):
        self.exposure_spinbox.setRange(exp_range)

    def set_freq_range(self, freq_range):
        self.freq_spinbox.setRange(freq_range)


class QCustomWavemeterChannelNoPID(QFrame):
    def __init__(self, chan_name, wm_channel, frequency, stretched_label, parent=None):
        QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.make_layout(chan_name, wm_channel, frequency, stretched_label)

    def make_layout(self, name, wm_channel, frequency, stretched_label):

        shell_font = "MS Shell Dlg 2"
        chan_name = QLabel(name)
        chan_name.setFont(QFont(shell_font, pointSize=16))
        chan_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        wm_chan_label = QLabel("WM Channel " + str(wm_channel))
        wm_chan_label.setFont(QFont(shell_font, pointSize=13))
        wm_chan_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.power_meter = MQProgressBar()
        self.power_meter.setOrientation(Qt.Orientation.Vertical)
        self.power_meter.setMeterColor("orange", "red")
        self.power_meter.setMeterBorder("orange")

        if stretched_label is True:
            self.current_frequency = StretchedLabel(str(frequency))
        else:
            self.current_frequency = QLabel(str(frequency))

        self.current_frequency.setFont(QFont(shell_font, pointSize=60))
        self.current_frequency.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_frequency.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding
        )

        exposure_label = QLabel("Set Exposure (ms)")
        exposure_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
        exposure_label.setFont(QFont(shell_font, pointSize=13))

        self.measure_button = TextChangingButton("WLM Measure")

        # editable fields
        self.exposure_spinbox = QDoubleSpinBox()
        self.exposure_spinbox.setFont(QFont(shell_font, pointSize=16))
        self.exposure_spinbox.setDecimals(0)
        self.exposure_spinbox.setSingleStep(1)
        self.exposure_spinbox.setRange(
            0, 10000.0
        )  # 10 seconds is the max exposure time
        self.exposure_spinbox.setKeyboardTracking(False)

        layout = QHBoxLayout()

        left_grid_widget = QWidget()
        left_grid_layout = QGridLayout()

        left_grid_layout.addWidget(self.exposure_spinbox, 7, 3, 1, 3)
        left_grid_layout.addWidget(chan_name, 0, 0, 1, 6)
        left_grid_layout.addWidget(self.current_frequency, 1, 0, 5, 6)
        left_grid_layout.addWidget(exposure_label, 6, 3, 1, 3)
        left_grid_widget.setLayout(left_grid_layout)
        layout.addWidget(left_grid_widget, 3)

        right_col_widget = QWidget()
        right_col = QVBoxLayout()

        right_col.addWidget(self.measure_button)

        right_col.addWidget(wm_chan_label)
        right_col.addStretch()

        right_col_widget.setLayout(right_col)
        right_col_widget.setMinimumSize(200, 200)
        right_col_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        layout.addWidget(right_col_widget, 1)

        layout.addWidget(self.power_meter, 0, Qt.AlignRight)

        layout.minimumSize()

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # icon = QCustomWavemeterChannel("Repumper", 1, 4, "Under Exposed", False, True)
    icon = QCustomWavemeterChannelNoPID("Repumper", 1, "Under Exposed", False)

    icon.show()
    app.exec_()
