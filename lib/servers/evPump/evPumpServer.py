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
UPDATESTAT = 356575

from common.lib.servers.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError
from twisted.internet import reactor
from labrad.server import Signal
from labrad import types as T
from twisted.internet.defer import returnValue
from labrad.support import getNodeName
from labrad.units import WithUnit as U

SERVERNAME = 'eVPump'
TIMEOUT = 1.0
BAUDRATE = 115200

class eVPump(SerialDeviceServer):
    name = SERVERNAME
    regKey = 'eVPump'
    port = None
    serNode = getNodeName()
    timeout = T.Value(TIMEOUT,'s')
    temperature = None
    power = None
    current = None
    status = None

    currentchanged = Signal(UPDATECURR, 'signal: current changed', 'v')
    powerchanged = Signal(UPDATEPOW, 'signal: power changed', 'v')
    temperaturechanged = Signal(UPDATETMP, 'signal: temp changed', 'v')
    statuschanged = Signal(UPDATESTAT, 'signal: stat changed', 's')
    
    @inlineCallbacks
    def initServer( self ):
        if not self.regKey or not self.serNode: 
            raise SerialDeviceError( 'Must define regKey and serNode attributes' )
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
        self.measure_pump()

    @setting(1, 'toggle laser', value = 'b')
    def toggle_laser(self, c, value):
        if value:
            yield self.ser.write_line('ON')
        else:
            yield self.ser.write_line('OFF')
            
    @setting(2, 'toggle shutter', value = 'b')
    def toggle_shutter(self, c, value):
        if value:
            yield self.ser.write_line('SHT:1')
        else:
            yield self.ser.write_line('SHT:0')
            
    @setting(3, 'set power', value = 'v[W]')
    def set_power(self, c, value):
        value = str(value['W'])
        yield self.ser.write_line('P:' + value)
        
    @setting(4, 'read power', returns = 'v[W]')
    def read_power(self,c):
        yield None
        returnValue(self.power)
        
    @setting(5, 'set current', value = 'v[A]')
    def set_current(self, c, value):
        value = str(value['A'])
        yield self.ser.write_line('C1:' + value)
        
    @setting(6, 'read current', returns = 'v[A]')
    def read_current(self,c):
        yield None
        returnValue(self.current)

    @setting(7, 'diode status', returns = 'b')
    def diode_status(self,c):
        yield self.ser.write_line('?D')
        value = yield self.ser.read_line()
        value = bool(float(value))
        returnValue(value)
        
    @setting(8, 'system status', returns = 's')
    def system_status(self,c):
        yield None
        returnValue(self.status)
        
    @setting(9, 'get power setpoint', returns = 'v[W]')
    def get_power_setpoint(self, c):
        yield self.ser.write_line('?PSET')
        value = yield self.ser.read_line()
        value = U(float(value), 'W')
        returnValue(value)
        
    @setting(15, 'get current setpoint', returns = 'v[A]')
    def get_current_setpoint(self, c):
        yield self.ser.write_line('?CS1')
        value = yield self.ser.read_line()
        if value:
            value = U(float(value), 'A')
        else:
            value = U(0.0, 'A')
        returnValue(value)
        
    @setting(10, 'get shutter status', returns = 'b')
    def get_shutter_status(self, c):
        yield self.ser.write_line('?SHT')
        value = yield self.ser.read_line()
        value = bool(float(value))
        returnValue(value)
    
    @setting(11, 'set control mode', mode = 's')
    def set_control_mode(self, c, mode):
        if mode == 'current':
            yield self.ser.write_line('M:0')
        elif mode == 'power':
            yield self.ser.write_line('M:1')            
        else:
            yield None
            
    @setting(12, 'get control mode', returns = 's')
    def get_control_mode(self, c):
        yield self.ser.write_line('?M')
        value = yield self.ser.read_line()
        if value == '0':
            value = 'current'
        elif value == '1':
            value = 'power'
        else:
            value = None
        returnValue(value)
        
    @setting(13, 'get temperature', returns = 'v[degC]')
    def get_temperature(self,c):
        yield None
        returnValue(self.temperature)
        
    @setting(14, 'get diode current limit', returns = 'v[A]')
    def get_current_limit(self, c):
        yield self.ser.write_line('?DCL')
        value = yield self.ser.read_line()
        value = float(value)
        value = U(value, 'A')
        returnValue(value)

    @inlineCallbacks
    def _read_power(self):
        yield self.ser.write_line('?P')
        power = yield self.ser.read_line()
        try:    
            self.power = U(float(power),'W')
        except:
            self.power = None
            
    @inlineCallbacks
    def _read_current(self):
        yield self.ser.write_line('?C')
        current = yield self.ser.read_line()
        try:
            self.current = U(float(current),'A')    
        except:
            self.current = None
            
    @inlineCallbacks
    def _read_temperature(self):
        yield self.ser.write_line('?T')
        temp = yield self.ser.read_line()
        try:
            self.temperature = U(float(temp),'degC')
        except:
            self.temperature = None
            
    @inlineCallbacks
    def _read_status(self):
        yield self.ser.write_line('?F')
        self.status = yield self.ser.read_line()

    @inlineCallbacks
    def measure_pump(self):
        reactor.callLater(.1, self.measure_pump)
        yield self._read_power()
        yield self._read_current()
        yield self._read_temperature()
        yield self._read_status()
        self.currentchanged(self.current)
        self.powerchanged(self.power) 
        self.temperaturechanged(self.temperature)
        self.statuschanged(self.status)
    
if __name__ == "__main__":
    from labrad import util
    util.runServer(eVPump())