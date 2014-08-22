# -*- coding: utf-8 -*-
"""
### BEGIN NODE INFO
[info]
name = Types Server
version = 1.0
description = 
instancename = TypesServer

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
import labrad.units as _u
from twisted.internet.defer import returnValue


class TypesServer(LabradServer):
    """
    This is intended as a server for testing and understanding LabRAD types,
    in particular how they are handled.
    """
    
    name = 'Types Server'



    @setting(1, returns='b')
    def return_bool(self, c):

        return True

        
    @setting(2, returns='i')
    def return_int(self, c):

        return 23


    @setting(3, returns='w')
    def return_uint(self, c):

        return 86


    @setting(4, returns='v[Hz]')
    def return_v_unit(self, c):

        return _u.WithUnit(60.0, 'Hz')


    @setting(5, returns='v[]')
    def return_v_brackets(self, c):
        
        return 34.


    @setting(6, returns='c[m]')
    def return_c_unit(self, c):

        return _u.WithUnit(60.0, 'm')


    @setting(7, returns='c[]')
    def return_c_brackets(self, c):
        
        return 1. + 1j*34.
        

    @setting(8, returns='*v[]')
    def return_star_v_brackets(self, c):
        
        return [5., 6., 7.]       




    @setting(20, 'return_floatList', returns= '?')
    def return_floatList(self, c):
        """
        Returns
        -------
        [87.04, 0.001, -1.09, 1e-5, 2.]
        """
        
        yield None
        returnValue([87.04, 0.001, -1.09, 1e-5, 2.])


    @setting(21, 'return_npArray1D', returns= '?')
    def return_npArray1D(self, c):
        """
        Returns
        -------
        _n.array([1., 2., 1e-5, 237])
        """
        
        yield None
        returnValue(_n.array([1., 2., 1e-5, 237]) )
 

    @setting(22, 'return_npArray2D', returns= '?')
    def return_npArray2D(self, c):
        """
        Returns
        -------
        _n.array([[1., 4.6, 1e-5], [45, -1, 1./45.]])
        """
        
        yield None
        returnValue(_n.array([[1., 4.6, 1e-5], [45, -1, 1./45.]]) )   
    
    
    @setting(23, 'return_npArray3D', returns= '?')
    def return_npArray3D(self, c):
        """
        Returns
        -------
        _n.empty( (492, 656, 1) )
        """
        
        yield None
        returnValue(_n.empty( (492, 656, 1) ) )   
    
        



if __name__ == "__main__":
    from labrad import util
    util.runServer(TypesServer())