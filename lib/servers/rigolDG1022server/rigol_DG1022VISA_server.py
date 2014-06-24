

"""
### BEGIN NODE INFO
[info]
name = Rigol DG1022
version = 1.1
description = 

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.server import LabradServer, setting
import visa
from twisted.internet.defer import inlineCallbacks, returnValue
from labrad.units import WithUnit
from labrad import types as T
from twisted.internet.interfaces.IReactorTime import callLater




class RigolDG1022( LabradServer ):

    """
    Server for communication with RigolDG1022
    """
    name = 'Rigol DG1022 Server'
    address = 'USB0::0x09C4::0x0400::DG1D150900594'
    serNode = 'coach_k'
    timeout = WithUnit(1.0, 's')

    lookup = {'sine':'SIN', 'square':'SQU', 'ramp':'RAMP', 'pulse':'PULS', 'noise':'NOIS'}

    @inlineCallbacks
    def initServer( self ):
        self.device = yield visa.instrument(self.address)

    @setting( 0, "Query Device", returns = 's')
    def query (self, c):
        yield self.device.write("*IDN?")
        ID = yield callLater(0.1, self.rigolRead)
        returnValue(ID)

    @setting(1, "Set Output", output = 'b')
    def setOutput(self, c, output):
        if output:
            yield self.device.write("OUTP ON")
        else:
            yield self.device.write("OUTP OFF")

    @setting(2, "Apply Wave form", channel = 'i: channel', form = 's: sine, square, ramp, pulse, noise, DC', frequency = 'v: Hz',
             amplitude = 'v: Vpp', offset = 'v: VDC')
    
    def applyWaveForm(self, c, channel, form, frequency, amplitude, offset):
        if channel == 1:
            chan = ''
        else: chan = ':CH2'
        output = "APPL:" + self.lookup[form] + chan + ' ' + str(int(frequency)) + ',' + str(amplitude) + ',' + str(offset)
        yield self.device.write(output)
        
    def rigolRead(self, c):
        value = yield self.device.read
        returnValue(value)
        
        


if __name__ == '__main__':
    from labrad import util
    util.runServer(RigolDG1022())
