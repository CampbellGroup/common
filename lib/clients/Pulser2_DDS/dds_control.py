from common.lib.clients.qtui.QCustomFreqPower import QCustomFreqPower
from twisted.internet.defer import inlineCallbacks, returnValue
from common.lib.clients.connection import Connection
from PyQt5.QtWidgets import *

import logging

logger = logging.getLogger(__name__)

"""
The DDS Control GUI lets the user control the DDS channels of the Pulser
"""


class DDSChannel(QCustomFreqPower):
    def __init__(self, chan, reactor, cxn, context, parent=None):
        super(DDSChannel, self).__init__("DDS: {}".format(chan), True, parent)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.reactor = reactor
        self.context = context
        self.chan = chan
        self.cxn = cxn
        self.import_labrad()

    def import_labrad(self):
        from labrad import types as T
        from labrad.types import Error

        self.Error = Error
        self.T = T
        self.setup_widget()

    @inlineCallbacks
    def setup_widget(self, connect=True):
        # get ranges
        self.server = yield self.cxn.get_server("Pulser")
        min_power, max_power = yield self.server.get_dds_amplitude_range(
            self.chan, context=self.context
        )
        min_freq, max_freq = yield self.server.get_dds_frequency_range(
            self.chan, context=self.context
        )
        self.set_power_range((min_power, max_power))
        self.set_freq_range((min_freq, max_freq))
        # get initial values
        init_power = yield self.server.amplitude(self.chan, context=self.context)
        init_freq = yield self.server.frequency(self.chan, context=self.context)
        init_state = yield self.server.output(self.chan, context=self.context)
        self.set_state_no_signal(init_state)
        self.set_power_no_signal(init_power["dBm"])
        self.set_freq_no_signal(init_freq["MHz"])
        # connect functions
        if connect:
            self.power_spinbox.valueChanged.connect(self.power_changed)
            self.freq_spinbox.valueChanged.connect(self.freq_changed)
            self.switch_button.toggled.connect(self.switch_changed)

    def set_param_no_signal(self, param, value):
        if param == "amplitude":
            self.set_power_no_signal(value)
        elif param == "frequency":
            self.set_freq_no_signal(value)
        elif param == "state":
            self.set_state_no_signal(value)

    @inlineCallbacks
    def power_changed(self, pwr):
        val = self.T.Value(pwr, "dBm")
        try:
            yield self.server.amplitude(self.chan, val, context=self.context)
        except self.Error as e:
            old_value = yield self.server.amplitude(self.chan, context=self.context)
            self.set_power_no_signal(old_value)
            self.display_error(e.msg)

    @inlineCallbacks
    def freq_changed(self, freq):
        val = self.T.Value(freq, "MHz")
        try:
            yield self.server.frequency(self.chan, val, context=self.context)
        except self.Error as e:
            old_value = yield self.server.frequency(self.chan, context=self.context)
            self.set_freq_no_signal(old_value)
            self.display_error(e.msg)

    @inlineCallbacks
    def switch_changed(self, pressed):
        try:
            yield self.server.output(self.chan, pressed, context=self.context)
        except self.Error as e:
            old_value = yield self.server.frequency(self.chan, context=self.context)
            self.set_state_no_signal(old_value)
            self.display_error(e.msg)

    def display_error(self, text):
        # runs the message box in a non-blocking method
        message = QMessageBox(self)
        message.setText(text)
        message.open()
        message.show()
        message.raise_()

    def closeEvent(self, x):
        self.reactor.stop()


class DDSControlWidget(QFrame):
    SIGNALID = 319182

    def __init__(self, reactor, cxn=None):
        super(DDSControlWidget, self).__init__()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.reactor = reactor
        self.cxn = cxn
        self.initialized = False
        self.setup_dds()

    @inlineCallbacks
    def setup_dds(self):
        if self.cxn is None:
            self.cxn = Connection(name="DDS Client")
            yield self.cxn.connect()
        self.context = yield self.cxn.context()
        try:
            from labrad.types import Error

            self.Error = Error
            yield self.initialize()
        except Exception as e:
            logger.error(e)
            logger.error("Pulser not available")
            self.setDisabled(True)
        self.cxn.add_on_connect("Pulser", self.reinitialize)
        self.cxn.add_on_disconnect("Pulser", self.disable)

    @inlineCallbacks
    def initialize(self):
        server = yield self.cxn.get_server("Pulser")

        yield server.signal__new_dds_parameter(self.SIGNALID, context=self.context)

        yield server.addListener(
            listener=self.follow_signal,
            source=None,
            ID=self.SIGNALID,
            context=self.context,
        )

        self.display_channels, self.widgets_per_row = (
            yield self.get_displayed_channels()
        )
        self.widgets = {}.fromkeys(self.display_channels)
        self.do_layout()
        self.initialized = True

    @inlineCallbacks
    def get_displayed_channels(self):
        """
        get a list of all available channels from the pulser. only show the ones
        listed in the registry. If there is no listing, will display all channels.
        """
        server = yield self.cxn.get_server("Pulser")
        all_channels = yield server.get_dds_channels(context=self.context)
        channels_to_display, widgets_per_row = yield self.registry_load_displayed(
            all_channels, 1
        )
        if channels_to_display is None:
            channels_to_display = all_channels
        if widgets_per_row is None:
            widgets_per_row = 1
        channels = [name for name in channels_to_display if name in all_channels]
        returnValue((channels, widgets_per_row))

    @inlineCallbacks
    def registry_load_displayed(self, all_names, default_widgets_per_row):
        reg = yield self.cxn.get_server("Registry")
        yield reg.cd(["Clients", "DDS Control"], True, context=self.context)
        try:
            displayed = yield reg.get("display_channels", context=self.context)
        except self.Error as e:
            if e.code == 21:
                # key error
                yield reg.set("display_channels", all_names, context=self.context)
                displayed = None
            else:
                raise
        try:
            widgets_per_row = yield reg.get("widgets_per_row", context=self.context)
        except self.Error as e:
            if e.code == 21:
                # key error
                yield reg.set("widgets_per_row", 1, context=self.context)
                widgets_per_row = None
            else:
                raise
        returnValue((displayed, widgets_per_row))

    @inlineCallbacks
    def reinitialize(self):
        self.setDisabled(False)
        server = yield self.cxn.get_server("Pulser")
        if not self.initialized:
            yield server.signal__new_dds_parameter(self.SIGNALID, context=self.context)
            yield server.addListener(
                listener=self.follow_signal,
                source=None,
                ID=self.SIGNALID,
                context=self.context,
            )
            self.do_layout()
            self.initialized = True
        else:
            # update any changes in the parameters
            yield server.signal__new_dds_parameter(self.SIGNALID, context=self.context)
            # iterating over all setup channels
            for widget in self.widgets.values():
                if widget is not None:
                    yield widget.setup_widget(connect=False)

    def do_layout(self):
        layout = QGridLayout()
        q_box = QGroupBox("Pulser DDS Control")
        sub_layout = QGridLayout()
        q_box.setLayout(sub_layout)
        layout.addWidget(q_box)
        item = 0
        for chan in self.display_channels:
            widget = DDSChannel(chan, self.reactor, self.cxn, self.context)
            self.widgets[chan] = widget
            sub_layout.addWidget(
                widget, item // self.widgets_per_row, item % self.widgets_per_row
            )
            item += 1
        self.setLayout(layout)

    @inlineCallbacks
    def disable(self, _, __):
        self.setDisabled(True)
        yield None

    @inlineCallbacks
    def enable(self, _, __):
        self.setEnabled(True)
        yield None

    def follow_signal(self, x, y):
        chan, param, val = y
        if chan in self.widgets.keys():
            # this check is needed in case signal comes in about a channel that is not displayed
            self.widgets[chan].set_param_no_signal(param, val)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor

    qt5reactor.install()
    from twisted.internet import reactor

    trap_drive_Widget = DDSControlWidget(reactor)
    trap_drive_Widget.show()
    reactor.run()
