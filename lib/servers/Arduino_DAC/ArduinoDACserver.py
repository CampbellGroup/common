"""
### BEGIN NODE INFO
[info]
name = ArduinoDAC
version = 1.0
description = 
instancename = ArduinoDAC

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""


'''
Created on June 16, 2015

@author: anthonyransford

'''

from common.lib.servers.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.types import Error
from twisted.internet import reactor
from labrad.server import Signal
from labrad import types as T
from twisted.internet.task import LoopingCall
from twisted.internet.defer import returnValue
from labrad.support import getNodeName
import time

SERVERNAME = 'ArduinoDAC'
TIMEOUT = 1.0
BAUDRATE = 57600

class ArduinoDAC( SerialDeviceServer ):
    name = SERVERNAME
    regKey = 'arduinoDAC'
    port = None
    serNode = getNodeName()
    timeout = T.Value(TIMEOUT,'s')
    
    
    @inlineCallbacks
    def initServer( self ):
        if not self.regKey or not self.serNode: raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        port = yield self.getPortFromReg( self.regKey )
        self.port = port
        try:
            serStr = yield self.findSerial( self.serNode )
            self.initSerial( serStr, port, baudrate = BAUDRATE )
        except SerialConnectionError, e:
            self.ser = None
            if e.code == 0:
                print 'Could not find serial server for node: %s' % self.serNode
                print 'Please start correct serial server'
            elif e.code == 1:
                print 'Error opening serial connection'
                print 'Check set up and restart serial server'
            else: raise
    
    @setting(1, chan = 'i', value = 'i')
    def DACOutput(self, c, chan, value):
        if value > 255:
            value = 255
        elif value < 0:
            value = 0
        yield self.ser.write(chr(chan))
        yield self.ser.write(chr(value))               
    
if __name__ == "__main__":
    from labrad import util
    util.runServer( ArduinoDAC() )
