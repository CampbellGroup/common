"""
### BEGIN NODE INFO
[info]
name = Keithley 2231A Server
version = 1.0
description =
instancename = Keithley_Sever

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
import labrad.units as _units
from labrad.units import V, A
from twisted.internet.defer import inlineCallbacks, returnValue

TIMEOUT = Value(1.0, 's')

class KeithleyWrapper(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a Keithley 2231A device."""
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

    def parse_channel(self, channel=None):
        """
        Get the proper string form (including a leading space) to talk to
        specific device channels.
        Returns
        -------
        str, channel name for commands with a leading space.
        """
        if channel == 1:
            channel_str = ' CH1'
        elif channel == 2:
            channel_str = ' CH2'
        elif channel == 3:
            channel_str = ' CH3'
        # Why should this else exist? 
        else:
            channel_str = ''
        return channel_str

    @inlineCallbacks
    def set_output(self, channel, output):
        """
        Set channel's output state.
        Parameters
        ----------
        channel: int, channel to control the output of.
        output: bool, turn on or off channel
        """
        # First select the appropriate channel
        yield self.set_channel(channel=channel)
        # Explicitly setting the important space in command.
        command = 'CHANnel:OUTPut' + ' ' + str(int(output))
        yield self.write(command)

    @inlineCallbacks
    def measure_output(self, channel):
        """
        Measure channel's output state.
        Parameters
        ----------
        channel: int, channel to control the output of.
        Returns
        -------
        bool
        """
        # First select the appropriate channel
        yield self.set_channel(channel=channel)
        command = 'CHANnel:OUTPut?'
        yield self.write(command)
        state = yield self.read()
        state = self._convert_state_to_bool(state)
        state = bool(state)  # convert to boolean
        returnValue(state)

    def _convert_state_to_bool(self, state):
        """
        Parameters
        ----------
        state: str, channel output state
        Returns
        -------
        bool
        """
        if state == '0':
            output_state = False
        elif state == '1':
            output_state = True
        else:
            output_state = None
        return output_state

    # Measure commands
    @inlineCallbacks
    def measure_voltage(self, channel=None):
        """
        Get the output voltage of channel.
        Parameters
        ----------
        channel: int, channel number
        """
        channel_str = self.parse_channel(channel=channel)
        command = 'MEAS:VOLT:DC? ' + channel_str
        yield self.write(command)
        voltage = yield self.read()
        voltage = _units.WithUnit(float(voltage), 'V')
        returnValue(voltage)
        
    @inlineCallbacks
    def measure_current(self, channel=None):
        """
        Get the output current of channel.
        Parameters
        ----------
        channel: int, channel number
        """
        channel_str = self.parse_channel(channel=channel)
        command = 'MEAS:CURRent:DC? ' + channel_str
        yield self.write(command)
        current = yield self.read()
        current = _units.WithUnit(float(current), 'A')
        returnValue(current)

    # Source commands.  These commands allow you to output various values.
    @inlineCallbacks
    def set_voltage(self, channel, voltage=None):
        """
        Set channel's output voltage.
        """
        channel_str = self.parse_channel(channel)
        voltage_in_volts = voltage['V']
        voltage_in_volts = str(voltage_in_volts)
        command = 'APPly' + channel_str + ',' + voltage_in_volts + 'V'
        yield self.write(command)
        volts = yield self.measure_voltage(channel=channel)
        units_volts = _units.WithUnit(volts, 'V')
        returnValue(units_volts)

    @inlineCallbacks
    def applied_voltage_current(self, channel):
        """
        Gets the channel's applied voltage and curent.
        Not a measurement, output is the voltage and current that
        is set by the user either at the box on via the client
        """
        channel_str = self.parse_channel(channel)
        command = 'APPL?' + channel_str
        yield self.write(command)
        out = yield self.read()
        returnValue(out)

    @inlineCallbacks
    def set_current(self, channel, current=None):
        """
        Set channel's output current.
        Parameters
        ----------
        channel: int, channel number
        current: WithUnit Amps, default(None)
        """
        yield self.set_channel(channel=channel)
        current_in_amps = current['A']
        current_in_amps = str(current_in_amps)
        command = 'CURRent' + ' ' + current_in_amps + 'A'
        yield self.write(command)
        current = yield self.measure_current(channel=channel)
        units_current = _units.WithUnit(current, 'A')
        returnValue(units_current)

    # Instrument commands.
    @inlineCallbacks
    def set_channel(self, channel):
        """
        Select channel.
        Parameters
        ----------
        channel: int, channel to select
        """
        channel_str = self.parse_channel(channel)
        command = "INSTrument:SELect" + channel_str
        yield self.write(command)

    @inlineCallbacks
    def query_channel(self):
        """
        Parameters
        ----------
        channel: int, channel to select
        """
        command = "INSTrument:SELect?"
        yield self.write(command)
        channel = yield self.read()
        returnValue(channel)
        
class Keithley_Server(DeviceServer):
    name = 'Keithley_Server'
    deviceName = 'Keithley_Server'
    deviceWrapper = KeithleyWrapper

    @inlineCallbacks
    def initServer(self):
        print 'loading config info...',
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield self.reg.cd(['','settings'], True)
        yield DeviceServer.initServer(self)
        self.listeners = set()

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'KeithleyBField', 'Links'], True)
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

    @setting(100, 'test_beep')
    def test_beep(self, c):
        '''
        Sends a command to the device, telling it to beep.
        This may be useful when testing the connection to LABRAD.
        Takes no arguments. 
        '''
        dev = self.selectDevice(c)
        output = 'SYSTem:BEEPer'
        yield dev.write(output)

    @setting(101, 'remote_mode', state = 'i')
    def remote_mode(self, c, state):
        '''
        Turn remote mode on or off. 
        Takes an integer input (0 or 1).
        0 will turn remote mode off, and 1 will turn it on.
        You can visualize this on the device, a 'Y' with a bar above
        it will appear on the left side when remote mode is on. 
        '''
        dev = self.selectDevice(c)
        if state == 0:
            output = 'SYSTem:LOCal'
        else:
            output = 'SYSTem:REMote'
        yield dev.write(output)

    @setting(102, channel='i', output='b')
    def output(self, c, channel, output=None):
        """
        Parameters
        ----------
        channel: int, channel to control
        output: bool, control whether channel is on or off.
        c: passed context to address specific device
        """
        dev = self.selectDevice(c)
        if output is None:
            output_state = yield dev.measure_output(channel)
        else:
            yield dev.set_output(channel, output)
            output_state = yield dev.measure_output(channel)
        returnValue(output_state)

    @setting(103, channel='i', voltage='v[V]', returns='v[V]')
    def voltage(self, c, channel, voltage=None):
        """
        Get or set the Keithley's channel voltage.
        Parameters
        ----------
        channel: int, channel to control
        voltage: WithUnit volts, channel output voltage value, default(None)
        Returns
        -------
        WithUnit voltage, voltage output of channel
        """
        dev = self.selectDevice(c)
        if voltage is not None:
            yield dev.set_voltage(channel, voltage)
        volts = yield dev.measure_voltage(channel=channel)
        returnValue(volts)

    @setting(104, channel='i', current='v[A]', returns='v[A]')
    def current(self, c, channel, current=None):
        """
        Get or set the Keithley's channel current.
        Parameters
        ----------
        channel: int, channel to control
        current: WithUnit Amps, channel output current value, default(None)
        Returns
        -------
        WithUnit Amps, current output of channel
        """
        dev = self.selectDevice(c)
        if current is not None:
            yield dev.set_current(channel, current)
        current = yield dev.measure_current(channel=channel)
        returnValue(current)

    @setting(105, channel='i', returns='?')
    def channel(self, c, channel=None):
        """
        Enable channel or query enabled channel.
        Parameters
        ----------
        channel: int, channel to query or enable
        Returns
        -------
        """
        dev = self.selectDevice(c)
        if channel is not None:
            yield dev.set_channel(channel)
        enabled_channel = yield dev.query_channel()
        returnValue(enabled_channel)

    @setting(106, volt ='*v[V]')
    def all_voltage(self, c, volt):
        '''
        '''
        dev = self.selectDevice(c)
        command = 'APP:VOLT ' + str(volt[0]) + ',' + str(volt[1]) + ',' + str(volt[2])
        yield dev.write(command)

    @setting(107, curr = '*v[A]')
    def all_current(self, c, curr):
        '''
        Change to take list of currents
        '''
        dev = self.selectDevice(c)
        command = 'APP:CURR ' + str(curr[0]) + ',' + str(curr[1]) + ',' + str(curr[2])
        yield dev.write(command)

    @setting(108, chan = 'i')
    def query_initial(self, c, chan):
        '''
        '''
        dev = self.selectDevice(c)
        command = 'Stat:oper:inst:isum' + str(chan) + ':cond?'
        yield dev.write(command)
        out = yield dev.read()
        returnValue(int(out))
        
    @setting(109, out_set='i', returns='?')
    def get_applied_voltage_current(self, c, out_set=None):
        dev = self.selectDevice(c)
        
        out1 = yield dev.applied_voltage_current(1)
        out1 = out1.split(', ')
        out2 = yield dev.applied_voltage_current(2)
        out2 = out2.split(', ')
        out3 = yield dev.applied_voltage_current(3)
        out3 = out3.split(', ')
            
        if out_set is not None:
            if out_set == 1:
                values1 = _units.WithUnit(float(out1[0]), 'V')
                values2 = _units.WithUnit(float(out2[0]), 'V')
                values3 = _units.WithUnit(float(out3[0]), 'V')
            elif out_set == 2:
                values1 = _units.WithUnit(float(out1[1]), 'A')
                values2 = _units.WithUnit(float(out2[1]), 'A')
                values3 = _units.WithUnit(float(out3[1]), 'A')
        else:
            for i in range(2):
                out1[i] = float(out1[i])
                out2[i] = float(out2[i])
                out3[i] = float(out3[i])
                
            values1 = out1
            values2 = out2
            values3 = out3
        
        returnValue([values1, values2, values3])
            
if __name__ == '__main__':
    from labrad import util
    util.runServer(Keithley_Server())
