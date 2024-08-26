class piezo_config(object):
    """
    Configuration file for piezo controller client.
    Info is the configuration dictionary in the form:
    {channel_name: (port, display_location, inverted)), }
    """

    info = {
        "Channel 1": (1, (1, 0), False),
        "Channel 2": (2, (1, 1), False),
        "Channel 3": (3, (3, 0), False),
        "Channel 4": (4, (3, 1), False),
    }
