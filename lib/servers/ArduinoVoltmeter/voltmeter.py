"""
### BEGIN NODE INFO
[info]
name = ArduinoVoltmeter
version = 1.0
description =
instancename = ArduinoVoltmeter
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 404417978
timeout = 20
### END NODE INFO
"""

from labrad.types import Value
from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall

TIMEOUT = Value(10.0, 's')


class VoltmeterDevice(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a Arduino device."""
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
        """Write a data value to the voltmeter control."""
        yield self.packet().write_line(code).send()

    @inlineCallbacks
    def read_line(self):
        """read value from voltmeter. """
        p = self.packet()
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)


class ArduinoVoltmeter(DeviceServer):
    name = 'ArduinoVoltmeter'
    deviceName = 'ArduinoVoltmeter'
    deviceWrapper = VoltmeterDevice
    loopingtime = .001
    on = False

    @inlineCallbacks
    def initServer(self):
        print 'loading config info...',
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)
        self.voltage_loop = LoopingCall(self.loop)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'ArduinoVoltmeter', 'Links'], True)
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

    @inlineCallbacks
    def loop(self):
        self.voltage = yield self.dev.read_line()
        print self.voltage

    @setting(100, 'voltmeter_on', state='?')
    def voltmeter_on(self, c, state=None):
        if type(state) == bool:
            dev = self.selectDevice(c)
            yield dev.write(chr(state))
            self.on = state
        else:
            returnValue(self.on)

    @setting(200, 'read_voltage', returns='s')
    def read_voltage(self, c):
        if self.on:
            self.dev = self.selectDevice(c)
            self.voltage_loop.start(self.loopingtime)
        else:
            self.voltage_loop.stop()


def convert_4_bytes_to_time_voltaged(data):
    pass


if __name__ == "__main__":
    from labrad import util
    util.runServer(ArduinoVoltmeter())
