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

    name = "Pi Camera"
    _image_data = None

    @setting(1)
    def capture_image(self, c):
        """
        Take a picture with the camera, populating self._image_data with a
        numpy array.
        """
        with picamera.PiCamera() as camera:
            with picamera.array.PiRGBArray(camera) as output:
                camera.capture(output, "rgb")
                print(
                    "Captured %dx%d image"
                    % (output.array.shape[1], output.array.shape[0])
                )
                self._image_data = output.array

    @setting(2)
    def image_array(self, returns="?"):
        """
        Return the numpy array of capture image data.
        """
        image_array = self._image_data
        image_array = _n.array(image_array, dtype="float")
        yield None
        returnValue(image_array)

    @setting(3)
    def red_image_array(self, returns="?"):
        """
        Return the numpy array of R values of captured image data.
        """
        red_array = self._image_data[:, :, 0]
        red_array = _n.array(red_array, dtype="float")
        yield None
        returnValue(red_array)

    @setting(4)
    def green_image_array(self, returns="?"):
        """
        Return the numpy array of G values of captured image data.
        """
        green_array = self._image_data[:, :, 1]
        green_array = _n.array(green_array, dtype="float")
        yield None
        returnValue(green_array)

    @setting(5)
    def blue_image_array(self, returns="?"):
        """
        Return the numpy array of B values of captured image data.
        """
        blue_array = self._image_data[:, :, 2]
        blue_array = _n.array(blue_array, dtype="float")
        yield None
        returnValue(blue_array)


if __name__ == "__main__":
    from labrad import util

    util.runServer(PiCamera())
