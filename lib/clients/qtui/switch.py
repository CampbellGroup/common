import sys
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from common.lib.clients.qtui.q_custom_text_changing_button import TextChangingButton


class QCustomSwitchChannel(QFrame):
    def __init__(self, title, labels=None, parent=None):
        QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(title, labels)

    def makeLayout(self, title, labels):
        layout = QGridLayout()
        title = QLabel(title)
        title.setFont(QtGui.QFont("MS Shell Dlg 2", pointSize=16))
        layout.addWidget(title, 0, 0, 1, 3)

        # editable fields

        self.TTLswitch = TextChangingButton(labels)
        self.TTLswitch.setAutoDefault(True)
        layout.addWidget(self.TTLswitch, 1, 0, 1, 3)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon = QCustomSwitchChannel("369", ("Opened", "Closed"))
    icon.show()
    app.exec_()
