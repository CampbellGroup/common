from common.lib.clients.qtui.QCustomSpinBox import QCustomSpinBox
from common.lib.clients.qtui.switch import QCustomSwitchChannel
from twisted.internet.defer import inlineCallbacks
from PyQt5.QtWidgets import *
import logging

logger = logging.getLogger(__name__)


class KeithleyClient(QFrame):

    def __init__(self, reactor, parent=None):
        """initializes the GUI creates the reactor"""
        super(KeithleyClient, self).__init__()
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.connect()
        self.reactor = reactor

    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection"""
        from labrad.wrappers import connectAsync
        from labrad.units import WithUnit as U

        self.U = U
        self.cxn = yield connectAsync(name="keithley client")
        self.server = self.cxn.keithley_server
        yield self.server.select_device(0)
        self.initialize_gui()

    @inlineCallbacks
    def initialize_gui(self):
        layout = QGridLayout()
        self.setWindowTitle("Keithley Power Supply: 2231A-30-3")
        q_box = QGroupBox("Keithley 2231A: Magnetic Field Coils")
        sub_layout = QGridLayout()
        q_box.setLayout(sub_layout)
        layout.addWidget(q_box, 0, 0)

        # turn remote mode on (nothing will work without it on)
        yield self.server.remote_mode(1)

        # Make remote mode widget
        self.remotewidget = QCustomSwitchChannel("Remote Mode", ("On", "Off"))
        # Set remote mode button to on
        self.remotewidget.TTLswitch.setChecked(1)
        # If you press the button, it switches it on/off
        self.remotewidget.TTLswitch.toggled.connect(
            lambda state=self.remotewidget.TTLswitch.isDown(): self.remote_toggled(
                state
            )
        )
        self.remotewidget.setFrameStyle(QFrame.NoFrame)

        # Finds the output setting of each channel
        # Sets the initial condition
        initial_output1 = yield self.server.query_initial(1)
        if bool((initial_output1 & 0b1000) >> 3):
            initial_output1 = True
        initial_output2 = yield self.server.query_initial(2)
        if bool((initial_output2 & 0b1000) >> 3):
            initial_output2 = True
        initial_output3 = yield self.server.query_initial(3)
        if bool((initial_output3 & 0b1000) >> 3):
            initial_output3 = True

        # Gets all initial voltages and currents
        initial_vals = yield self.server.get_applied_voltage_current()

        # Makes widgets for voltage in each channel
        # Sets initial values as found above
        self.volt1widget = QCustomSpinBox((0, 30), suffix="V")
        self.volt1widget.set_value(initial_vals[0][0])
        self.volt2widget = QCustomSpinBox((0, 30), suffix="V")
        self.volt2widget.set_value(initial_vals[1][0])
        self.volt3widget = QCustomSpinBox((0, 5), suffix="V")
        self.volt3widget.set_value(initial_vals[2][0])

        # Makes widgets for current in each channel
        # Sets initial values as found above
        self.amp1widget = QCustomSpinBox((0, 3), suffix="A")
        self.amp1widget.set_value(initial_vals[0][1])
        self.amp2widget = QCustomSpinBox((0, 3), suffix="A")
        self.amp2widget.set_value(initial_vals[1][1])
        self.amp3widget = QCustomSpinBox((0, 3), suffix="A")
        self.amp3widget.set_value(initial_vals[2][1])

        # Makes widget for the output of each channel
        self.output1widget = QCustomSwitchChannel("Output Channel 1", ("On", "Off"))
        self.output1widget.TTLswitch.setChecked(int(initial_output1))
        self.output1widget.setFrameStyle(QFrame.NoFrame)
        self.output2widget = QCustomSwitchChannel("Output Channel 2", ("On", "Off"))
        self.output2widget.TTLswitch.setChecked(int(initial_output2))
        self.output2widget.setFrameStyle(QFrame.NoFrame)
        self.output3widget = QCustomSwitchChannel("Output Channel 3", ("On", "Off"))
        self.output3widget.TTLswitch.setChecked(int(initial_output3))
        self.output3widget.setFrameStyle(QFrame.NoFrame)

        # Updates widgets when values are changed through the gui
        self.volt1widget.spin_level.valueChanged.connect(
            lambda value=self.volt1widget.spin_level.value(), chan=1: self.volt_changed(
                chan, value
            )
        )
        self.volt2widget.spin_level.valueChanged.connect(
            lambda value=self.volt2widget.spin_level.value(), chan=2: self.volt_changed(
                chan, value
            )
        )
        self.volt3widget.spin_level.valueChanged.connect(
            lambda value=self.volt3widget.spin_level.value(), chan=3: self.volt_changed(
                chan, value
            )
        )

        self.amp1widget.spin_level.valueChanged.connect(
            lambda value=self.amp1widget.spin_level.value(), chan=1: self.amp_changed(
                chan, value
            )
        )
        self.amp2widget.spin_level.valueChanged.connect(
            lambda value=self.amp2widget.spin_level.value(), chan=2: self.amp_changed(
                chan, value
            )
        )
        self.amp3widget.spin_level.valueChanged.connect(
            lambda value=self.amp3widget.spin_level.value(), chan=3: self.amp_changed(
                chan, value
            )
        )

        self.output1widget.TTLswitch.toggled.connect(
            lambda state=self.output1widget.TTLswitch.isDown(), chan=1: self.output_toggled(
                chan, state
            )
        )
        self.output2widget.TTLswitch.toggled.connect(
            lambda state=self.output2widget.TTLswitch.isDown(), chan=2: self.output_toggled(
                chan, state
            )
        )
        self.output3widget.TTLswitch.toggled.connect(
            lambda state=self.output3widget.TTLswitch.isDown(), chan=3: self.output_toggled(
                chan, state
            )
        )

        # Adds widgets to layout
        sub_layout.addWidget(self.output1widget, 0, 0, 1, 2)
        sub_layout.addWidget(self.output2widget, 0, 2, 1, 2)
        sub_layout.addWidget(self.output3widget, 0, 4, 1, 2)
        sub_layout.addWidget(self.volt1widget, 1, 0)
        sub_layout.addWidget(self.volt2widget, 1, 2)
        sub_layout.addWidget(self.volt3widget, 1, 4)
        sub_layout.addWidget(self.amp1widget, 1, 1)
        sub_layout.addWidget(self.amp2widget, 1, 3)
        sub_layout.addWidget(self.amp3widget, 1, 5)
        sub_layout.addWidget(self.remotewidget, 2, 0)
        self.setLayout(layout)

    @inlineCallbacks
    def volt_changed(self, chan, value):
        value = self.U(value, "V")
        yield self.server.voltage(chan, value)

    @inlineCallbacks
    def amp_changed(self, chan, value):
        value = self.U(value, "A")
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
            self.volt1widget.set_value(initial_vals[0][0])
            self.volt2widget.set_value(initial_vals[1][0])
            self.volt3widget.set_value(initial_vals[2][0])
            self.amp1widget.set_value(initial_vals[0][1])
            self.amp2widget.set_value(initial_vals[1][1])
            self.amp3widget.set_value(initial_vals[2][1])

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor

    qt5reactor.install()
    from twisted.internet import reactor

    keithleyWidget = KeithleyClient(reactor)
    keithleyWidget.show()
    run = reactor.run()
