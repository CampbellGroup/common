import sys
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from common.lib.clients.qtui.q_custom_text_changing_button import TextChangingButton


class QCustomFreqPower(QFrame):
    def __init__(self, title, switchable=True, parent=None):
        QWidget.__init__(self, parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.make_layout(title, switchable)

    def make_layout(self, title, switchable):
        layout = QGridLayout()
        # labels
        title = QLabel(title)
        title.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        freq_label = QLabel("Frequency (MHz)")
        power_label = QLabel("Power (dBm)")
        if switchable:
            layout.addWidget(title, 0, 0, 1, 3)
        else:
            layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(freq_label, 1, 0, 1, 1)
        layout.addWidget(power_label, 1, 1, 1, 1)
        # editable fields
        self.freq_spinbox = QDoubleSpinBox()
        self.freq_spinbox.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=14))
        self.freq_spinbox.setDecimals(3)
        self.freq_spinbox.setSingleStep(0.1)
        self.freq_spinbox.setRange(10.0, 250.0)
        self.freq_spinbox.setKeyboardTracking(False)
        self.power_spinbox = QDoubleSpinBox()
        self.power_spinbox.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=14))
        self.power_spinbox.setDecimals(3)
        self.power_spinbox.setSingleStep(0.1)
        self.power_spinbox.setRange(-145.0, 30.0)
        self.power_spinbox.setKeyboardTracking(False)
        layout.addWidget(self.freq_spinbox, 2, 0)
        layout.addWidget(self.power_spinbox, 2, 1)
        if switchable:
            self.switch_button = TextChangingButton(("I", "O"))
            layout.addWidget(self.switch_button, 2, 2)
        self.setLayout(layout)

    def set_power_range(self, powerrange):
        self.power_spinbox.setRange(*powerrange)

    def set_freq_range(self, freqrange):
        self.freq_spinbox.setRange(*freqrange)

    def set_power_no_signal(self, power):
        self.power_spinbox.blockSignals(True)
        self.power_spinbox.setValue(power)
        self.power_spinbox.blockSignals(False)

    def set_freq_no_signal(self, freq):
        self.freq_spinbox.blockSignals(True)
        self.freq_spinbox.setValue(freq)
        self.freq_spinbox.blockSignals(False)

    def set_state_no_signal(self, state):
        self.switch_button.blockSignals(True)
        self.switch_button.setChecked(state)
        self.switch_button.set_appearance(state)
        self.switch_button.blockSignals(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon = QCustomFreqPower("Control")
    icon.show()
    app.exec_()
