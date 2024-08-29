from PyQt5.QtWidgets import *
from twisted.internet.defer import inlineCallbacks

from common.lib.clients.qtui.q_custom_text_changing_button import TextChangingButton
from lib.clients.Multiplexer.multiplexerchannel import QCustomWavemeterChannelNoPID

try:
    from config.multiplexerclient_config import MultiplexerConfig
except:
    from common.lib.config.multiplexerclient_config import multiplexer_config

import socket
import os

SIGNALID1 = 445566
SIGNALID2 = 143533
SIGNALID3 = 111221
SIGNALID4 = 549210
SIGNALID5 = 190909
SIGNALID6 = 102588
SIGNALID7 = 148323
SIGNALID8 = 238883


class WavemeterClient(QWidget):

    def __init__(self, reactor, parent=None):
        """initializes the GUI, creates the reactor
        and empty dictionary for channel widgets to
        be stored for iteration. also grabs chan info
        from multiplexer_config
        """
        super(WavemeterClient, self).__init__()
        self.password = os.environ["LABRADPASSWORD"]
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.reactor = reactor
        self.name = socket.gethostname() + " Wave Meter Client"
        self.d = {}
        self.wmChannels = {}
        self.connect()
        self._check_window_size()

    def _check_window_size(self):
        """Checks screen size to make sure window fits in the screen."""
        desktop = QDesktopWidget()
        screensize = desktop.availableGeometry()
        width = screensize.width()
        height = screensize.height()
        min_pixel_size = 1080
        if width <= min_pixel_size or height <= min_pixel_size:
            self.showMaximized()

    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection to the wavemeter computer and
        connects incoming signals to relavent functions

        """
        self.chaninfo = MultiplexerConfig.channels
        self.wavemeterIP = MultiplexerConfig.ip
        from labrad.wrappers import connectAsync

        self.cxn = yield connectAsync(
            self.wavemeterIP, name=self.name, password=self.password
        )
        self.server = yield self.cxn.multiplexerserver
        yield self.server.signal__frequency_changed(SIGNALID1)
        yield self.server.signal__selected_channels_changed(SIGNALID2)
        yield self.server.signal__update_exp(SIGNALID3)
        yield self.server.signal__output_changed(SIGNALID5)
        yield self.server.signal__amplitude_changed(SIGNALID8)

        yield self.server.addListener(
            listener=self.update_frequency, source=None, ID=SIGNALID1
        )
        yield self.server.addListener(
            listener=self.toggle_meas, source=None, ID=SIGNALID2
        )
        yield self.server.addListener(
            listener=self.update_exp, source=None, ID=SIGNALID3
        )
        yield self.server.addListener(
            listener=self.update_wlm_output, source=None, ID=SIGNALID5
        )
        yield self.server.addListener(
            listener=self.update_amplitude, source=None, ID=SIGNALID8
        )

        # starts display of wavemeter data
        self.initialize_gui()

    @inlineCallbacks
    def initialize_gui(self):
        layout = QGridLayout()

        self.setWindowTitle("Wavemeter")

        # this "group" contains all 8 channel outputs and settings
        q_box = QGroupBox("Wave Length and Lock settings")
        sub_layout = QGridLayout()
        q_box.setLayout(sub_layout)
        layout.addWidget(q_box, 0, 0)

        # button to start wavemeter measurement (turn wavemeter on)
        self.startSwitch = TextChangingButton("Wavemeter")
        self.startSwitch.setMaximumHeight(50)
        initstartvalue = yield self.server.get_wlm_output()
        self.startSwitch.setChecked(initstartvalue)
        self.startSwitch.toggled.connect(self.set_output)
        sub_layout.addWidget(self.startSwitch, 0, 0)

        # create display box for each channel
        # need to modify QCustomWavemeterChannel to get rid of PID button
        for chan in self.chaninfo:
            wm_channel = self.chaninfo[chan][0]
            hint = self.chaninfo[chan][1]
            position = self.chaninfo[chan][2]
            stretched = self.chaninfo[chan][3]
            widget = QCustomWavemeterChannelNoPID(chan, wm_channel, hint, stretched)

            from common.lib.clients.qtui import RGBconverter as RGB

            RGB = RGB.RGBconverter()
            color = int(2.998e8 / (float(hint) * 1e3))
            color = RGB.wav2RGB(color)
            color = tuple(color)

            widget.current_frequency.setStyleSheet("color: rgb" + str(color))
            widget.exposure_spinbox.valueChanged.connect(
                lambda exp=widget.exposure_spinbox.value(), chan=wm_channel: self.exp_changed(
                    exp, chan
                )
            )
            initvalue = yield self.server.get_exposure(wm_channel)
            widget.exposure_spinbox.setValue(initvalue)
            initmeas = yield self.server.get_switcher_signal_state(wm_channel)
            initmeas = initmeas
            widget.measure_button.setChecked(bool(initmeas))
            widget.measure_button.toggled.connect(
                lambda state=widget.measure_button.isDown(), chan=wm_channel: self.change_state(
                    state, chan
                )
            )

            self.d[wm_channel] = widget
            sub_layout.addWidget(self.d[wm_channel], position[1], position[0], 1, 3)

        self.setLayout(layout)

    # updates exposure time from GUI?
    @inlineCallbacks
    def exp_changed(self, exp, chan):
        # these are switched, dont know why
        exp = int(exp)
        yield self.server.set_exposure_time(chan, exp)

    # sets display of update frequency and light exposure level
    def update_frequency(self, c, signal):
        chan = signal[0]
        if chan in self.d:
            freq = signal[1]

            if not self.d[chan].measure_button.isChecked():
                self.d[chan].current_frequency.setText("Not Measured")
            elif freq == -3.0:
                self.d[chan].current_frequency.setText("Under Exposed")
            elif freq == -4.0:
                self.d[chan].current_frequency.setText("Over Exposed")
            elif freq == -17.0:
                self.d[chan].current_frequency.setText("Data Error")
            else:
                self.d[chan].current_frequency.setText(str(freq)[0:10])

    def toggle_meas(self, c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d:
            self.d[chan].measure_button.setChecked(value)

    def update_exp(self, c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d:
            self.d[chan].exposure_spinbox.setValue(value)

    def update_wlm_output(self, c, signal):
        self.startSwitch.setChecked(signal)

    def update_amplitude(self, c, signal):
        wmChannel = signal[0]
        value = signal[1]
        if wmChannel in self.d:
            self.d[wmChannel].power_meter.setValue(int(value))

    def set_button_off(self, wmChannel):
        self.d[wmChannel].lock_channel_button.setChecked(False)

    @inlineCallbacks
    def change_state(self, state, chan):
        yield self.server.set_switcher_signal_state(chan, state)

    @inlineCallbacks
    def set_output(self, state):
        yield self.server.set_wlm_output(state)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor

    qt5reactor.install()
    from twisted.internet import reactor

    wavemeterWidget = WavemeterClient(reactor)
    wavemeterWidget.show()
    reactor.run()
