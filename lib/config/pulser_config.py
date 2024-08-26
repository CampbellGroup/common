from dataclasses import dataclass
from typing import Tuple


@dataclass
class TTLChannel:
    """
    Stores complete configuration of each TTL channel
    """

    channel_number: int
    is_manual: bool
    manual_state: bool
    inverted_manual: bool
    inverted_auto: bool


@dataclass
class DDSChannel:
    """
    Stores complete configuration of each DDS channel
    """

    channel_number: int
    allowed_freq_range: Tuple[float, float]  # MHz/ms
    allowed_ampl_range: Tuple[float, float]  # dB/ms
    frequency: float
    amplitude: float

    state: bool = True
    name: str = None  # will get assigned automatically

    # attributes relating to the phyiscal hardware parameters. Generally shouldn't be touched
    board_freq_range: Tuple[float, float] = (0.0, 2000.0)
    board_ramp_range: Tuple[float, float] = (0.000113687, 7.4505806)  # MHz/ms
    board_amp_ramp_range: Tuple[float, float] = (0.00174623, 22.8896)  # dB/ms
    board_ampl_range: Tuple[float, float] = (-46.0, 7.0)
    board_phase_range: Tuple[float, float] = (0.0, 360.0)
    off_parameters: Tuple[float, float] = (0.0, -46.0)
    phase_coherent_model: bool = True
    is_remote: bool = False


@dataclass
class RemoteDDSChannel:
    """TODO: what does this actually do?"""

    ip: str
    server: str
    reset: str = "reset_dds"
    program: str = "program_dds"


class PulserConfiguration:
    """
    Stores the hardware configuration of the Pulser, as well as dicts defining the TTL and DDS channels
    """

    # settings related to the Pulser hardware
    time_resolution: str = (
        "40.0e-9"  # seconds. this needs to be a string because it gets cast in various ways later
    )
    time_resolved_resolution: float = (
        10.0e-9  # the resolution of the time tagging in seconds
    )
    max_switches = 1022  # max number of switches that can be in a pulse sequence
    reset_step_duration = (
        3  # duration of advanceDDS and resetDDS TTL pulses in units of time steps
    )
    collection_time_range = (0.010, 5.0)  # range for normal pmt counting in seconds
    sequence_time_range = (0.0, 85.0)  # range for duration of pulse sequence in seconds
    line_trigger_limits: tuple = (0, 15000)  # values in microseconds
    has_second_pmt: bool = False
    has_dac: bool = False
    ok_device_id: str = "Pulser2"
    ok_device_file: str = "photon_2015_7_13.bit"

    # normalPMTflow defaults
    default_collection_mode: str = "Normal"  # default PMT mode
    default_collection_time: dict = {
        "Normal": 0.100,
        "Differential": 0.100,
    }  # default counting rates

    # name: (channelNumber, ismanual, manualstate,  manualinversion, autoinversion)
    ttl_channel_dict = {}
    ttl_channel_dict["866DP"] = TTLChannel(12, False, True, False, True)
    ttl_channel_dict["crystallization"] = TTLChannel(1, True, False, False, False)
    ttl_channel_dict["bluePI"] = TTLChannel(2, True, False, True, False)
    ttl_channel_dict["camera"] = TTLChannel(5, False, False, True, True)
    ttl_channel_dict["coil_dir"] = TTLChannel(6, False, False, True, True)
    # ------------INTERNAL CHANNELS----------------------------------------#
    ttl_channel_dict["Internal866"] = TTLChannel(0, False, False, False, False)
    ttl_channel_dict["DiffCountTrigger"] = TTLChannel(16, False, False, False, False)
    ttl_channel_dict["TimeResolvedCount"] = TTLChannel(17, False, False, False, False)
    ttl_channel_dict["AdvanceDDS"] = TTLChannel(18, False, False, False, False)
    ttl_channel_dict["ResetDDS"] = TTLChannel(19, False, False, False, False)
    ttl_channel_dict["ReadoutCount"] = TTLChannel(20, False, False, False, False)

    # address, allowedfreqrange, allowedamplrange, frequency, amplitude, **args):
    dds_channel_dict = {}
    dds_channel_dict["866DP"] = DDSChannel(0, (70.0, 90.0), (-63.0, -5.0), 80.0, -33.0)
    dds_channel_dict["global397"] = DDSChannel(
        1, (70.0, 100.0), (-63.0, -12.0), 90.0, -33.0
    )
    dds_channel_dict["radial"] = DDSChannel(
        2, (90.0, 130.0), (-63.0, -12.0), 110.0, -63.0
    )
    dds_channel_dict["854DP"] = DDSChannel(3, (70.0, 90.0), (-63.0, -4.0), 80.0, -33.0)
    dds_channel_dict["729DP"] = DDSChannel(
        4, (150.0, 250.0), (-63.0, -5.0), 220.0, -33.0
    )

    remoteChannels = {}
