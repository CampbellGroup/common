"""
### BEGIN NODE INFO
[info]
name = Bristol 521
version = 1.0
description =
instancename = Bristol 521

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue
import ctypes
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

FREQSIGNAL = 917223
AMPSIGNAL = 874195

class BristolServer(LabradServer):
    """
    Server for Bristol 521 wavelength meter.

    A DLL is required to run this server.  See initServer for the path location
    for the library.
    """
    name = 'Bristol 521'

    # Set up signals to be sent to listeners
    freqchanged = Signal(FREQSIGNAL, 'signal: frequency changed', '(v)')
    ampchanged = Signal(AMPSIGNAL, 'signal: amplitude changed', '(v)')

    def initServer(self):

        # load wavemeter dll file for use of API functions
        self.dll = ctypes.CDLL("CLDevIFace.dll")
        self.set_dll_variables()
        self.handle = self.dll.CLOpenUSBSerialDevice(ctypes.c_int(4))
        self.dll.CLSetLambdaUnits(self.handle, ctypes.c_uint(1))
        self.dll.CLSetPowerUnits(self.handle, ctypes.c_uint(0))
        if self.handle != -1:
            print 'Connected'
            self.measure()
        else:
            print 'Could not connect'            
        self.listeners = set()


    def set_dll_variables(self):
        """
        Allocate c_types for dll functions.
        """
        self.dll.CLGetLambdaReading.restype = ctypes.c_double
        self.dll.CLOpenUSBSerialDevice.restype = ctypes.c_int
        self.dll.CLGetPowerReading.restype = ctypes.c_double

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @setting(1, "get_wavelength", returns='v')
    def get_wavelength(self, c):
        yield None
        returnValue(self.freqchanged)

    @setting(2, "get_power", returns='v')
    def get_power(self, c):
        yield None
        returnValue(self.powerchanged)

    def measure(self):
        # TODO: Improve this with a looping call
        wl = self.dll.CLGetLambdaReading(self.handle)
        power = self.dll.CLGetPowerReading(self.handle)
        self.freqchanged = wl
        self.powerchanged = power
        reactor.callLater(0.1, self.measure)



if __name__ == "__main__":
    from labrad import util
    util.runServer(BristolServer())
