class multiplexer_config(object):
    '''
    configuration file for multiplexer client
    info is the configuration dictionary in the form
    {channel_name: (port, hint, display_location, stretched)), }
    '''
    info = {'Channel 1' :(1, '384.230000', (1,1), True, False),
            'Channel 2' :(2, '384.230000', (1,2), True, False),
            'Channel 3' :(3, '384.230000', (1,3), True, False),
            'Channel 4' :(4, '384.230000', (5,1), True, False),
            'Channel 5': (5, '405.645745', (5,2), True, False),
            'Channel 6': (6, '320.571975', (5,3), True, False),
            'Channel 7': (7, '751.526150', (9,1), True, False),
            'Channel 8': (8, '384.230000', (9,2), True, False)
            }
