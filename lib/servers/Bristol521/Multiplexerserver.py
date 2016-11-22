"""
### BEGIN NODE INFO
[info]
name = Bristol 521
version = 1.0
description =
instancename = MBristol 521

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

FREQSIGNAL = 917223
AMPSIGNAL = 917223

class BristolServer(LabradServer):
    """
    Server for Bristol 521 wavelength meter.

    A DLL is required to run this server.  See initServer for the path location
    for the library.
    """
    name = 'Multiplexerserver'

    # Set up signals to be sent to listeners
    freqchanged = Signal(FREQSIGNAL, 'signal: frequency changed', '(v)')
    ampchanged = Signal(AMPSIGNAL, 'signal: amplitude changed', '(v)')

    def initServer(self):

        # load wavemeter dll file for use of API functions

        dll_path = "C:\Windows\System32\CLDevlface.dll"
        self.wmdll = ctypes.windll.LoadLibrary(dll_path)\
        self.set_dll_variables()
        self.measure()
        self.listeners = set()


    def set_dll_variables(self):
        """
        Allocate c_types for dll functions.
        """
        self.wmdll.CLGetLambdaReading.restype = ctypes.c_double

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @setting(1, "get_wavelength")
    def get_wavelength(self, c):
        pass


    def measure(self):
        # TODO: Improve this with a looping call
        reactor.callLater(0.1, self.measureChan)



if __name__ == "__main__":
    from labrad import util
    util.runServer(MultiplexerServer())
