"""
### BEGIN NODE INFO
[info]
name = ev_pump
version = 1.0
description =
instancename = ev_pump

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from common.lib.servers.serialdeviceserver import (
    SerialDeviceServer,
    setting,
    inlineCallbacks,
    SerialDeviceError,
    SerialConnectionError,
)
from labrad import types as T
from twisted.internet.defer import returnValue
from labrad.support import getNodeName

SERVERNAME = "ev_pump"
TIMEOUT = 1.0
BAUDRATE = 57600


class eVPump(SerialDeviceServer):
    name = SERVERNAME
    regKey = "evpump"
    port = None
    serNode = getNodeName()
    timeout = T.Value(TIMEOUT, "s")

    @inlineCallbacks
    def initServer(self):
        if not self.regKey or not self.serNode:
            raise SerialDeviceError("Define regKey and serNode attributes")
        port = yield self.getPortFromReg(self.regKey)
        self.port = port
        try:
            serStr = yield self.findSerial(self.serNode)
            print(serStr, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            self.initSerial(serStr, port, baudrate=BAUDRATE)
        except SerialConnectionError as e:
            self.ser = None
            if e.code == 0:
                print("Could not find serial server for node %s" % self.serNode)
                print("Please start correct serial server")
            elif e.code == 1:
                print("Error opening serial connection")
                print("Check set up and restart serial server")
            else:
                raise


if __name__ == "__main__":
    from labrad import util

    util.runServer(eVPump())
