import numpy as np
import array
from decimal import Decimal

try:
    from config.pulser.hardwareConfiguration import hardwareConfiguration
except:
    from common.lib.config.pulser.hardwareConfiguration import hardwareConfiguration


class Sequence():
    """Sequence for programming pulses"""
    def __init__(self, parent):
        self.parent = parent
        self.channelTotal = hardwareConfiguration.channelTotal
        self.timeResolution = Decimal(hardwareConfiguration.timeResolution)
        self.MAX_SWITCHES = hardwareConfiguration.maxSwitches
        self.resetstepDuration = hardwareConfiguration.resetstepDuration
        # dictionary in the form time:which channels to switch
        # time is expressed as timestep with the given resolution
        # which channels to switch is a channelTotal-long array with 1 to
        # switch ON, -1 to switch OFF, 0 to do nothing
        self.switchingTimes = {0: np.zeros(self.channelTotal, dtype=np.int8)}
        # keeps track of how many switches are to be performed
        # (same as the number of keys in the switching Times dictionary"
        self.switches = 1
        # dictionary for storing information about dds switches, in the format:
        # timestep: {channel_name: integer representing the state}
        self.ddsSettingList = []
        self.advanceDDS = hardwareConfiguration.channelDict['AdvanceDDS'].channelnumber
        self.resetDDS = hardwareConfiguration.channelDict['ResetDDS'].channelnumber

    def addDDS(self, name, start, num, typ):
        timeStep = self.secToStep(start)
        self.ddsSettingList.append((name, timeStep, num, typ))

    def addPulse(self, channel, start, duration):
        """adding TTL pulse, times are in seconds"""
        start = self.secToStep(start)
        duration = self.secToStep(duration)
        self._addNewSwitch(start, channel, 1)
        self._addNewSwitch(start + duration, channel, -1)

    def extendSequenceLength(self, timeLength):
        """Allows to extend the total length of the sequence"""
        timeLength = self.secToStep(timeLength)
        self._addNewSwitch(timeLength, 0, 0)

    def secToStep(self, sec):
        '''converts seconds to time steps'''
        start = '{0:.9f}'.format(sec)  # round to nanoseconds
        start = Decimal(start)  # convert to decimal
        step = (start/self.timeResolution).to_integral_value()
        step = int(step)
        return step

    def numToHex(self, number):
        '''converts the number to the hex representation for a total of 32 bits
        i.e: 3 -> 00000000...000100 ->  \x00\x00\x03\x00, note that the order
        of 8bit pieces is switched'''
        a, b = number // 65536, number % 65536
        return str(np.uint16([a, b]).data)

    def _addNewSwitch(self, timeStep, chan, value):
        if self.switchingTimes.has_key(timeStep):
            if self.switchingTimes[timeStep][chan]:
                double_switch = 'Double switch at time {} for channel {}'
                raise Exception(double_switch.format(timeStep, chan))
            self.switchingTimes[timeStep][chan] = value
        else:
            if self.switches == self.MAX_SWITCHES:
                max_switches = "Exceeded maximum number of switches {}"
                raise Exception(max_switches.format(self.switches))
            self.switchingTimes[timeStep] = np.zeros(self.channelTotal,
                                                     dtype=np.int8)

            self.switches += 1
            self.switchingTimes[timeStep][chan] = value

    def progRepresentation(self, parse=True):
        if parse:
            self.ddsSettings = self.parseDDS()
            self.ttlProgram = self.parseTTL()
        return self.ddsSettings, self.ttlProgram

    def userAddedDDS(self):
        return bool(len(self.ddsSettingList))

    def parseDDS(self):
        if not self.userAddedDDS():
            return None
        state = self.parent._getCurrentDDS()
        # time / boolean whether in a middle of a pulse
        pulses_end = {}.fromkeys(state, (0, 'stop'))
        dds_program = {}.fromkeys(state, '')
        lastTime = 0
        # sort by starting time
        entries = sorted(self.ddsSettingList, key=lambda t: t[1])
        possibleError = (0, '')
        while True:
            try:
                name, start, num, typ = entries.pop(0)
            except IndexError:
                if start == lastTime:
                    # still have unprogrammed entries
                    self.addToProgram(dds_program, state)
                    self._addNewSwitch(lastTime, self.advanceDDS, 1)
                    self._addNewSwitch(lastTime + self.resetstepDuration,
                                       self.advanceDDS, -1)

                # add termination
                for name in dds_program.iterkeys():
                    dds_program[name] += '\x00\x00'
                # at the end of the sequence, reset dds
                lastTTL = max(self.switchingTimes.keys())
                self._addNewSwitch(lastTTL, self.resetDDS, 1)
                self._addNewSwitch(lastTTL + self.resetstepDuration,
                                   self.resetDDS, -1)

                return dds_program
            end_time, end_typ = pulses_end[name]
            if start > lastTime:
                # the time has advanced, so need to program the previous state
                if possibleError[0] == lastTime and len(possibleError[1]):
                    # if error exists and belongs to that time
                    raise Exception(possibleError[1])
                self.addToProgram(dds_program, state)
                if not lastTime == 0:
                    self._addNewSwitch(lastTime, self.advanceDDS, 1)
                    self._addNewSwitch(lastTime + self.resetstepDuration,
                                       self.advanceDDS, -1)

                lastTime = start
            if start == end_time:
                # overwite only when extending pulse
                if end_typ == 'stop' and typ == 'start':
                    possibleError = (0, '')
                    state[name] = num
                    pulses_end[name] = (start, typ)
                elif end_typ == 'start' and typ == 'stop':
                    possibleError = (0, '')
            elif end_typ == typ:
                found_overlap = 'Found Overlap Of Two Pules for channel {}'
                possibleError = (start, found_overlap.format(name))
                state[name] = num
                pulses_end[name] = (start, typ)
            else:
                state[name] = num
                pulses_end[name] = (start, typ)

    def addToProgram(self, prog, state):
        for name, num in state.iteritems():
            if not hardwareConfiguration.ddsDict[name].phase_coherent_model:
                buf = self.parent._intToBuf(num)
            else:
                buf = self.parent._intToBuf_coherent(num)
            prog[name] += buf

    def parseTTL(self):
        """Returns the representation of the sequence for programming the
        FPGA"""
        rep = ''
        lastChannels = np.zeros(self.channelTotal)
        powerArray = 2**np.arange(self.channelTotal, dtype=np.uint64)
        for key, newChannels in sorted(self.switchingTimes.iteritems()):
            # computes the action of switching on the state
            channels = lastChannels + newChannels
            if (channels < 0).any():
                switch = 'Trying to switch off channel that is not already on'
                raise Exception(switch)
            channelInt = np.dot(channels, powerArray)
            # converts the new state to hex and adds it to the sequence
            rep = rep + self.numToHex(key) + self.numToHex(channelInt)
            lastChannels = channels
        rep = rep + 2*self.numToHex(0)  # adding termination
        return rep

    def humanRepresentation(self):
        """Returns the human readable version of the sequence for FPGA for
        debugging"""
        dds, ttl = self.progRepresentation(parse=False)
        ttl = self.ttlHumanRepresentation(ttl)
        dds = self.ddsHumanRepresentation(dds)
        return ttl, dds

    def ddsHumanRepresentation(self, dds):
        program = []
        for name, buf in dds.iteritems():
            arr = array.array('B', buf)
            arr = arr[:-2]  # remove termination
            channel = hardwareConfiguration.ddsDict[name]
            coherent = channel.phase_coherent_model
            freq_min, freq_max = channel.boardfreqrange
            ampl_min, ampl_max = channel.boardamplrange

            def chunks(l, n):
                """ Yield successive n-sized chunks from l."""
                for i in xrange(0, len(l), n):
                    yield l[i:i+n]
            if not coherent:
                for a, b, c, d in chunks(arr, 4):
                    freq_num = (256*b + a)
                    ampl_num = (256*d + c)
                    val = float(16**4 - 1)
                    freq = freq_min + freq_num * (freq_max - freq_min) / val
                    ampl = ampl_min + ampl_num * (ampl_max - ampl_min) / val
                    program.append((name, freq, ampl))
            else:
                for a, b, c, d, e, f, g, h in chunks(arr, 8):
                    freq_num = 256**2*(256*h + g) + (256*f + e)
                    ampl_num = 256*d + c
                    freq_diff = freq_max - freq_min
                    val_one = float(16**8 - 1)
                    freq = freq_min + freq_num * freq_diff / val_one
                    ampl_diff = ampl_max - ampl_min
                    val_two = float(16**4 - 1)
                    ampl = ampl_min + ampl_num * ampl_diff / val_two
                    program.append((name, freq, ampl))
        return program

    def ttlHumanRepresentation(self, rep):
        # does the decoding from the string
        arr = np.fromstring(rep, dtype=np.uint16)
        # once decoded, need to be able to manipulate large numbers
        arr = np.array(arr, dtype=np.uint32)
        arr = arr.reshape(-1, 4)
        times = (65536 * arr[:, 0] + arr[:, 1]) * float(self.timeResolution)
        channels = (65536 * arr[:, 2] + arr[:, 3])

        def expandChannel(ch):
            '''function for getting the binary representation, i.e 2**32 is
            1000...0'''
            expand = bin(ch)[2:].zfill(32)
            reverse = expand[::-1]
            return reverse

        channels = map(expandChannel, channels)
        return np.vstack((times, channels)).transpose()
