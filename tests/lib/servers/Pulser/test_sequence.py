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
        self.sequence = _sequence.Sequence(parent=None)
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

    def test_addPulse_switches_count(self):
        expected_count = 2
        self.sequence.addPulse(channel=12, start=0.0, duration=2.0)
        count = self.sequence.switches
        self.assertEqual(expected_count, count)

    def test_addPulse_raises_exception_with_two_pulse_conflicts(self):
        self.sequence.addPulse(channel=12, start=1.0, duration=2.0)
        self.assertRaises(Exception, self.sequence.addPulse,
                          channel=12, start=1.0, duration=2.0)
