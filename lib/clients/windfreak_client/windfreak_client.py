from PyQt5.QtWidgets import *
from twisted.internet.defer import inlineCallbacks
from common.lib.clients.windfreak_client.windfreak_gui import QCustomWindfreakGui
import sys
import logging

logger = logging.getLogger(__name__)

trigger_modes = (
    "disabled",
    "full frequency sweep",
    "single frequency step",
    "stop all",
    "rf enable",
    "remove interrupts",
    "reserved",
    "reserved",
    "am modulation",
    "fm modulation",
)

reference_modes = ["external", "internal 27mhz", "internal 10mhz"]


class WindfreakClient(QWidget):
    def __init__(self, reactor, parent=None):
        super(WindfreakClient, self).__init__()
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.reactor = reactor
        self.channel = {}
        self.channel_GUIs = {}
        self.connect()
        self.active_channel = 0

    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync

        self.cxn = yield connectAsync(name="Windfreak GUI")
        self.server = self.cxn.windfreak
        self.initialize_gui()

    @inlineCallbacks
    def initialize_gui(self):
        layout = QVBoxLayout()

        self.gui = QCustomWindfreakGui()
        connection_error = False
        try:
            init_freq = yield self.server.get_freq(0)
            init_power = yield self.server.get_power(0)
            init_onoff = yield self.server.get_enable(0)
            init_sweep_low = yield self.server.get_sweep_freq_low(0)
            init_sweep_high = yield self.server.get_sweep_freq_high(0)
            init_sweep_freq_step = yield self.server.get_sweep_freq_step(0)
            init_sweep_time_step = yield self.server.get_sweep_time_step(0)
            init_sweep_onoff = yield self.server.get_sweep_cont(0)
            init_sweep_low_power = yield self.server.get_sweep_power_low(0)
            init_sweep_high_power = yield self.server.get_sweep_power_high(0)
            init_sweep_single = yield self.server.get_sweep_single(0)
            init_phase = yield self.server.get_phase(0)
        except Exception:
            init_freq = 0
            init_power = -46.0
            init_onoff = False
            init_sweep_low = 0
            init_sweep_high = 0
            init_sweep_freq_step = 0
            init_sweep_time_step = 0
            init_sweep_onoff = False
            init_sweep_low_power = -46.0
            init_sweep_high_power = -46.0
            init_sweep_single = False
            init_phase = -46.0
            connection_error = True

        self.gui.a.freq_input.spin_level.setValue(float(init_freq))
        self.gui.a.power_input.spin_level.setValue(float(init_power))
        self.gui.a.onoff_button.setDown(init_onoff)
        self.gui.a.sweep_low_freq_input.spin_level.setValue(float(init_sweep_low))
        self.gui.a.sweep_high_freq_input.spin_level.setValue(float(init_sweep_high))
        self.gui.a.sweep_freq_step_input.spin_level.setValue(float(init_sweep_freq_step))
        self.gui.a.sweep_time_step_input.spin_level.setValue(float(init_sweep_time_step))
        self.gui.a.sweep_onoff_button.setDown(init_sweep_onoff)
        self.gui.a.sweep_low_power_input.spin_level.setValue(float(init_sweep_low_power))
        self.gui.a.sweep_high_power_input.spin_level.setValue(
            float(init_sweep_high_power)
        )
        self.gui.a.sweep_single_onoff_button.setDown(init_sweep_single)
        self.gui.a.phase_input.spin_level.setValue(float(init_phase))

        self.gui.a.freq_input.spin_level.valueChanged.connect(
            lambda: self.change_freq(0, float(self.gui.a.freq_input.spin_level.text()))
        )
        self.gui.a.power_input.spin_level.valueChanged.connect(
            lambda: self.change_power(0, float(self.gui.a.power_input.spin_level.text()))
        )
        self.gui.a.onoff_button.toggled.connect(
            lambda: self.toggle_onoff(0, self.gui.a.onoff_button.isDown())
        )
        self.gui.a.sweep_low_power_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_low_power(
                0, float(self.gui.a.sweep_low_power_input.spin_level.text())
            )
        )
        self.gui.a.sweep_high_power_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_high_power(
                0, float(self.gui.a.sweep_high_power_input.spin_level.text())
            )
        )
        self.gui.a.sweep_low_freq_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_low_lim(
                0, float(self.gui.a.sweep_low_freq_input.spin_level.text())
            )
        )
        self.gui.a.sweep_high_freq_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_high_lim(
                0, float(self.gui.a.sweep_high_freq_input.spin_level.text())
            )
        )
        self.gui.a.sweep_freq_step_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_freq_step(
                0, float(self.gui.a.sweep_freq_step_input.spin_level.text())
            )
        )
        self.gui.a.sweep_time_step_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_time_step(
                0, float(self.gui.a.sweep_time_step_input.spin_level.text())
            )
        )
        self.gui.a.sweep_onoff_button.toggled.connect(
            lambda state=self.gui.a.sweep_onoff_button.isDown(): self.toggle_sweep(
                0, state
            )
        )
        self.gui.a.sweep_single_onoff_button.toggled.connect(
            lambda state=self.gui.a.sweep_single_onoff_button.isDown(): self.toggle_sweep_single(
                0, state
            )
        )
        self.gui.a.phase_input.spin_level.valueChanged.connect(
            lambda: self.change_phase(0, float(self.gui.a.phase_input.spin_level.text()))
        )

        try:
            init_freq = yield self.server.get_freq(1)
            init_power = yield self.server.get_power(1)
            init_onoff = yield self.server.get_enable(1)
            init_sweep_low = yield self.server.get_sweep_freq_low(1)
            init_sweep_high = yield self.server.get_sweep_freq_high(1)
            init_sweep_freq_step = yield self.server.get_sweep_freq_step(1)
            init_sweep_time_step = yield self.server.get_sweep_time_step(1)
            init_sweep_onoff = yield self.server.get_sweep_cont(1)
            init_sweep_low_power = yield self.server.get_sweep_power_low(1)
            init_sweep_high_power = yield self.server.get_sweep_power_high(1)
            init_sweep_single = yield self.server.get_sweep_single(1)
            init_phase = yield self.server.get_phase(1)
        except Exception:
            pass  # Default values for disconencted device are already set above

        self.gui.b.freq_input.spin_level.setValue(float(init_freq))
        self.gui.b.power_input.spin_level.setValue(float(init_power))
        self.gui.b.onoff_button.setDown(init_onoff)
        self.gui.b.sweep_low_freq_input.spin_level.setValue(float(init_sweep_low))
        self.gui.b.sweep_high_freq_input.spin_level.setValue(float(init_sweep_high))
        self.gui.b.sweep_freq_step_input.spin_level.setValue(float(init_sweep_freq_step))
        self.gui.b.sweep_time_step_input.spin_level.setValue(float(init_sweep_time_step))
        self.gui.b.sweep_onoff_button.setDown(init_sweep_onoff)
        self.gui.b.sweep_low_power_input.spin_level.setValue(float(init_sweep_low_power))
        self.gui.b.sweep_high_power_input.spin_level.setValue(
            float(init_sweep_high_power)
        )
        self.gui.b.sweep_single_onoff_button.setDown(init_sweep_single)
        self.gui.b.phase_input.spin_level.setValue(float(init_phase))

        self.gui.b.freq_input.spin_level.valueChanged.connect(
            lambda: self.change_freq(1, float(self.gui.b.freq_input.spin_level.text()))
        )
        self.gui.b.power_input.spin_level.valueChanged.connect(
            lambda: self.change_power(1, float(self.gui.b.power_input.spin_level.text()))
        )
        self.gui.b.onoff_button.toggled.connect(
            lambda state=self.gui.a.onoff_button.isDown(): self.toggle_onoff(1, state)
        )
        self.gui.b.sweep_low_power_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_low_power(
                1, float(self.gui.b.sweep_low_power_input.spin_level.text())
            )
        )
        self.gui.b.sweep_high_power_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_high_power(
                1, float(self.gui.b.sweep_high_power_input.spin_level.text())
            )
        )
        self.gui.b.sweep_low_freq_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_low_lim(
                1, float(self.gui.b.sweep_low_freq_input.spin_level.text())
            )
        )
        self.gui.b.sweep_high_freq_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_high_lim(
                1, float(self.gui.b.sweep_high_freq_input.spin_level.text())
            )
        )
        self.gui.b.sweep_freq_step_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_freq_step(
                1, float(self.gui.b.sweep_freq_step_input.spin_level.text())
            )
        )
        self.gui.b.sweep_time_step_input.spin_level.valueChanged.connect(
            lambda: self.change_sweep_time_step(
                1, float(self.gui.b.sweep_time_step_input.spin_level.text())
            )
        )
        self.gui.b.sweep_onoff_button.toggled.connect(
            lambda state=self.gui.a.sweep_onoff_button.isDown(): self.toggle_sweep(
                1, state
            )
        )
        self.gui.b.sweep_single_onoff_button.toggled.connect(
            lambda state=self.gui.a.sweep_single_onoff_button.isDown(): self.toggle_sweep_single(
                1, state
            )
        )
        self.gui.b.phase_input.spin_level.valueChanged.connect(
            lambda: self.change_phase(1, float(self.gui.b.phase_input.spin_level.text()))
        )
        try:
            trig_mode = yield self.server.get_trigger_mode()
            init_trigger_mode = trigger_modes.index(trig_mode)
            ref_mode = yield self.server.get_reference_mode()
            init_reference_mode = reference_modes.index(ref_mode)
        except Exception:
            init_trigger_mode = 4
            init_reference_mode = 1

        self.gui.c.trigger_mode.setCurrentIndex(init_trigger_mode)
        self.gui.c.reference_mode.setCurrentIndex(init_reference_mode)

        self.gui.c.trigger_mode.activated.connect(
            lambda: self.change_trigger(self.gui.c.trigger_mode.currentIndex())
        )
        self.gui.c.reference_mode.activated.connect(
            lambda: self.change_reference(self.gui.c.reference_mode.currentIndex())
        )

        layout.addWidget(self.gui)
        # layout.minimumSize()
        self.setLayout(layout)
        if connection_error:
            self.setDisabled(True)

    @inlineCallbacks
    def sweep_single_on(self, chan):
        yield self.server.set_sweep_single(chan, True)

    @inlineCallbacks
    def sweep_single_off(self, chan):
        yield self.server.set_sweep_single(chan, False)

    @inlineCallbacks
    def change_sweep_low_power(self, chan, num):
        yield self.server.set_sweep_power_low(chan, num)

    @inlineCallbacks
    def change_sweep_high_power(self, chan, num):
        yield self.server.set_sweep_power_high(chan, num)

    @inlineCallbacks
    def change_sweep_low_lim(self, chan, num):
        yield self.server.set_sweep_freq_low(chan, num)

    @inlineCallbacks
    def change_sweep_high_lim(self, chan, num):
        yield self.server.set_sweep_freq_high(chan, num)

    @inlineCallbacks
    def change_sweep_freq_step(self, chan, num):
        yield self.server.set_sweep_freq_step(chan, num)

    @inlineCallbacks
    def change_sweep_time_step(self, chan, num):
        yield self.server.set_sweep_time_step(chan, num)

    @inlineCallbacks
    def change_freq(self, chan, num):
        yield self.server.set_freq(chan, num)

    @inlineCallbacks
    def change_power(self, chan, num):
        yield self.server.set_power(chan, num)

    @inlineCallbacks
    def toggle_onoff(self, chan, state):
        yield self.server.set_enable(chan, state)

    @inlineCallbacks
    def toggle_sweep(self, chan, state):
        yield self.server.set_sweep_cont(chan, state)

    @inlineCallbacks
    def toggle_sweep_single(self, chan, state):
        yield self.server.set_sweep_single(chan, state)

    @inlineCallbacks
    def change_phase(self, chan, num):
        yield self.server.set_phase(chan, num)

    @inlineCallbacks
    def change_trigger(self, idx):
        yield self.server.set_trigger_mode(trigger_modes[idx])

    @inlineCallbacks
    def change_reference(self, idx):
        yield self.server.set_reference_mode(reference_modes[idx])


if __name__ == "__main__":
    a = QApplication(sys.argv)
    import qt5reactor

    qt5reactor.install()
    from twisted.internet import reactor

    client_inst = WindfreakClient(reactor)
    client_inst.show()
    run = reactor.run()
