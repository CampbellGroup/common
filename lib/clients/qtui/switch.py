import sys
from PyQt4 import QtGui, QtCore

class TextChangingButton(QtGui.QPushButton):
    """Button that changes its text to ON or OFF and colors when it's pressed""" 
    def __init__(self, labels = None, parent = None):
        super(TextChangingButton, self).__init__(parent)
        self.labels = labels
        self.setCheckable(True)
        self.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=10))
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        #connect signal for appearance changing
        self.toggled.connect(self.setAppearance)
        self.setAppearance(self.isDown())
    
    def setAppearance(self, down):
        if down:
            if self.labels == None:
                self.setText('On')
            else:
                self.setText(self.labels[0])
            self.setPalette(QtGui.QPalette(QtCore.Qt.darkGreen))
        else:
            if self.labels == None:
                self.setText('Off')
            else:
                self.setText(self.labels[1])
            self.setPalette(QtGui.QPalette(QtCore.Qt.black))
    
    def sizeHint(self):
        return QtCore.QSize(37, 26)

class QCustomSwitchChannel(QtGui.QFrame):
    def __init__(self, title, labels = None, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(title, labels)
    
    def makeLayout(self, title, labels):
        layout = QtGui.QGridLayout()
        title = QtGui.QLabel(title)
        title.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        layout.addWidget(title, 0,0,1,3)
        
        #editable fields

        self.TTLswitch = TextChangingButton(labels)
        self.TTLswitch.setAutoDefault(True)
        layout.addWidget(self.TTLswitch, 1,0, 2,1)          
        self.setLayout(layout)
    

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    icon = QCustomSwitchChannel('369', ('Opened', 'Closed'))
    icon.show()
    app.exec_()