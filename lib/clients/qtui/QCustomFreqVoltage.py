import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class QCustomFreqVoltage(QFrame):
    def __init__(self, title, parent=None):
        QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(title)

    def makeLayout(self, title):
        layout = QGridLayout()
        # labels
        title = QLabel(title)
        title.setFont(QFont("MS Shell Dlg 2", pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        freqlabel = QLabel("Frequency (Hz)")
        voltagelabel = QLabel("VPP (V)")
        layout.addWidget(freqlabel, 1, 0, 1, 1)
        layout.addWidget(voltagelabel, 1, 1, 1, 1)
        # editable fields
        self.spinFreq = QDoubleSpinBox()
        self.spinFreq.setFont(QFont("MS Shell Dlg 2", pointSize=16))
        self.spinFreq.set_decimals(3)
        self.spinFreq.setSingleStep(0.1)
        self.spinFreq.setRange(10.0, 250.0)
        self.spinFreq.setKeyboardTracking(False)
        self.spinVoltage = QDoubleSpinBox()
        self.spinVoltage.setFont(QFont("MS Shell Dlg 2", pointSize=16))
        self.spinVoltage.set_decimals(2)
        self.spinVoltage.setSingleStep(0.1)
        self.spinVoltage.setRange(-145.0, 30.0)
        self.spinVoltage.setKeyboardTracking(False)
        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(self.spinFreq, 2, 0)
        layout.addWidget(self.spinVoltage, 2, 1)
        self.setLayout(layout)

    def setVoltageRange(self, voltagerange):
        self.spinVoltage.setRange(*voltagerange)

    def setFreqRange(self, freqrange):
        self.spinFreq.setRange(*freqrange)

    def setVoltageNoSignal(self, voltage):
        self.spinVoltage.blockSignals(True)
        self.spinVoltage.setValue(voltage)
        self.spinVoltage.blockSignals(False)

    def setFreqNoSignal(self, freq):
        self.spinFreq.blockSignals(True)
        self.spinFreq.setValue(freq)
        self.spinFreq.blockSignals(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon = QCustomFreqVoltage("Control")
    icon.show()
    app.exec_()
