import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from common.lib.clients_py3.qtui.q_custom_text_changing_button import \
    TextChangingButton


class QCustomFreqPower(QtWidgets.QFrame):
    def __init__(self, title, switchable = True, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(title, switchable)

    def makeLayout(self, title, switchable):
        layout = QtWidgets.QGridLayout()
        #labels
        title = QtWidgets.QLabel(title)
        title.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        title.setAlignment(QtCore.Qt.AlignCenter)
        freqlabel = QtWidgets.QLabel('Frequency (MHz)')
        powerlabel = QtWidgets.QLabel('Power (dBm)')
        if switchable:
            layout.addWidget(title,0, 0, 1, 3)
        else:
            layout.addWidget(title,0, 0, 1, 2)
        layout.addWidget(freqlabel,1, 0, 1, 1)
        layout.addWidget(powerlabel,1, 1, 1, 1)
        #editable fields
        self.spinFreq = QtWidgets.QDoubleSpinBox()
        self.spinFreq.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.spinFreq.setDecimals(3)
        self.spinFreq.setSingleStep(0.1)
        self.spinFreq.setRange(10.0,250.0)
        self.spinFreq.setKeyboardTracking(False)
        self.spinPower = QtWidgets.QDoubleSpinBox()
        self.spinPower.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.spinPower.setDecimals(3)
        self.spinPower.setSingleStep(0.1)
        self.spinPower.setRange(-145.0, 30.0)
        self.spinPower.setKeyboardTracking(False)
        layout.addWidget(self.spinFreq,     2, 0)
        layout.addWidget(self.spinPower,    2, 1)
        if switchable:
            self.buttonSwitch = TextChangingButton(("I", "O"))
            layout.addWidget(self.buttonSwitch, 2, 2)
        self.setLayout(layout)

    def setPowerRange(self, powerrange):
        self.spinPower.setRange(*powerrange)

    def setFreqRange(self, freqrange):
        self.spinFreq.setRange(*freqrange)

    def setPowerNoSignal(self, power):
        self.spinPower.blockSignals(True)
        self.spinPower.setValue(power)
        self.spinPower.blockSignals(False)

    def setFreqNoSignal(self, freq):
        self.spinFreq.blockSignals(True)
        self.spinFreq.setValue(freq)
        self.spinFreq.blockSignals(False)

    def setStateNoSignal(self, state):
        self.buttonSwitch.blockSignals(True)
        self.buttonSwitch.setChecked(state)
        self.buttonSwitch.setAppearance(state)
        self.buttonSwitch.blockSignals(False)

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    icon = QCustomFreqPower('Control')
    icon.show()
    app.exec_()
