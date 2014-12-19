from labrad.server import LabradServer, setting
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet import reactor
from labrad import types as T
from twisted.internet.defer import returnValue
from Labjackapi import u3

"""
### BEGIN NODE INFO
[info]
name = LabJack
version = 1.0
description = 
instancename = LabJack

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""


'''
Created on Dec 19, 2014

@author: anthonyransford

'''

class LabJackserver(LabradServer):
    """
    LabJack DAC and ADC server
    """
    name = 'LabJackserver'
    
    def initServer(self):
        try:
            self.device = u3.U3()
        except:
            print "ERROR: Could not connect to LabJack"
        
    @setting(11, 'Set DAC', chan = 'i',  volts = 'v')
    def dacOutput(self, c, chan, volts):
        dac_value = self.device.voltageToDACBits(volts, dacNumber = chan, is16Bits = True)
        self.device.getFeedback(u3.DAC16(chan, dac_value))
        
    @setting(12, 'Get ADC Voltage', chan = 'i', returns = 'v')
    def Ain(self, c, chan):
        ainbits, = self.device.getFeedback(u3.AIN(chan))
        ainValue = yield self.device.binaryToCalibratedAnalogVoltage(ainbits, isLowVoltage = False, channelNumber = chan)
        returnValue(ainValue)
        
if __name__ == "__main__":
    from labrad import util
    util.runServer( LabJackserver() )
