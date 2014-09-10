class DDS_config(object):
    '''
    configuration file for arduino switch client
    info is the configuration dictionary in the form
    {channel_name: (port, display_location, inverted)), }
    '''
    info = {'Channel 1': (0, (1,0), 1),
            'Channel 2': (0, (2,0), 2),
            'Channel 3': (0, (3,0), 3),
            'Channel 4': (0, (4,0), 4),
            }
