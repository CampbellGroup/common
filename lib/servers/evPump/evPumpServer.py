# Created on Mar 25, 2016
# @author: Anthony Ransford
"""
### BEGIN NODE INFO
[info]
name = evpump
version = 1.0
description =
instancename = evpump
[startup]
cmdline = %PYTHON% %FILE%
timeout = 20
[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
import labrad.errors
from labrad.types import Value
from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from labrad.units import WithUnit as U

TIMEOUT = Value(5, "s")  # serial read timeout

UPDATECURR = 150327
UPDATEPOW = 114327
UPDATETMP = 153422
UPDATESTAT = 356575


class evPumpDevice(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a evPump device."""
        print(
            'connecting to "%s" on port "%s"...' % (server.name, port),
        )
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(115200)
        p.read()  # clear out the read buffer
        p.timeout(TIMEOUT)
        yield p.send()

        self.timeInterval = 0.2
        self.loop = LoopingCall(self.main_loop)
        self.loopDone = self.loop.start(self.timeInterval, now=True)

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
        """Write, then read."""
        p = self.packet()
        p.write_line(code)
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)

    @inlineCallbacks
    def main_loop(self):
        temp = yield self.query("?T")
        status = yield self.query("?F")
        current = yield self.query("?C")
        power = yield self.query("?P")
        __server__.update_signals(temp, status, current, power)


class eVPump(DeviceServer):
    deviceName = "evPump"
    name = "evpump"
    deviceWrapper = evPumpDevice

    temperature = 0
    power = None
    current = None
    status = None

    currentchanged = Signal(UPDATECURR, "signal__current_changed", "v")
    powerchanged = Signal(UPDATEPOW, "signal__power_changed", "v")
    temperaturechanged = Signal(UPDATETMP, "signal__temp_changed", "v")
    statuschanged = Signal(UPDATESTAT, "signal__stat_changed", "s")

    @inlineCallbacks
    def initServer(self):
        print(
            "loading config info...",
        )
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)

    @inlineCallbacks
    def selectDevice(self, context, key=None):
        try:
            super().selectDevice(context, key=key)
        except labrad.errors.NoDevicesAvailableError:
            print("Keithley 3320G server has no available devices")
            returnValue(None)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(["", "Servers", "evPump", "Links"], True)
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
            devName = "%s - %s" % (serServer, port)
            devs += [(devName, (server, port))]
        returnValue(devs)

    @setting(100, "toggle_laser", value="b")
    def toggle_laser(self, c, value):
        dev = self.selectDevice(c)
        if value is True:
            yield dev.write("ON")
        else:
            yield dev.write("OFF")

    @setting(200, "toggle_shutter", value="b")
    def toggle_shutter(self, c, value):
        dev = self.selectDevice(c)
        if value:
            yield dev.write("SHT:1")
        else:
            yield dev.write("SHT:0")

    @setting(300, "set_power", value="v[W]")
    def set_power(self, c, value):
        dev = self.selectDevice(c)
        value = str(value["W"])
        yield dev.write("P:" + value)

    @setting(400, "get_power", returns="v[W]")
    def get_power(self, c):
        yield None
        returnValue(self.power)

    @setting(500, "set_current", value="v[A]")
    def set_current(self, c, value):
        dev = self.selectDevice(c)
        value = str(value["A"])
        yield dev.write("C1:" + value)

    @setting(600, "get_current", returns="v[A]")
    def get_current(self, c):
        yield None
        returnValue(self.current)

    @setting(700, "diode_status", returns="b")
    def diode_status(self, c):
        dev = self.selectDevice(c)
        value = yield dev.query("?D")
        value = bool(float(value))
        returnValue(value)

    @setting(800, "system_status", returns="s")
    def system_status(self, c):
        yield None
        returnValue(self.status)

    @setting(900, "get_power_setpoint", returns="v[W]")
    def get_power_setpoint(self, c):
        dev = self.selectDevice(c)
        value = yield dev.query("?PSET")
        value = U(float(value), "W")
        returnValue(value)

    @setting(101, "get_current_setpoint", returns="v[A]")
    def get_current_setpoint(self, c):
        dev = self.selectDevice(c)
        value = yield dev.query("?CS1")
        if value:
            value = U(float(value), "A")
        else:
            value = U(0.0, "A")
        returnValue(value)

    @setting(102, "get_shutter_status", returns="b")
    def get_shutter_status(self, c):
        dev = self.selectDevice(c)
        value = yield dev.query("?SHT")
        value = bool(float(value))
        returnValue(value)

    @setting(103, "set_control_mode", mode="s")
    def set_control_mode(self, c, mode):
        dev = self.selectDevice(c)
        if mode == "current":
            yield dev.write("M:0")
        elif mode == "power":
            yield dev.write("M:1")
        else:
            yield None

    @setting(104, "get_control_mode", returns="s")
    def get_control_mode(self, c):
        dev = self.selectDevice(c)
        value = yield dev.query("?M")
        if value == "0":
            value = "current"
        elif value == "1":
            value = "power"
        else:
            value = None
        returnValue(value)

    @setting(105, "get_temperature", returns="v[degC]")
    def get_temperature(self, c):
        yield None
        returnValue(self.temperature)

    @setting(106, "get_diode_current_limit", returns="v[A]")
    def get_diode_current_limit(self, c):
        dev = self.selectDevice(c)
        value = yield dev.query("?DCL")
        value = float(value)
        value = U(value, "A")
        returnValue(value)

    def update_signals(self, temp, status, current, power):

        self.status = status

        try:
            self.temperature = U(float(temp), "degC")
        except:
            self.temperature = None

        try:
            self.power = U(float(power), "W")
        except:
            self.power = None

        try:
            self.current = U(float(current), "A")
        except:
            self.current = None

        self.currentchanged(self.current)
        self.powerchanged(self.power)
        self.temperaturechanged(self.temperature)
        self.statuschanged(self.status)


__server__ = eVPump()

if __name__ == "__main__":
    from labrad import util

    util.runServer(__server__)
