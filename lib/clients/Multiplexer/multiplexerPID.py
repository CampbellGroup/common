import sys

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *


class QCustomPID(QFrame):
    def __init__(self, DACPort, parent=None):
        QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(DACPort)

    def makeLayout(self, DACPort):
        layout = QGridLayout()
        pLabel = QLabel("P")
        pLabel.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        pLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        iLabel = QLabel("I")
        iLabel.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        iLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        dLabel = QLabel("D")
        dLabel.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        dLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        dtLabel = QLabel("dt")
        dtLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        dtLabel.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        sensLabel = QLabel("PID Sensitivity")
        sensLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        sensLabel.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        factorLabel = QLabel("Factor (V)")
        factorLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        factorLabel.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        exponentLabel = QLabel("THz*10^")
        exponentLabel.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        exponentLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        polarityLabel = QLabel("Polarity")
        polarityLabel.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        polarityLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

        # editable fields
        self.spinP = QDoubleSpinBox()
        self.spinP.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        self.spinP.setDecimals(3)
        self.spinP.setSingleStep(0.001)
        self.spinP.setRange(0, 100)
        self.spinP.setKeyboardTracking(False)

        self.spinI = QDoubleSpinBox()
        self.spinI.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        self.spinI.setDecimals(3)
        self.spinI.setSingleStep(0.001)
        self.spinI.setRange(0, 100)
        self.spinI.setKeyboardTracking(False)

        self.spinD = QDoubleSpinBox()
        self.spinD.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        self.spinD.setDecimals(3)
        self.spinD.setSingleStep(0.001)
        self.spinD.setRange(0, 100)
        self.spinD.setKeyboardTracking(False)

        self.spinDt = QDoubleSpinBox()
        self.spinDt.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        self.spinDt.setDecimals(3)
        self.spinDt.setSingleStep(0.001)
        self.spinDt.setRange(0, 100)
        self.spinDt.setKeyboardTracking(False)

        self.spinFactor = QDoubleSpinBox()
        self.spinFactor.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        self.spinFactor.setDecimals(2)
        self.spinFactor.setSingleStep(0.01)
        self.spinFactor.setRange(0, 9.99)
        self.spinFactor.setKeyboardTracking(False)

        self.spinExp = QDoubleSpinBox()
        self.spinExp.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        self.spinExp.setDecimals(0)
        self.spinExp.setSingleStep(1)
        self.spinExp.setRange(-6, 3)
        self.spinExp.setKeyboardTracking(False)

        self.polarityBox = QComboBox(self)
        self.polarityBox.addItem("Positive")
        self.polarityBox.addItem("Negative")

        self.useDTBox = QCheckBox("Use Const dt")
        self.useDTBox.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))

        layout.addWidget(pLabel, 0, 0, 1, 1)
        layout.addWidget(self.spinP, 0, 1, 1, 1)
        layout.addWidget(iLabel, 1, 0, 1, 1)
        layout.addWidget(self.spinI, 1, 1, 1, 1)
        layout.addWidget(dLabel, 2, 0, 1, 1)
        layout.addWidget(self.spinD, 2, 1, 1, 1)

        layout.addWidget(self.useDTBox, 0, 3, 1, 1)
        layout.addWidget(dtLabel, 1, 2, 1, 1)
        layout.addWidget(self.spinDt, 1, 3, 1, 1)
        layout.addWidget(polarityLabel, 2, 2, 1, 1)
        layout.addWidget(self.polarityBox, 2, 3, 1, 1)

        layout.addWidget(sensLabel, 0, 4, 1, 2)
        layout.addWidget(factorLabel, 1, 4, 1, 1)
        layout.addWidget(self.spinFactor, 1, 5, 1, 1)
        layout.addWidget(exponentLabel, 2, 4, 1, 1)
        layout.addWidget(self.spinExp, 2, 5, 1, 1)

        layout.minimumSize()

        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon = QCustomPID(1)
    icon.show()
    app.exec_()
