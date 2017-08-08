"""
### BEGIN NODE INFO
[info]
name = dac8718
version = 1.0
description =
instancename = dac8718

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
from labrad.server import setting
from twisted.internet.defer import inlineCallbacks, returnValue


class DACDevice(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a evPump device."""
        print 'connecting to "%s" on port "%s"...' % (server.name, port),
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(9600)
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
        """Write a data value to the heat switch."""
        yield self.packet().write(code).send()

    @inlineCallbacks
    def query(self, code):
        """ Write, then read. """
        p = self.packet()
        p.write_line(code)
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)


class DAC8718(DeviceServer):
    name = 'dac8718'
    deviceWrapper = DACDevice

    @inlineCallbacks
    def initServer(self):
        print 'loading config info...',
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        print self.serialLinks
        yield DeviceServer.initServer(self)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'dac8718', 'Links'], True)
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

    @setting(100, chan='i', value='i')
    def DACOutput(self, c, chan, value):
        """
        Output voltage value (in bits from 0 to 2^16) on chan.

        Parameters
        ----------
        chan: int, DAC channel, valid from 0-15
        """

        dev = self.selectDevice(c)
        chan = chan + 8
        if value > 2**16 - 1:
            value = 2**16 - 1
        elif value < 0:
            value = 0

        value = bin(value)[2:]

        if len(value) != 16:
            buff = 16 - len(value)
            value = '0'*buff + value

        value1 = value[0:8]
        value1 = int('0b' + value1, 2)
        value2 = value[8:]
        value2 = int('0b' + value2, 2)
        yield dev.write(chr(chan))
        yield dev.write(chr(value1))
        yield dev.write(chr(value2))

TIMEOUT = Value(1, 's')

if __name__ == "__main__":
    from labrad import util
    util.runServer(DAC8718())
