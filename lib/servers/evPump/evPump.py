"""
### BEGIN NODE INFO
[info]
name = eVPump
version = 1.0
description = 
instancename = eVPump
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

'''
Created on Mar 25, 2016

@author: Anthony Ransford
'''

UPDATECURR = 150327
UPDATEPOW = 114327
UPDATETMP = 153422

from common.lib.servers.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError, PortRegError
from labrad.types import Error
from twisted.internet import reactor
from labrad.server import Signal
from labrad import types as T
from twisted.internet.task import LoopingCall
from twisted.internet.defer import returnValue
from labrad.support import getNodeName
from labrad.units import WithUnit as U
from labrad.util import wakeupCall

SERVERNAME = 'eVPump'
TIMEOUT = 1.0
BAUDRATE = 115200

class eVPump( SerialDeviceServer ):
    name = SERVERNAME
    regKey = 'eVPump'
    port = None
    serNode = getNodeName()
    timeout = T.Value(TIMEOUT,'s')
    temperature = None
    power = None
    current = None

    currentchanged = Signal(UPDATECURR, 'signal: current changed', 'v')
    powerchanged = Signal(UPDATEPOW, 'signal: power changed', 'v')
    temperaturechanged = Signal(UPDATETMP, 'signal: temp changed', 'v')
    
    @inlineCallbacks
    def initServer( self ):
        if not self.regKey or not self.serNode: raise SerialDeviceError( 'Must define regKey and serNode attributes' )
        port = yield self.getPortFromReg( self.regKey )
        self.port = port
        print port
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
        self.measurePump()
        
    @inlineCallbacks
    def _readPower(self):
        yield self.ser.write_line('?P')
        power = yield self.ser.read_line()
        try:    
            self.power = U(float(power),'W')
        except:
            self.power = None
            
    @inlineCallbacks
    def _readCurrent(self):
        yield self.ser.write_line('?C')
        current = yield self.ser.read_line()
        try:
            self.current = U(float(current),'A')    
        except:
            self.current = None
            
    @inlineCallbacks
    def _readTemperature(self):
        yield self.ser.write_line('?HS')
        temp = yield self.ser.read_line()
        try:
            self.temperature = U(float(temp),'degC')
        except:
            self.temperature = None

    @inlineCallbacks
    def measurePump(self):
        reactor.callLater(.1, self.measurePump)
        yield self._readPower()
        yield self._readCurrent()
        yield self._readTemperature()
        print self.current, self.power, self.temperature
        self.currentchanged(self.current)
        self.powerchanged(self.power) 
        self.temperaturechanged(self.temperature)
    
if __name__ == "__main__":
    from labrad import util
    util.runServer(eVPump())