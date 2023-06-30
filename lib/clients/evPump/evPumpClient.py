"""
Created on Mar 25, 2016

@author: Anthony Ransford
"""
from twisted.internet.defer import inlineCallbacks
from common.lib.clients.connection import connection
from PyQt4 import QtGui, QtCore
from common.lib.clients.qtui.switch import QCustomSwitchChannel

SIGNALID1 = 421956
SIGNALID2 = 444296
SIGNALID3 = 123462
SIGNALID4 = 649731


class eVPumpClient(QtGui.QFrame):

    def __init__(self, reactor, cxn=None):
        super(eVPumpClient, self).__init__()
        self._max_current = 24.0  # maximum laser diode current in Amps
        self._max_power = 15.2  # maximum laser output power in Watts
        self.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        self.cxn = cxn
        self.reactor = reactor
        from labrad.units import WithUnit as U
        self.U = U
        self.connect()

    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection to pump server and
        connects incoming signals to relevant functions
        """
        if self.cxn is None:
            self.cxn = connection(name='eV Pump Client')
            yield self.cxn.connect()
        self.server = yield self.cxn.get_server('evpump')

        yield self.server.signal__current_changed(SIGNALID1)
        yield self.server.signal__power_changed(SIGNALID2)
        yield self.server.signal__temp_changed(SIGNALID3)
        yield self.server.signal__stat_changed(SIGNALID4)

        yield self.server.addListener(listener=self.update_current,
                                      source=None, ID=SIGNALID1)
        yield self.server.addListener(listener=self.update_power, source=None,
                                      ID=SIGNALID2)
        yield self.server.addListener(listener=self.update_temperature,
                                      source=None, ID=SIGNALID3)
        yield self.server.addListener(listener=self.update_system_status,
                                      source=None, ID=SIGNALID4)

        self.initialize_GUI()

    @inlineCallbacks
    def initialize_GUI(self):
        layout = QtGui.QGridLayout()
        font = QtGui.QFont()
        font.setBold(True)
        font.setPointSize(18)

        self.title = QtGui.QLabel('Millennia eV Pump Laser')
        self.title.setFont(font)
        self.title.setAlignment(QtCore.Qt.AlignCenter)

        self.temp_label = QtGui.QLabel('Diode Temp degC')
        self.current_label = QtGui.QLabel('Current')
        self.power_label = QtGui.QLabel('Power')
        self.power_control_label = QtGui.QLabel('Power Control')
        self.status_label = QtGui.QLabel('Laser Status: ')
        self.current_control_label = QtGui.QLabel('Current Control (A)')
        self.control_mode_label = QtGui.QLabel('Control Mode')

        self.control_combo = QtGui.QComboBox()
        self.control_combo.addItems(['Power Control', 'Current Control'])

        self.power_spinbox = QtGui.QDoubleSpinBox()
        self.power_spinbox.setFont(QtGui.QFont('MS Shell Dlg 2', pointSize=16))
        self.power_spinbox.setDecimals(2)
        self.power_spinbox.setSingleStep(0.01)
        self.power_spinbox.setRange(0.0, 15.1)
        self.power_spinbox.valueChanged.connect(self.change_power)
        self.power_spinbox.setKeyboardTracking(False)

        self.current_spinbox = QtGui.QDoubleSpinBox()
        self.current_spinbox.setFont(QtGui.QFont('MS Shell Dlg 2', pointSize=16))
        self.current_spinbox.setDecimals(3)
        self.current_spinbox.setSingleStep(0.001)
        self.current_spinbox.setRange(0.0, 8.1)
        self.current_spinbox.valueChanged.connect(self.change_current)
        self.current_spinbox.setKeyboardTracking(False)

        self.temp_display = QtGui.QLCDNumber()
        self.temp_display.setDigitCount(5)

        self.current_progress_bar = QtGui.QProgressBar()
        self.current_progress_bar.setOrientation(QtCore.Qt.Vertical)

        self.laser_switch = QCustomSwitchChannel('Laser', ('On', 'Off'))
        self.laser_switch.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.shutter_switch = QCustomSwitchChannel('Shutter', ('Open', 'Closed'))
        self.shutter_switch.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)


        self.power_progress_bar = QtGui.QProgressBar()
        self.power_progress_bar.setOrientation(QtCore.Qt.Vertical)
        self.power_progress_bar.setMaximum(100)
        self.power_progress_bar.setMinimum(0)

        layout.addWidget(self.title,                0, 0, 1, 3)
        layout.addWidget(self.current_progress_bar, 2, 0, 8, 1)
        layout.addWidget(self.power_progress_bar,   2, 1, 8, 1)
        layout.addWidget(self.current_label,        1, 0, 1, 1)
        layout.addWidget(self.power_label,          1, 1, 1, 1)
        layout.addWidget(self.temp_label,           10, 0, 1, 2)
        layout.addWidget(self.status_label,         11, 0, 1, 1)
        layout.addWidget(self.temp_display,         9, 2, 4, 1)
        layout.addWidget(self.laser_switch,         6, 2)
        layout.addWidget(self.shutter_switch,       7, 2)
        layout.addWidget(self.power_control_label,  2, 2)
        layout.addWidget(self.current_control_label, 4, 2)
        layout.addWidget(self.power_spinbox,        3, 2)
        layout.addWidget(self.current_spinbox,      5, 2)
        layout.addWidget(self.control_combo,        1, 2)

        self.laser_switch.TTLswitch.toggled.connect(self.on_laser_toggled)
        self.shutter_switch.TTLswitch.toggled.connect(self.on_shutter_toggled)
        self.control_combo.activated[str].connect(self.change_control)
        self.freeze_mode()

        # This initializations need to be at the end so that the widgets
        # connected to active signals are created quickly (indicators)
        init_power = yield self.server.get_power_setpoint()
        self.power_spinbox.setValue(init_power['W'])

        init_current = yield self.server.get_current_setpoint()
        self.current_spinbox.setValue(init_current['A'])

        initOn = yield self.server.diode_status()
        self.laser_switch.TTLswitch.setChecked(initOn)

        initShutter = yield self.server.get_shutter_status()
        self.shutter_switch.TTLswitch.setChecked(initShutter)

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

        diode_status = yield self.server.diode_status()
        if diode_status is True:
            yield self.freeze_mode()

        elif diode_status is False:
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

        last_mode = yield self.server.get_control_mode()
        if last_mode == 'current':
            self.control_combo.setCurrentIndex(1)
            self.power_spinbox.setEnabled(False)
            self.current_spinbox.setEnabled(True)
        elif last_mode == 'power':
            self.control_combo.setCurrentIndex(0)
            self.power_spinbox.setEnabled(True)
            self.current_spinbox.setEnabled(False)
        else:
            self.control_combo.setCurrentIndex(-1)

    def update_current(self, c, current):
        current_percentage = 100.*current['A']/self._max_current
        self.current_progress_bar.setValue(current_percentage)
        self.current_progress_bar.setFormat(str(current['A']) + 'A')

    def update_power(self, c, power):
        power_percentage = 100.*power['W']/self._max_power
        self.power_progress_bar.setValue(power_percentage)
        self.power_progress_bar.setFormat(str(power['W']) + 'W')

    def update_temperature(self, c, temperature):
        self.temp_display.display(str(temperature['degC']))

    def update_system_status(self, c, sys_status):
        css_text = "<span style>Laser Status: <br/></span>"
        if sys_status == 'System Ready':
            css_text += "<span style='color:#00ff00;'>%s</span>" % sys_status
        else:
            css_text += "<span style='color:#ff0000;'>%s</span>" % sys_status
        self.status_label.setText(css_text)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    PumpWidget = eVPumpClient(reactor)
    PumpWidget.show()
    run = reactor.run()  # @UndefinedVariable
