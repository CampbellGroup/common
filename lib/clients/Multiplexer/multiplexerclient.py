from common.lib.clients.qtui.multiplexerchannel import QCustomWavemeterChannel
from common.lib.clients.qtui.multiplexerPID import QCustomPID
from common.lib.clients.qtui.q_custom_text_changing_button import TextChangingButton
from twisted.internet.defer import inlineCallbacks, returnValue
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *

try:
    from config.multiplexerclient_config import multiplexer_config
except ImportError:
    from common.lib.config.multiplexerclient_config import multiplexer_config

import socket
import os
import numpy as np

import logging
logger = logging.getLogger(__name__)

SIGNALID1 = 445566
SIGNALID2 = 143533
SIGNALID3 = 111221
SIGNALID4 = 549210
SIGNALID5 = 190909
SIGNALID6 = 102588
SIGNALID7 = 148323
SIGNALID8 = 238883
SIGNALID9 = 462917

# this is the signal for the updated frequencies


class WavemeterClient(QWidget):

    def __init__(self, reactor, parent=None):
        """
        initializes the GUI creates the reactor
        and empty dictionary for channel widgets to
        be stored for iteration. also grabs chan info
        from multiplexer_config
        """
        super(WavemeterClient, self).__init__()
        self.password = os.environ['LABRADPASSWORD']
        self.parent = parent
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.reactor = reactor
        self.name = socket.gethostname() + ' Wave Meter Client'
        self.d = {}
        self.wmChannels = {}
        self.connect()
        self._check_window_size()
        self.pattern_1 = {}
        self.pattern_2 = {}
        logger.info('client initialized')

    def _check_window_size(self):
        """Checks screen size to make sure window fits in the screen. """
        desktop = QDesktopWidget()
        screensize = desktop.availableGeometry()
        width = screensize.width()
        height = screensize.height()
        min_pixel_size = 1080
        if width <= min_pixel_size or height <= min_pixel_size:
            self.showMaximized()

    @inlineCallbacks
    def connect(self):
        """
        Creates an Asynchronous connection to the wavemeter computer and
        connects incoming signals to relevant functions
        """
        self.chaninfo = multiplexer_config.info
        self.wavemeterIP = multiplexer_config.ip
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(self.wavemeterIP,
                                      name=self.name,
                                      password=self.password)

        self.server = yield self.cxn.multiplexerserver
        yield self.server.signal__frequency_changed(SIGNALID1)
        yield self.server.signal__selected_channels_changed(SIGNALID2)
        yield self.server.signal__update_exp(SIGNALID3)
        yield self.server.signal__lock_changed(SIGNALID4)
        yield self.server.signal__output_changed(SIGNALID5)
        yield self.server.signal__pidvoltage_changed(SIGNALID6)
        yield self.server.signal__channel_lock_changed(SIGNALID7)
        yield self.server.signal__amplitude_changed(SIGNALID8)
        # yield self.server.signal__pattern_changed(SIGNALID9)

        yield self.server.addListener(listener=self.update_frequency, source=None, ID=SIGNALID1)
        yield self.server.addListener(listener=self.toggle_measurement, source=None, ID=SIGNALID2)
        yield self.server.addListener(listener=self.update_exp, source=None, ID=SIGNALID3)
        yield self.server.addListener(listener=self.toggle_lock, source=None, ID=SIGNALID4)
        yield self.server.addListener(listener=self.update_wlm_output, source=None, ID=SIGNALID5)
        yield self.server.addListener(listener=self.update_pid_voltage, source=None, ID=SIGNALID6)
        yield self.server.addListener(listener=self.toggle_channel_cock, source=None, ID=SIGNALID7)
        yield self.server.addListener(listener=self.update_amplitude, source=None, ID=SIGNALID8)

        self.initializeGUI()

    @inlineCallbacks
    def initializeGUI(self):

        layout = QGridLayout()

        self.setWindowTitle('Multiplexed Wavemeter')

        q_box = QGroupBox('Wavelength and Lock settings')
        sub_layout = QGridLayout()
        q_box.setLayout(sub_layout)
        layout.addWidget(q_box, 0, 0)

        self.lockSwitch = TextChangingButton('Lock Wave Meter')
        self.lockSwitch.setMaximumHeight(50)
        self.startSwitch = TextChangingButton('Wavemeter')
        self.startSwitch.setMaximumHeight(50)
        init_start_value = yield self.server.get_wlm_output()
        init_lock_value = yield self.server.get_lock_state()
        self.lockSwitch.setChecked(init_lock_value)
        self.startSwitch.setChecked(init_start_value)

        self.lockSwitch.toggled.connect(self.set_lock)
        self.startSwitch.toggled.connect(self.set_output)

        sub_layout.addWidget(self.lockSwitch, 0, 2)
        sub_layout.addWidget(self.startSwitch, 0, 0)

        for chan in self.chaninfo:
            wm_channel = self.chaninfo[chan][0]
            hint = self.chaninfo[chan][1]
            position = self.chaninfo[chan][2]
            stretched = self.chaninfo[chan][3]
            display_pid = self.chaninfo[chan][4]
            dac_port = self.chaninfo[chan][5]
            widget = QCustomWavemeterChannel(chan, wm_channel, dac_port, hint, stretched, display_pid)

            if display_pid:
                try:
                    rails = self.chaninfo[chan][6]
                    widget.pid_indicator.set_rails(rails)
                except AttributeError:
                    rails = [-10.0, 10.0]

                    widget.pid_indicator.set_rails(rails)
            from common.lib.clients.qtui import RGBconverter as RGB
            RGB = RGB.RGBconverter()
            color = int(2.998e8 / (float(hint) * 1e3))
            color = RGB.wav2RGB(color)
            color = tuple(color)

            if dac_port != 0:
                self.wmChannels[dac_port] = wm_channel
                init_course = yield self.get_pid_course(dac_port, hint)
                widget.spinFreq.setValue(init_course)
                widget.spinFreq.valueChanged.connect(
                    lambda freq=widget.spinFreq.value(), dac_port=dac_port: self.freq_changed(freq, dac_port))
                widget.setPID.clicked.connect(
                    lambda state=widget.setPID.isDown(), chan=chan, dac_port=dac_port: self.initialize_pid_gui(dac_port,
                                                                                                               chan))
                init_lock = yield self.server.get_channel_lock(dac_port, wm_channel)
                widget.lockChannel.setChecked(bool(init_lock))
                widget.lockChannel.toggled.connect(
                    lambda state=widget.lockChannel.isDown(), dac_port=dac_port: self.lock_single_channel(state,
                                                                                                          dac_port))
            else:
                widget.spinFreq.setValue(float(hint))
                widget.lockChannel.toggled.connect(
                    lambda state=widget.lockChannel.isDown(), wm_channel=wm_channel: self.set_button_off(wm_channel))

            widget.current_frequency.setStyleSheet('color: rgb' + str(color))
            widget.spinExp.valueChanged.connect(
                lambda exp=widget.spinExp.value(), wm_channel=wm_channel: self.exp_changed(exp, wm_channel))
            init_value = yield self.server.get_exposure(wm_channel)
            widget.spinExp.setValue(init_value)
            init_meas = yield self.server.get_switcher_signal_state(wm_channel)
            init_meas = init_meas
            widget.measSwitch.setChecked(bool(init_meas))
            widget.measSwitch.toggled.connect(
                lambda state=widget.measSwitch.isDown(), wm_channel=wm_channel: self.change_state(state, wm_channel))
            widget.zeroVoltage.clicked.connect(
                lambda widget=widget, dac_port=dac_port: self.set_voltage_zero(widget, dac_port))

            self.d[wm_channel] = widget
            sub_layout.addWidget(self.d[wm_channel], position[1], position[0], 1, 3)

        self.setLayout(layout)

    @inlineCallbacks
    def initialize_pid_gui(self, dac_port, chan):
        self.pid = QCustomPID(dac_port)
        self.pid.setWindowTitle(chan + ' PID settings')
        self.pid.move(self.pos())
        self.index = {1: 0, -1: 1}

        p_init = yield self.server.get_pid_p(dac_port)
        i_init = yield self.server.get_pid_i(dac_port)
        d_init = yield self.server.get_pid_d(dac_port)
        dt_init = yield self.server.get_pid_dt(dac_port)
        const_init = yield self.server.get_const_dt(dac_port)
        sens_init = yield self.server.get_pid_sensitivity(dac_port)
        pol_init = yield self.server.get_pid_polarity(dac_port)

        self.pid.spinP.setValue(p_init)
        self.pid.spinI.setValue(i_init)
        self.pid.spinD.setValue(d_init)
        self.pid.spinDt.setValue(dt_init)
        self.pid.useDTBox.setCheckState(bool(const_init))
        self.pid.spinFactor.setValue(sens_init[0])
        self.pid.spinExp.setValue(sens_init[1])
        self.pid.polarityBox.setCurrentIndex(self.index[pol_init])

        self.pid.spinP.valueChanged.connect(
            lambda p=self.pid.spinP.value(), dac_port=dac_port: self.change_p(p, dac_port))
        self.pid.spinI.valueChanged.connect(
            lambda i=self.pid.spinI.value(), dac_port=dac_port: self.change_i(i, dac_port))
        self.pid.spinD.valueChanged.connect(
            lambda d=self.pid.spinD.value(), dac_port=dac_port: self.change_d(d, dac_port))
        self.pid.spinDt.valueChanged.connect(
            lambda dt=self.pid.spinDt.value(), dac_port=dac_port: self.change_dt(dt, dac_port))
        self.pid.useDTBox.stateChanged.connect(
            lambda state=self.pid.useDTBox.isChecked(), dac_port=dac_port: self.const_dt(state, dac_port))
        self.pid.spinFactor.valueChanged.connect(
            lambda factor=self.pid.spinFactor.value(), dac_port=dac_port: self.change_factor(factor, dac_port))
        self.pid.spinExp.valueChanged.connect(
            lambda exponent=self.pid.spinExp.value(), dac_port=dac_port: self.change_exponent(exponent, dac_port))
        self.pid.polarityBox.currentIndexChanged.connect(lambda index=self.pid.polarityBox.currentIndex(),
                                                                dac_port=dac_port: self.change_polarity(index, dac_port))

        self.pid.show()

    @inlineCallbacks
    def exp_changed(self, exp, chan):
        #  these are switched, don't know why

        exp = int(exp)
        yield self.server.set_exposure_time(chan, exp)

    def update_frequency(self, c, signal):
        chan = signal[0]
        if chan in self.d:
            freq = signal[1]

            if not self.d[chan].measSwitch.isChecked():
                self.d[chan].current_frequency.setText('Not Measured')
            elif freq == -3.0:
                self.d[chan].current_frequency.setText('Under Exposed')
            elif freq == -4.0:
                self.d[chan].current_frequency.setText('Over Exposed')
            elif freq == -17.0:
                self.d[chan].current_frequency.setText('Data Error')
            else:
                self.d[chan].current_frequency.setText(str(freq)[0:10])

    def update_pid_voltage(self, c, signal):
        dac_port = signal[0]
        value = signal[1]
        if dac_port in self.wmChannels:
            try:
                self.d[self.wmChannels[dac_port]].pid_voltage.setText('DAC Voltage (mV)  ' + "{:.1f}".format(value))
                self.d[self.wmChannels[dac_port]].pid_indicator.update_slider(value / 1000.0)
            except:
                pass

    def toggle_measurement(self, c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d:
            self.d[chan].measSwitch.blockSignals(True)
            self.d[chan].measSwitch.setChecked(value)
            self.d[chan].measSwitch.blockSignals(False)

    def toggle_lock(self, c, signal):
        self.lockSwitch.blockSignals(True)
        self.lockSwitch.setChecked(signal)
        self.lockSwitch.blockSignals(False)

    def toggle_channel_cock(self, c, signal):
        wm_channel = signal[1]
        state = signal[2]
        if wm_channel in self.d:
            self.d[wm_channel].lockChannel.blockSignals(True)
            self.d[wm_channel].lockChannel.setChecked(bool(state))
            self.d[wm_channel].lockChannel.blockSignals(False)

    def update_exp(self, c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d:
            self.d[chan].spinExp.blockSignals(True)
            self.d[chan].spinExp.setValue(value)
            self.d[chan].spinExp.blockSignals(False)

    def update_wlm_output(self, c, signal):
        self.startSwitch.blockSignals(True)
        self.startSwitch.setChecked(signal)
        self.startSwitch.blockSignals(False)

    def update_amplitude(self, c, signal):
        wm_channel = signal[0]
        value = signal[1]
        if wm_channel in self.d:
            self.d[wm_channel].power_meter.blockSignals(True)
            self.d[wm_channel].power_meter.setValue(int(value))
            self.d[wm_channel].power_meter.blockSignals(False)

    def update_pattern(self, c, signal):
        chan = signal[0]
        if1 = signal[1]
        points = 512
        if chan in self.pattern_1:
            self.pattern_1[chan].setData(x=np.arange(points), y=if1)

    def set_button_off(self, wm_channel):
        self.d[wm_channel].lockChannel.setChecked(False)

    @inlineCallbacks
    def change_state(self, state, chan):
        yield self.server.set_switcher_signal_state(chan, state)

    @inlineCallbacks
    def lock_single_channel(self, state, dac_port):
        wm_channel = self.wmChannels[dac_port]
        yield self.server.set_channel_lock(dac_port, wm_channel, state)

    @inlineCallbacks
    def freq_changed(self, freq, dac_port):
        yield self.server.set_pid_course(dac_port, freq)

    @inlineCallbacks
    def set_lock(self, state):
        yield self.server.set_lock_state(state)

    @inlineCallbacks
    def set_output(self, state):
        yield self.server.set_wlm_output(state)

    @inlineCallbacks
    def get_pid_course(self, dac_port, hint):
        course = yield self.server.get_pid_course(dac_port)
        try:
            course = float(course)
        except ValueError:
            try:
                course = float(hint)
            except ValueError:
                course = 600
        returnValue(course)

    @inlineCallbacks
    def change_p(self, p, dac_port):
        yield self.server.set_pid_p(dac_port, p)

    @inlineCallbacks
    def change_i(self, i, dac_port):
        yield self.server.set_pid_i(dac_port, i)

    @inlineCallbacks
    def change_d(self, d, dac_port):
        yield self.server.set_pid_d(dac_port, d)

    @inlineCallbacks
    def change_dt(self, dt, dac_port):
        yield self.server.set_pid_dt(dac_port, dt)

    @inlineCallbacks
    def const_dt(self, state, dac_port):
        if state == 0:
            yield self.server.set_const_dt(dac_port, False)
        else:
            yield self.server.set_const_dt(dac_port, True)

    @inlineCallbacks
    def change_factor(self, factor, dac_port):
        yield self.server.set_pid_sensitivity(dac_port, factor, int(self.pid.spinExp.value()))

    @inlineCallbacks
    def change_exponent(self, exponent, dac_port):
        yield self.server.set_pid_sensitivity(dac_port, self.pid.spinFactor.value(), int(exponent))

    @inlineCallbacks
    def change_polarity(self, index, dac_port):
        if index == 0:
            yield self.server.set_pid_polarity(dac_port, 1)
        else:
            yield self.server.set_pid_polarity(dac_port, -1)

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
