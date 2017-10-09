class AndorConfig(object):
    '''
    path to atmcd64d.dll SDK library
    '''
    def __init__(self):
        #default parameters
        self.path_to_dll = ('C:\\Program Files\\Andor SOLIS\\atmcd64d_legacy.dll')
        self.set_temperature = -20 #degrees C
        self.read_mode = 'Image'
        self.acquisition_mode = 'Single Scan'
        self.trigger_mode = 'Internal'
        self.exposure_time = 0.100 #seconds
        self.binning = [1, 1] #numbers of pixels for horizontal and vertical binning
        self.image_path = ('C:\\Users\\scientist\\Pictures\\iXonImages\\')
        self.camera_ip = "128.111.15.92"
		