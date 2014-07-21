# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 10:23:36 2014

@author: Campbell Lab
"""

"""
### BEGIN NODE INFO
[info]
name = Interactive Emitter Server
version = 1.0
description = 
instancename = InteractiveEmitter

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting, Signal
#from twisted.internet import reactor
from twisted.internet.defer import  returnValue #, inlineCallbacks
#import labrad

# This value can't start with zero.
SIGNAL_VALUE = 434567
SIGNAL_FLOAT = 434569


class InteractiveEmitter(LabradServer):
    """
    Emitter server designed to work interactively with an interactive emitter
    client.
    """
    
    debug = False   
    
    name = 'Interactive Emitter Server'

    # This is the Signal to be emitted with ID# 123456 the name for the 
    # client to call is signal__emitted_signal and the labrad type is string
    onEvent = Signal(SIGNAL_VALUE, 'signal: emitted signal', 's')
    onFloat = Signal(SIGNAL_FLOAT, 'signal: efs', 's')

    @setting(1, 'Emit Signal', returns='')
    def emitSignal(self, c):
        """function that will onEvent to send signal to listeners
    
        """
        
        # Sends signal
        self.onEvent('Output!')

    
    @setting(2, 'trigger_signal')
    def trigger_signal(self, c):
        """
        trigger the signal.
        """
        self.onEvent('Was triggered!')        
        

    @setting(3, 'return_float', returns='v')
    def return_float(self, c):
        """
        Returns
        -------
        6.626
        """
        
        yield None
        returnValue(6.626)


    @setting(27, 'Emit Float Available', returns='')
    def emitFloatAvailable(self, c):
        """
        Emits onFloat signal to listeners
        """
        if self.debug : print "emitFloatAvailable() called."
        # Sends signal
        self.onFloat('Float now available')



    @setting(28, 'float data', returns='v')
    def float_data(self, c):
        """
        Return a single float data point.

        c - context for the device

        """
        if self.debug : print "float_data()"

        yield None
        returnValue(1115.4534)


if __name__ == "__main__":
    from labrad import util
    util.runServer(InteractiveEmitter())