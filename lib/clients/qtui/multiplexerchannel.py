import sys
from PyQt4 import QtGui, QtCore

class StretchedLabel(QtGui.QLabel):
    def __init__(self, *args, **kwargs):
        QtGui.QLabel.__init__(self, *args, **kwargs)
        self.setMinimumSize(400, 150)
#        self.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
#        self.setFont(QtGui.QFont('MS Shell Dlg 2', pointSize=50))


    def resizeEvent(self, evt):
               
        font = self.font()
        font.setPixelSize(self.width() * 0.14 - 14 )
        self.setFont(font)

class TextChangingButton(QtGui.QPushButton):
    """Button that changes its text to ON or OFF and colors when it's pressed""" 
    def __init__(self, addtext = None, parent = None):
        super(TextChangingButton, self).__init__(parent)
        self.setCheckable(True)
        self.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=10))
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        #connect signal for appearance changing
        self.addtext = addtext
        if self.addtext == None: 
            self.addtext = ''
        else:
            self.addtext = self.addtext + '       '
        self.toggled.connect(self.setAppearance)
        self.setAppearance(self.isDown())
    
    def setAppearance(self, down, addtext = None):
        if down:
            self.setText(self.addtext + 'On')
            self.setPalette(QtGui.QPalette(QtCore.Qt.darkGreen))
        else:
            self.setText(self.addtext + 'Off')
            self.setPalette(QtGui.QPalette(QtCore.Qt.black))
    def sizeHint(self):
        return QtCore.QSize(37, 26)

class QCustomWavemeterChannel(QtGui.QFrame):
    def __init__(self, title, frequency, stretchedlabel, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(title, frequency, stretchedlabel)
    
    def makeLayout(self, title, frequency, stretchedlabel):
        layout = QtGui.QGridLayout()
        title = QtGui.QLabel(title)
        title.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        title.setAlignment(QtCore.Qt.AlignCenter)
        if stretchedlabel == True:
            self.currentfrequency = StretchedLabel(frequency)
        else:
            self.currentfrequency = QtGui.QLabel(frequency)
        self.currentfrequency.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=50))
        self.currentfrequency.setAlignment(QtCore.Qt.AlignCenter)
#        self.currentfrequency.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        frequencylabel = QtGui.QLabel('Set Frequency')
        exposurelabel = QtGui.QLabel('Set Exposure (ms)')
        layout.addWidget(title, 0,0,1,3)
        layout.addWidget(self.currentfrequency,1, 0, 1, 3)
        layout.addWidget(frequencylabel,2, 0, 1, 1)
        layout.addWidget(exposurelabel,2, 1, 1, 1)
        #editable fields
        self.spinFreq = QtGui.QDoubleSpinBox()
        self.spinFreq.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.spinFreq.setDecimals(6)
        self.spinFreq.setSingleStep(0.000001)
        self.spinFreq.setRange(300.0,800.0)
        self.spinFreq.setKeyboardTracking(False)
        self.spinExp = QtGui.QDoubleSpinBox()
        self.spinExp.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.spinExp.setDecimals(0)
        self.spinExp.setSingleStep(1)
        self.spinExp.setRange(0, 2000.0)
        self.spinExp.setKeyboardTracking(False)
        layout.addWidget(self.spinFreq,     3, 0)
        layout.addWidget(self.spinExp,    3, 1)
        self.measSwitch = TextChangingButton('WLM Measure')
        layout.addWidget(self.measSwitch, 3, 2)
        layout.minimumSize()
            
        self.setLayout(layout)
    
    def setExpRange(self, exprange):
        self.spinExp.setRange(exprange)
    
    def setFreqRange(self, freqrange):
        self.spinFreq.setRange(freqrange)
        

if __name__=="__main__":
    app = QtGui.QApplication(sys.argv)
    icon = QCustomWavemeterChannel('369','Under Exposed', True)
    icon.show()
    app.exec_()
