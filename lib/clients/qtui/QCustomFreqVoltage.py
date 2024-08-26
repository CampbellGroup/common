import sys
from PyQt4 import QtGui, QtCore


class QCustomFreqVoltage(QtGui.QFrame):
    def __init__(self, title, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(title)

    def makeLayout(self, title):
        layout = QtGui.QGridLayout()
        # labels
        title = QtGui.QLabel(title)
        title.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        title.setAlignment(QtCore.Qt.AlignCenter)
        freqlabel = QtGui.QLabel("Frequency (Hz)")
        voltagelabel = QtGui.QLabel("VPP (V)")
        layout.addWidget(freqlabel, 1, 0, 1, 1)
        layout.addWidget(voltagelabel, 1, 1, 1, 1)
        # editable fields
        self.spinFreq = QtGui.QDoubleSpinBox()
        self.spinFreq.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        self.spinFreq.setDecimals(3)
        self.spinFreq.setSingleStep(0.1)
        self.spinFreq.setRange(10.0, 250.0)
        self.spinFreq.setKeyboardTracking(False)
        self.spinVoltage = QtGui.QDoubleSpinBox()
        self.spinVoltage.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        self.spinVoltage.setDecimals(2)
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
    app = QtGui.QApplication(sys.argv)
    icon = QCustomFreqVoltage("Control")
    icon.show()
    app.exec_()
