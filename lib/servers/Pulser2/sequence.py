import numpy
import array

try:
    from config.pulser.hardwareConfiguration import hardwareConfiguration
except ImportError:
    from common.lib.config.pulser.hardwareConfiguration import hardwareConfiguration

from decimal import Decimal


class Sequence:
    """Sequence for programming pulses"""
    def __init__(self, parent):
        self.parent = parent
        self.channelTotal = hardwareConfiguration.channelTotal
        self.timeResolution = Decimal(hardwareConfiguration.timeResolution)
        self.MAX_SWITCHES = hardwareConfiguration.maxSwitches
        self.resetstepDuration = hardwareConfiguration.resetstepDuration
        # dictionary in the form time:which channels to switch
        # time is expressed as timestep with the given resolution
        # which channels to switch is a channelTotal-long array with 1 to switch ON, -1 to switch OFF, 0 to do nothing
        self.switchingTimes = {0: numpy.zeros(self.channelTotal, dtype=numpy.int8)}
        self.switches = 1  # keeps track of how many switches are to be performed
        # (same as the number of keys in the switching Times dictionary
        #  for storing information about dds switches, in the format:
        # timestep: {channel_name: integer representing the state}
        self.ddsSettingList = []
        self.advanceDDS = hardwareConfiguration.channelDict['AdvanceDDS'].channelnumber
        self.resetDDS = hardwareConfiguration.channelDict['ResetDDS'].channelnumber

    def add_dds(self, name, start, num, typ):
        time_step = self.sec_to_step(start)
        self.ddsSettingList.append((name, time_step, num, typ))

    def add_pulse(self, channel, start, duration):
        """adding TTL pulse, times are in seconds"""
        start = self.sec_to_step(start)
        duration = self.sec_to_step(duration)
        self._add_new_switch(start, channel, 1)
        self._add_new_switch(start + duration, channel, -1)

    def extend_sequence_length(self, time_length):
        """Allows to extend the total length of the sequence"""
        time_length = self.sec_to_step(time_length)
        self._add_new_switch(time_length, 0, 0)

    def sec_to_step(self, sec):
        """converts seconds to time steps"""
        start = '{0:.9f}'.format(sec)  # round to nanoseconds
        start = Decimal(start)  # convert to decimal
        step = (start / self.timeResolution).to_integral_value()
        step = int(step)
        return step

    def num_to_hex(self, number):
        """converts the number to the hex representation for a total of 32 bits"""
        number = int(number)
        b = bytearray(4)
        b[2] = number % 256
        b[3] = (number//256) % 256
        b[0] = (number//65536) % 256
        b[1] = (number//16777216) % 256
        return b

    def _add_new_switch(self, time_step, chan, value):
        if time_step in self.switchingTimes:
            if self.switchingTimes[time_step][chan]:  # checks if 0 or 1/-1
                # if set to turn off, but want on, replace with zero, fixes error adding 2 TTLs back to back
                if self.switchingTimes[time_step][chan] * value == -1:
                    self.switchingTimes[time_step][chan] = 0
                else:
                    raise Exception('Double switch at time {} for channel {}'.format(time_step, chan))
            else:
                self.switchingTimes[time_step][chan] = value
        else:
            if self.switches == self.MAX_SWITCHES:
                raise Exception("Exceeded maximum number of switches {}".format(self.switches))
            self.switchingTimes[time_step] = numpy.zeros(self.channelTotal, dtype=numpy.int8)
            self.switches += 1
            self.switchingTimes[time_step][chan] = value

    def prog_representation(self, parse=True):
        if parse:
            self.ddsSettings = self.parse_dds()
            self.ttlProgram = self.parse_ttl()
        return self.ddsSettings, self.ttlProgram

    def user_added_dds(self):
        return bool(len(self.ddsSettingList))

    def parse_dds(self):
        if not self.user_added_dds():
            return None
        state = self.parent.get_current_dds()
        pulses_end = {}.fromkeys(state, (0, 'stop'))  # time / boolean whether in a middle of a pulse
        dds_program = {}.fromkeys(state, bytearray())
        last_time = 0
        start = None
        entries = sorted(self.ddsSettingList, key=lambda t: t[1])  # sort by starting time
        possible_error = (0, '')
        while True:
            try:
                name, start, num, typ = entries.pop(0)
            except IndexError:
                if start == last_time:
                    # still have unprogrammed entries
                    self.add_to_program(dds_program, state)
                    self._add_new_switch(last_time, self.advanceDDS, 1)
                    self._add_new_switch(last_time + self.resetstepDuration, self.advanceDDS, -1)
                # add termination
                for name in dds_program.keys():
                    dds_program[name] += b'\x00\x00'
                # at the end of the sequence, reset dds
                last_ttl = max(self.switchingTimes.keys())
                self._add_new_switch(last_ttl, self.resetDDS, 1)
                self._add_new_switch(last_ttl + self.resetstepDuration, self.resetDDS, -1)
                return dds_program
            end_time, end_typ = pulses_end[name]
            if start > last_time:
                # the time has advanced, so need to program the previous state
                if possible_error[0] == last_time and len(possible_error[1]):
                    raise Exception(possible_error[1])  # if error exists and belongs to that time
                self.add_to_program(dds_program, state)
                if not last_time == 0:
                    self._add_new_switch(last_time, self.advanceDDS, 1)
                    self._add_new_switch(last_time + self.resetstepDuration, self.advanceDDS, -1)
                last_time = start
            if start == end_time:
                # overwrite only when extending pulse
                if end_typ == 'stop' and typ == 'start':
                    possible_error = (0, '')
                    state[name] = num
                    pulses_end[name] = (start, typ)
                elif end_typ == 'start' and typ == 'stop':
                    possible_error = (0, '')
            elif end_typ == typ:
                possible_error = (start, 'Found Overlap Of Two Pules for channel {}'.format(name))
                state[name] = num
                pulses_end[name] = (start, typ)
            else:
                state[name] = num
                pulses_end[name] = (start, typ)

    def add_to_program(self, prog, state):
        for name, num in state.items():
            # if not hardwareConfiguration.ddsDict[name].phase_coherent_model:
            #     buf = self.parent._intToBuf(num)
            # else:
            buf = self.parent.int_to_buf_coherent(num)
            prog[name] += buf

    def parse_ttl(self):
        """Returns the representation of the sequence for programming the FPGA"""
        rep = bytearray()
        last_channels = numpy.zeros(self.channelTotal)
        power_array = 2**numpy.arange(self.channelTotal, dtype=numpy.uint64)
        for key, new_channels in sorted(self.switchingTimes.items()):
            channels = last_channels + new_channels  # computes the action of switching on the state
            if (channels < 0).any():
                raise Exception('Trying to switch off channel that is not already on')
            channel_int = numpy.dot(channels, power_array)
            # convert the new state to hex and adds it to the sequence
            rep = rep + self.num_to_hex(key) + self.num_to_hex(channel_int)
            last_channels = channels
        rep = rep + 2 * self.num_to_hex(0)  # adding termination
        return rep

    def human_representation(self):
        """Returns the human-readable version of the sequence for FPGA for debugging"""
        dds, ttl = self.prog_representation(parse=False)
        ttl = self.ttl_human_representation(ttl)
        dds = self.dds_human_representation(dds)
        return ttl, dds

    def dds_human_representation(self, dds):
        program = []
        print(dds)
        for name, buf in dds.items():
            arr = array.array('B', buf)
            arr = arr[:-2]  # remove termination
            channel = hardwareConfiguration.ddsDict[name]
            coherent = channel.phase_coherent_model
            freq_min, freq_max = channel.boardfreqrange
            ampl_min, ampl_max = channel.boardamplrange

            def chunks(arr, n):
                """ Yield successive n-sized chunks from arr."""
                for i in range(0, len(arr), n):
                    yield arr[i:i + n]
            if not coherent:
                for a, b, c, d in chunks(arr, 4):
                    freq_num = (256*b + a)
                    ampl_num = (256*d + c)
                    freq = freq_min + freq_num * (freq_max - freq_min) / float(16**4 - 1)
                    ampl = ampl_min + ampl_num * (ampl_max - ampl_min) / float(16**4 - 1)
                    program.append((name, freq, ampl))
            else:
                for a0, a1, amp0, amp1, a2, a3, a4, a5, f0, f1, f2, f3, f4, f5, f6, f7, in chunks(arr, 16):
                    freq_num = 256**2*(256*f7 + f6) + (256*f5 + f4)
                    ampl_num = 256*amp1 + amp0
                    freq = freq_min + freq_num * (freq_max - freq_min) / float(16**8 - 1)
                    ampl = ampl_min + ampl_num * (ampl_max - ampl_min) / float(16**4 - 1)
                    program.append((name, freq, ampl))
        return program

    def ttl_human_representation(self, rep):
        rep = str(rep)  # recast rep from bytearray into string
        # noinspection PyArgumentList
        arr = numpy.fromstring(rep, dtype=numpy.uint16)  # does the decoding from the string
        # arr = numpy.frombuffer(rep, dtype = numpy.uint16)
        arr = numpy.array(arr, dtype=numpy.uint32)  # once decoded, need to be able to manipulate large numbers
        # arr = numpy.array(rep,dtype = numpy.uint16)
        arr = arr.reshape(-1, 4)
        times = (65536 * arr[:, 0] + arr[:, 1]) * float(self.timeResolution)
        channels = (65536 * arr[:, 2] + arr[:, 3])

        def expand_channel(ch):
            """function for getting the binary representation, i.e 2**32 is 1000...0"""
            expand = bin(ch)[2:].zfill(32)
            reverse = expand[::-1]
            return reverse

        channels = map(expand_channel, channels)
        return numpy.vstack((times, channels)).transpose()
