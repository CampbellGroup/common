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
        self.lookup = {'sine':'SIN', 'square':'SQU', 'ramp':'RAMP', 'pulse':'PULS', 'noise':'NOIS', 'DC':'DC'}
    
    @inlineCallbacks
    def setOutput(self, output, channel = None):
        '''
        Turns on or off the rigol output of specified channel
        '''
        print output, channel
        if channel == 2:
            channel = ':CH2'
        else: channel = ''
        
        if output :
            yield self.write("OUTP" + channel + " ON")
        else:
            yield self.write("OUTP" + channel + " OFF")
            
    @inlineCallbacks
    def applyWaveForm(self, channel, form, frequency, amplitude, offset):
        '''
        Applys waveform from self.lookup dictionary with given parameters
        '''
        if channel == 2:
            chan = ':CH2'
        else: chan = ''
        
        output = "APPL:" + self.lookup[form] + chan + ' ' + str(int(frequency['Hz'])) + ',' + str(amplitude['V']) + ',' + str(offset['V'])
        print output
        yield self.write(output)

class RigolServer(GPIBManagedServer):
    name = 'Rigol DG1022A Server' # Server name
    deviceName = 'RIGOL TECHNOLOGIES DG1022A' # Model string returned from *IDN?
    deviceWrapper = RigolWrapper

    @setting(10, 'Set Output', channel = 'i', output = 'b')
    def setDeviceOutput(self, c, output, channel = None): # uses passed context "c" to address specific device 
        dev = self.selectedDevice(c)
        yield dev.setOutput(output, channel)
    
    @setting(69, 'Apply Waveform', channel = 'i', form = 's', frequency = ['v[Hz]'], amplitude = ['v[V]'], offset = ['v[V]']  )
    def applyDeviceWaveform(self, c, channel, form, frequency, amplitude, offset):
        dev = self.selectedDevice(c)
        yield dev.applyWaveForm(channel, form, frequency, amplitude, offset)


__server__ = RigolServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
