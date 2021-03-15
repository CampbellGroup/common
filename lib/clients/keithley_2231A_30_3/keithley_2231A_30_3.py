from common.lib.clients.qtui.QCustomSpinBox import QCustomSpinBox
from common.lib.clients.qtui.switch import QCustomSwitchChannel
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui
from common.lib.clients.qtui.q_custom_text_changing_button import \
    TextChangingButton
import time as time


class kiethleyclient(QtGui.QWidget):

    def __init__(self, reactor, parent = None):
        """initializels the GUI creates the reactor
        """
        super(kiethleyclient, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.connect()
        self.reactor = reactor

    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection
        """
        from labrad.wrappers import connectAsync
        from labrad.units import WithUnit as U
        self.U = U
        self.cxn = yield connectAsync(name = "kiethley client")
        self.server = self.cxn.keithley_server
        yield self.server.select_device(0)
        self.initializeGUI()
        
    @inlineCallbacks
    def initializeGUI(self):
        layout = QtGui.QGridLayout()
        self.setWindowTitle('Keithley Power Supply: 2231A-30-3')
        qBox = QtGui.QGroupBox('Kiethley 2231A: Magnetic Field Coils')
        subLayout = QtGui.QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)
        
        #turn remote mode on (nothing will work without it on)
        yield self.server.remote_mode(1)

        # Make remote mode widget
        self.remotewidget = QCustomSwitchChannel('Remote Mode', ('On', 'Off'))
        # Set remote mode button to on
        self.remotewidget.TTLswitch.setChecked(1)
        # If you press the button, it switches it on/off
        self.remotewidget.TTLswitch.toggled.connect(lambda state = self.remotewidget.TTLswitch.isDown(): self.remote_toggled(state))

        # Finds the output setting of each channel
        # Sets the initial condition
        initial_output1 = yield self.server.query_initial(1)
        if bool((initial_output1 & 0b1000)>>3):
            initial_output1 = True
        initial_output2 = yield self.server.query_initial(2)
        if bool((initial_output2 & 0b1000)>>3):
            initial_output2 = True
        initial_output3 = yield self.server.query_initial(3)
        if bool((initial_output3 & 0b1000)>>3):
            initial_output3 = True

        # Gets all initial voltages and currents 
        initial_vals = yield self.server.get_applied_voltage_current()
        
        # Makes widgets for voltage in each channel
        # Sets initial values as found above
        self.volt1widget = QCustomSpinBox('Voltage (V)', (0, 30))
        self.volt1widget.setValues(initial_vals[0][0])
        self.volt2widget = QCustomSpinBox('Voltage (V)', (0, 30))
        self.volt2widget.setValues(initial_vals[1][0])
        self.volt3widget = QCustomSpinBox('Voltage (V)', (0, 5))
        self.volt3widget.setValues(initial_vals[2][0])

        # Makes widgets for current in each channel
        # Sets initial values as found above
        self.amp1widget = QCustomSpinBox('Current (A)', (0, 3))
        self.amp1widget.setValues(initial_vals[0][1])
        self.amp2widget = QCustomSpinBox('Current (A)', (0, 3))
        self.amp2widget.setValues(initial_vals[1][1])
        self.amp3widget = QCustomSpinBox('Current (A)', (0, 3))
        self.amp3widget.setValues(initial_vals[2][1])

        # Makes widget for the output of each channel
        self.output1widget = QCustomSwitchChannel('Output Channel 1', ('On', 'Off'))
        self.output1widget.TTLswitch.setChecked(int(initial_output1))
        self.output2widget = QCustomSwitchChannel('Output Channel 2', ('On', 'Off'))
        self.output2widget.TTLswitch.setChecked(int(initial_output2))
        self.output3widget = QCustomSwitchChannel('Output Channel 3', ('On', 'Off'))
        self.output3widget.TTLswitch.setChecked(int(initial_output3))
        
        # Updates widgets when values are changed through the gui
        self.volt1widget.spinLevel.valueChanged.connect(lambda value = self.volt1widget.spinLevel.value(), chan = 1 : self.voltchanged(chan, value))
        self.volt2widget.spinLevel.valueChanged.connect(lambda value = self.volt2widget.spinLevel.value(), chan = 2 : self.voltchanged(chan, value))
        self.volt3widget.spinLevel.valueChanged.connect(lambda value = self.volt3widget.spinLevel.value(), chan = 3 : self.voltchanged(chan, value))

        self.amp1widget.spinLevel.valueChanged.connect(lambda value = self.amp1widget.spinLevel.value(), chan = 1 : self.ampchanged(chan, value))
        self.amp2widget.spinLevel.valueChanged.connect(lambda value = self.amp2widget.spinLevel.value(), chan = 2 : self.ampchanged(chan, value))
        self.amp3widget.spinLevel.valueChanged.connect(lambda value = self.amp3widget.spinLevel.value(), chan = 3 : self.ampchanged(chan, value))

        self.output1widget.TTLswitch.toggled.connect(lambda state = self.output1widget.TTLswitch.isDown(), chan = 1 : self.output_toggled(chan, state))
        self.output2widget.TTLswitch.toggled.connect(lambda state = self.output2widget.TTLswitch.isDown(), chan = 2 : self.output_toggled(chan, state))
        self.output3widget.TTLswitch.toggled.connect(lambda state = self.output3widget.TTLswitch.isDown(), chan = 3 : self.output_toggled(chan, state))
   
        #Adds widgets to layout
        subLayout.addWidget(self.output1widget, 0,1)
        subLayout.addWidget(self.output2widget, 0,2)
        subLayout.addWidget(self.output3widget, 0,3)
        subLayout.addWidget(self.volt1widget, 1,1)
        subLayout.addWidget(self.volt2widget, 1,2)
        subLayout.addWidget(self.volt3widget, 1,3)
        subLayout.addWidget(self.amp1widget, 2,1)
        subLayout.addWidget(self.amp2widget, 2,2)
        subLayout.addWidget(self.amp3widget, 2,3)
        subLayout.addWidget(self.remotewidget, 3,1)
        self.setLayout(layout)

    @inlineCallbacks
    def voltchanged(self, chan, value):
        value = self.U(value, 'V')
        yield self.server.voltage(chan, value)
        
    @inlineCallbacks
    def ampchanged(self, chan, value):
        value = self.U(value, 'A')
        yield self.server.current(chan, value)

    @inlineCallbacks
    def output_toggled(self, chan, state):
        yield self.server.output(chan, state)
            
    @inlineCallbacks
    def remote_toggled(self, state):
        yield self.server.remote_mode(state)
        if state == 1:
            # Applied votlage/current can change when remote mode is toggled on,
            # since users can change them at the box
            initial_vals = yield self.server.get_applied_voltage_current()
            self.volt1widget.setValues(initial_vals[0][0])
            self.volt2widget.setValues(initial_vals[1][0])
            self.volt3widget.setValues(initial_vals[2][0])
            self.amp1widget.setValues(initial_vals[0][1])
            self.amp2widget.setValues(initial_vals[1][1])
            self.amp3widget.setValues(initial_vals[2][1])
        
    def closeEvent(self, x):
        self.reactor.stop()

if __name__ == "__main__":
    a = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    kiethleyWidget = kiethleyclient(reactor)
    kiethleyWidget.show()
    run = reactor.run()
