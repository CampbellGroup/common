# -*- coding: utf-8 -*-
"""Andor iXon configuration file."""


class andor_config(object):
    '''
    path to atmcd32d.dll SDK library
    '''
    path_to_dll = 'C:\\Program Files\\Andor SOLIS\\atmcd32d.dll'
    # default parameters
    set_temperature = -80 # degrees C
    read_mode = 'Image'
    acquisition_mode = 'Single Scan'
    trigger_mode = 'Internal'
    exposure_time = 0.12 # seconds
    binning = [1, 1] # numbers of pixels for horizontal and vertical binning
    image_path = 'C:\\Users\\QSimYb\\Desktop\\camera_images\\'
    image_rotation = 90 # CCW
    mirror_x = True
    mirror_y = False
