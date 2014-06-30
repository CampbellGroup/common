class switch_config(object):
    '''
    configuration file for multiplexer client
    info is the configuration dictionary in the form
    {channel_name: (port, display_location, inverted)), }
    '''
    info = {'399': (9, (0,1), False),
            '935': (10, (0,2), False)
            }