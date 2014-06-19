"""
### BEGIN NODE INFO
[info]
name = ArduinoTTL
version = 1.0
description = 
instancename = ArduinoTTL

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""


'''
Created on May 17, 2014

@author: anthonyransford
'''

from serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.types import Error
from twisted.internet import reactor
from labrad.server import Signal
from labrad import types as T
from twisted.internet.task import LoopingCall
from twisted.internet.defer import returnValue

SERVERNAME = 'ArduinoTTL'
TIMEOUT = 1.0
BAUDRATE = 57600

class ArduinoTTL( SerialDeviceServer ):
    name = SERVERNAME
    regKey = 'arduinoTTL'
    port = None
    serNode = 'qsimexpcontrol'
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
    
    @setting(1, 'TTL Output', chan = 'i', state = 'b')
    def ttlOutput(self, c, chan, state):
        output = (chan << 2) | (state + 2)
        yield self.ser.write(chr(output))
        
    @setting(2, 'TTL Read', chan = 'i', returns = 'b')
    def ttlInput(self, c, chan):
        output = (chan << 2) 
        yield self.ser.flushinput()
        yield self.ser.write(chr(output))
        status  = yield self.ser.read()
        status = status.encode('hex')

        try: 
            status = int(status)
            if status == 1:
                print 'status is 1'
                returnValue(True)
            elif status == 0:
                print 'status is 0'
                returnValue(False)
            else: print status, 'invalid TTL', returnValue(False)
        except ValueError: 
            print  status, 'Error Reading'
            returnValue(False)
                
    
if __name__ == "__main__":
    from labrad import util
    util.runServer( ArduinoTTL() )
