from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class FixedWidthButton(QPushButton):
    def __init__(self, text, size):
        super(FixedWidthButton, self).__init__(text)
        self.size = size
        self.setFont(QFont(self.font().family(), pointSize=10))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)

    def sizeHint(self):
        return QSize(*self.size)


class ProgressBar(QProgressBar):
    def __init__(self, reactor, parent=None):
        super(ProgressBar, self).__init__(parent)
        self.reactor = reactor
        self.setFont(QFont(self.font().family(), pointSize=10))
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.set_status("", 0.0)

    def set_status(self, status_name, percentage):
        self.setValue(int(percentage))
        self.setFormat("{0} %p%".format(status_name))

    def closeEvent(self, x):
        self.reactor.stop()
