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
name = Rigol DG1022A Server
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
    def Output(self, output = None, channel = None):
        '''
        Turns on or off the rigol output of specified channel
        '''
        channel = self.parsechannel(channel)

        if output :
            yield self.write("OUTP" + channel + " ON")
        elif output == False:
            yield self.write("OUTP" + channel + " OFF")
        else:
            yield self.write("OUTP" + channel + "?")
            state = self.read()
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
    def WaveFunction(self, function = None, channel = None):
        '''
        Changes wave form
        '''
        channel = self.parsechannel(channel)
        if function == None:
            output = "FUNC" + channel + "?"
        else""
            output = "FUNC " + self.lookup[function] + channel
        yield self.write(output)
        
    @inlineCallbacks
    def Frequency(self, frequency = None, channel = None):
        '''
        Sets frequency
        '''
        channel = self.parsechannel(channel)
        if frequency == None:
            output = "FREQ" + channel +"?"
        else:
            output = "FREQ " + channel + str(int(frequency['Hz']))
        yield self.write(output)
        
    @inlineCallbacks
    def Voltage(self, voltage = None, channel = None):
        '''
        sets voltage
        '''
        channel = self.parsechannel(channel)
        if voltage == None:
            output = "VOLT" + channel + "?"
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
    name = 'Rigol DG1022A Server' # Server name
    deviceName = 'RIGOL TECHNOLOGIES DG1022A' # Model string returned from *IDN?
    deviceWrapper = RigolWrapper

    @setting(10, 'Output', channel = 'i', output = 'b')
    def deviceOutput(self, c, output = None, channel = None): # uses passed context "c" to address specific device 
        dev = self.selectedDevice(c)
        yield dev.Output(output, channel)
    
    @setting(69, 'Apply Waveform', channel = 'i', function = 's', frequency = ['v[Hz]'], amplitude = ['v[V]'], offset = ['v[V]']  )
    def applyDeviceWaveform(self, c, function, frequency, amplitude, offset, channel = None):
        dev = self.selectedDevice(c)
        yield dev.applyWaveForm(channel, function, frequency, amplitude, offset)
        
    @setting(707, 'Wave Function', channel = 'i', form = 's')
    def deviceFunction(self, c, function = None, channel = None):
        dev = self.selectedDevice(c)
        yield dev.setWaveFunction(function, channel)


__server__ = RigolServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
