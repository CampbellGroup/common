
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

    def output_on(self):
        self.query('OUTP ON')
        
    def output_off(self):
        self.query('OUTP OFF')
        

class RigolDG1022Server(GPIBManagedServer):
    name = 'Rigol DG1022'
    deviceName = 'RIGOL TECHNOLOGIES,DG1022A'
    deviceWrapper = RigolDG1022Wrapper

    def initContext(self, c):
         c['dict'] ={}
         
    @setting(10, 'Output On')   
    def OutputOn(self, c):
        dev = self.selectedDevice(c)
        dev.output_on()

    @setting(11, 'Output Off')   
    def OutputOff(self, c):
        dev = self.selectedDevice(c)
        dev.output_off()
        
        
if __name__=='__main__':
    from labrad import util
    util.runServer(RigolDG1022Server())
            
            
