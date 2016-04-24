class multiplexer_config(object):
    '''
    multiplexer client configuration file
    
    Attributes
    ----------
    info: dict
    {channel_name: (port, hint, display_location, stretched, display_pid, dac, dac_rails))}
    '''
    info = {'Laser 1' :(1, '461.251000', (0,1), True, False, 1, [-10,10]),
            'Laser 2' :(2, '607.616000', (0,2), True, False, 2, [-10,10]),
            'Laser 3' :(3, '384.230000', (0,3), True, False, 3, [-10,10]),
            'Laser 4' :(4, '384.230000', (0,4), True, False, 4, [-10,10]),
            'Laser 5': (5, '405.645745', (5,1), True, False, 5, [-10,10]),
            'Laser 6': (6, '320.571975', (5,2), True, False, 6, [-10,10]),
            'Laser 7': (7, '751.526150', (5,3), True, False, 7, [-10,10]),
            'Laser 8': (8, '384.230000', (5,4), True, False, 8, [-10,10])
            }
    ip = 'localhost'
