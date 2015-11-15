# -*- coding: utf-8 -*-
"""
### BEGIN NODE INFO
[info]
name = Pi Camera
version = 1.0
description = 
instancename = PiCamera

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
import numpy as _n
import picamera
import picamera.array
from labrad.server import LabradServer, setting
from twisted.internet.defer import returnValue


class PiCamera(LabradServer):
    """
    Raspberry Pi based camera server.
    
    This can take basic images, and later it should be able to get beam 
    profiles.
    """
    name = 'Pi Camera'
    _image_data = None


    @setting(1)
    def capture_image(self, c):
        """
        Take a picture with the camera, populating self._image_data with a 
        numpy array.
        """
        with picamera.PiCamera() as camera:
            with picamera.array.PiRGBArray(camera) as output:
                camera.capture(output, 'rgb')
                print('Captured %dx%d image' % (
                        output.array.shape[1], output.array.shape[0]))
                self._image_data = output.array

        print "capture_image type(self._image_data):", type(self._image_data)


    @setting(2)
    def image_array(self, returns='?'):
        """
        Return the numpy array of capture image data after it has been 
        flattened to be something like greyscale, summing over RGB elements.
        """
        yield None
        print "image_array type(self._image_data):", type(self._image_data)
        print "self._image_data[0]:", self._image_data[0]
        print "len(self._image_data):", len(self._image_data)
        print "len(self._image_data[0]):", len(self._image_data[0])
        print "len(self._image_data[0][0]):", len(self._image_data[0][0])
        print "self._image_data[0][0]:", self._image_data[0][0]
        print "sum(self._image_data[0][0]):", sum(self._image_data[0][0])
        returnValue(self._image_data)

    @setting(3)
    def red_image_array(self, returns='?'):
        """
        Return the numpy array of R values of captured image data.
        """        
        red_array = self._image_data[:, :, 0]
        yield None
        returnValue(red_array)        


    @setting(4)
    def green_image_array(self, returns='?'):
        """
        Return the numpy array of G values of captured image data.
        """        
        green_array = self._image_data[:, :, 1]
        yield None
        returnValue(green_array) 

    @setting(5)
    def blue_image_array(self, returns='?'):
        """
        Return the numpy array of B values of captured image data.
        """        
        blue_array = self._image_data[:, :, 2]
        yield None
        returnValue(blue_array)   
        
if __name__ == "__main__":
    from labrad import util
    util.runServer(PiCamera())
    