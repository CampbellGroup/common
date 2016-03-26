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

    @setting(1, 'toggle laser', value = 'b')
    def toggleLaser(self, c, value):
        if value:
            yield self.ser.write_line('ON')
        else:
            yield self.ser.write_line('OFF')
            
    @setting(2, 'toggle shutter', value = 'b')
    def toggleShutter(self, c, value):
        if value:
            yield self.ser.write_line('SHT:1')
        else:
            yield self.ser.write_line('SHT:0')
            
    @setting(3, 'set power', value = 'v[W]')
    def setPower(self, c, value):
        value = str(value['W'])
        yield self.ser.write_line('P:' + value)
        
    @setting(4, 'read power', returns = 'v[W]')
    def readPower(self,c):
        yield None
        returnValue(self.power)
        
    @setting(5, 'set current', value = 'v[A]')
    def setCurrent(self, c, value):
        value = str(value['A'])
        yield self.ser.write_line('C1:' + value)
        
    @setting(6, 'read current', returns = 'v[A]')
    def readCurrent(self,c):
        yield None
        returnValue(self.current)
        
    @setting(7, 'diode status', returns = 'b')
    def diodeStatus(self,c):
        yield self.ser.write_line('?D')
        value = yield self.ser.read_line()
        value = bool(float(value))
        returnValue(value)
        
    @setting(8, 'system status', returns = 's')
    def systemStatus(self,c):
        yield self.ser.write_line('?F')
        value = self.ser.read_line()
        returnValue(value)
        
    @setting(9, 'get power setpoint', returns = 'v[W]')
    def getPowerSetpoint(self, c):
        yield self.ser.write_line('?PSET')
        value = yield self.ser.read_line()
        value = U(float(value), 'W')
        returnValue(value)
        
    @setting(15, 'get current setpoint', returns = 'v[A]')
    def getCurrentSetpoint(self, c):
        yield self.ser.write_line('?CS1')
        value = yield self.ser.read_line()
        if value:
            value = U(float(value), 'A')
        else:
            value = U(0.0, 'A')
        returnValue(value)
        
    @setting(10, 'get shutter status', returns = 'b')
    def getShutterStatus(self, c):
        yield self.ser.write_line('?SHT')
        value = yield self.ser.read_line()
        value = bool(float(value))
        returnValue(value)
    
    @setting(11, 'set control mode', mode = 's')
    def setControlMode(self, c, mode):
        if mode == 'current':
            yield self.ser.write_line('M:0')
        elif mode == 'power':
            yield self.ser.write_line('M:1')            
        else:
            yield None
            
    @setting(12, 'get control mode', returns = 's')
    def getControlMode(self, c):
        yield self.ser.write_line('?M')
        value = yield self.ser.read_line()
        if value == '0':
            value = 'current'
        elif value == '1':
            value = 'power'
        else:
            value = None
        returnValue(value)
        
    @setting(13, 'read temperature', returns = 'v[degC]')
    def readTemperature(self,c):
        yield None
        returnValue(self.temperature)
        
    @setting(14, 'get diode current limit', returns = 'v[A]')
    def getCurrentLimit(self, c):
        yield self.ser.write_line('?DCL')
        value = yield self.ser.read_line()
        value = float(value)
        value = U(value, 'A')
        returnValue(value)

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
        yield self.ser.write_line('?T')
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
        self.currentchanged(self.current)
        self.powerchanged(self.power) 
        self.temperaturechanged(self.temperature)
    
if __name__ == "__main__":
    from labrad import util
    util.runServer(eVPump())