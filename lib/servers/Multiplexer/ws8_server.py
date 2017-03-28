"""
### BEGIN NODE INFO
[info]
name = Multiplexer Server
version = 0.9
description =
instancename = Multiplexer Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue
import ctypes
from twisted.internet import reactor

UPDATEEXP = 122387
CHANSIGNAL = 122485
FREQSIGNAL = 122456
LOCKSIGNAL = 112456
OUTPUTCHANGED = 121212
CHANNELLOCK = 282388
AMPCHANGED = 142308


class MultiplexerServer(LabradServer):
    """
    Multiplexer server for WS-U wavelength meter.

    A DLL is required to run this server.  See initServer for the path location
    for the library.
    """
    name = 'Multiplexerserver'

    # Set up signals to be sent to listeners
    channel_text = 'signal: selected channels changed'
    measuredchanged = Signal(CHANSIGNAL, channel_text, '(ib)')
    freqchanged = Signal(FREQSIGNAL, 'signal: frequency changed', '(iv)')
    updateexp = Signal(UPDATEEXP, 'signal: update exp', '(ii)')
    outputchanged = Signal(OUTPUTCHANGED, 'signal: output changed', 'b')
    channellock = Signal(CHANNELLOCK, 'signal: channel lock changed', '(wwb)')
    ampchanged = Signal(AMPCHANGED, 'signal: amplitude changed', '(wv)')

    def initServer(self):

        # load wavemeter dll file for use of API functions self.d and self.l
        # are dummy c_types for unused wavemeter functions

        dll_path = "C:\Windows\System32\wlmData.dll"
        self.wmdll = ctypes.windll.LoadLibrary(dll_path)
        self.d = ctypes.c_double(0)
        self.l = ctypes.c_long(0)
        self.b = ctypes.c_bool(0)

        # Getting the amplitude in the GetAmplitudeNum function can
        # return the max, min, and average of the interference pattern
        self.AmplitudeMin = ctypes.c_long(0)
        self.AmplitudeMax = ctypes.c_long(2)
        self.AmplitudeAvg = ctypes.c_long(4)

        self.set_dll_variables()
        self.WavemeterVersion = self.wmdll.GetWLMVersion(ctypes.c_long(1))

        self.measureChan()

        self.listeners = set()

    def set_dll_variables(self):
        """
        Allocate c_types for dll functions.
        """
        self.wmdll.GetActiveChannel.restype = ctypes.c_long
        self.wmdll.GetAmplitudeNum.restype = ctypes.c_long
        self.wmdll.GetDeviationMode.restype = ctypes.c_bool
        self.wmdll.GetDeviationSignalNum.restype = ctypes.c_double
        self.wmdll.GetExposureNum.restype = ctypes.c_long
        self.wmdll.GetFrequencyNum.restype = ctypes.c_double
        self.wmdll.GetSwitcherMode.restype = ctypes.c_long
        self.wmdll.GetSwitcherSignalStates.restype = ctypes.c_long
        self.wmdll.GetChannelsCount.restype = ctypes.c_long
        self.wmdll.GetWLMVersion.restype = ctypes.c_long

        self.wmdll.SetDeviationMode.restype = ctypes.c_long
        self.wmdll.SetDeviationSignalNum.restype = ctypes.c_double
        self.wmdll.SetExposureNum.restype = ctypes.c_long
        self.wmdll.SetSwitcherSignalStates.restype = ctypes.c_long
        self.wmdll.SetSwitcherMode.restype = ctypes.c_long
        self.wmdll.SetDeviationSignal.restype = ctypes.c_long
        self.wmdll.SetActiveChannel.restype = ctypes.c_long

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @setting(1, "check_wlm_running")
    def instance(self, c):
        instance = self.wmdll.Instantiate
        instance.restype = ctypes.c_long
        RFC = ctypes.c_long(-1)
        # RFC, reason for call, used to check if wavemeter is running
        # (in wavemeter .h library)
        status = yield instance(RFC, self.l, self.l, self.l)
        returnValue(status)

    # Set functions

    @setting(93, "set_active_channel", chan='w')
    def set_active_channel(self, c, chan):
        chan_c = ctypes.c_long(chan)
        yield self.wmdll.SetActiveChannel(ctypes.c_long(1), self.l, chan_c, self.l)

    @setting(10, "set_exposure_time", chan='i', ms='i')
    def set_exposure_time(self, c, chan, ms):
        notified = self.getOtherListeners(c)
        ms_c = ctypes.c_long(ms)
        chan_c = ctypes.c_long(chan)
        yield self.wmdll.SetExposureNum(chan_c, 1,  ms_c)
        self.updateexp((chan, ms), notified)

    @setting(12, "set_switcher_mode", mode='b')
    def set_switcher_mode(self, c, mode):
        """ Allows measuring of multiple channels with multiplexer.
        Should always be set to on."""
        mode_c = ctypes.c_long(mode)
        yield self.wmdll.SetSwitcherMode(mode_c)

    @setting(13, "set_switcher_signal_state", chan='i', state='b')
    def set_switcher_signal_state(self, c, chan, state):
        """ Turns on and off individual channel measurement"""
        notified = self.getOtherListeners(c)
        chan_c = ctypes.c_long(chan)
        state_c = ctypes.c_long(state)
        yield self.wmdll.SetSwitcherSignalStates(chan_c, state_c,
                                                 ctypes.c_long(1))
        self.measuredchanged((chan, state), notified)

    @setting(15, "set_dac_voltage", dacPort='i', value='v')
    def set_dac_voltage(self, c, dacPort, value):
        """Sets voltage of specified DAC channel in V. Can only be used
        when all PID control is off: set_lock_state = 0"""
        chan_c = ctypes.c_long(dacPort)
        # convert Volts to mV
        value = value*1000
        value_c = ctypes.c_double(value)
        yield self.wmdll.SetDeviationSignalNum(chan_c, value_c)

    @setting(16, "set_wlm_output", output='b')
    def set_wlm_output(self, c, output):
        """Start or stops wavemeter
        """
        notified = self.getOtherListeners(c)
        if output is True:
            yield self.wmdll.Operation(2)
        else:
            yield self.wmdll.Operation(0)
        self.outputchanged(output, notified)



    # Get Functions

    @setting(20, "get_amplitude", chan='w', returns='v')
    def get_amplitude(self, c, chan):
        chan_c = ctypes.c_long(chan)
        amp = yield self.wmdll.GetAmplitudeNum(chan_c, self.AmplitudeMax,
                                               self.l)
        self.ampchanged((chan, amp))
        returnValue(amp)

    @setting(21, "get_exposure", chan='i', returns='i')
    def get_exposure(self, c, chan):
        chan_c = ctypes.c_long(chan)
        exp = yield self.wmdll.GetExposureNum(chan_c, 1, self.l)
        returnValue(exp)

    @setting(22, "get_frequency", chan='i', returns='v')
    def get_frequency(self, c, chan):
        chan_c = ctypes.c_long(chan)
        freq = yield self.wmdll.GetFrequencyNum(chan_c, self.d)
        self.freqchanged((chan, freq))
        returnValue(freq)

    @setting(23, "get_lock_state", returns='b')
    def get_lock_state(self, c):
        state = yield self.wmdll.GetDeviationMode(0)
        returnValue(state)

    @setting(24, "get_switcher_mode", returns='b')
    def get_switcher_mode(self, c):
        state = yield self.wmdll.GetSwitcherMode(0)
        returnValue(bool(state))

    @setting(26, "get_switcher_signal_state", chan='i', returns='b')
    def get_switcher_signal_state(self, c, chan):
        chan_c = ctypes.c_long(chan)
        use_c = ctypes.c_long(0)
        show_c = ctypes.c_long(0)
        yield self.wmdll.GetSwitcherSignalStates(chan_c, ctypes.pointer(use_c),
                                                 ctypes.pointer(show_c))

        use = bool(use_c)
        returnValue(use)

    @setting(28, "get_wlm_output", returns='b')
    def get_wlm_output(self, c):
        value = yield self.wmdll.GetOperationState(ctypes.c_short(0))
        if value == 2:
            value = True
        else:
            value = False
        returnValue(value)

    @setting(31, "get_total_channels", returns='w')
    def get_total_channels(self, c):
        count = yield self.wmdll.GetChannelsCount(ctypes.c_long(0))
        returnValue(count)

    def measureChan(self):
        # TODO: Improve this with a looping call
        reactor.callLater(0.1, self.measureChan)
        count = self.wmdll.GetChannelsCount(ctypes.c_long(0))
        for chan in range(count):
            if self.get_switcher_signal_state(self, chan + 1):
                self.get_frequency(self, chan + 1)
                #self.get_output_voltage(self, chan + 1)
                self.get_amplitude(self, chan + 1)


if __name__ == "__main__":
    from labrad import util
    util.runServer(MultiplexerServer())
