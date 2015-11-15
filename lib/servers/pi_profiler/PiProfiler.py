# -*- coding: utf-8 -*-
"""
### BEGIN NODE INFO
[info]
name = Pi Camera
version = 1.0
description = 
instancename = PiCamera

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
import numpy as _n
from labrad.server import LabradServer, setting
from twisted.internet.defer import returnValue


class PiCamera(LabradServer):
    """
    Raspberry Pi based camera server.
    
    This can take basic images, and later it should be able to get beam 
    profiles.
    """
    name = 'Pi Camera'

    @setting(1, 'faux_echo', string='s', returns='s')
    def fauxEcho(self, c, string):
        """
        """
        return string


        
if __name__ == "__main__":
    from labrad import util
    util.runServer(PiCamera())
    