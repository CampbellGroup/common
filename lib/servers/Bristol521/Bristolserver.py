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
from twisted.internet.task import LoopingCall

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
    freqchanged = Signal(FREQSIGNAL, 'signal: frequency changed', 'v')
    powerchanged = Signal(AMPSIGNAL, 'signal: amplitude changed', 'v')

    def initServer(self):

        # load wavemeter dll file for use of API functions
        self.com_port = 3
        self.power = 0.0
        self.wl = 0.0
        self.listeners = set()
        self.update_loop = LoopingCall(self.measure)
        self.connected = self.connect_bristol()
        print self.connected
        if self.connected:
            self.update_loop.start(0)


    def connect_bristol(self):
        self.dll = ctypes.CDLL("CLDevIFace.dll")
        self.set_dll_variables()
        self.handle = self.dll.CLOpenUSBSerialDevice(ctypes.c_int(self.com_port))
        self.dll.CLSetLambdaUnits(self.handle, ctypes.c_uint(1))
        self.dll.CLSetPowerUnits(self.handle, ctypes.c_uint(0))
        if self.handle != -1:
            connected = True
        else:
            connected = False
        return connected

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
        returnValue(self.wl)

    @setting(2, "get_power", returns='v')
    def get_power(self, c):
        yield None
        returnValue(self.power)

    @setting(3, "get_status", returns ='w')
    def get_status(self, c):
        yield None
        returnValue(self.connected)

    def measure(self):
        self.wl = self.dll.CLGetLambdaReading(self.handle)
        self.power = self.dll.CLGetPowerReading(self.handle)
        self.freqchanged(self.wl)
        self.powerchanged(self.power)



if __name__ == "__main__":
    from labrad import util
    util.runServer(BristolServer())
