'''
Created on Mar 25, 2016

@author: qsimexpcontrol
'''

from twisted.internet.defer import inlineCallbacks
from common.lib.clients.connection import connection
from PyQt4 import QtGui, QtCore
from common.lib.clients.qtui.switch import QCustomSwitchChannel
from common.lib.clients.qtui.QCustomSpinBox import QCustomSpinBox

SIGNALID1 = 421956
SIGNALID2 = 444296
SIGNALID3 = 123462

class eVPumpClient(QtGui.QWidget):
    
    def __init__(self, reactor, cxn = None):
        super(eVPumpClient, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.cxn = cxn
        self.reactor = reactor 
        from labrad.units import WithUnit as U
        self.U = U        
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection to pumpserver and
        connects incoming signals to relavent functions
        
        """
        if self.cxn is None:
            self.cxn = connection(name='eV Pump Client')
            yield self.cxn.connect()
        self.server = yield self.cxn.get_server('eVPump')

        yield self.server.signal__current_changed(SIGNALID1)
        yield self.server.signal__power_changed(SIGNALID2)
        yield self.server.signal__temp_changed(SIGNALID3)

        yield self.server.addListener(listener = self.updateCurrent, source = None, ID = SIGNALID1)
        yield self.server.addListener(listener = self.updatePower, source = None, ID = SIGNALID2)
        yield self.server.addListener(listener = self.updateTemp,  source = None, ID = SIGNALID3)

        self.initializeGUI()
    
    @inlineCallbacks    
    def initializeGUI(self):  
        layout = QtGui.QGridLayout() 
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(18)
        self.title = QtGui.QLabel('Millenia eV Pump Laser')
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.title.setFont(font)
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        self.templabel = QtGui.QLabel('Laser Diode Temp')
        self.currentlabel = QtGui.QLabel('Current')
        self.powerlabel = QtGui.QLabel('Power')

        self.powerspinbox = QtGui.QDoubleSpinBox()
        self.powerspinbox.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.powerspinbox.setDecimals(2)
        self.powerspinbox.setSingleStep(0.01)
        self.powerspinbox.setRange(0.0,15.0)
        self.powerspinbox.valueChanged.connect(self.changePower)
        self.powerspinbox.setKeyboardTracking(False)
        initpower = yield self.server.read_power()
        self.powerspinbox.setValue(initpower['W'])
        
        self.tempdisplay = QtGui.QLCDNumber()
        self.tempdisplay.setDigitCount(5)

        self.currentprogbar = QtGui.QProgressBar()
        self.currentprogbar.setOrientation(QtCore.Qt.Vertical)
        
        self.laserswitch = QCustomSwitchChannel('Laser',('On','Off'))
        self.shutterswitch = QCustomSwitchChannel('Shutter',('Open','Closed'))

        self.laserswitch.TTLswitch.toggled.connect(self.onLasertoggled)
        self.shutterswitch.TTLswitch.toggled.connect(self.onShuttertoggled)

        self.powerprogbar = QtGui.QProgressBar()
        self.powerprogbar.setOrientation(QtCore.Qt.Vertical)
        self.powerprogbar.setGeometry(30, 40, 25, 200)
        self.powerprogbar.setMaximum(100)
        self.powerprogbar.setMinimum(0)

        layout.addWidget(self.title,          0,0,1,2)
        layout.addWidget(self.currentprogbar, 2,0,8,1)
        layout.addWidget(self.powerprogbar,   2,1,8,1)
        layout.addWidget(self.currentlabel,   1,0,1,1)
        layout.addWidget(self.powerlabel,     1,1,1,1)
        layout.addWidget(self.templabel,      10,0,1,1)
        layout.addWidget(self.tempdisplay,    10,1,1,1)
        layout.addWidget(self.laserswitch,    8,8)
        layout.addWidget(self.shutterswitch,    9,8)
        layout.addWidget(self.powerspinbox,       4,8)

        self.setLayout(layout)

    @inlineCallbacks
    def onShuttertoggled(self, value):  
        yield self.server.toggle_shutter(value)
        
    @inlineCallbacks
    def onLasertoggled(self, value):  
        yield self.server.toggle_laser(value)
        
    @inlineCallbacks
    def changePower(self, value):
        yield self.server.set_power(self.U(value, 'W'))
        
    def updateCurrent(self,c, current):
        currentperc = current['A']*100/24.0
        self.currentprogbar.setValue(currentperc)
        self.currentprogbar.setFormat(str(current['A']) + 'A')

    def updatePower(self,c, power):
        powerperc = power['W']*100/15.0
        self.powerprogbar.setValue(powerperc)
        self.powerprogbar.setFormat(str(power['W']) + 'W')
        
    def updateTemp(self,c, temp):
        self.tempdisplay.display(str(temp['degC']))

    def closeEvent(self, x):
        self.reactor.stop()
        
if __name__ == "__main__":
    a = QtGui.QApplication( [] )
    from common.lib.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    PumpWidget = eVPumpClient(reactor)
    PumpWidget.show()
    run = reactor.run()  # @UndefinedVariable