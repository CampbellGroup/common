# Created on Feb 22, 2012
# @author: Michael Ramm, Haeffner Lab
"""
### BEGIN NODE INFO
[info]
name = Pulser
version = 2.1
description =
instancename = Pulser

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.server import setting, Signal, LabradServer
from labrad.units import WithUnit
from twisted.internet import reactor
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred
from twisted.internet.threads import deferToThread
import time

try:
    from config.pulser.hardwareConfiguration import hardwareConfiguration
except ImportError:
    from common.lib.config.pulser.hardwareConfiguration import hardwareConfiguration

from sequence import Sequence
from errors import dds_access_locked
from api import API
import numpy as np


class Pulser(LabradServer):
    name = 'Pulser'
    onSwitch = Signal(611051, 'signal: switch toggled', '(ss)')
    on_dds_param = Signal(142006, 'signal: new dds parameter', '(ssv)')
    on_line_trigger_param = Signal(142007, 'signal: new line trigger parameter', '(bv)')

    # region Initialization functions
    ################################
    @inlineCallbacks
    def initServer(self):
        self.api = API()

        # load config from hardwareConfiguration
        self.channel_dict = hardwareConfiguration.channelDict
        self.collection_time = hardwareConfiguration.collectionTime
        self.collection_mode = hardwareConfiguration.collectionMode
        self.sequence_type = hardwareConfiguration.sequenceType
        self.is_programmed = hardwareConfiguration.isProgrammed
        self.time_resolution = float(hardwareConfiguration.timeResolution)
        self.dds_dict = hardwareConfiguration.ddsDict
        self.time_resolved_resolution = hardwareConfiguration.timeResolvedResolution
        self.remote_channels = hardwareConfiguration.remoteChannels
        self.collection_time_range = hardwareConfiguration.collectionTimeRange
        self.sequence_time_range = hardwareConfiguration.sequenceTimeRange
        self.have_second_pmt = hardwareConfiguration.secondPMT
        self.have_dac = hardwareConfiguration.DAC

        self.in_communication = DeferredLock()
        self.clear_next_pmt_counts = 0

        # line trigger settings
        self.linetrigger_enabled = False
        self.linetrigger_duration = WithUnit(0, 'us')
        self.linetrigger_limits = [WithUnit(v, 'us') for v in hardwareConfiguration.lineTriggerLimits]

        # initialize the board
        self.initialize_board()
        yield self.initialize_remote()
        self.initialize_ttl()
        yield self.initialize_dds()
        self.listeners = set()

        self.programmed_sequence = None

    def initialize_board(self):
        """connect to the OpalKelly FPGA board"""
        connected = self.api.connect_ok_board()
        if not connected:
            raise Exception("Pulser Not Found")

    def initialize_ttl(self):
        """set all TTLs to their initial settings"""
        for channel in iter(self.channel_dict.values()):
            channelnumber = channel.channelnumber
            if channel.ismanual:
                state = self.cnot(channel.manualinv, channel.manualstate)
                self.api.set_manual(channelnumber, state)
            else:
                self.api.set_auto(channelnumber, channel.autoinv)

    @inlineCallbacks
    def initialize_remote(self):
        """connect to any remote channels that are specified in the hardwareConfiguration"""
        self.remoteConnections = {}
        if len(self.remote_channels):
            from labrad.wrappers import connectAsync
            for name, rc in iter(self.remote_channels.items()):
                try:
                    self.remoteConnections[name] = yield connectAsync(rc.ip)
                    print('Connected to {}'.format(name))
                except Exception as e:
                    print('Not Able to connect to {}'.format(name))
                    print(e)
                    self.remoteConnections[name] = None

    @inlineCallbacks
    def initialize_dds(self):
        """
        Initializes the DDS boards
        """
        self.ddsLock = False
        self.api.initialize_dds()
        for name, channel in self.dds_dict.items():
            channel.name = name
            freq, ampl = (channel.frequency, channel.amplitude)
            self._check_range('amplitude', channel, ampl)
            self._check_range('frequency', channel, freq)
            yield self.in_communication.run(self._set_parameters, channel, freq, ampl)

    # endregion Initialization functions

    # region Sequence functions
    ##########################
    @setting(0, "New Sequence", returns='')
    def new_sequence(self, c):
        """Create a new empty pulse sequence"""
        c['sequence'] = Sequence(parent=self)

    @setting(1, "Program Sequence", returns='')
    def program_sequence(self, c, sequence):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        sequence = c.get('sequence')
        if not sequence:
            raise Exception("Please create new sequence first")
        self.programmed_sequence = sequence
        dds, ttl = sequence.prog_representation()
        yield self.in_communication.acquire()
        yield deferToThread(self.api.program_board, ttl)
        if dds is not None:
            yield self._program_dds_sequence(dds)
        self.in_communication.release()
        self.is_programmed = True

    @setting(2, "Start Infinite", returns='')
    def start_infinite(self, c):
        """
        Repeat the currently programmed pulse sequence running infinitely
        (until complete_infinite is called)
        """
        if not self.is_programmed:
            raise Exception("No programmed sequence")
        yield self.in_communication.acquire()
        yield deferToThread(self.api.set_number_repetitions, 0)
        yield deferToThread(self.api.reset_seq_counter)
        yield deferToThread(self.api.start_looped)
        self.sequence_type = 'Infinite'
        self.in_communication.release()

    @setting(3, "Complete Infinite Iteration", returns='')
    def complete_infinite(self, c):
        """
        Completes an infinitely repeating pulse sequence
        (started by start_infinite)
        """
        if self.sequence_type != 'Infinite':
            raise Exception("Not running infinite sequence")
        yield self.in_communication.acquire()
        yield deferToThread(self.api.start_single)
        self.in_communication.release()

    @setting(4, "Start Single", returns='')
    def start(self, c):
        """Start a single execution of the currently programmed pulse sequence"""
        if not self.is_programmed:
            raise Exception("No Programmed Sequence")
        yield self.in_communication.acquire()
        yield deferToThread(self.api.reset_seq_counter)
        yield deferToThread(self.api.start_single)
        self.sequence_type = 'One'
        self.in_communication.release()

    @setting(5, 'Add TTL Pulse', channel='s', start='v[s]', duration='v[s]')
    def add_ttl_pulse(self, c, channel, start, duration):
        """
        Add a TTL pulse to the pulse sequence, times are in seconds
        :param channel: the TTL channel to add
        :param start: the start of the pulse
        :param duration: the duration of the pulse
        """
        if channel not in self.channel_dict.keys():
            raise Exception("Unknown Channel {}".format(channel))
        hardware_addr = self.channel_dict.get(channel).channelnumber
        sequence = c.get('sequence')
        start = start['s']
        duration = duration['s']
        # simple error checking
        if not ((self.sequence_time_range[0] <= start <= self.sequence_time_range[1]) and (
                self.sequence_time_range[0] <= start + duration <= self.sequence_time_range[1])):
            raise Exception("Time boundaries are out of range")
        if not duration >= self.time_resolution:
            raise Exception("Incorrect duration")
        if not sequence:
            raise Exception("Please create new sequence first")
        sequence.add_pulse(hardware_addr, start, duration)

    @setting(6, 'Add TTL Pulses', pulses='*(sv[s]v[s])')
    def add_ttl_pulses(self, c, pulses):
        """
        Add multiple TTL Pulses to the sequence, times are in seconds.
        The pulses are a list in the same format as 'add ttl pulse'.
        """
        for pulse in pulses:
            channel = pulse[0]
            start = pulse[1]
            duration = pulse[2]
            yield self.add_ttl_pulse(c, channel, start, duration)

    @setting(7, "Extend Sequence Length", time_length='v[s]')
    def extend_sequence_length(self, c, time_length):
        """
        Allows to optionally extend the total length of the sequence beyond the last TTL pulse.
        :param time_length: the amount to extend the sequence by in seconds
        """
        sequence = c.get('sequence')
        if not (self.sequence_time_range[0] <= time_length['s'] <= self.sequence_time_range[1]):
            raise Exception("Time boundaries are out of range")
        if not sequence:
            raise Exception("Please create new sequence first")
        sequence.extend_sequence_length(time_length['s'])

    @setting(8, "Stop Sequence")
    def stop_sequence(self, c):
        """Stops any currently running sequence"""
        yield self.in_communication.acquire()
        yield deferToThread(self.api.reset_ram)
        if self.sequence_type == 'Infinite':
            yield deferToThread(self.api.stop_looped)
        elif self.sequence_type == 'One':
            yield deferToThread(self.api.stop_single)
        elif self.sequence_type == 'Number':
            yield deferToThread(self.api.stop_looped)
        self.in_communication.release()
        self.sequence_type = None
        self.ddsLock = False

    @setting(9, "Start Number", repetition='w')
    def start_number(self, c, repetition):
        """
        Executes the currently programmed pulse sequence some number of times
        :param repetition: the number of repetitions to run
        """
        if not self.is_programmed:
            raise Exception("No programmed sequence")

        if not 1 <= repetition <= (2 ** 16 - 1):
            raise Exception("Incorrect number of pulses")
        yield self.in_communication.acquire()
        yield deferToThread(self.api.set_number_repetitions, repetition)
        yield deferToThread(self.api.reset_seq_counter)
        yield deferToThread(self.api.start_looped)
        self.sequence_type = 'Number'
        self.in_communication.release()

    @setting(10, "Human Readable TTL", get_programmed='b', returns='*2s')
    def human_readable_ttl(self, c, get_programmed=False):
        """
        Returns a human-readable representation of TTLs in the programmed sequence
        :param get_programmed: bool. False (default) to get the sequence added by current context,
                                     True to get the last programmed sequence
        """
        sequence = c.get('sequence')
        if get_programmed:
            sequence = self.programmed_sequence
        if not sequence:
            raise Exception("Please create new sequence first")
        ttl, dds = sequence.human_representation()
        return ttl.tolist()

    @setting(11, "Human Readable DDS", get_programmed='b', returns='*(svv)')
    def human_readable_dds(self, c, get_programmed=False):
        """
        Returns a human-readable representation of DDSes in the programmed sequence
        :param get_programmed: bool. False(default) to get the sequence added by current context,
                                     True to get the last programmed sequence
        """
        sequence = c.get('sequence')
        if get_programmed:
            sequence = self.programmed_sequence
        if not sequence:
            raise Exception("Please create new sequence first")
        ttl, dds = sequence.human_representation()
        return dds

    @setting(16, 'Wait Sequence Done', timeout='v', returns='b')
    def wait_sequence_done(self, c, timeout=None):
        """Returns True if the sequence has completed within a timeout period"""
        if timeout is None:
            timeout = self.sequence_time_range[1]
        request_calls = int(timeout / 0.001)  # number of request calls
        for i in range(request_calls):
            yield self.in_communication.acquire()
            done = yield deferToThread(self.api.is_seq_done)
            self.in_communication.release()
            if done:
                returnValue(True)
            yield self.wait(0.001)
        returnValue(False)

    @setting(17, 'Repetitions Completed', returns='w')
    def repetitions_completed(self, c):
        """Returns how many repetitions have been completed in for the infinite or number modes"""
        yield self.in_communication.acquire()
        completed = yield deferToThread(self.api.how_many_sequences_done)
        self.in_communication.release()
        returnValue(completed)

    # endregion Sequence functions

    # region TTL Functions
    #####################
    @setting(12, 'Get Channels', returns='*(sw)')
    def get_channels(self, c):
        """Returns a list of all available channels, and the corresponding hardware numbers"""
        d = self.channel_dict
        keys = d.keys()
        numbers = [d[key].channelnumber for key in keys]
        return list(zip(keys, numbers))

    @setting(13, 'Switch Manual', channel_name='s', state='b')
    def switch_manual(self, c, channel_name, state=None):
        """
        Switches the given channel into the manual mode.
        By default, it will go into the last remembered state, but you can also pass the
        argument which state it should go into.
        :param channel_name: the channel to be switched
        :keyword param state: the state that the switch should return to
        """
        if channel_name not in self.channel_dict.keys():
            raise Exception("Incorrect Channel")
        channel = self.channel_dict[channel_name]
        channel_number = channel.channelnumber
        channel.ismanual = True
        if state is not None:
            channel.manualstate = state
        else:
            state = channel.manualstate
        yield self.in_communication.acquire()
        yield deferToThread(self.api.set_manual, channel_number, self.cnot(channel.manualinv, state))
        self.in_communication.release()
        if state:
            self.notify_other_listeners(c, (channel_name, 'ManualOn'), self.onSwitch)
        else:
            self.notify_other_listeners(c, (channel_name, 'ManualOff'), self.onSwitch)

    @setting(14, 'Switch Auto', channel_name='s', invert='b')
    def switch_auto(self, c, channel_name, invert=None):
        """
        Switches the given channel into the automatic mode, with an optional inversion.
        :param channel_name: the channel to be switched
        :param invert: whether to invert the state of the ttl
        """
        if channel_name not in self.channel_dict.keys():
            raise Exception("Incorrect Channel")
        channel = self.channel_dict[channel_name]
        channel_number = channel.channelnumber
        channel.ismanual = False
        if invert is not None:
            channel.autoinv = invert
        else:
            invert = channel.autoinv
        yield self.in_communication.acquire()
        yield deferToThread(self.api.set_auto, channel_number, invert)
        self.in_communication.release()
        self.notify_other_listeners(c, (channel_name, 'Auto'), self.onSwitch)

    @setting(15, 'Get State', channel_name='s', returns='(bbbb)')
    def get_state(self, c, channel_name):
        """
        Returns the current state of the switch: in the form
        (Manual/Auto, ManualOn/Off, ManualInversionOn/Off, AutoInversionOn/Off)
        """
        if channel_name not in self.channel_dict.keys():
            raise Exception("Incorrect Channel")
        channel = self.channel_dict[channel_name]
        answer = (channel.ismanual, channel.manualstate, channel.manualinv, channel.autoinv)
        return answer

    # endregion TTL Functions

    # region DDS functions
    ######################

    @setting(41, "Get DDS Channels", returns='*s')
    def get_dds_channels(self, c):
        """get the list of available channels"""
        return list(self.dds_dict.keys())

    @setting(43, "Amplitude", name='s', amplitude='v[dBm]', returns='v[dBm]')
    def amplitude(self, c, name=None, amplitude=None):
        """
        Get or set the amplitude of the named channel or the selected channel
        :param name: the name of the DDS in question
        :param amplitude: If specified, the amplitude will be set to this value.
                          If left blank, the current amplitude will be returned
        """
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
        """
        Get or set the frequency of the named channel or the selected channel
        :param name: the name of the DDS in question
        :param frequency: If specified, the frequency will be set to this value.
                          If left blank, the current frequency will be returned
        """
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
        Add DDS pulses to the pulse sequence
        :param values: these should be input in the form of a list of tuples:
        [(name, start, duration, frequency, amplitude, phase, ramp_rate, amp_ramp_rate)]
        NOTE:
        ramp_rate is in MHz/ms (even though it wants to be passed in as just MHz)
        amp_ramp_rate is in dB/ms (even though it wants to be passed in as just dB)
        """
        sequence = c.get('sequence')
        if not sequence:
            raise Exception("Please create new sequence first")
        for value in values:
            try:
                name, start, dur, freq, ampl = value
                phase = 0.0
                ramp_rate = 0.0
                amp_ramp_rate = 0.0
            except ValueError:
                name, start, dur, freq, ampl, phase, ramp_rate, amp_ramp_rate = value
            try:
                channel = self.dds_dict[name]
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
            if not self.sequence_time_range[0] < start <= self.sequence_time_range[1]:
                raise Exception(
                    "DDS start time out of acceptable input range for channel {0} at time {1}".format(name,
                                                                                                      start))
            if not self.sequence_time_range[0] < start + dur <= self.sequence_time_range[1]:
                raise Exception(
                    "DDS start time out of acceptable input range for channel {0} at time {1}".format(name,
                                                                                                      start + dur))
            if not dur == 0:  # 0-length pulses are ignored
                sequence.add_dds(name, start, num, 'start')
                sequence.add_dds(name, start + dur, num_off, 'stop')

    @setting(46, 'Get DDS Amplitude Range', name='s', returns='(vv)')
    def get_dds_ampl_range(self, c, name=None):
        """Returns the allowed amplitude range of the DDS"""
        channel = self._get_channel(c, name)
        return channel.allowedamplrange

    @setting(47, 'Get DDS Frequency Range', name='s', returns='(vv)')
    def get_dds_freq_range(self, c, name=None):
        """Returns the allowed frequency range of the DDS"""
        channel = self._get_channel(c, name)
        return channel.allowedfreqrange

    @setting(48, 'Output', name='s', state='b', returns=' b')
    def output(self, c, name=None, state=None):
        """
        To turn off and on the dds. Turning off the DDS sets the frequency and amplitude
        to the off_parameters provided in the configuration.

        If no state is provided, just returns the current state of the DDS
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
        """Clears the dds lock"""
        self.ddsLock = False

    def _check_range(self, t, channel, val):
        """Checks whether the current channel is valid given the config."""
        r = None
        if t == 'amplitude':
            r = channel.allowedamplrange
        elif t == 'frequency':
            r = channel.allowedfreqrange
        if not r[0] <= val <= r[1]:
            raise Exception("channel {0} : {1} of {2} is outside the allowed range".format(channel.name, t, val))

    def _get_channel(self, c, name):
        try:
            channel = self.dds_dict[name]
        except KeyError:
            raise Exception("Channel {0} not found".format(name))
        return channel

    @inlineCallbacks
    def _set_amplitude(self, channel, ampl):
        freq = channel.frequency
        yield self.in_communication.run(self._set_parameters, channel, freq, ampl)

    @inlineCallbacks
    def _set_frequency(self, channel, freq):
        ampl = channel.amplitude
        yield self.in_communication.run(self._set_parameters, channel, freq, ampl)

    @inlineCallbacks
    def _set_output(self, channel, state):
        if state and not channel.state:  # if turning on, and is currently off
            yield self.in_communication.run(self._set_parameters, channel, channel.frequency, channel.amplitude)
        elif channel.state and not state:  # if turning off and is currenly on
            freq, ampl = channel.off_parameters
            yield self.in_communication.run(self._set_parameters, channel, freq, ampl)

    @inlineCallbacks
    def _program_dds_sequence(self, dds):
        """takes the parsed dds sequence and programs the board with it"""
        self.ddsLock = True
        for name, channel in self.dds_dict.items():
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
        buf = self.int_to_buf_coherent(num)
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

    # noinspection PyUnresolvedReferences
    @inlineCallbacks
    def _set_dds_remote(self, channel, addr, buf):
        cxn = self.remoteConnections[channel.remote]
        remote_info = self.remote_channels[channel.remote]
        server, reset, program = remote_info.server, remote_info.reset, remote_info.program
        try:
            yield cxn.servers[server][reset]()
            yield cxn.servers[server][program]([(channel.channelnumber, buf)])
        except (KeyError, AttributeError):
            print('Not programing remote channel {}'.format(channel.remote))

    def get_current_dds(self):
        """Returns a dictionary {name:num} with the representation of the current dds state"""
        d = dict([(name, self._channel_to_num(channel)) for (name, channel) in self.dds_dict.items()])
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

    def _val_to_int_coherent(self, channel, freq, ampl, phase=0.0, ramp_rate=0.0, amp_ramp_rate=0.0):
        # add ramp for ramping functionality
        """
        takes the frequency and amplitude values for the specific channel and returns
        integer representation of the dds setting
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

    def int_to_buf_coherent(self, num):
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

    # endregion DDS functions

    # region PMT functions
    #####################

    @setting(21, 'Set Mode', mode='s', returns='')
    def set_mode(self, c, mode):
        """
        Set the counting mode, either 'Normal' or 'Differential'
        In the Normal Mode, the FPGA automatically sends the counts with a preset frequency
        In the differential mode, the FPGA uses triggers the pulse sequence
        frequency and to know when the repumping light is switched on or off.
        """
        if mode not in self.collection_time.keys():
            raise ValueError("Incorrect mode")
        self.collection_mode = mode
        count_rate = self.collection_time[mode]
        yield self.in_communication.acquire()
        if mode == 'Normal':
            # set the mode on the device and set update time for normal mode
            yield deferToThread(self.api.set_mode_normal)
            yield deferToThread(self.api.set_pmt_count_rate, count_rate)
        elif mode == 'Differential':
            yield deferToThread(self.api.set_mode_differential)
        self.clear_next_pmt_counts = 3  # assign to clear next two counts
        self.in_communication.release()

    @setting(22, 'Set Collection Time', new_time='v', mode='s', returns='')
    def set_collect_time(self, c, new_time, mode):
        """
        Sets how long to collect photons list in either 'Normal' or 'Differential' mode of operation
        """
        new_time = new_time['s']
        if not self.collection_time_range[0] <= new_time <= self.collection_time_range[1]:
            raise ValueError('incorrect collection time')
        if mode not in self.collection_time.keys():
            raise ValueError("Incorrect mode")
        if mode == 'Normal':
            self.collection_time[mode] = new_time
            yield self.in_communication.acquire()
            yield deferToThread(self.api.set_pmt_count_rate, new_time)
            self.clear_next_pmt_counts = 3  # assign to clear next two counts
            self.in_communication.release()
        elif mode == 'Differential':
            self.collection_time[mode] = new_time
            self.clear_next_pmt_counts = 3  # assign to clear next two counts

    @setting(23, 'Get Collection Time', returns='(vv)')
    def get_collect_time(self, c):
        """Returns the current PMT collection time"""
        return self.collection_time_range

    @setting(24, 'Reset FIFO Normal', returns='')
    def reset_fifo_normal(self, c):
        """
        Resets the FIFO on board, deleting all queued counts
        """
        yield self.in_communication.acquire()
        yield deferToThread(self.api.reset_fifo_normal)
        self.in_communication.release()

    @setting(25, 'Get PMT Counts', returns='*(vsv)')
    def get_all_counts(self, c):
        """
        Returns the list of counts stored on the FPGA in the form (v,s1,s2) where v is the count rate in KC/SEC
        and s can be 'ON' in normal mode or in Differential mode with 866 on and 'OFF' for differential
        mode when 866 is off. s2 is the approximate time of acquisition.
        NOTE: For some reason, FPGA ReadFromBlockPipeOut never times out, so can not implement requesting more packets
        than currently stored because it may hang the device.
        """
        yield self.in_communication.acquire()
        countlist = yield deferToThread(self.do_get_all_counts)
        self.in_communication.release()
        returnValue(countlist)

    @setting(26, 'Get Readout Counts', returns='*v')
    def get_readout_counts(self, c):
        """Returns a list of readout counts from the PMT"""
        yield self.in_communication.acquire()
        countlist = yield deferToThread(self.do_get_readout_counts)
        self.in_communication.release()
        returnValue(countlist)

    def do_get_readout_counts(self):
        """Returns a list of readout counts from the PMT"""
        in_fifo = self.api.get_readout_total()
        reading = self.api.get_readout_counts(in_fifo)
        split = self.split_len(reading, 4)
        countlist = list(map(self.info_from_buf_readout, split))
        return countlist

    @setting(27, 'Reset Readout Counts')
    def reset_readout_counts(self, c):
        """Resets the readout counts in the FIFO buffer"""
        yield self.in_communication.acquire()
        yield deferToThread(self.api.reset_fifo_readout)
        self.in_communication.release()

    def do_get_all_counts(self):
        """
        # TODO: what does this do?
        """
        in_fifo = self.api.get_normal_total()
        reading = self.api.get_normal_counts(in_fifo)
        split = self.split_len(reading, 4)
        countlist = map(self.info_from_buf, split)
        countlist = map(self.convert_kc_per_sec, countlist)
        countlist = self.append_times(countlist, time.time())
        countlist = self.clear_pmt_counts(countlist)
        return countlist

    def clear_pmt_counts(self, inp_list):
        """removes clear_next_pmt_counts count from the list"""
        inp_list = list(inp_list)
        try:
            while self.clear_next_pmt_counts:
                cleared = inp_list.pop(0)
                self.clear_next_pmt_counts -= 1
            return inp_list
        except IndexError:
            return []

    def info_from_buf(self, buf):
        """
        converts the received buffer into useful information
        the most significant digit of the buffer indicates whether 866 is on or off
        """
        count = self.info_from_buf_readout(buf)
        if count >= 2 ** 31:
            status = 'OFF'
            count = count % 2 ** 31
        else:
            status = 'ON'
        return [count, status]

    @staticmethod
    def info_from_buf_readout(buf):
        """
        converts the value in the FIFO buffer to a usable count
        """
        count = 65536 * (256 * buf[1] + buf[0]) + (256 * buf[3] + buf[2])
        return count

    def convert_kc_per_sec(self, inp):
        """converts raw PMT counts into kC/s, using the collection time and collection mode"""
        [raw_count, typ] = inp
        count_kc_per_sec = float(raw_count) / self.collection_time[self.collection_mode] / 1000.
        return [count_kc_per_sec, typ]

    def append_times(self, inp_list, time_last):
        """
        in the case that we received multiple PMT counts, uses the current time
        and the collection time to guess the arrival time of the previous readings
        i.e ( [[1,2],[2,3]] , timeLAst = 1.0, normalupdatetime = 0.1) -> ( [(1,2,0.9),(2,3,1.0)])
        """
        collection_time = self.collection_time[self.collection_mode]
        inp_list = list(inp_list)
        for i in range(len(inp_list)):
            inp_list[-i - 1].append(time_last - i * collection_time)
            inp_list[-i - 1] = tuple(inp_list[-i - 1])
        return inp_list

    def split_len(self, seq, length):
        """splits an iterable into length-long pieces"""
        return [seq[i:i + length] for i in range(0, len(seq), length)]

    @setting(28, 'Get Collection Mode', returns='s')
    def get_mode(self, c):
        """returns the collection mode (normal or differential)"""
        return self.collection_mode

    # endregion PMT functions

    # region debugging settings
    ##########################
    @setting(90, 'Internal Reset DDS', returns='')
    def internal_reset_dds(self, c):
        """resets all  DDSes"""
        yield self.in_communication.acquire()
        yield deferToThread(self.api.reset_all_dds)
        self.in_communication.release()

    @setting(91, 'Internal Advance DDS', returns='')
    def internal_advance_dds(self, c):
        """advances all DDSes"""
        yield self.in_communication.acquire()
        yield deferToThread(self.api.advance_all_dds)
        self.in_communication.release()

    @setting(92, "Reinitialize DDS", returns='')
    def reinitialize_dds(self, c):
        """Reprograms the DDS chip to its initial state"""
        yield self.in_communication.acquire()
        yield deferToThread(self.api.initialize_dds)
        self.in_communication.release()

    # endregion debugging settings

    # region Timetagging functions
    #############################

    @setting(31, "Reset Timetags")
    def reset_timetags(self, c):
        """Reset the time resolved FIFO to clear any residual timetags"""
        yield self.in_communication.acquire()
        yield deferToThread(self.api.reset_fifo_resolved)
        self.in_communication.release()

    @setting(32, "Get Timetags", returns='*v')
    def get_timetags(self, c):
        """Get the time resolved timetags"""
        yield self.in_communication.acquire()
        counted = yield deferToThread(self.api.get_resolved_total)
        raw = yield deferToThread(self.api.get_resolved_counts, counted)
        self.in_communication.release()
        # noinspection PyArgumentList
        arr = np.frombuffer(raw, dtype=np.uint16)
        del raw
        arr = arr.reshape(-1, 2)
        timetags = (65536 * arr[:, 0] + arr[:, 1]) * self.time_resolved_resolution
        returnValue(timetags)

    @setting(33, "Get TimeTag Resolution", returns='v')
    def get_time_tag_resolution(self, c):
        """Returns the timetag resolution"""
        return self.time_resolved_resolution

    # endregion Timetagging functions

    # region Line Trigger functions
    @setting(60, "Get Line Trigger Limits", returns='*v[us]')
    def get_line_trigger_limits(self, c):
        """get limits for duration of line triggering"""
        return self.linetrigger_limits

    @setting(61, 'Line Trigger State', enable='b', returns='b')
    def line_trigger_state(self, c, enable=None):
        """
        if the "enable" parameter is specified, disables/enables the line trigger
        otherwise, returns whether line triggering is active
        """
        if enable is not None:
            if enable:
                yield self.in_communication.run(self._enable_line_trigger, self.linetrigger_duration)
            else:
                yield self.in_communication.run(self._disable_line_trigger)
            self.linetrigger_enabled = enable
            self.notify_other_listeners(c, (self.linetrigger_enabled, self.linetrigger_duration),
                                        self.on_line_trigger_param)
        returnValue(self.linetrigger_enabled)

    @setting(62, "Line Trigger Duration", duration='v[us]', returns='v[us]')
    def line_trigger_duration(self, c, duration=None):
        """enable or disable line triggering. if enabling, can specify the offset_duration"""
        if duration is not None:
            if self.linetrigger_enabled:
                yield self.in_communication.run(self._enable_line_trigger, duration)
            self.linetrigger_duration = duration
            self.notify_other_listeners(c, (self.linetrigger_enabled, self.linetrigger_duration),
                                        self.on_line_trigger_param)
        returnValue(self.linetrigger_duration)

    @inlineCallbacks
    def _enable_line_trigger(self, delay):
        """enables the line trigger"""
        delay = int(delay['us'])
        yield deferToThread(self.api.enable_line_trigger, delay)

    @inlineCallbacks
    def _disable_line_trigger(self):
        """disables the line trigger"""
        yield deferToThread(self.api.disable_line_trigger)
    # endregion Line Trigger functions

    # Methods relating to using the optional second PMT
    # The secondary PMT is not implemented anywhere. So no need for these methods.
    # The functions it points to in the API are also commented out

    # @setting(36, 'Get Secondary PMT Counts', returns='*(vsv)')
    # def get_all_secondary_counts(self, c):
    #     if not self.haveSecondPMT:
    #         raise Exception("No Second PMT")
    #     yield self.inCommunication.acquire()
    #     countlist = yield deferToThread(self.do_get_all_secondary_counts)
    #     self.inCommunication.release()
    #     returnValue(countlist)

    # def do_get_all_secondary_counts(self):
    #     if not self.haveSecondPMT:
    #         raise Exception("No Second PMT")
    #     inFIFO = self.api.get_secondary_normal_total()
    #     reading = self.api.get_secondary_normal_counts(inFIFO)
    #     split = self.split_len(reading, 4)
    #     countlist = map(self.info_from_buf, split)
    #     countlist = map(self.convert_k_cper_sec, countlist)
    #     countlist = self.append_times(countlist, time.time())
    #     return countlist

    def wait(self, seconds, result=None):
        """Returns a deferred that will be fired later"""
        d = Deferred()
        # noinspection PyUnresolvedReferences
        reactor.callLater(seconds, d.callback, result)
        return d

    def cnot(self, control: bool, inp: bool) -> bool:
        """Inverts inp, dependent on the value of control"""
        if control:
            inp = not inp
        return inp

    def notify_other_listeners(self, context, message, f):
        """Notifies all listeners except the one in the given context, executing function f"""
        notified = self.listeners.copy()
        notified.remove(context.ID)
        f(message, notified)

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)


if __name__ == "__main__":
    from labrad import util

    util.runServer(Pulser())
