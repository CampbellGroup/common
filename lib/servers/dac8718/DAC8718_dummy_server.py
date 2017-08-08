"""
### BEGIN NODE INFO
[info]
name = DAC8718 Dummy Server
version = 1.0
description =
instancename = DAC8718 Dummy Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""


'''
Created on July 16, 2015

@author: anthonyransford

'''

from labrad.server import LabradServer, setting
from labrad.types import Error
from twisted.internet import reactor
from labrad import types as T
from labrad.support import getNodeName

class ArduinoDAC(LabradServer):

    name = 'DAC8718 Server'

    @setting(1, chan='i', value='i')
    def DACOutput(self, c, chan, value):
        """
        Output voltage value (in bits from 0 to 2^16) on chan.

        Parameters
        ----------
        chan: int, DAC channel, valid from 0-15
        """

        print chan
        print value

if __name__ == "__main__":
    from labrad import util
    util.runServer(ArduinoDAC())
