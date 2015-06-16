from labrad.server import LabradServer, setting
from twisted.internet.defer import returnValue
from labrad.units import WithUnit
from Labjackapi import u3


"""
### BEGIN NODE INFO
[info]
name = LabJack
version = 1.0
description =
instancename = LabJack

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""


class LabJackServer(LabradServer):
    """
    LabJack DAC and ADC server
    """
    name = 'LabJack'

    def initServer(self):
        try:
            self.device = u3.U3()
        except:
            print "ERROR: Could not connect to LabJack"

    @setting(11, channel='i',  volts='v')
    def output_voltage(self, c, channel, volts):
        """
        Set the analog output voltage of channel.

        Parameters
        ----------
        channel: int, channel to ouput DC voltage on.
        volts: WithUnit, voltage to output
        """
        # convert value to volts for LabJack API
        volts_without_units = volts['V']
        dac_value = self.device.voltageToDACBits(volts_without_units, dacNumber = channel, is16Bits = True)
        self.device.getFeedback(u3.DAC16(channel, dac_value))

    @setting(12, channel='i', returns='v')
    def measure_voltage(self, c, channel):
        """
        Measure the analog input voltage at channel.

        The value is rounded to 4 digits of precision.  This is probably far
        beyond the LabJack's capabilities.

        Parameters
        ----------
        channel: int, channel to ouput DC voltage on.

        Returns
        -------
        WithUnit voltage value
        """
        ainbits, = self.device.getFeedback(u3.AIN(channel))
        value = yield self.device.binaryToCalibratedAnalogVoltage(ainbits, isLowVoltage = False, channelNumber = channel)
        value = round(value, 4)
        # convert value to WithUnit, assumes value is in Volts.
        voltage = WithUnit(value, 'V')
        returnValue(voltage)


if __name__ == "__main__":
    from labrad import util
    util.runServer(LabJackServer())
