from PyQt4 import QtGui, QtCore


class TextChangingButton(QtGui.QPushButton):
    """Button that changes its text to ON or OFF and colors when it's pressed.
    """
    def __init__(self, labels=None, parent=None):
        super(TextChangingButton, self).__init__(parent)
        self.labels = labels
        self.setCheckable(True)
        self.setFont(QtGui.QFont('MS Shell Dlg 2', pointSize=10))
        self.setSizePolicy(QtGui.QSizePolicy.Minimum,
                           QtGui.QSizePolicy.Minimum)
        # connect signal for appearance changing
        self.toggled.connect(self.setAppearance)
        self.setAppearance(self.isDown())

    def setAppearance(self, down):
        if down:
            if self.labels is None:
                self.setText('On')
            else:
                self.setText(self.labels[0])
            self.setPalette(QtGui.QPalette(QtCore.Qt.darkGreen))
        else:
            if self.labels is None:
                self.setText('Off')
            else:
                self.setText(self.labels[1])
            self.setPalette(QtGui.QPalette(QtCore.Qt.black))

    def sizeHint(self):
        return QtCore.QSize(37, 26)
