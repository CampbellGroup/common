"""
### BEGIN NODE INFO
[info]
name = shutter_server
version = 1.0
description =
instancename = shutter_server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.types import Value
from labrad.server import Signal
from labrad.support import getNodeName
from common.lib.servers.serialdeviceserver \
    import SerialDeviceServer, setting, inlineCallbacks, \
    SerialDeviceError, SerialConnectionError, returnValue

SERVERNAME = 'shutter_server'
TIMEOUT = 1.0
BAUDRATE = 57600


class ShutterServer(SerialDeviceServer):
    name = SERVERNAME
    regKey = 'Shutter'
    serNode = getNodeName()
    timeout = Value(TIMEOUT, 's')

    on_shutter_changed = Signal(124973, 'signal: on_shutter_changed', '(ib)')

    @inlineCallbacks
    def initServer(self):
        if not self.regKey or not self.serNode:
            raise SerialDeviceError('Must define regKey & serNode attributes')
        self.port = yield self.getPortFromReg(self.regKey)
        try:
            serStr = yield self.findSerial(self.serNode)
            self.initSerial(serStr, self.port, baudrate=BAUDRATE)
        except SerialConnectionError as e:
            self.ser = None
            if e.code == 0:
                print('Could not find serial server for node: %s'
                      % self.serNode)
                print('Please start correct serial server')
            elif e.code == 1:
                print('Error opening serial connection')
                print('Check set up and restart serial server')
            else:
                raise

        self.listeners = set()
        # yield self.ser.read_line()
        # yield self.ser.read_line()

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @setting(100, chan='i', state='b')
    def set_channel_state(self, c, chan, state):
        output = (chan << 2) | (state + 2)
        yield self.ser.write(chr(output))
        notified = self.getOtherListeners(c)
        self.on_shutter_changed((chan, state), notified)

    @setting(200, chan='i', returns='b')
    def get_channel_state(self, c, chan):
        """ Function not tested """
        output = (chan << 2)
        yield self.ser.write(chr(output))
        status = yield self.ser.read_line()
        status = ord(status.encode('ascii'))
        if status == 1:
            returnValue(True)
        elif status == 0:
            returnValue(False)
        else:
            raise ValueError("Invalid returned value")


if __name__ == "__main__":
    from labrad import util
    util.runServer(ShutterServer())
