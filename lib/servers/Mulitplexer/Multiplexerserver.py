from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet.threads import deferToThread
from ctypes import *
from twisted.internet import reactor

"""
### BEGIN NODE INFO
[info]
name = Multiplexer Server
version = 1.0
description =
instancename = Multiplexer Server

[startup]
cmdline = %PYTHON% %FILE%self.wmdll.SetPIDCourseNum
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

UPDATEEXP = 122387
CHANSIGNAL = 122485
FREQSIGNAL = 122456
LOCKSIGNAL = 112456
OUTPUTCHANGED = 121212
PIDVOLTAGE = 902484


class PID(object):
    """
    Discrete PID control
    """

    def __init__(self, P=2.0, I=0.0, D=1.0, Derivator=0, Integrator=0,
                 Integrator_max=500, Integrator_min=-500):

        self.Kp = P
        self.Ki = I
        self.Kd = D
        self.Derivator = Derivator
        self.Integrator = Integrator
        self.Integrator_max = Integrator_max
        self.Integrator_min = Integrator_min

        self.set_point = 0.0
        self.error = 0.0

    def update(self, current_value):
        """
        Calculate PID output value for given reference input and feedback
        """
        self.error = self.set_point - current_value

        self.P_value = self.Kp * self.error
        self.D_value = self.Kd * (self.error - self.Derivator)
        self.Derivator = self.error

        self.Integrator = self.Integrator + self.error

        if self.Integrator > self.Integrator_max:
            self.Integrator = self.Integrator_max
        elif self.Integrator < self.Integrator_min:
            self.Integrator = self.Integrator_min

        self.I_value = self.Integrator * self.Ki

        PID = self.P_value + self.I_value + self.D_value

        return PID

    def setPoint(self, set_point):
        """
        Initilize the setpoint of PID
        """
        self.set_point = set_point
        self.Integrator = 0
        self.Derivator = 0

    def setIntegrator(self, Integrator):
        self.Integrator = Integrator

    def setDerivator(self, Derivator):
        self.Derivator = Derivator

    def setKp(self, P):
        self.Kp = P

    def setKi(self, I):
        self.Ki = I

    def setKd(self, D):
        self.Kd = D

    def getPoint(self):
        return self.set_point

    def getError(self):
        return self.error

    def getIntegrator(self):
        return self.Integrator

    def getDerivator(self):
        return self.Derivator


class MultiplexerServer(LabradServer):
    """
    Multiplexer Server for Wavelength Meter
    """
    name = 'Multiplexerserver'

    # Set up signals to be sent to listeners
    channel_string = 'signal: selected channels changed'
    measuredchanged = Signal(CHANSIGNAL, channel_string, '(ib)')
    freqchanged = Signal(FREQSIGNAL, 'signal: frequency changed', '(iv)')
    updateexp = Signal(UPDATEEXP, 'signal: update exp', '(ii)')
    lockchanged = Signal(LOCKSIGNAL, 'signal: lock changed', 'b')
    outputchanged = Signal(OUTPUTCHANGED, 'signal: output changed', 'b')
    voltage_string = 'signal: pidvoltage changed'
    pidvoltagechanged = Signal(PIDVOLTAGE, voltage_string, '(iv)')

    def initServer(self):

        # load wavemeter dll file for use of API functions self.d and self.l
        # are dummy c_types for unused wavemeter functions

        self.d = c_double(0)
        self.l = c_long(0)
        self.b = c_bool(0)
        self.wmdll = windll.LoadLibrary("C:\Windows\System32\wlmData.dll")

        #allocates c_types for dll functions
        self.wmdll.GetActiveChannel.restype        = c_long
        self.wmdll.GetAmplitudeNum.restype         = c_long
        self.wmdll.GetDeviationMode.restype        = c_bool
        self.wmdll.GetDeviationSignalNum.restype   = c_double
        self.wmdll.GetExposureNum.restype          = c_long
        self.wmdll.GetFrequencyNum.restype         = c_double
        self.wmdll.GetPIDCourseNum.restype         = c_long
        self.wmdll.GetSwitcherMode.restype         = c_long
        self.wmdll.GetSwitcherSignalStates.restype = c_long

        self.wmdll.SetDeviationMode.restype        = c_long
        self.wmdll.SetDeviationSignalNum.restype   = c_double
        self.wmdll.SetExposureNum.restype          = c_long
        self.wmdll.SetPIDCourseNum.restype         = c_long
        self.wmdll.SetSwitcherSignalStates.restype = c_long
        self.wmdll.SetSwitcherMode.restype         = c_long
        self.wmdll.SetDeviationSignal.restype      = c_long

        self.measureChan()

        self.listeners = set()

        # Main program functions

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
        instance.restype = c_long
        RFC = c_long(-1)
        # RFC, reason for call, used to check if wavemeter is running
        # (in wavemeter .h library
        status = yield instance(RFC, self.l, self.l, self.l)
        returnValue(status)

    # Set Functions

    @setting(10, "set_exposure_time", chan='i', ms='i')
    def set_exposure_time(self, c, chan, ms):
        notified = self.getOtherListeners(c)
        ms_c = c_long(ms)
        chan_c = c_long(chan)
        yield self.wmdll.SetExposureNum(chan_c, 1,  ms_c)
        self.updateexp((chan, ms), notified)

    @setting(11, "set_lock_state", state='b')
    def set_lock_state(self, c, state):
        notified = self.getOtherListeners(c)
        state_c = c_bool(state)
        yield self.wmdll.SetDeviationMode(state_c)
        self.lockchanged(state, notified)

    @setting(12, "set_switcher_mode", mode='b')
    def set_switcher_mode(self, c, mode):
        mode_c = c_long(mode)
        yield self.wmdll.SetSwitcherMode(mode_c)

    @setting(13, "set_switcher_signal_state", chan='i', state='b')
    def set_switcher_state(self, c, chan, state):
        notified = self.getOtherListeners(c)
        chan_c = c_long(chan)
        state_c = c_long(state)
        yield self.wmdll.SetSwitcherSignalStates(chan_c, state_c, c_long(1))
        self.measuredchanged((chan, state), notified)

    @setting(14, "set_pid_course", chan='i', course='v')
    def set_pid_course(self, c, chan, course):
        chan_c = c_long(chan)
        course_c = c_char_p('=' + str(course))
        yield self.wmdll.SetPIDCourseNum(chan_c, course_c)

    @setting(15, "set_dac_voltage", chan='i', value='v')
    def set_dac_voltage(self, c, chan, value):
        chan_c = c_long(chan)
        # convert Volts to mV
        value = value*1000
        value_c = c_double(value)
        yield self.wmdll.SetDeviationSignalNum(chan_c, value_c)

    @setting(16, "set_wlm_output", output='b')
    def set_wlm_output(self, c, output):
        '''Start or stops wavemeter
        '''
        notified = self.getOtherListeners(c)
        if output is True:
            yield self.wmdll.Operation(2)
        else:
            yield self.wmdll.Operation(0)
        self.outputchanged(output, notified)

    # Get Functions

    @setting(20, "get_amplitude", chan='i', returns='v')
    def get_amplitude(self, c, chan):
        chan_c = c_long(chan)
        amp = yield self.wmdll.GetAmplitudeNum(chan_c, c_long(2), self.l)
        returnValue(amp)

    @setting(21, "get_exposure", chan='i', returns='i')
    def get_exposure(self, c, chan):
        chan_c = c_long(chan)
        exp = yield self.wmdll.GetExposureNum(chan_c, 1, self.l)
        returnValue(exp)

    @setting(22, "get_frequency", chan='i', returns='v')
    def get_frequency(self, c, chan):
        chan_c = c_long(chan)
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

    @setting(25, "get_output_voltage", chan='i', returns='v')
    def get_output_voltage(self, c, chan):
        chan_c = c_long(chan)
        volts = yield self.wmdll.GetDeviationSignalNum(chan_c, self.d)
        self.pidvoltagechanged((chan, volts))
        returnValue(volts)

    @setting(26, "get_switcher_signal_state", chan='i', returns='b')
    def get_switcher_signal_state(self, c, chan):
        chan_c = c_long(chan)
        use_c = c_long(0)
        show_c = c_long(0)
        yield self.wmdll.GetSwitcherSignalStates(chan_c, pointer(use_c),
                                                 pointer(show_c))

        use = bool(use_c)
        returnValue(use)

    @setting(27, "get_pid_course", chan='i', returns='s')
    def get_pid_course(self, c, chan):
        chan_c = c_long(chan)
        course_c = create_string_buffer(1024)
        yield self.wmdll.GetPIDCourseNum(chan_c, pointer(course_c))
        value = str(course_c.value)
        returnValue(value)

    @setting(28, "get_wlm_output", returns='b')
    def get_wlm_output(self, c):
        value = yield self.wmdll.GetOperationState(c_short(0))
        if value == 2:
            value = True
        else:
            value = False
        returnValue(value)

    @setting(29, "get_individual_lock_state", returns='b')
    def get_individual_lock_state(self, c, chan):
        return False

    def measure_chan(self):
        # TODO: Improve this with a looping call
        reactor.callLater(0.1, self.measure_chan)
        for chan in range(8):
            if self.get_switcher_signal_state(self, chan + 1):
                self.get_frequency(self, chan + 1)
                self.get_output_voltage(self, chan + 1)
                if self.get_individual_lock_state(self, chan + 1):
                    value = self.calcPID(chan)
                    print value
                    # self.setDACVoltage(chan + 1, value )

if __name__ == "__main__":
    from labrad import util
    util.runServer(MultiplexerServer())
