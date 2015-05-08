from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet.threads import deferToThread
from ctypes import *
from labrad.units import WithUnit
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

class MultiplexerServer(LabradServer):
    """
    Multiplexer Server for Wavelength Meter
    """
    name = 'Multiplexerserver'

    #Set up signals to be sent to listeners
    measuredchanged = Signal(CHANSIGNAL, 'signal: selected channels changed', '(ib)')
    freqchanged = Signal(FREQSIGNAL, 'signal: frequency changed', '(iv)')
    updateexp = Signal(UPDATEEXP, 'signal: update exp', '(ii)')
    lockchanged = Signal(LOCKSIGNAL, 'signal: lock changed', 'b')
    outputchanged = Signal(OUTPUTCHANGED, 'signal: output changed', 'b')
    pidvoltagechanged = Signal(PIDVOLTAGE, 'signal: PIDvoltage changed', '(iv)')
    
    def initServer(self):

        #load wavemeter dll file for use of API functions self.d and self.l are dummy c_types for unused wavemeter functions
        
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
        
        self.listeners = set()output

        #####Main program functions 
        
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)
    
    def expireContext(self, c):
        self.listeners.remove(c.ID)
    
    def getOtherListeners(self,c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @setting(1, "Check WLM Running")
    def instance(self,c):
        instance = self.wmdll.Instantiate
        instance.restype = c_long
        RFC = c_long(-1)    
        #RFC, reason for call, used to check if wavemeter is running (in wavemeter .h library
        status = yield instance(RFC,self.l,self.l,self.l)
        returnValue(status)
       
#####Set Functions
         
    @setting(10, "Set Exposure Time", chan = 'i', ms = 'i')
    def setExposureTime(self,c,chan,ms):

        notified = self.getOtherListeners(c)
        ms_c = c_long(ms)
        chan_c = c_long(chan)
        yield self.wmdll.SetExposureNum(chan_c, 1,  ms_c)
        self.updateexp((chan,ms), notified)

        
    @setting(11, "Set Lock State", state = 'b')
    def setLockState(self,c,state):
        notified = self.getOtherListeners(c)
        state_c = c_bool(state)
        yield self.wmdll.SetDeviationMode(state_c) 
        self.lockchanged(state, notified)      
        
    @setting(12, "Set Switcher Mode", mode = 'b')
    def setSwitcherMode(self, c, mode):
        mode_c = c_long(mode)
        yield self.wmdll.SetSwitcherMode(mode_c)      
        
    @setting(13, "Set Switcher Signal State", chan = 'i', state = 'b')
    def setSwitcherState(self, c, chan, state):
        notified = self.getOtherListeners(c)
        chan_c = c_long(chan)        
        state_c = c_long(state)
        yield self.wmdll.SetSwitcherSignalStates(chan_c, state_c, c_long(1))       
        self.measuredchanged((chan,state), notified)

    @setting(14, "Set PID Course", chan = 'i', course = 'v')
    def setPIDCourse(self, c, chan, course):
        chan_c = c_long(chan)
        course_c = c_char_p('=' + str(course))
        yield self.wmdll.SetPIDCourseNum(chan_c, course_c)

    @setting(15, "Set DAC Voltage", chan = 'i', value = 'v')
    def setDACVoltage(self, c, chan, value):
        chan_c = c_long(chan)
        #convert Volts to mV
        value = value*1000
        value_c = c_double(value)
        yield self.wmdll.SetDeviationSignalNum(chan_c, value_c)

    @setting(16, "Set WLM Output", output = 'b')
    def setWLMOutput(self, c, output):
        '''Start or stops wavemeter
        '''
        notified = self.getOtherListeners(c)
        if output == True:
            yield self.wmdll.Operation(2)
        else:
            yield self.wmdll.Operation(0)
        self.outputchanged(output, notified)
        
###Get Functions      
output
    @setting(20, "Get Amplitude", chan = 'i', returns = 'v')
    def getAmp(self, c, chan): 
        chan_c = c_long(chan)        
        amp = yield self.wmdll.GetAmplitudeNum(chan_c, c_long(2), self.l) 
        returnValue(amp)

    @setting(21, "Get Exposure", chan = 'i', returns = 'i')
    def getExp(self, c, chan): 
        chan_c = c_long(chan)
        exp = yield self.wmdll.GetExposureNum(chan_c ,1,self.l) 
        returnValue(exp)

    @setting(22,"Get Frequency", chan = 'i', returns = 'v')
    def getFrequency(self, c, chan):
        chan_c = c_long(chan)
        freq = yield self.wmdll.GetFrequencyNum(chan_c,self.d)
        self.freqchanged((chan,freq))
        returnValue(freq)
        
    @setting(23, "Get Lock State", returns = 'b')
    def getLockState(self, c):
        state = yield self.wmdll.GetDeviationMode(0)
        returnValue(state)

    @setting(24, "Get Switcher Mode", returns = 'b')
    def getSwitcherMode(self, c):
        state = yield self.wmdll.GetSwitcherMode(0)
        returnValue(bool(state))
        
    @setting(25,"Get Output Voltage", chan = 'i', returns = 'v')
    def getOutputVoltage(self, c, chan):
        chan_c = c_long(chan)
        volts = yield self.wmdll.GetDeviationSignalNum(chan_c,self.d)
        self.pidvoltagechanged((chan,volts))
        returnValue(volts)  
        

    
    @setting(26, "Get Switcher Signal State", chan = 'i', returns = 'b')
    def getSwitcherState(self, c, chan):
        chan_c = c_long(chan)
        use_c = c_long(0)
        show_c = c_long(0)
        yield self.wmdll.GetSwitcherSignalStates(chan_c, pointer(use_c), pointer(show_c))
        use = bool(use_c)
        returnValue(use)
        
    @setting(27, "Get PID Course", chan = 'i', returns = 's')
    def getPIDCourse(self, c, chan):
        chan_c = c_long(chan)
        course_c = create_string_buffer(1024)
        yield self.wmdll.GetPIDCourseNum(chan_c, pointer(course_c))
        value = str(course_c.value)
        returnValue(value)

    @setting(28, "Get WLM Output", returns = 'b')
    def getWLMOutput(self, c):
        value = yield self.wmdll.GetOperationState(c_short(0))
        if value == 2:
            value = True
        else:
            value = False
        returnValue(value)

            
    def measureChan(self):
        #TODO: Improve this with a looping call
        reactor.callLater(0.1, self.measureChan)
        for chan in range(8):
            if self.getSwitcherState(self, chan + 1):
                self.getFrequency(self, chan + 1) 
                self.getOutputVoltage(self, chan + 1)    
        
if __name__ == "__main__":
    from labrad import util
    util.runServer(MultiplexerServer())
    
    
