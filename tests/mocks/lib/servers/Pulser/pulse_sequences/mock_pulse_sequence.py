"""
pulse_sequence Mock
"""
from mock import Mock
from common.lib.servers.Pulser.pulse_sequences.pulse_sequence import \
    pulse_sequence

mock_pulse_sequence = Mock(spec_set=pulse_sequence)
