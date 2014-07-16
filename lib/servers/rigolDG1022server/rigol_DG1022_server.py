# Copyright (C) 2014  Anthony Ransford
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
name = Rigol DG1022
version = 1.1
description = Controls Rigol signal generators

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

class RigolDG1022Wrapper(GPIBDeviceWrapper):

    def initialize(self):
        lookup = {'sine':'SIN', 'square':'SQU', 'ramp':'RAMP', 'pulse':'PULS', 'noise':'NOIS'}
    
    @inlineCallbacks    
    def setOutput(self, output = None, chan = None):
        if output == True:
            yield self.write("OUTP ON")
        elif output == False:
            yield self.write("OUTP OFF")
        elif output == None:
            yield None
        else:
            print "Invalid Input Setting"
        self.write("OUTP?")
        state = self.read()
        returnValue(state)
        
class RigolDG1022Server(GPIBManagedServer):
    name = 'Rigol DG1022'
    deviceName = 'RIGOL TECHNOLOGIES,DG1022A'
    deviceWrapper = RigolDG1022Wrapper
    
    @setting(1, 'Output', output = 'b', returns =  's')
    def output(self, c, output = None):
        dev = self.selectedDevice(c)
        state = dev.setOutput(output)
        returnValue(state)
        
if __name__=='__main__':
    from labrad import util
    util.runServer(RigolDG1022Server())
            
            