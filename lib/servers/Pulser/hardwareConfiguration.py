"""
This is the hardware configuration file for the Pulser
"""


class channelConfiguration(object):
    """
    Stores complete configuration for each of the channels
    TODO descriptions of each attribute here.
    """
    def __init__(self, channelNumber, ismanual, manualstate,  manualinversion, autoinversion):
        self.channelnumber = channelNumber
        
        # This should probably just be manual.  self.manual is True or False then.
        self.ismanual = ismanual
        
        # I don't think this name is correct.  I think this is the default state.
        self.manualstate = manualstate
        self.manualinv = manualinversion
        self.autoinv = autoinversion
   
     
class ddsConfiguration(object):
    """
    Stores complete configuration of each DDS board
    """
    def __init__(self, address, allowedfreqrange, allowedamplrange, frequency, amplitude, **args):
        self.channelnumber = address
        self.allowedfreqrange = allowedfreqrange
        self.allowedamplrange = allowedamplrange
        self.frequency = frequency
        self.amplitude = amplitude
        self.state = True
        self.boardfreqrange = args.get('boardfreqrange', (0.0, 800.0))
        self.boardamplrange = args.get('boardamplrange', (-63.0, -3.0))
        self.boardphaserange = args.get('boardphaserange', (0.0, 360.0))
        self.off_parameters = args.get('off_parameters', (0.0, -63.0))
        self.phase_coherent_model = args.get('phase_coherent_model', True)        
        self.remote = args.get('remote', False)
        self.name = None #will get assigned automatically


class remoteChannel(object):
    def __init__(self, ip, server, **args):
        self.ip = ip
        self.server = server
        self.reset = args.get('reset', 'reset_dds')
        self.program = args.get('program', 'program_dds')
        
        
class hardwareConfiguration(object):
    channelTotal = 32
    timeResolution = '40.0e-9' #seconds
    timeResolvedResolution = 10.0e-9
    maxSwitches = 1022
    resetstepDuration = 2 #duration of advanceDDS and resetDDS TTL pulses in units of timesteps
    collectionTimeRange = (0.010, 5.0) #range for normal pmt counting
    sequenceTimeRange = (0.0, 300.0) #range for duration of pulse sequence in seconds?  
    isProgrammed = False
    sequenceType = None # None for not programmed, can be 'one' or 'infinite'
    collectionMode = 'Normal' # default PMT mode
    collectionTime = {'Normal':0.100,'Differential':0.100} #default counting rates
    okDeviceID = 'Pulser'
    okDeviceFile = 'pulser_2013_06_05.bit'
    lineTriggerLimits = (0, 15000)#values in microseconds 
    secondPMT = False
    DAC = False
    
    # TODO: Add MOT_beams_frequency, Scope_Trigger
    # channel dictionary entry format
    # name: (channelNumber, ismanual, manualstate,  manualinversion, autoinversion)
    channelDict = {
        'MOT_laser':    channelConfiguration(12, False,  False, False, True), 
        'MOT_coils':    channelConfiguration(14, False,  False, False, True),  
        'Repump_laser': channelConfiguration(13, False,  False, False, True),
        'ML_laser':     channelConfiguration(15, False,  False, False, True),
#        'Camera': channelConfiguration(21, True,  True, False, True),
#        'Imaging_laser':     channelConfiguration(22, True, False, False, True),
        'ch1':  channelConfiguration(1,  False,  False, False, True),  # C14 right 
        'ch2':  channelConfiguration(2,  False,  False, False, True),  # C47 right
        'ch3':  channelConfiguration(3,  False,  False, False, True),  # C5 right
        'ch4':  channelConfiguration(4,  False,  False, False, True),  # C9 right
        'ch5':  channelConfiguration(5,  False,  False, False, True),  # C64 right
        'ch6':  channelConfiguration(6,  False,  False, False, True),  # C6 right
        'ch7':  channelConfiguration(7,  False,  False, False, True),  # C26 right
        'ch8':  channelConfiguration(8,  False,  False, False, True),  # C58 right
        'ch9':  channelConfiguration(9,  False,  False, False, True),  # C3 right
        'ch10': channelConfiguration(10, False,  False, False, True),  # C39 right
        'ch11': channelConfiguration(11, False,  False, False, True),  # C57 right
        'ch23': channelConfiguration(23, False,  False, False, True),  
        'ch24': channelConfiguration(24, False,  False, False, True),
        'ch25': channelConfiguration(25, False,  False, False, True),  
        'ch26': channelConfiguration(26, False,  False, False, True),
        'ch27': channelConfiguration(27, False,  False, False, True),
        'ch28': channelConfiguration(28, False,  False, False, True),
        'ch29': channelConfiguration(29, False,  False, False, True),
                   #------------INTERNAL CHANNEgiLS----------------------------------------#
                   'Internal866':channelConfiguration(0, False, False, False, False), # C44 right
                   'DiffCountTrigger':channelConfiguration(16, False, False, False, False),
                   'TimeResolvedCount':channelConfiguration(17, False, False, False, False),
                   'AdvanceDDS':channelConfiguration(18, False, False, False, False),
                   'ResetDDS':channelConfiguration(19, False, False, False, False),
                   'ReadoutCount':channelConfiguration(20, False, False, False, False),
                }
    #address, allowedfreqrange, allowedamplrange, frequency, amplitude, **args):
    ddsDict =   {
                '866DP':ddsConfiguration(        0,  (70.0,90.0),    (-63.0,-5.0),   80.0,   -33.0),
                'global397':ddsConfiguration(    1,  (70.0,100.0),   (-63.0,-12.0),  90.0,   -33.0),
                'radial':ddsConfiguration(       2,  (90.0,130.0),   (-63.0,-12.0),   110.0,  -63.0),
#                  'radial':ddsConfiguration(       2,  (74.0,74.0),   (-63.0,-5.0),   74.0,  -63.0),
                '854DP':ddsConfiguration(        3,  (70.0,90.0),    (-63.0,-4.0),   80.0,   -33.0),
                '729DP':ddsConfiguration(        4,  (150.0,250.0),  (-63.0,-5.0),   220.0,  -33.0),
                }
    remoteChannels = {
                    }
