"""
### BEGIN NODE INFO
[info]
name = TPI1001B
version = 1.0
description = RF Consultants Signal Generator
instancename = TPI1001B

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.types import Value
from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

TIMEOUT = Value(5.0, 's')


class TPI1001BDevice(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a Piezo device."""
        print('connecting to "%s" on port "%s"...' % (server.name, port),)
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(3000000)
        p.read()  # clear out the read buffer
        p.timeout(TIMEOUT)
        yield p.send()

    def packet(self):
        """Create a packet in our private context."""
        return self.server.packet(context=self.ctx)

    def shutdown(self):
        """Disconnect from the serial port when we shut down."""
        return self.packet().close().send()

    @inlineCallbacks
    def write(self, code):
        """Write a data value."""
        yield self.packet().write_line(code).send()

    @inlineCallbacks
    def read(self):
        """Read a line of data"""
        p = self.packet()
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)

    @inlineCallbacks
    def query(self, code):
        """ Write, then read. """
        p = self.packet()
        p.write_line(code)
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)


class TPI1001B(DeviceServer):
    name = 'TPI1001B'
    deviceWrapper = TPI1001BDevice

    @inlineCallbacks
    def initServer(self):
        print('loading config info...',)
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        print(self.serialLinks)
        yield DeviceServer.initServer(self)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'TPI1001B', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys)

    @inlineCallbacks
    def findDevices(self):
        """Find available devices from list stored in the registry."""
        devs = []
        for name, (serServer, port) in self.serialLinks.items():
            if serServer not in self.client.servers:
                continue
            server = self.client[serServer]
            ports = yield server.list_serial_ports()
            if port not in ports:
                continue
            devName = '%s - %s' % (serServer, port)
            devs += [(devName, (server, port))]
        returnValue(devs)

    @setting(100, 'user_control')
    def user_control(self, c):
        dev = self.selectDevice(c)
        yield dev.write()


if __name__ == "__main__":
    from labrad import util
    util.runServer(TPI1001B())
