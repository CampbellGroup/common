import sys
from PyQt4 import QtGui
from common.lib.clients.qtui.q_custom_text_changing_button import TextChangingButton


class QCustomSwitchChannel(QtGui.QFrame):
    def __init__(self, title, labels=None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(title, labels)

    def makeLayout(self, title, labels):
        layout = QtGui.QGridLayout()
        title = QtGui.QLabel(title)
        title.setFont(QtGui.QFont('MS Shell Dlg 2', pointSize=16))
        layout.addWidget(title, 0, 0, 1, 3)

        # editable fields

        self.TTLswitch = TextChangingButton(labels)
        self.TTLswitch.setAutoDefault(True)
        layout.addWidget(self.TTLswitch, 1, 0, 1, 3)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    icon = QCustomSwitchChannel('369', ('Opened', 'Closed'))
    icon.show()
    app.exec_()
