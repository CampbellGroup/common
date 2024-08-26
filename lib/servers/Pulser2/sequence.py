import numpy
import array
from typing import Union, Tuple, Dict, List

try:
    from config.pulser_config import PulserConfiguration
except ImportError:
    from common.lib.config.pulser_config import PulserConfiguration

from decimal import Decimal


class Sequence:
    """Sequence for programming pulses"""

    def __init__(self, parent):
        self.parent = parent

        self.ttl_channel_count = PulserConfiguration.ttl_channel_total
        self.time_resolution = Decimal(PulserConfiguration.time_resolution)
        self.max_switches = PulserConfiguration.max_switches
        self.reset_step_duration = PulserConfiguration.reset_step_duration
        # dictionary in the form "time:switches"
        # "time" is expressed as timestep with the given resolution
        # "switches" is a ttl_channel_count-long array with 1 to switch ON, -1 to switch OFF, 0 to do nothing
        self.ttl_switching_times = {
            0: numpy.zeros(self.ttl_channel_count, dtype=numpy.int8)
        }
        # same as the number of keys in the ttl_switching_times dictionary
        self.ttl_switches = 1  # keeps track of how many switches are to be performed
        # for storing information about dds switches, in the format:
        # timestep: {channel_name: integer representing the state}
        self.dds_setting_list = []

        self.advance_dds = PulserConfiguration.ttl_channel_dict[
            "AdvanceDDS"
        ].channel_number
        self.reset_dds = PulserConfiguration.ttl_channel_dict["ResetDDS"].channel_number

    def add_dds_pulse(self, name: str, start: float, num, typ: str) -> None:
        """
        Adds a DDS switching event to the sequence
        :param name: the name of the DDS as defined in the pulser's hardware configuration
        :param start: the start time in seconds
        :param num: the integer representation of the DDS program, as output py Pulser._val_to_int_cogerent
        :param typ: a flag that is either "start" or "stop", which tells the DDS to turn on or off
        """
        time_step = self._sec_to_step(start)
        self.dds_setting_list.append((name, time_step, num, typ))

    def add_ttl_pulse(self, channel: int, start: float, duration: float) -> None:
        """
        adds TTL pulse to the sequence
        :param channel: the integer TTL channel
        :param start: the start time in seconds
        :param duration: the duration in seconds
        """
        start = self._sec_to_step(start)
        duration = self._sec_to_step(duration)
        self._add_new_switch(start, channel, 1)
        self._add_new_switch(start + duration, channel, -1)

    def extend_sequence_length(self, time_length: float) -> None:
        """
        Allows to extend the total length of the sequence.
        :param time_length: the time to extend by, in seconds
        """
        time_length = self._sec_to_step(time_length)
        self._add_new_switch(time_length, 0, 0)

    def _sec_to_step(self, sec) -> int:
        """converts seconds to time steps"""
        start = "{0:.9f}".format(sec)  # round to nanoseconds
        start = Decimal(start)  # convert to decimal
        step = (start / self.time_resolution).to_integral_value()
        step = int(step)
        return step

    def _num_to_hex(self, number: Union[int, float]) -> bytes:
        """
        converts the number to the hex representation for a total of 32 bits
        i.e: 3 -> 00000000...000100 ->  \x00\x00\x03\x00, note that the order of 8bit pieces is switched'''
        """
        number = int(number)
        b = bytearray(4)
        b[2] = number % 256
        b[3] = (number // 256) % 256
        b[0] = (number // 65536) % 256
        b[1] = (number // 16777216) % 256
        return bytes(b)

    def _add_new_switch(self, time_step: int, chan: int, value: int) -> None:
        """

        :param time_step:
        :param chan:
        :param value: should be 1 for switching on, -1 for switching off, or 0 for staying the same
        :return:
        """
        if time_step in self.ttl_switching_times:
            if self.ttl_switching_times[time_step][chan]:  # checks if 0 or 1/-1
                # if set to turn off, but want on, replace with zero, fixes error adding 2 TTLs back to back
                if self.ttl_switching_times[time_step][chan] * value == -1:
                    self.ttl_switching_times[time_step][chan] = 0
                else:
                    raise Exception(
                        "Double switch at time {} for channel {}".format(
                            time_step, chan
                        )
                    )
            else:
                self.ttl_switching_times[time_step][chan] = value
        else:
            if self.ttl_switches == self.max_switches:
                raise Exception(
                    "Exceeded maximum number of switches {}".format(self.ttl_switches)
                )
            self.ttl_switching_times[time_step] = numpy.zeros(
                self.ttl_channel_count, dtype=numpy.int8
            )
            self.ttl_switches += 1
            self.ttl_switching_times[time_step][chan] = value

    def prog_representation(self, parse: bool = True) -> Tuple[Dict[str, bytes], bytes]:
        """
        Returns the programmatic representation of the pulse sequence.
        :param parse: flag that determines whether the sequence should re-compute the representation before returning
        :returns: Two items: The first is a dict of DDS programs, with the keys being the DDS names.
        The second is the full TTL program as a byte string
        """
        if parse:
            self.ddsSettings = self.parse_dds()
            self.ttlProgram = self.parse_ttl()
        return self.ddsSettings, self.ttlProgram

    @property
    def user_added_dds(self) -> bool:
        """a flag that checks whether a dds has been added to the sequence"""
        return bool(len(self.dds_setting_list))

    def parse_dds(self) -> Union[None, Dict[str, bytes]]:
        """creates a byte string to program each DDS and returns it as a dict"""
        if not self.user_added_dds:
            return None
        # get the state of the pulser. This will be a dict of the form {name: channel_number}:
        state = self.parent.get_current_dds()
        pulses_end = {}.fromkeys(
            state, (0, "stop")
        )  # time / boolean whether in a middle of a pulse
        dds_program = {}.fromkeys(state, b"")
        last_time = 0
        start = None
        entries = sorted(
            self.dds_setting_list, key=lambda t: t[1]
        )  # sort by starting time
        possible_error = (0, "")
        while True:
            try:
                name, start, num, typ = entries.pop(0)
            # if there's nothing left to pop, finalize and then return
            except IndexError:
                if start == last_time:
                    # still have unprogrammed entries
                    self.add_to_program(dds_program, state)
                    self._add_new_switch(last_time, self.advance_dds, 1)
                    self._add_new_switch(
                        last_time + self.reset_step_duration, self.advance_dds, -1
                    )
                # add termination
                for name in dds_program.keys():
                    dds_program[name] += b"\x00\x00"
                # at the end of the sequence, reset dds
                last_ttl = max(self.ttl_switching_times.keys())
                self._add_new_switch(last_ttl, self.reset_dds, 1)
                self._add_new_switch(
                    last_ttl + self.reset_step_duration, self.reset_dds, -1
                )
                return dds_program
            end_time, end_typ = pulses_end[name]
            if start > last_time:
                # the time has advanced, so need to program the previous state
                if possible_error[0] == last_time and len(possible_error[1]):
                    raise Exception(
                        possible_error[1]
                    )  # if error exists and belongs to that time
                self.add_to_program(dds_program, state)
                if not last_time == 0:
                    self._add_new_switch(last_time, self.advance_dds, 1)
                    self._add_new_switch(
                        last_time + self.reset_step_duration, self.advance_dds, -1
                    )
                last_time = start
            if start == end_time:
                # overwrite only when extending pulse
                if end_typ == "stop" and typ == "start":
                    possible_error = (0, "")
                    state[name] = num
                    pulses_end[name] = (start, typ)
                elif end_typ == "start" and typ == "stop":
                    possible_error = (0, "")
            elif end_typ == typ:
                possible_error = (
                    start,
                    "Found Overlap Of Two Pules for channel {}".format(name),
                )
                state[name] = num
                pulses_end[name] = (start, typ)
            else:
                state[name] = num
                pulses_end[name] = (start, typ)

    def add_to_program(self, prog: dict, state: dict):
        for name, num in state.items():
            """
            Takes in the DDS program and the current pulser DDS dict, and adds the DDS numbers to the program
            TODO: does this need to be a full method, or should it be inside parse_dds?
            """
            buf = self.parent.int_to_buf_coherent(num)
            prog[name] += buf

    def parse_ttl(self) -> bytes:
        """Returns the bytewise representation of the TTL sequence for programming the FPGA"""
        rep = bytes()
        last_channels = numpy.zeros(self.ttl_channel_count)
        power_array = 2 ** numpy.arange(self.ttl_channel_count, dtype=numpy.uint64)
        for key, new_channels in sorted(self.ttl_switching_times.items()):
            channels = (
                last_channels + new_channels
            )  # computes the action of switching on the state
            if (channels < 0).any():
                raise Exception("Trying to switch off channel that is not already on")
            channel_int = numpy.dot(channels, power_array)
            # convert the new state to hex and adds it to the sequence
            rep = rep + self._num_to_hex(key) + self._num_to_hex(channel_int)
            last_channels = channels
        rep = rep + 2 * self._num_to_hex(0)  # adding termination
        return rep

    def human_representation(
        self,
    ) -> Tuple[numpy.array, List[Tuple[str, float, float]]]:
        """Returns the human-readable version of the sequence for FPGA for debugging"""
        dds, ttl = self.prog_representation(parse=False)
        ttl = self.ttl_human_representation(ttl)
        dds = self.dds_human_representation(dds)
        return ttl, dds

    def dds_human_representation(
        self, dds: Dict[str, bytes]
    ) -> List[Tuple[str, float, float]]:
        """
        returns a human-readable representation of the DDSes in the sequence.
        :param dds: the dds program, as output by self.parse_dds
        :return: a list of tuples containing (<name>, <frequency>, <amplitude>)
        """
        program = []
        for name, buf in dds.items():
            arr = array.array("B", buf)
            arr = arr[:-2]  # remove termination
            channel = PulserConfiguration.dds_channel_dict[name]
            coherent = channel.phase_coherent_model
            freq_min, freq_max = channel.board_freq_range
            ampl_min, ampl_max = channel.board_ampl_range

            def chunks(arr, n):
                """Yield successive n-sized chunks from arr."""
                for i in range(0, len(arr), n):
                    yield arr[i : i + n]

            if not coherent:
                for a, b, c, d in chunks(arr, 4):
                    freq_num = 256 * b + a
                    ampl_num = 256 * d + c
                    freq = freq_min + freq_num * (freq_max - freq_min) / float(
                        16**4 - 1
                    )
                    ampl = ampl_min + ampl_num * (ampl_max - ampl_min) / float(
                        16**4 - 1
                    )
                    program.append((name, freq, ampl))
            else:
                for (
                    a0,
                    a1,
                    amp0,
                    amp1,
                    a2,
                    a3,
                    a4,
                    a5,
                    f0,
                    f1,
                    f2,
                    f3,
                    f4,
                    f5,
                    f6,
                    f7,
                ) in chunks(arr, 16):
                    freq_num = 256**2 * (256 * f7 + f6) + (256 * f5 + f4)
                    ampl_num = 256 * amp1 + amp0
                    freq = freq_min + freq_num * (freq_max - freq_min) / float(
                        16**8 - 1
                    )
                    ampl = ampl_min + ampl_num * (ampl_max - ampl_min) / float(
                        16**4 - 1
                    )
                    program.append((name, freq, ampl))
        return program

    def ttl_human_representation(self, rep: bytes) -> numpy.array:
        """
        returns a human-readable representation of the TTLs in the sequence.
        :param rep: the TTL program, as output by self.parse_ttl
        :return: an array of stitching times and channels
        """
        rep = str(rep)  # recast rep from bytes into string
        # noinspection PyArgumentList
        # arr = numpy.fromstring(rep, dtype=numpy.uint16)  # does the decoding from the string
        arr = numpy.frombuffer(rep, dtype=numpy.uint16)
        arr = numpy.array(
            arr, dtype=numpy.uint32
        )  # once decoded, need to be able to manipulate large numbers
        # arr = numpy.array(rep,dtype = numpy.uint16)
        arr = arr.reshape(-1, 4)
        times = (65536 * arr[:, 0] + arr[:, 1]) * float(self.time_resolution)
        channels = 65536 * arr[:, 2] + arr[:, 3]

        def expand_channel(ch):
            """function for getting the binary representation, i.e 2**32 is 1000...0"""
            expand = bin(ch)[2:].zfill(32)
            reverse = expand[::-1]
            return reverse

        channels = list(map(expand_channel, channels))
        return numpy.vstack((times, channels)).transpose()
