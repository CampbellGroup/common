'''
Created on Mar 25, 2016

@author: Anthony Ransford
'''

from twisted.internet.defer import inlineCallbacks
from common.lib.clients.connection import connection
from PyQt4 import QtGui, QtCore
from common.lib.clients.qtui.switch import QCustomSwitchChannel

SIGNALID1 = 421956
SIGNALID2 = 444296
SIGNALID3 = 123462
SIGNALID4 = 649731

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
        yield self.server.signal__stat_changed(SIGNALID4)

        yield self.server.addListener(listener=self.update_current, source=None, ID=SIGNALID1)
        yield self.server.addListener(listener=self.update_power, source=None, ID=SIGNALID2)
        yield self.server.addListener(listener=self.update_temp, source=None, ID=SIGNALID3)
        yield self.server.addListener(listener=self.update_stat, source=None, ID=SIGNALID4)

        self.initialize_GUI()
    
    @inlineCallbacks   
    def initialize_GUI(self):  
        layout = QtGui.QGridLayout() 
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(18)
        
        self.title = QtGui.QLabel('Millenia eV Pump Laser')
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.title.setFont(font)
        self.title.setAlignment(QtCore.Qt.AlignCenter)
        
        self.templabel = QtGui.QLabel('Diode Temp degC')
        self.currentlabel = QtGui.QLabel('Current')
        self.powerlabel = QtGui.QLabel('Power')
        self.powercontrollabel = QtGui.QLabel('Power Control')
        self.statuslabel = QtGui.QLabel('Laser Status: ')
        self.currentcontrollabel = QtGui.QLabel('Current Control (A)')
        self.controlmodelabel = QtGui.QLabel('Control Mode')
        
        self.controlcombo = QtGui.QComboBox()
        self.controlcombo.addItems(['Power Control','Current Control'])

        self.powerspinbox = QtGui.QDoubleSpinBox()
        self.powerspinbox.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.powerspinbox.setDecimals(2)
        self.powerspinbox.setSingleStep(0.01)
        self.powerspinbox.setRange(0.0,15.0)
        self.powerspinbox.valueChanged.connect(self.change_power)
        self.powerspinbox.setKeyboardTracking(False)
        
        self.currentspinbox = QtGui.QDoubleSpinBox()
        self.currentspinbox.setFont(QtGui.QFont('MS Shell Dlg 2',pointSize=16))
        self.currentspinbox.setDecimals(3)
        self.currentspinbox.setSingleStep(0.001)
        self.currentspinbox.setRange(0.0,7.2)
        self.currentspinbox.valueChanged.connect(self.change_current)
        self.currentspinbox.setKeyboardTracking(False)
        
        self.tempdisplay = QtGui.QLCDNumber()
        self.tempdisplay.setDigitCount(5)

        self.currentprogbar = QtGui.QProgressBar()
        self.currentprogbar.setOrientation(QtCore.Qt.Vertical)
        
        self.laserswitch = QCustomSwitchChannel('Laser',('On','Off'))
        self.shutterswitch = QCustomSwitchChannel('Shutter',('Open','Closed'))

        self.powerprogbar = QtGui.QProgressBar()
        self.powerprogbar.setOrientation(QtCore.Qt.Vertical)
        self.powerprogbar.setMaximum(100)
        self.powerprogbar.setMinimum(0)

        layout.addWidget(self.title,               0, 0, 1, 3)
        layout.addWidget(self.currentprogbar,      2, 0, 8, 1)
        layout.addWidget(self.powerprogbar,        2, 1, 8, 1)
        layout.addWidget(self.currentlabel,        1, 0, 1, 1)
        layout.addWidget(self.powerlabel,          1, 1, 1, 1)
        layout.addWidget(self.templabel,          10, 0, 1, 2)
        layout.addWidget(self.statuslabel,        11, 0, 1, 1)
        layout.addWidget(self.tempdisplay,         9, 2, 4, 1)
        layout.addWidget(self.laserswitch,         6, 2)
        layout.addWidget(self.shutterswitch,       7, 2)
        layout.addWidget(self.powercontrollabel,   2, 2) 
        layout.addWidget(self.currentcontrollabel, 4, 2)        
        layout.addWidget(self.powerspinbox,        3, 2)
        layout.addWidget(self.currentspinbox,      5, 2)
        layout.addWidget(self.controlcombo,        1, 2)
        
        self.laserswitch.TTLswitch.toggled.connect(self.on_laser_toggled)
        self.shutterswitch.TTLswitch.toggled.connect(self.on_shutter_toggled)
        self.controlcombo.activated[str].connect(self.change_control)
        self.freeze_mode()
        # This initializations need to be at the end so that the widgets connected to active signals are created quickly (indicators)
        initpower = yield self.server.get_power_setpoint()
        self.powerspinbox.setValue(initpower['W'])
        
        initcurrent = yield self.server.get_current_setpoint()
        self.currentspinbox.setValue(initcurrent['A'])
        
        initOn = yield self.server.diode_status()
        self.laserswitch.TTLswitch.setChecked(initOn)
        
        self.setLayout(layout)

    @inlineCallbacks
    def on_shutter_toggled(self, value):  
        yield self.server.toggle_shutter(value)
        
    @inlineCallbacks
    def on_laser_toggled(self, value):  
        yield self.server.toggle_laser(value)
        
    @inlineCallbacks
    def change_power(self, value):
        yield self.server.set_power(self.U(value, 'W'))
        
    @inlineCallbacks
    def change_current(self, value):
        yield self.server.set_current(self.U(value, 'A'))
        
    @inlineCallbacks
    def change_control(self, mode):
        
        diodestatus = yield self.server.diode_status()
        if diodestatus == True:
            yield self.freeze_mode()
            
        elif diodestatus == False:
            if mode == 'Current Control':
                yield self.server.set_control_mode('current')
                yield self.freeze_mode()
            elif mode == 'Power Control':
                yield self.server.set_control_mode('power')
                yield self.freeze_mode()
            else:
                yield None
    @inlineCallbacks            
    def freeze_mode(self):

        lastmode = yield self.server.get_control_mode()
        if lastmode == 'current':
            self.controlcombo.setCurrentIndex(1)
            self.powerspinbox.setEnabled(False)
            self.currentspinbox.setEnabled(True)
        elif lastmode == 'power':
            self.controlcombo.setCurrentIndex(0)
            self.powerspinbox.setEnabled(True)
            self.currentspinbox.setEnabled(False)
        else:
            self.controlcombo.setCurrentIndex(-1)
        
    def update_current(self,c, current):
        currentperc = current['A']*100/24.0
        self.currentprogbar.setValue(currentperc)
        self.currentprogbar.setFormat(str(current['A']) + 'A')

    def update_power(self,c, power):
        powerperc = power['W']*100/15.0
        self.powerprogbar.setValue(powerperc)
        self.powerprogbar.setFormat(str(power['W']) + 'W')
        
    def update_temp(self,c, temp):
        self.tempdisplay.display(str(temp['degC']))
        
    def update_stat(self,c, stat):
        css_text = "<span style>Laser Status: <br/></span>" 
        if stat == 'System Ready':
            css_text += "<span style='color:#00ff00;'>%s</span>" % stat
        else: 
            css_text += "<span style='color:#ff0000;'>%s</span>" % stat
        self.statuslabel.setText(css_text)

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