"""
### BEGIN NODE INFO
[info]
name = Piezo_Server
version = 1.0
description =
instancename = Piezo_Server

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
from labrad.units import V

TIMEOUT = Value(1.0, 's')

class PiezoDevice(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a Piezo device."""
        print 'connecting to "%s" on port "%s"...' % (server.name, port),
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(38400)
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


class Piezo_Server(DeviceServer):
    name = 'Piezo_Server'
    deviceName = 'Piezo_Server'
    deviceWrapper = PiezoDevice

    @inlineCallbacks
    def initServer(self):
        print 'loading config info...',
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield self.reg.cd(['', 'settings'], True)
        yield DeviceServer.initServer(self)
        self.listeners = set()

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'UCLAPiezo', 'Links'], True)
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

    @setting(100, 'device_info')
    def device_info(self, c):
        dev = self.selectDevice(c)
        output = 'id?'
        yield dev.write(output)
        device_type = yield dev.read()
        device_id = yield dev.read()
        hardware_id = yield dev.read()
        firmware = yield dev.read()
        returnValue([device_type, device_id, hardware_id, firmware])
        
    @setting(101, 'output_channel', chan = 'i', state = 'i')
    def output_channel(self, c, chan, state=2):
        dev = self.selectDevice(c)
        if state != 2:
            output = 'out.w ' + str(chan) + ' ' + str(state)
            yield dev.write(output)
            yield dev.read() #clear output from the change
            current_setting = str(state)
        else:
            output = 'out.r ' + str(chan)
            yield dev.write(output)
            current_setting = yield dev.read()
        out = [str(chan), current_setting]
        returnValue(out)
        
    @setting(102, 'set_voltage', chan = 'i', voltage = 'v[V]')
    def set_voltage(self, c, chan, voltage = -1.):
        dev = self.selectDevice(c)
        if voltage < 0:
            output = 'vout.r ' + str(chan)
            yield dev.write(output)
            current_volt = yield dev.read()
        elif 0*V <= voltage <= 150*V:
            output = 'vout.w ' + str(chan) + ' ' + str(voltage['V'])
            yield dev.write(output)
            yield dev.read() #clear output from the change
            current_volt = str(voltage['V'])
        out = [str(chan), current_volt]
        returnValue(out)
    
    @setting(103, 'remote_mode', state = 'i')
    def remote_mode(self, c, state=2):
        dev = self.selectDevice(c)
        if state != 2:
            output = 'remote.w ' + str(state)
            yield dev.write(output)
            current_mode = str(state)
        else:
            output = 'remote.r'
            yield dev.write(output)
            current_mode = yield dev.read()        
        returnValue(current_mode)
    
if __name__ == "__main__":
    from labrad import util
    util.runServer(Piezo_Server())
