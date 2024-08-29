import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from common.lib.clients.qtui.QCustomPowerMeter import MQProgressBar
from common.lib.clients.qtui.q_custom_text_changing_button import (
    TextChangingButton as _TextChangingButton,
)


class StretchedLabel(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args)

    def resizeEvent(self, evt):
        font = self.font()
        font.setPixelSize(int(self.width() * 0.14 - 14))
        self.setFont(font)


class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)


# noinspection PyArgumentList
class QMiniWavemeterChannel(QFrame):
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

        self.pid_voltage = QLabel("DAC Voltage (mV)  -.-")
        self.pid_voltage.setFont(QFont(shell_font, pointSize=12))

        # if display_pid_voltage:
        #     self.pid_indicator = SlideIndicator([-10.0, 10.0])

        self.power_meter = MQProgressBar()
        self.power_meter.setOrientation(Qt.Orientation.Vertical)
        self.power_meter.setMeterColor("orange", "red")
        self.power_meter.setMeterBorder("orange")

        if stretched_label is True:
            self.current_frequency = StretchedLabel(frequency)
        else:
            self.current_frequency = QLabel(frequency)

        self.current_frequency.setFont(QFont(shell_font, pointSize=22))
        self.current_frequency.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_frequency.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding
        )

        layout = QHBoxLayout()

        left_grid_widget = QWidget()
        left_grid_layout = QGridLayout()

        left_grid_layout.addWidget(chan_name, 0, 0, 1, 6)
        left_grid_layout.addWidget(self.current_frequency, 1, 0, 5, 6)
        left_grid_widget.setLayout(left_grid_layout)
        layout.addWidget(left_grid_widget, 3)

        # right_col.addWidget(self.pid_indicator)
        # right_col.addWidget(self.pid_voltage)

        layout.addWidget(self.power_meter, 0, Qt.AlignRight)

        layout.minimumSize()

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon = QMiniWavemeterChannel("Repumper", 1, 4, "Under Exposed", True, True)
    icon.show()
    app.exec_()
