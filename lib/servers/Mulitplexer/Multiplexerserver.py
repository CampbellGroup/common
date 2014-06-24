from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet.threads import deferToThread
from ctypes import c_long, c_double, c_buffer, c_float, c_int, c_bool, c_char_p, windll, pointer
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

class MultiplexerServer(LabradServer):
    """
    Multiplexer Server for Wavelength Meter
    """
    name = 'Multiplexerserver'

    #Set up signals to be sent to listeners
    measuredchanged = Signal(CHANSIGNAL, 'signal: selected channels changed', '(ib)')
    freqchanged = Signal(FREQSIGNAL, 'signal: frequency changed', '(iv)')
    updateexp = Signal(UPDATEEXP, 'signal: update exp', '(ii)')
    
    def initServer(self):
        
        self.d = c_double(0)
        self.l = c_long(0)    
        self.b = c_bool(0)    
        self.wmdll = windll.LoadLibrary("C:\Windows\System32\wlmData.dll")
        #load wavemeter dll file for use of API functions self.d and self.l are dummy c_types for unused wavemeter functions
 
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
        
        self.measureChan()
        
        #allocates c_types for dll functions
        
        self.listeners = set()

    @setting(1, "Check WLM Running")
    def instance(self,c):
        instance = self.wmdll.Instantiate
        instance.restype = c_long
        RFC = c_long(-1)    
        #RFC, reason for call, used to check if wavemeter is running (in wavemeter .h library
        status = yield instance(RFC,self.l,self.l,self.l)
        returnValue(status)

        
        
#####Main program functions        spinExp.setValue(initvalue)

         
    @setting(10, "Set Exposure Time", chan = 'i', ms = 'i')
    def setExposureTime(self,c,chan,ms):

        ms_c = c_long(ms)
        chan_c = c_long(chan)
        yield self.wmdll.SetExposureNum(chan_c, 1,  ms_c)
        self.updateexp((chan,ms))

        
    @setting(11, "Set Lock State", state = 'b')
    def setLockState(self,c,state):
        state_c = c_bool(state)
        yield self.wmdll.SetDeviationMode(state_c)       
        
    @setting(12, "Set Switcher Mode", mode = 'b')
    def setSwitcherMode(self, c, mode):
        mode_c = c_long(mode)
        yield self.wmdll.SetSwitcherMode(mode_c)      
        
    @setting(13, "Set Switcher Signal State", chan = 'i', state = 'b')
    def setSwitcherState(self, c, chan, state):
        chan_c = c_long(chan)        
        state_c = c_long(state)
        yield self.wmdll.SetSwitcherSignalStates(chan_c, state_c, c_long(1))       
        self.measuredchanged((chan,state))

    @setting(14, "Set PID Course", chan = 'i', course = 'v')
    def setPIDCourse(self, c, chan, course):
        chan_c = c_long(chan)
        course_c = c_char_p('=' + str(course))
        yield self.wmdll.SetPIDCourseNum(chan_c, course_c)
        
        
#####Set Functions

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
        
    @setting(23, "Get Lock State")
    def getLockState(self):
        state = self.wmdll.GetDeviationMode(self.b)
        returnValue(state)
        
    @setting(24,"Get Output Voltage", chan = 'i', returns = 'v')
    def getOutputVoltage(self, c, chan):
        chan_c = c_long(chan)
        volts = yield self.wmdll.GetDeviationSignalNum(chan_c,self.d)
        returnValue(volts)  
        
    @setting(25, "Get Switcher Mode", returns = 'b')
    def getSwitcherMode(self, c):
        state = self.wmdll.GetSwitcherMode(self.l)
        returnValue(state)
    
    @setting(26, "Get Switcher Signal State", chan = 'i', returns = 'b')
    def getSwitcherState(self, c, chan):
        chan_c = c_long(chan)
        use_c = c_long(0)
        show_c = c_long(0)
        yield self.wmdll.GetSwitcherSignalStates(chan_c, pointer(use_c), pointer(show_c))
        use = bool(use_c)
        returnValue(use)
            
    def measureChan(self):
        #TODO: Improve this with a looping call
        reactor.callLater(0.1, self.measureChan)
        for chan in range(8):
            if self.getSwitcherState(self, chan + 1):
                self.getFrequency(self, chan + 1)     
        
if __name__ == "__main__":
    from labrad import util
    util.runServer(MultiplexerServer())
    
    
