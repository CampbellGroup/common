# Copyright (C) 2011 Anthony Ransford
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

"""
### BEGIN NODE INFO
[info]
name = Rigol DG1022 Server
version = 1.3
description = 

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.server import setting
from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue

class RigolWrapper(GPIBDeviceWrapper):
    
    def initialize(self):
        '''
        Provides a lookup table for waveform to GPIB lingo
        '''
        self.lookup = {'sine':'SIN', 'square':'SQU', 'ramp':'RAMP', 'pulse':'PULS', 'noise':'NOIS', 'DC' : 'DC', 'USER':'USER'}
        
    def parsechannel(self, channel = None):
        if channel == 2:
            channel = ':CH2'
        else: channel = ''
        return channel
    
    @inlineCallbacks
    def Output(self, channel, output = None):
        '''
        Turns on or off the rigol output of specified channel
        '''
        channel = self.parsechannel(channel)

        if output == True:
            yield self.write("OUTP" + channel + " ON")
        elif output == False:
            yield self.write("OUTP" + channel + " OFF")
        else:
            yield self.write("OUTP" + channel + "?")
            state = yield self.read()
            returnValue(state)
            
            
    @inlineCallbacks
    def applyWaveForm(self, function, frequency, amplitude, offset, channel = None):
        '''
        Applys waveform from self.lookup dictionary with given parameters
        '''
        channel = self.parsechannel(channel)
        output = "APPL:" + self.lookup[function] + channel + ' ' + str(int(frequency['Hz'])) + ',' + str(amplitude['V']) + ',' + str(offset['V'])
        yield self.write(output)
     
    @inlineCallbacks    
    def WaveFunction(self, channel, function = None):
        '''
        Changes wave form
        '''
        channel = self.parsechannel(channel)
        if function == None:
            output = "FUNC" + channel + "?"
            yield self.write(output)
            func = yield self.read()
            returnValue(func)
        else:
            output = "FUNC" + channel + " " + self.lookup[function]
            yield self.write(output)

        
    @inlineCallbacks
    def Frequency(self, channel, frequency = None):
        '''
        Sets frequency
        '''
        channel = self.parsechannel(channel)
        if frequency == None:
            output = "FREQ" + channel +"?"
            yield self.write(output)
            freq = yield  self.read()
            returnValue(freq)
        else:
            output = "FREQ " + channel + str(frequency['Hz'])
            yield self.write(output)

    @inlineCallbacks
    def setDC(self, channel, voltage = None):
        '''
        sets DC output value
        '''
        channel = self.parsechannel(channel)
        if voltage == None:
            output = "VOLT:OFFS" + channel
            yield self.write(output)
            volts = self.read()
            returnValue(volts)
        else:
            output = 'APPL:DC' + channel + ' DEF,DEF,' + str(voltage['V'])
            yield self.write(output)
            
    @inlineCallbacks
    def Offset(self, channel, offset = None):
        channel = self.parsechannel(channel)
        if offset == None:
            output = "VOLT:OFFS" + channel
            yield self.write(output)
            offset = self.read()
            returnValue(offset)
        else:
            output = "VOLT:OFFS" + channel + " " + str(offset['V'])
            yield self.write(output) 
        
        
    @inlineCallbacks
    def Amplitude(self, channel, voltage = None):
        '''
        sets amp
        '''
        channel = self.parsechannel(channel)
        if voltage == None:
            output = "VOLT" + channel + "?"
            yield self.write(output)
            volts = yield self.read()
            returnValue(volts)
        else:
            output = "VOLT" + channel + " " + str(voltage['V'])
            yield self.write(output)

    @inlineCallbacks
    def AMSource(self, source):
        '''
        Select internal or external modulation source, the default is INT
        '''
        output = "AM:SOUR " + source
        yield self.write(output)
        
    @inlineCallbacks
    def AMFunction(self, function):
        '''
        Select the internal modulating wave of AM
        In internal modulation mode, the modulating wave could be sine,
        square, ramp, negative ramp, triangle, noise or arbitrary wave, the
        default is sine.
        '''
        output = "AM:INT:FUNC " + self.lookup[function]
        yield self.write(output)
        
    @inlineCallbacks
    def AMFrequency(self, frequency):
        '''
        Set the frequency of AM internal modulation in Hz
        Frequency range: 2mHz to 20kHz
        '''
        output = "AM:INT:FREQ " + str(frequency['Hz'])
        yield self.write(output)
        
    @inlineCallbacks
    def AMDepth(self, depth):
        '''
        Set the depth of AM internal modulation in percent
        Depth range: 0% to 120%
        '''
        output = "AM:DEPT " + str(depth)
        yield self.write(output)
        
    @inlineCallbacks
    def AMState(self, state):
        '''
        Disable or enable AM function
        '''
        if state:
            state = 'ON'
        else:
            state = 'OFF'
            
        output = "AM:STAT " + state
        yield self.write(output)

    @inlineCallbacks
    def FMSource(self, source):
        '''
        Select internal or external modulation source, the default is INT
        '''
        output = "FM:SOUR " + source
        yield self.write(output)
        
    @inlineCallbacks
    def FMFunction(self, function):
        '''
        In internal modulation mode, the modulating wave could be sine,
        square, ramp, negative ramp, triangle, noise or arbitrary wave, the
        default is sine
        '''
        output = "FM:INT:FUNC " + self.lookup[function]
        yield self.write(output)
        
    @inlineCallbacks
    def FMFrequency(self, frequency):
        '''
        Set the frequency of FM internal modulation in Hz
        Frequency range: 2mHz to 20kHz
        '''
        output = "FM:INT:FREQ " + str(frequency['Hz'])
        yield self.write(output)
        
    @inlineCallbacks
    def FMDeviation(self, deviation):
        '''
        Set the frequency deviation of FM in Hz.
        '''
        output = "FM:DEV " + str(deviation)
        yield self.write(output)
        
    @inlineCallbacks
    def FMState(self, state):
        '''
        Disable or enable FM function
        '''
        if state:
            state = 'ON'
        else:
            state = 'OFF'
            
        output = "FM:STAT " + state
        yield self.write(output)
        

class RigolServer(GPIBManagedServer):
    name = 'Rigol DG1022 Server' # Server name
    deviceName = 'RIGOL TECHNOLOGIES DG1022' # Model string returned from *IDN?
    deviceWrapper = RigolWrapper

    @setting(10, 'Output', channel = 'i', output = 'b')
    def deviceOutput(self, c, channel, output = None): # uses passed context "c" to address specific device 
        dev = self.selectedDevice(c)
        yield dev.Output(channel, output)
    
    @setting(69, 'Apply Waveform', channel = 'i', function = 's', frequency = ['v[Hz]'], amplitude = ['v[V]'], offset = ['v[V]']  )
    def applyDeviceWaveform(self, c, function, frequency, amplitude, offset, channel = None):
        dev = self.selectedDevice(c)
        yield dev.applyWaveForm(function, frequency, amplitude, offset, channel)
        
    @setting(707, 'Wave Function', channel = 'i', function = 's')
    def deviceFunction(self, c, channel, function = None):
        dev = self.selectedDevice(c)
        func = yield dev.WaveFunction(channel, function)
        returnValue(func)

    @setting(131, 'Amplitude', channel = 'i', value = 'v[V]')
    def Amplitude(self, c, channel, value = None):
        dev = self.selectedDevice(c)
        volts = yield dev.Amplitude(channel, value)
        returnValue(volts)

    @setting(92, 'Frequency', channel = 'i', value = 'v[Hz]')
    def Frequency(self, c, channel, value = None):
        dev = self.selectedDevice(c)
        freq = yield dev.Frequency(channel, value)
        returnValue(freq)

    @setting(9, 'Apply DC', channel = 'i', value = 'v[V]')
    def setDC(self, c, channel, value = None):
        dev = self.selectedDevice(c)
        volts = yield dev.setDC(channel, value)
        returnValue(volts)
        
    @setting(99, 'Offset', channel = 'i', value = 'v[V]')
    def Offset(self, c, channel, value = None):
        dev = self.selectedDevice(c)
        offset = yield dev.Offset(channel, value)
        returnValue(offset)
        
__server__ = RigolServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
