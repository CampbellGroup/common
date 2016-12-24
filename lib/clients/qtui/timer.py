import sys
from PyQt4 import QtGui, QtCore
from twisted.internet.task import LoopingCall

class QCustomTimer(QtGui.QFrame):
    def __init__(self, title, show_control=True, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(title, show_control)
        
    def makeLayout(self, title, show_control):
        layout = QtGui.QGridLayout()
        title = QtGui.QLabel(title)
        title.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        layout.addWidget(title, 0,0,1,3)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.tick)
        self.time = 0
        self.timer.start(1000)
        self.timerlabel = QtGui.QLabel('00:00:00')
        self.timerlabel.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=35))
        
        if show_control:
            self.start_button = QtGui.QPushButton('Start')
            self.start_button.clicked.connect(self.start)
            layout.addWidget(self.start_button, 2, 0)
            
            self.stop_button = QtGui.QPushButton('Stop')
            self.stop_button.clicked.connect(self.stop)
            layout.addWidget(self.stop_button, 2, 1)
            
            self.reset_button = QtGui.QPushButton('Reset')
            self.reset_button.clicked.connect(self.reset)
            layout.addWidget(self.reset_button, 2, 2)
            
        layout.addWidget(self.timerlabel, 1, 0, 1, 3)
        self.setLayout(layout)
        
    def stop(self):
        self.timer.stop()
        
    def start(self):
        self.timer.start(1000)
        
    def reset(self):
        self.time = 0
        self.timerlabel.setText('00:00:00')
        
    def tick(self):
        self.time += 1
        m, s = divmod(self.time, 60)
        h, m = divmod(m, 60)

        if len(str(s)) == 1:
            s_string = '0' + str(s)
        else:
            s_string = str(s)

        if len(str(m)) == 1:
            m_string = '0' + str(m)
        else:
            m_string = str(m)

        if len(str(h)) == 1:
            h_string = '0' + str(h)
        else:
            h_string = str(h)

        self.timerlabel.setText(h_string + ':' + m_string + ':' + s_string)
        
if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    icon = QCustomTimer('Load Time')
    icon.show()
    app.exec_()
