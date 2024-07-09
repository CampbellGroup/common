from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet.threads import deferToThread
from labrad.units import WithUnit
from errors import dds_access_locked
import numpy as np


class DDS(LabradServer):
    """Contains the DDS functionality for the pulser server"""

    on_dds_param = Signal(142006, 'signal: new dds parameter', '(ssv)')

    @inlineCallbacks
    def initialize_dds(self):
        self.ddsLock = False
        self.api.initialize_dds()
        for name, channel in self.ddsDict.items():
            channel.name = name
            freq, ampl = (channel.frequency, channel.amplitude)
            self._check_range('amplitude', channel, ampl)
            self._check_range('frequency', channel, freq)
            yield self.inCommunication.run(self._set_parameters, channel, freq, ampl)

    @setting(41, "Get DDS Channels", returns='*s')
    def get_dds_channels(self, c):
        """get the list of available channels"""
        return list(self.ddsDict.keys())

    @setting(43, "Amplitude", name='s', amplitude='v[dBm]', returns='v[dBm]')
    def amplitude(self, c, name=None, amplitude=None):
        """Get or set the amplitude of the named channel or the selected channel"""
        # get the hardware channel
        if self.ddsLock and amplitude is not None:
            raise dds_access_locked()
        channel = self._get_channel(c, name)
        if amplitude is not None:
            # setting the ampplitude
            amplitude = amplitude['dBm']
            self._check_range('amplitude', channel, amplitude)
            if channel.state:
                # only send to hardware if the channel is on
                yield self._set_amplitude(channel, amplitude)
            channel.amplitude = amplitude
            self.notify_other_listeners(c, (name, 'amplitude', channel.amplitude), self.on_dds_param)
        amplitude = WithUnit(channel.amplitude, 'dBm')
        returnValue(amplitude)

    @setting(44, "Frequency", name='s', frequency=['v[MHz]'], returns=['v[MHz]'])
    def frequency(self, c, name=None, frequency=None):
        """Get or set the frequency of the named channel or the selected channel"""
        # get the hardware channel
        if self.ddsLock and frequency is not None:
            raise dds_access_locked()
        channel = self._get_channel(c, name)
        if frequency is not None:
            # setting the frequency
            frequency = frequency['MHz']
            self._check_range('frequency', channel, frequency)
            if channel.state:
                # only send to hardware if the channel is on
                yield self._set_frequency(channel, frequency)
            channel.frequency = frequency
            self.notify_other_listeners(c, (name, 'frequency', channel.frequency), self.on_dds_param)
        frequency = WithUnit(channel.frequency, 'MHz')
        returnValue(frequency)

    @setting(45, 'Add DDS Pulses', values=['*(sv[s]v[s]v[MHz]v[dBm]v[deg]v[MHz]v[dB])'])
    def add_dds_pulses(self, c, values):
        """
        input in the form of a list [(name, start, duration, frequency, amplitude, phase, ramp_rate, amp_ramp_rate)]
        """
        sequence = c.get('sequence')
        if not sequence:
            raise Exception("Please create new sequence first")
        for value in values:
            try:
                name, start, dur, freq, ampl = value
                phase = 0.0
                ramp_rate = 0.0
            except ValueError:
                name, start, dur, freq, ampl, phase, ramp_rate, amp_ramp_rate = value
            try:
                channel = self.ddsDict[name]
            except KeyError:
                raise Exception("Unknown DDS channel {}".format(name))
            start = start['s']
            dur = dur['s']
            freq = freq['MHz']
            ampl = ampl['dBm']
            phase = phase['deg']
            ramp_rate = ramp_rate['MHz']
            amp_ramp_rate = amp_ramp_rate['dB']
            freq_off, ampl_off = channel.off_parameters
            if freq == 0 or ampl == 0:  # off state
                freq, ampl = freq_off, ampl_off
            else:
                self._check_range('frequency', channel, freq)
                self._check_range('amplitude', channel, ampl)
            num = self.settings_to_num(channel, freq, ampl, phase, ramp_rate, amp_ramp_rate)
            if not channel.phase_coherent_model:
                num_off = self.settings_to_num(channel, freq_off, ampl_off)
            else:
                # note that keeping the frequency the same when switching off to preserve phase coherence
                num_off = self.settings_to_num(channel, freq, ampl_off, phase, ramp_rate, amp_ramp_rate)
            # note < sign, because start can not be 0.
            # this would overwrite the 0 position of the ram,
            # and cause the dds to change before pulse sequence is launched
            if not self.sequenceTimeRange[0] < start <= self.sequenceTimeRange[1]:
                raise Exception(
                    "DDS start time out of acceptable input range for channel {0} at time {1}".format(name, start))
            if not self.sequenceTimeRange[0] < start + dur <= self.sequenceTimeRange[1]:
                raise Exception("DDS start time out of acceptable input range for channel {0} at time {1}".format(name,
                                                                                                                  start + dur))
            if not dur == 0:  # 0-length pulses are ignored
                sequence.add_dds(name, start, num, 'start')
                sequence.add_dds(name, start + dur, num_off, 'stop')

    @setting(46, 'Get DDS Amplitude Range', name='s', returns='(vv)')
    def get_dds_ampl_range(self, c, name=None):
        channel = self._get_channel(c, name)
        return channel.allowedamplrange

    @setting(47, 'Get DDS Frequency Range', name='s', returns='(vv)')
    def get_dds_freq_range(self, c, name=None):
        channel = self._get_channel(c, name)
        return channel.allowedfreqrange

    @setting(48, 'Output', name='s', state='b', returns=' b')
    def output(self, c, name=None, state=None):
        """
        To turn off and on the dds. Turning off the DDS sets the frequency and amplitude
        to the off_parameters provided in the configuration.
        """
        if self.ddsLock and state is not None:
            raise dds_access_locked()
        channel = self._get_channel(c, name)
        if state is not None:
            yield self._set_output(channel, state)
            channel.state = state
            self.notify_other_listeners(c, (name, 'state', channel.state), self.on_dds_param)
        returnValue(channel.state)

    @setting(49, 'Clear DDS Lock')
    def clear_dds_lock(self, c):
        self.ddsLock = False

    def _check_range(self, t, channel, val):
        if t == 'amplitude':
            r = channel.allowedamplrange
        elif t == 'frequency':
            r = channel.allowedfreqrange
        if not r[0] <= val <= r[1]: raise Exception(
            "channel {0} : {1} of {2} is outside the allowed range".format(channel.name, t, val))

    def _get_channel(self, c, name):
        try:
            channel = self.ddsDict[name]
        except KeyError:
            raise Exception("Channel {0} not found".format(name))
        return channel

    @inlineCallbacks
    def _set_amplitude(self, channel, ampl):
        freq = channel.frequency
        yield self.inCommunication.run(self._set_parameters, channel, freq, ampl)

    @inlineCallbacks
    def _set_frequency(self, channel, freq):
        ampl = channel.amplitude
        yield self.inCommunication.run(self._set_parameters, channel, freq, ampl)

    @inlineCallbacks
    def _set_output(self, channel, state):
        if state and not channel.state:  # if turning on, and is currently off
            yield self.inCommunication.run(self._set_parameters, channel, channel.frequency, channel.amplitude)
        elif channel.state and not state:  # if turning off and is currenly on
            freq, ampl = channel.off_parameters
            yield self.inCommunication.run(self._set_parameters, channel, freq, ampl)

    @inlineCallbacks
    def _program_dds_sequence(self, dds):
        """takes the parsed dds sequence and programs the board with it"""
        self.ddsLock = True
        for name, channel in self.ddsDict.items():
            buf = dds[name]
            yield self.program_dds_chanel(channel, buf)

    @inlineCallbacks
    def _set_parameters(self, channel, freq, ampl):
        buf = self.settings_to_buf(channel, freq, ampl)
        yield self.program_dds_chanel(channel, buf)

    def settings_to_buf(self, channel, freq, ampl):
        num = self.settings_to_num(channel, freq, ampl)
        # if not channel.phase_coherent_model:
        #     buf = self._int(num)
        # else:
        buf = self._int_to_buf_coherent(num)
        # buf = buf + '\x00\x00' #adding termination
        # buf = bytearray.fromhex(u'0000') + buf
        # print buf
        return buf

    def settings_to_num(self, channel, freq, ampl, phase=0.0, ramp_rate=0.0, amp_ramp_rate=0.0):
        # if not channel.phase_coherent_model:
        #     num = self._valToInt(channel, freq, ampl)
        # else:
        num = self._val_to_int_coherent(channel, freq, ampl, phase, ramp_rate, amp_ramp_rate)
        return num

    @inlineCallbacks
    def program_dds_chanel(self, channel, buf):
        addr = channel.channelnumber
        if not channel.remote:
            yield deferToThread(self._set_dds_local, addr, buf)
        else:
            yield self._set_dds_remote(channel, addr, buf)

    def _set_dds_local(self, addr, buf):
        self.api.reset_all_dds()
        self.api.set_dds_channel(addr)
        self.api.program_dds(buf)

    @inlineCallbacks
    def _set_dds_remote(self, channel, addr, buf):
        cxn = self.remoteConnections[channel.remote]
        remote_info = self.remoteChannels[channel.remote]
        server, reset, program = remote_info.server, remote_info.reset, remote_info.program
        try:
            yield cxn.servers[server][reset]()
            yield cxn.servers[server][program]([(channel.channelnumber, buf)])
        except (KeyError, AttributeError):
            print('Not programing remote channel {}'.format(channel.remote))

    def _get_current_dds(self):
        """Returns a dictionary {name:num} with the representation of the current dds state"""
        d = dict([(name, self._channel_to_num(channel)) for (name, channel) in self.ddsDict.items()])
        return d

    def _channel_to_num(self, channel):
        """Returns the current state of the channel in the num representation"""
        if channel.state:
            # if on, use current values. else, use off values
            freq, ampl = (channel.frequency, channel.amplitude)
            self._check_range('amplitude', channel, ampl)
            self._check_range('frequency', channel, freq)
        else:
            freq, ampl = channel.off_parameters
        num = self.settings_to_num(channel, freq, ampl)
        return num

    def _val_to_int_coherent(self, channel, freq, ampl, phase=0.0, ramp_rate=0.0,
                             amp_ramp_rate=0.0):  # add ramp for ramping functionality
        """
        takes the frequency and amplitude values for the specific channel and returns integer representation of the dds setting
        freq is in MHz
        power is in dbm
        """
        ans = 0
        # changed the precision from 32 to 64 to handle super fine frequency tuning
        for val, r, m, precision in [(freq, channel.boardfreqrange, 1, 64), (ampl, channel.boardamplrange, 2 ** 64, 16),
                                     (phase, channel.boardphaserange, 2 ** 80, 16)]:
            minim, maxim = r
            resolution = (maxim - minim) / float(2 ** precision - 1)
            seq = int((val - minim) / resolution)  # sequential representation
            ans += m * seq

        # add ramp rate
        minim, maxim = channel.boardramprange
        resolution = (maxim - minim) / float(2 ** 16 - 1)
        if ramp_rate < minim:  # if the ramp rate is smaller than the minim, thenn treat it as no rampp
            seq = 0
        elif ramp_rate > maxim:
            seq = 2 ** 16 - 1
        else:
            seq = int((ramp_rate - minim) / resolution)

        ans += 2 ** 96 * seq

        # add amp ramp rate

        minim, maxim = channel.board_amp_ramp_range
        minim_slope = 1 / maxim
        maxim_slope = 1 / minim
        resolution = (maxim_slope - minim_slope) / float(2 ** 16 - 1)
        if amp_ramp_rate < minim:
            seq_amp_ramp = 0
        elif amp_ramp_rate > maxim:
            seq_amp_ramp = 1
        else:
            slope = 1 / amp_ramp_rate
            seq_amp_ramp = int(np.ceil((slope - minim_slope) / resolution))  # return ceiling of the number

        ans += 2 ** 112 * seq_amp_ramp

        return ans

        # ans = 0
        # for val,r,m, precision in [(freq,channel.boardfreqrange, 1, 32),
        #                            (ampl,channel.boardamplrange, 2 ** 32,  16),
        #                            (phase,channel.boardphaserange, 2 ** 48,  16)]:
        #     minim, maxim = r
        #     resolution = (maxim - minim) / float(2**precision - 1)
        #     seq = int((val - minim)/resolution) #sequential representation
        #     ans += m*seq
        # return ans

    def _int_to_buf_coherent(self, num):
        """
        takes the integer representing the setting and returns the buffer string for dds programming
        """
        # freq_num = (num % 2**32)*2**32
        freq_num = (num % 2 ** 64)  # change according to the new DDS which supports 64 bit tuning of the frequency.
        b = bytearray(8)  # initialize the byte array to sent to the pulser later
        for i in range(8):
            b[i] = (freq_num // (2 ** (i * 8))) % 256
            # print i, "=", (freq_num//(2**(i*8)))%256

        # phase
        phase_num = (num // 2 ** 80) % (2 ** 16)
        phase = bytearray(2)
        phase[0] = phase_num % 256
        phase[1] = (phase_num // 256) % 256

        # amplitude
        ampl_num = (num // 2 ** 64) % (2 ** 16)
        amp = bytearray(2)
        amp[0] = ampl_num % 256
        amp[1] = (ampl_num // 256) % 256

        # ramp rate. 16 bit tunability from roughly 116 Hz/ms to 7.5 MHz/ms
        ramp_rate = (num // 2 ** 96) % (2 ** 16)
        ramp = bytearray(2)
        ramp[0] = ramp_rate % 256
        ramp[1] = (ramp_rate // 256) % 256

        # amplitude ramp rate
        amp_ramp_rate = (num // 2 ** 112) % (2 ** 16)
        amp_ramp = bytearray(2)
        amp_ramp[0] = amp_ramp_rate % 256
        amp_ramp[1] = (amp_ramp_rate // 256) % 256

        # a = bytearray.fromhex(u'0000') + amp + bytearray.fromhex(u'0000 0000')
        a = phase + amp + amp_ramp + ramp

        ans = a + b
        return ans
