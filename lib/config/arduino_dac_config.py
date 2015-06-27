class arduino_dac_config(object):
    '''
    configuration file for arduino switch client
    info is the configuration dictionary in the form
    {channel_name: (port, display_location, inverted)), }
    '''
    info = {'Channel 1': ('first dac', 1),
            'Channel 2': ('second dac', 2),
	    'Channel 3': ('third dac', 3),
	    'Channel 4': ('fourth dac', 4),
	    'Channel 5': ('fifth dac', 5),
            'Channel 6': ('sixth dac', 6),
	    'Channel 7': ('seventh dac', 7),
	    'Channel 8': ('eigth dac', 8),
            }
