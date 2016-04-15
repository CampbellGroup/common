from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue
import ctypes
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
CHANNELLOCK = 282388
AMPCHANGED = 142308


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
    channel_text = 'signal: selected channels changed'
    measuredchanged = Signal(CHANSIGNAL, channel_text, '(ib)')
    freqchanged = Signal(FREQSIGNAL, 'signal: frequency changed', '(iv)')
    updateexp = Signal(UPDATEEXP, 'signal: update exp', '(ii)')
    lockchanged = Signal(LOCKSIGNAL, 'signal: lock changed', 'b')
    outputchanged = Signal(OUTPUTCHANGED, 'signal: output changed', 'b')
    voltage_text = 'signal: pidvoltage changed'
    pidvoltagechanged = Signal(PIDVOLTAGE, voltage_text, '(iv)')
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

        # Each variable that can be changed (P,I,D,etc..) in the
        # SetPIDSettings function is assigned a constant which must be
        # passed to the function when calling. Below is the map.
        self.PID_P = ctypes.c_long(1034)
        self.PID_I = ctypes.c_long(1035)
        self.PID_D = ctypes.c_long(1036)
        self.PID_dt = ctypes.c_long(1060)
        self.PIDConstdt = ctypes.c_long(1059)
        self.DeviationSensitivityFactor = ctypes.c_long(1037)
        self.DeviationSensitivityDimension = ctypes.c_long(1040)
        self.DeviationUnit = ctypes.c_long(1041)
        self.DeviationPolarity = ctypes.c_long(1038)
        self.DeviationChannel = ctypes.c_long(1063)
        self.UseFrequencyUnits = ctypes.c_long(2)

        # Getting the amplitude in the GetAmplitudeNum function can
        # return the max, min, and average of the interference pattern
        self.AmplitudeMin = ctypes.c_long(0)
        self.AmplitudeMax = ctypes.c_long(2)
        self.AmplitudeAvg = ctypes.c_long(4)

        # allocates c_types for dll functions
        self.wmdll.GetActiveChannel.restype = ctypes.c_long
        self.wmdll.GetAmplitudeNum.restype = ctypes.c_long
        self.wmdll.GetDeviationMode.restype = ctypes.c_bool
        self.wmdll.GetDeviationSignalNum.restype = ctypes.c_double
        self.wmdll.GetExposureNum.restype = ctypes.c_long
        self.wmdll.GetFrequencyNum.restype = ctypes.c_double
        self.wmdll.GetPIDCourseNum.restype = ctypes.c_long
        self.wmdll.GetSwitcherMode.restype = ctypes.c_long
        self.wmdll.GetSwitcherSignalStates.restype = ctypes.c_long
        self.wmdll.GetChannelsCount.restype = ctypes.c_long
        self.wmdll.GetPIDSetting.restype = ctypes.c_long

        self.wmdll.SetDeviationMode.restype = ctypes.c_long
        self.wmdll.SetDeviationSignalNum.restype = ctypes.c_double
        self.wmdll.SetExposureNum.restype = ctypes.c_long
        self.wmdll.SetPIDCourseNum.restype = ctypes.c_long
        self.wmdll.SetSwitcherSignalStates.restype = ctypes.c_long
        self.wmdll.SetSwitcherMode.restype = ctypes.c_long
        self.wmdll.SetDeviationSignal.restype = ctypes.c_long
        self.wmdll.SetPIDSetting.restype = ctypes.c_long

        self.measureChan()

        self.listeners = set()

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @setting(1, "Check WLM Running")
    def instance(self, c):
        instance = self.wmdll.Instantiate
        instance.restype = ctypes.c_long
        RFC = ctypes.c_long(-1)
        # RFC, reason for call, used to check if wavemeter is running
        # (in wavemeter .h library)
        status = yield instance(RFC, self.l, self.l, self.l)
        returnValue(status)

    # Set functions

    @setting(10, "Set Exposure Time", chan='i', ms='i')
    def setExposureTime(self, c, chan, ms):
        notified = self.getOtherListeners(c)
        ms_c = ctypes.c_long(ms)
        chan_c = ctypes.c_long(chan)
        yield self.wmdll.SetExposureNum(chan_c, 1,  ms_c)
        self.updateexp((chan, ms), notified)

    @setting(11, "Set Lock State", state='b')
    def setLockState(self, c, state):
        """ Turns on PID regulation for all channels. Must be on
        for individual channel locking to work."""
        notified = self.getOtherListeners(c)
        state_c = ctypes.c_bool(state)
        yield self.wmdll.SetDeviationMode(state_c)
        self.lockchanged(state, notified)

    @setting(12, "Set Switcher Mode", mode='b')
    def setSwitcherMode(self, c, mode):
        """ Allows measuring of multiple channels with multiplexer.
        Should always be set to on."""
        mode_c = ctypes.c_long(mode)
        yield self.wmdll.SetSwitcherMode(mode_c)

    @setting(13, "Set Switcher Signal State", chan='i', state='b')
    def setSwitcherState(self, c, chan, state):
        """ Turns on and off individual channel measurement"""
        notified = self.getOtherListeners(c)
        chan_c = ctypes.c_long(chan)
        state_c = ctypes.c_long(state)
        yield self.wmdll.SetSwitcherSignalStates(chan_c, state_c,
                                                 ctypes.c_long(1))

        self.measuredchanged((chan, state), notified)

    @setting(14, "Set PID Course", dacPort='w', course='v')
    def setPIDCourse(self, c, dacPort, course):
        """Set reference frequency in THz for the PID control"""
        chan_c = ctypes.c_long(dacPort)
        course_c = ctypes.c_char_p('=' + str(course))
        yield self.wmdll.SetPIDCourseNum(chan_c, course_c)

    @setting(15, "Set DAC Voltage", dacPort='i', value='v')
    def setDACVoltage(self, c, dacPort, value):
        """Sets voltage of specified DAC channel in V. Can only be used
        when all PID control is off: set_lock_state = 0"""
        chan_c = ctypes.c_long(dacPort)
        # convert Volts to mV
        value = value*1000
        value_c = ctypes.c_double(value)
        yield self.wmdll.SetDeviationSignalNum(chan_c, value_c)

    @setting(16, "Set WLM Output", output='b')
    def setWLMOutput(self, c, output):
        """Start or stops wavemeter
        """
        notified = self.getOtherListeners(c)
        if output is True:
            yield self.wmdll.Operation(2)
        else:
            yield self.wmdll.Operation(0)
        self.outputchanged(output, notified)

    @setting(17, "set pid p", dacPort='w', P='v')
    def set_pid_p(self, c, dacPort, P):
        """Sets the P PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        value = ctypes.c_double(P)
        yield self.wmdll.SetPIDSetting(self.PID_P, port_c, self.l, value)

    @setting(18, "set pid i", dacPort='w', I='v')
    def set_pid_i(self, c, dacPort, I):
        """Sets the I PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        value = ctypes.c_double(I)
        yield self.wmdll.SetPIDSetting(self.PID_I, port_c, self.l, value)

    @setting(19, "set pid d", dacPort='w', D='v')
    def set_pid_d(self, c, dacPort, D):
        """Sets the D PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        value = ctypes.c_double(D)
        yield self.wmdll.SetPIDSetting(self.PID_D, port_c, self.l, value)

    @setting(39, "set pid dt", dacPort='w', dt='v')
    def set_pid_dt(self, c, dacPort, dt):
        """Sets the dt PID settings for a given DAC port."""
        if dt <= 0:
            returnValue("dt must be greater than zero")
        else:
            port_c = ctypes.c_long(dacPort)
            value = ctypes.c_double(dt)
            yield self.wmdll.SetPIDSetting(self.PID_dt, port_c, self.l, value)

    @setting(121, "set const dt", dacPort='w', dt='b')
    def set_const_dt(self, c, dacPort, dt):
        """Activates the dt PID settings for a given DAC port. This makes each
        dt in the integration constant as opposed to oscillating values based
        on the system time, which changes when changing wm settings."""
        port_c = ctypes.c_long(dacPort)
        value = ctypes.c_long(dt)
        yield self.wmdll.SetPIDSetting(self.PIDConstdt, port_c, value, self.d)

    @setting(40, "set pid sensitivity", dacPort='w', sensitivityFactor='v',
             sensitivityExponent='i')
    def set_pid_sensitivity(self, c, dacPort, sensitivityFactor,
                            sensitivityExponent):
        """Sets the sensitivity of the analog output for a given DAC port.
        Sensitivity = (sensitivityFactor*V)/(THz*10^[sensitivityExponent])
        sensitivityFactor range is [1,9.99]."""
        port_c = ctypes.c_long(dacPort)
        sFactor = ctypes.c_double(sensitivityFactor)
        sExponent = ctypes.c_long(sensitivityExponent)
        # Make sure the units are set to frequency
        yield self.wmdll.SetPIDSetting(self.DeviationUnit, port_c,
                                       self.UseFrequencyUnits, self.d)

        yield self.wmdll.SetPIDSetting(self.DeviationSensitivityDimension,
                                       port_c, sExponent, self.d)

        yield self.wmdll.SetPIDSetting(self.DeviationSensitivityFactor, port_c,
                                       self.l, sFactor)

    @setting(41, "set pid polarity", dacPort='w', polarity='i')
    def set_pid_polarity(self, c, dacPort, polarity):
        """Sets the polarity for a given DAC port. Allowed values are +/- 1."""
        if polarity == 1 or polarity == -1:
            port_c = ctypes.c_long(dacPort)
            value = ctypes.c_long(polarity)
            yield self.wmdll.SetPIDSetting(self.DeviationPolarity, port_c,
                                           value, self.d)

        else:
            returnValue("Polarity must be +/- 1")

    @setting(42, "set channel lock", dacPort='w', waveMeterChannel='w',
             lock='b')
    def set_channel_lock(self, c, dacPort, waveMeterChannel, lock):
        """Locks a wavemeter channel to a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        chan_c = ctypes.c_long(waveMeterChannel)

        # Check to ensure a valid PID Course number is set, otherwise
        # trying to lock a channel turns off lock to main PID lock switch

        course_c = ctypes.create_string_buffer(1024)
        yield self.wmdll.GetPIDCourseNum(port_c, ctypes.pointer(course_c))
        course = float(course_c.value)
        if course <= 0:
            returnValue("Set PID Course to a valid number")
        else:
            notified = self.getOtherListeners(c)
            if lock == 1:
                yield self.wmdll.SetPIDSetting(self.DeviationChannel, port_c,
                                               chan_c, self.d)

            elif lock == 0:
                yield self.wmdll.SetPIDSetting(self.DeviationChannel, port_c,
                                               ctypes.c_long(0), self.d)

            self.channellock((dacPort, waveMeterChannel, lock), notified)

    # Get Functions

    @setting(20, "Get Amplitude", chan='w', returns='v')
    def getAmp(self, c, chan):
        chan_c = ctypes.c_long(chan)
        amp = yield self.wmdll.GetAmplitudeNum(chan_c, self.AmplitudeMax,
                                               self.l)

        self.ampchanged((chan, amp))
        returnValue(amp)

    @setting(21, "Get Exposure", chan='i', returns='i')
    def getExp(self, c, chan):
        chan_c = ctypes.c_long(chan)
        exp = yield self.wmdll.GetExposureNum(chan_c, 1, self.l)
        returnValue(exp)

    @setting(22, "Get Frequency", chan='i', returns='v')
    def getFrequency(self, c, chan):
        chan_c = ctypes.c_long(chan)
        freq = yield self.wmdll.GetFrequencyNum(chan_c, self.d)
        self.freqchanged((chan, freq))
        returnValue(freq)

    @setting(23, "Get Lock State", returns='b')
    def getLockState(self, c):
        state = yield self.wmdll.GetDeviationMode(0)
        returnValue(state)

    @setting(24, "Get Switcher Mode", returns='b')
    def getSwitcherMode(self, c):
        state = yield self.wmdll.GetSwitcherMode(0)
        returnValue(bool(state))

    @setting(25, "Get Output Voltage", dacPort='w', returns='v')
    def getOutputVoltage(self, c, dacPort):
        """Gets the output voltage (mV) of the specified DAC channel"""
        chan_c = ctypes.c_long(dacPort)
        volts = yield self.wmdll.GetDeviationSignalNum(chan_c, self.d)
        self.pidvoltagechanged((dacPort, volts))
        returnValue(volts)

    @setting(26, "Get Switcher Signal State", chan='i', returns='b')
    def getSwitcherState(self, c, chan):
        chan_c = ctypes.c_long(chan)
        use_c = ctypes.c_long(0)
        show_c = ctypes.c_long(0)
        yield self.wmdll.GetSwitcherSignalStates(chan_c, ctypes.pointer(use_c),
                                                 ctypes.pointer(show_c))

        use = bool(use_c)
        returnValue(use)

    @setting(27, "Get PID Course", dacPort='w', returns='s')
    def getPIDCourse(self, c, dacPort):
        chan_c = ctypes.c_long(dacPort)
        course_c = ctypes.create_string_buffer(1024)
        yield self.wmdll.GetPIDCourseNum(chan_c, ctypes.pointer(course_c))
        value = str(course_c.value)
        returnValue(value)

    @setting(28, "Get WLM Output", returns='b')
    def getWLMOutput(self, c):
        value = yield self.wmdll.GetOperationState(ctypes.c_short(0))
        if value == 2:
            value = True
        else:
            value = False
        returnValue(value)

    @setting(29, "Get Channel Lock", dacPort='w', waveMeterChannel='w',
             returns='?')
    def getSingleLockState(self, c, dacPort, waveMeterChannel):
        """ Checks if the wm channel is assigned to the DAC port, equivalent to
        that wm channel being locked. 0 means no channel assigned which is
        equivalent to unlocked."""
        port_c = ctypes.c_long(dacPort)
        wmChannel = ctypes.c_long()
        yield self.wmdll.GetPIDSetting(self.DeviationChannel, port_c,
                                       ctypes.pointer(wmChannel), self.d)

        returnChannel = wmChannel.value
        if returnChannel == waveMeterChannel:
            returnValue(1)
        elif returnChannel == 0:
            returnValue(0)

    @setting(31, "get total channels", returns='w')
    def getChannelCount(self, c):
        count = yield self.wmdll.GetChannelsCount(ctypes.c_long(0))
        returnValue(count)

    @setting(32, "get pid p", dacPort='w', returns='v')
    def get_pid_p(self, c, dacPort):
        """Gets the P PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        P = ctypes.c_double()
        yield self.wmdll.GetPIDSetting(self.PID_P, port_c, self.l,
                                       ctypes.pointer(P))

        returnValue(P.value)

    @setting(33, "get pid i", dacPort='w', returns='v')
    def get_pid_i(self, c, dacPort):
        """Gets the I PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        I = ctypes.c_double()
        yield self.wmdll.GetPIDSetting(self.PID_I, port_c, self.l,
                                       ctypes.pointer(I))

        returnValue(I.value)

    @setting(34, "get pid d", dacPort='w', returns='v')
    def get_pid_d(self, c, dacPort):
        """Gets the D PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        D = ctypes.c_double()
        yield self.wmdll.GetPIDSetting(self.PID_D, port_c, self.l,
                                       ctypes.pointer(D))

        returnValue(D.value)

    @setting(35, "get pid dt", dacPort='w', returns='v')
    def get_pid_dt(self, c, dacPort):
        """Gets the dt PID settings for a given DAC port."""
        port_c = ctypes.c_long(dacPort)
        dt = ctypes.c_double()
        yield self.wmdll.GetPIDSetting(self.PID_dt, port_c, self.l,
                                       ctypes.pointer(dt))

        returnValue(dt.value)

    @setting(122, "get const dt", dacPort='w', returns='i')
    def get_const_dt(self, c, dacPort):
        """Gets the dt PID settings for a given DAC port. This makes each dt in
        the integration constant as opposed to oscillating values based on the
        system time, which changes when changing wm settings."""
        port_c = ctypes.c_long(dacPort)
        dt = ctypes.c_long()
        yield self.wmdll.GetPIDSetting(self.PIDConstdt, port_c,
                                       ctypes.pointer(dt), self.d)

        returnValue(dt.value)

    @setting(55, "get pid sensitivity", dacPort='w', returns='*v')
    def get_pid_sensitivity(self, c, dacPort):
        """Gets the PID sensitivity for a given DAC port
        [sensitivity factor, sensitivity power]."""
        port_c = ctypes.c_long(dacPort)
        sFactor = ctypes.c_double()
        sExponent = ctypes.c_long()
        yield self.wmdll.GetPIDSetting(self.DeviationSensitivityDimension,
                                       port_c, ctypes.pointer(sExponent),
                                       self.d)

        yield self.wmdll.GetPIDSetting(self.DeviationSensitivityFactor, port_c,
                                       self.l, ctypes.pointer(sFactor))

        returnValue([sFactor.value, sExponent.value])

    @setting(36, "get pid polarity", dacPort='w', returns='i')
    def get_pid_polarity(self, c, dacPort):
        """Gets the polarity for a given DAC port. Allowed values are +/- 1."""
        port_c = ctypes.c_long(dacPort)
        polarity = ctypes.c_long()
        yield self.wmdll.GetPIDSetting(self.DeviationPolarity, port_c,
                                       ctypes.pointer(polarity), self.d)

        returnValue(polarity.value)

    def measureChan(self):
        #TODO: Improve this with a looping call
        reactor.callLater(0.1, self.measureChan)
        count = self.wmdll.GetChannelsCount(ctypes.c_long(0))
        for chan in range(count):
            if self.getSwitcherState(self, chan + 1):
                self.getFrequency(self, chan + 1)
                self.getOutputVoltage(self, chan + 1)
                self.getAmp(self, chan + 1)
#                if self.getSingleLockState(self, chan + 1):
#                    value = self.calcPID(chan)
#                    print value
#                    self.setDACVoltage(chan + 1, value)


if __name__ == "__main__":
    from labrad import util
    util.runServer(MultiplexerServer())
