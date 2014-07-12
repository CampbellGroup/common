# -*- coding: utf-8 -*-

"""
### BEGIN NODE INFO
[info]
name = Basic Server
version = 1.0
description = 
instancename = BasicServer

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


class BasicServer(LabradServer):
    """
    Basic Server
    """
    
    name = 'Basic Server'



    @setting(1, 'faux_echo', string='s', returns='s')
    def fauxEcho(self, c, string):
        """
        """
        return string


    @setting(2, 'return_float', returns='v')
    def return_float(self, c):
        """
        Returns
        -------
        137.036
        """
        
        yield None
        returnValue(137.036)

    @setting(3, 'return_floatList', returns= '?')
    def return_floatList(self, c):
        """
        Returns
        -------
        [87.04, 0.001, -1.09, 1e-5, 2.]
        """
        
        yield None
        returnValue([87.04, 0.001, -1.09, 1e-5, 2.])

    @setting(4, 'return_npArray1D', returns= '?')
    def return_npArray1D(self, c):
        """
        Returns
        -------
        _n.array([1., 2., 1e-5, 237])
        """
        
        yield None
        returnValue(_n.array([1., 2., 1e-5, 237]) )
 

    @setting(5, 'return_npArray2D', returns= '?')
    def return_npArray2D(self, c):
        """
        Returns
        -------
        _n.array([[1., 4.6, 1e-5], [45, -1, 1./45.]])
        """
        
        yield None
        returnValue(_n.array([[1., 4.6, 1e-5], [45, -1, 1./45.]]) )   
    
    



if __name__ == "__main__":
    from labrad import util
    util.runServer(BasicServer())