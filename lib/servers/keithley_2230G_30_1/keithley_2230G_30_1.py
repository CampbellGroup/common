"""
### BEGIN NODE INFO
[info]
name = Keithley 2230G Server
version = 1.3
description =

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
from labrad.server import setting
import labrad.units as _units
from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue


class KeithleyWrapper(GPIBDeviceWrapper):

    def initialize(self):
        pass

    def parse_channel(self, channel=None):
        """
        Get the proper GPIB string form (including a leading space) to talk to
        specific device channel's.
        Returns
        -------
        str, channel name for GPIB commands with a leading space.
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


class KeithleyServer(GPIBManagedServer):
    name = 'Keithley 2230G Server'  # server name
    deviceName = 'Keithley instruments 2230G-30-1'
    deviceWrapper = KeithleyWrapper

    # Note, settings 1 through 4 are already claimed by the parent class
    @setting(5, channel='i', output='b')
    def output(self, c, channel, output=None):
        """
        Parameters
        ----------
        channel: int, channel to control
        output: bool, control whether channel is on or off.
        c: passed context to address specific device
        """
        dev = self.selectedDevice(c)
        if output is None:
            output_state = yield dev.measure_output(channel)
        else:
            yield dev.set_output(channel, output)
            output_state = yield dev.measure_output(channel)
        returnValue(output_state)

    @setting(6, channel='i', voltage='v[V]', returns='v[V]')
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
        dev = self.selectedDevice(c)
        if voltage is not None:
            yield dev.set_voltage(channel, voltage)
        volts = yield dev.measure_voltage(channel=channel)
        returnValue(volts)

    @setting(7, channel='i', current='v[A]', returns='v[A]')
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
        dev = self.selectedDevice(c)
        if current is not None:
            yield dev.set_current(channel, current)
        current = yield dev.measure_current(channel=channel)
        returnValue(current)

    @setting(8, channel='i', returns='?')
    def channel(self, c, channel=None):
        """
        Enable channel or query enabled channel.
        Parameters
        ----------
        channel: int, channel to query or enable
        Returns
        -------
        """
        dev = self.selectedDevice(c)
        if channel is not None:
            yield dev.set_channel(channel)
        enabled_channel = yield dev.query_channel()
        returnValue(enabled_channel)


__server__ = KeithleyServer()


if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
