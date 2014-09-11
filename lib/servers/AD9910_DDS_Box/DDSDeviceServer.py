# Copyright (C) 2010  Michael Lenander & Julian Kelly
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
### BEGIN NODE INFO
[info]
name = DDS Device Server
version = 1.0.0
description = DDSDeviceServer
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting, inlineCallbacks, returnValue
from labrad.units import WithUnit as W

class ArduinoDDSDevice(DeviceWrapper):
    
    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a Arduino DDS device."""
        print 'connecting to "%s" on port "%s"...' % (server.name, port),
        self.server = server
        self.ctx = server.context()
        self.port = port
        print self.port
        self.settings = {'Amplitude': W(-3, 'dbm'), 'Frequency': W(161, 'MHz')}
        p = self.packet()
        p.open(port)
        p.baudrate(9600)
#        yield self.server.open(port)
#        yield self.server.baudrate(9600)
        p.read() # clear out the read buffer
#        yield self.server.timeout(TIMEOUT)
        p.timeout(TIMEOUT)
        yield p.send()
        print 'done.'
        
    def packet(self):
        """Create a packet in our private context."""
        return self.server.packet(context=self.ctx)
    
    def shutdown(self):
        """Disconnect from the serial port when we shut down."""
        return self.packet().close().send()
    
    @inlineCallbacks
    def write(self, code):
        """Write a data value to arduino."""
#        yield self.server.write(code)
        yield self.packet().write_line(code).send()
        
    @inlineCallbacks
    def read(self):
        """Read data from the arduino"""
        ans = yield self.server.read(context = self.ctx)
        returnValue(ans)
        
    @inlineCallbacks
    def flushinput(self):
        """flush serial data"""
        yield self.server.flushinput(context = self.ctx)
        
    def setAmplitude(self, chan, amplitude, set = True):
        voltage = 10**((amplitude['dbm'] -10.0)/20)
        hexamp =  str(hex(int((voltage - 0.00022387211) * 16383/0.276376)))[2:]
        hexamp =  hexamp.rjust(4, '0')
        output = '/I' + str(chan) + 'A' + hexamp
        if set:
            self.settings['Amplitude'] = amplitude
        self.write(output)
        
    def setFrequency(self, chan, frequency):
        hexfreq = str(hex(int((frequency['Hz']) * 2147483647/(500e6))))[2:]
        hexfreq = hexfreq.rjust(8, '0')
        hexfreq = hexfreq.replace('L', '')
        self.settings['Frequency'] = frequency
        output = '/I' + str(chan) + 'F' + hexfreq
        self.write(output)
        
    def ddsOutput(self, chan, state):
        if state:
            amp = self.settings['Amplitude']
            self.setAmplitude(chan, amp)
        else:
            self.setAmplitude(chan, W(-63, 'dbm'), set = False)
            

class DDSDeviceServer(DeviceServer):
    name = 'DDSDeviceServer'
    deviceWrapper = ArduinoDDSDevice

    @inlineCallbacks
    def initServer(self):
        print 'loading config info...',
        yield self.loadConfigInfo()
        print 'done.'
        yield DeviceServer.initServer(self)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.client.registry
        p = reg.packet()
        p.cd(['', 'Ports'], True)
        p.get('ArduinoDDS', '*(ss)', key='links')
        ans = yield p.send()
        self.serialLinks = ans['links']

    @inlineCallbacks
    def findDevices(self):
        """Find available devices from list stored in the registry."""
        devs = []
        for name, port in self.serialLinks:
            if name not in self.client.servers:
                continue
            server = self.client[name]
            ports = yield server.list_serial_ports()
            if port not in ports:
                continue
            devName = '%s - %s' % (name, port)
            devs += [(devName, (server, port))]
        returnValue(devs)
        
    @setting(19, chan = 'i', amp = 'v[dbm]')
    def amplitude(self, c, chan, amp):
        dev = self.selectedDevice(c)
        dev.setAmplitude(chan, amp)
        
    @setting(20, chan = 'i', freq = 'v[MHz]')
    def frequency(self, c, chan, freq):
        dev = self.selectedDevice(c)
        dev.setFrequency(chan, freq)
        
    @setting(21, chan = 'i', state = 'b')
    def output(self, c, chan, state):
        dev = self.selectedDevice(c)
        dev.ddsOutput(chan, state)
        
TIMEOUT = W(1, 's') # serial read timeout

#####
# Create a server instance and run it

__server__ = DDSDeviceServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
