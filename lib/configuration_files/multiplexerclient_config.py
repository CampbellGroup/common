class multiplexer_config(object):
    '''
    configuration file for multiplexer client
    info is the configuration dictionary in the form
    {channel_name: (port, hint, display_location, stretched)), }
    '''
    info = {'Channel 1' :(1, '384.230000', (1,1), True),
            'Channel 2' :(2, '384.230000', (1,2), True),
            'Channel 3' :(3, '384.230000', (1,3), True),
            'Channel 4' :(4, '384.230000', (2,1), True),
            'Channel 5': (5, '405.645745', (2,2), True),
            'Channel 6': (6, '320.571975', (2,3), True),
            'Channel 7': (7, '751.526150', (3,1), True),
            'Channel 8': (8, '384.230000', (3,2), True)
            }
