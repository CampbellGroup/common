# Created on Feb 12, 2017
# @author: Anthony Ransford

"""
### BEGIN NODE INFO
[info]
name = itead_motor_server
version = 1.0
description = drives stepper motors
instancename = itead_motor_server
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
from labrad.server import setting
from twisted.internet.defer import inlineCallbacks, returnValue

TIMEOUT = Value(5, 's')  # serial read timeout
BAUDRATE = 115200


class StepperController(DeviceWrapper):

    """
    arduino dual stepper devices
    """

    @inlineCallbacks
    def connect(self, server, port):
        """Here we make a connection to the serial server in LabRAD where all
        the serial communication is handled"""
        print 'connecting to "%s" on port "%s"...' % (server.name, port),
        self.server = server
        self.ctx = server.context()  # grabs an identification number from the server
        self.port = port
        # The following opens a communication on a com port specifying a baudrate and a timeout
        p = self.packet()
        p.open(port)
        p.baudrate(BAUDRATE)
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


class StepperMotorServer(DeviceServer):

    deviceName = 'stepper_motor_server'
    name = 'stepper_motor_server'
    deviceWrapper = StepperController

    @inlineCallbacks
    def initServer(self):
        """
        Makes a connection to the registry where port information and other server
        specific settings can be retrieved.
        """
        print 'loading config info...',
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)  # starts server after configurations loaded

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry, including device serial ports
        The registry must have a key value pair in the form of the tuple ("server name", "comport")
        e.g. ("qsimexpcontrol Serial Server", "/dev/ttyACMarduinoTTL")
        """
        reg = self.reg
        yield reg.cd(['', 'Servers', 'StepperMotor', 'Links'], True)  # opens folder
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys)  # list of serial connections

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

    @setting(101, 'move_steps', steps='i')
    def move_steps(self, c, steps):
        """
        moves stepper motor N steps, if positive the move CW else CCW
        each step currently corresponds to 1.8 degrees
        """
        dev = self.selectDevice(c)
        value = yield dev.write(str(steps))

if __name__ == "__main__":
    from labrad import util
    util.runServer(StepperMotorServer())
