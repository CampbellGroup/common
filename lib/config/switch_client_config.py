class switch_config(object):
    """
    configuration file for arduino switch client
    info is the configuration dictionary in the form
    {channel_name: (port, display_location, inverted)), }
    """

    info = {
        "Channel 9": (9, (0, 1), False),
        "Channel 10": (10, (0, 2), False),
        "Channel 11": (11, (0, 3), False),
        "Channel 12": (12, (0, 4), False),
    }
