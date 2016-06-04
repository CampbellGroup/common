"""
Test sequence.py module
"""
import unittest as _ut
import numpy as _n
import common.lib.servers.Pulser.sequence as _sequence
import common.lib.config.pulser.hardwareConfiguration as _hw_config
from decimal import Decimal


class TestSequence(_ut.TestCase):

    def setUp(self):
        self.sequence = _sequence.Sequence()
        self._set_sequence_with_common_hardware_configuration()

    def tearDown(self):
        self.sequence = None
        del self.sequence

    def _set_sequence_with_common_hardware_configuration(self):
        """
        The hardware configuration for common is manually set.

        This basically fully overwrites __init__ and it would be much
        better set this by some other means, i.e. not manually.
        """
        config = _hw_config.hardwareConfiguration
        self.sequence.channelTotal = config.channelTotal
        self.sequence.timeResolution = Decimal(config.timeResolution)
        self.sequence.MAX_SWITCHES = config.maxSwitches
        self.sequence.resetstepDuration = config.resetstepDuration
        switch_dict = {0: _n.zeros(config.channelTotal, dtype=_n.int8)}
        self.sequence.switchingTimes = switch_dict
        advance_dds = config.channelDict['AdvanceDDS'].channelnumber
        self.sequence.advanceDDS = advance_dds
        reset_dds = config.channelDict['ResetDDS'].channelnumber
        self.sequence.resetDDS = reset_dds
