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
SIGNAL_VALUE = 234567


class InteractiveEmitter(LabradServer):
    """
    Emitter server designed to work interactively with an interactive emitter
    client.
    """
    
    name = 'Interactive Emitter Server'

    # This is the Signal to be emitted with ID# 123456 the name for the 
    # client to call is signal__emitted_signal and the labrad type is string
    onEvent = Signal(SIGNAL_VALUE, 'signal: emitted signal', 's')


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


if __name__ == "__main__":
    from labrad import util
    util.runServer(InteractiveEmitter())