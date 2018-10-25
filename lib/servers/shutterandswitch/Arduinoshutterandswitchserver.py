"""
### BEGIN NODE INFO
[info]
name = ArduinoTTL
version = 1.0
description =
instancename = ArduinoTTL

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.types import Value
from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

TIMEOUT = Value(1.0, 's')


class TTLDevice(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a TTL device."""
        print('connecting to "%s" on port "%s"...' % (server.name, port))
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(57600)
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
        yield self.packet().write_line(code).send()

    @inlineCallbacks
    def query(self, code):
        """ Write, then read. """
        p = self.packet()
        p.write_line(code)
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)


class ArduinoTTL(DeviceServer):
    name = 'ArduinoTTL'
    deviceName = 'ArduinoTTL'
    deviceWrapper = TTLDevice

    on_switch_changed = Signal(124973, 'signal: on_switch_changed', '(ib)')

    @inlineCallbacks
    def initServer(self):
        print('loading config info...')
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
        self.listeners = set()

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'ArduinoTTL', 'Links'], True)
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

    def initContext(self, c):
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    @setting(100, 'TTL Output', chan='i', state='b')
    def ttlOutput(self, c, chan, state):
        dev = self.selectDevice(c)
        output = (chan << 2) | (state + 2)
        yield dev.write(chr(output))
        notified = self.getOtherListeners(c)
        self.on_switch_changed((chan, state), notified)

    @setting(200, 'TTL Read', chan='i', returns='b')
    def ttlInput(self, c, chan):
        dev = self.selectDevice(c)
        output = (chan << 2)
        status = yield dev.query(chr(output))
        status = status.encode('hex')

        try:
            status = int(status)
            if status == 1:
                print('status is 1')
                returnValue(True)
            elif status == 0:
                print('status is 0')
                returnValue(False)
            else:
                print(status, 'invalid TTL', returnValue(False))
        except ValueError:
            print(status, 'Error Reading')
            returnValue(False)


if __name__ == "__main__":
    from labrad import util
    util.runServer(ArduinoTTL())
