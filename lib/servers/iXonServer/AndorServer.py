from AndorVideo import AndorVideo
from PyQt5.QtWidgets import *

a = QApplication([])
import qt5reactor

qt5reactor.install()

from twisted.internet.defer import returnValue, DeferredLock, Deferred, inlineCallbacks
from twisted.internet.threads import deferToThread
from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from labrad.server import LabradServer, setting, Signal
from AndorCamera import AndorCamera
from labrad.units import WithUnit
import numpy as np

"""
### BEGIN NODE INFO
[info]
name =  Andor Server
version = 1.0
description =

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

IMAGE_UPDATED_SIGNAL = 142312


class AndorServer(LabradServer):
    """Contains methods that interact with the Andor CCD Cameras"""

    name = "Andor Server"
    image_updated = Signal(IMAGE_UPDATED_SIGNAL, "signal: image updated", "*i")

    def initServer(self):
        self.listeners = set()
        self.camera = AndorCamera()
        self.lock = DeferredLock()
        self.gui = AndorVideo(self)

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    """
    Temperature Related Settings
    """

    @setting(0, "Get Temperature", returns="v[degC]")
    def get_temperature(self, c):
        """Gets Current Device Temperature"""
        temperature = None
        print("acquiring: {}".format(self.get_temperature.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.get_temperature.__name__))
            temperature = yield deferToThread(self.camera.get_temperature)
        finally:
            print("releasing: {}".format(self.get_temperature.__name__))
            self.lock.release()
        if temperature is not None:
            temperature = WithUnit(temperature, "degC")
            returnValue(temperature)

    @setting(1, "Get Cooler State", returns="b")
    def get_cooler_state(self, c):
        """Returns Current Cooler State"""
        cooler_state = None
        print("acquiring: {}".format(self.get_cooler_state.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.get_cooler_state.__name__))
            cooler_state = yield deferToThread(self.camera.get_cooler_state)
        finally:
            print("releasing: {}".format(self.get_cooler_state.__name__))
            self.lock.release()
        if cooler_state is not None:
            returnValue(cooler_state)

    @setting(3, "Set Temperature", setTemp="v[degC]", returns="")
    def set_temperature(self, c, setTemp):
        """Sets The Target Temperature"""
        print("acquiring: {}".format(self.set_temperature.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.set_temperature.__name__))
            yield deferToThread(self.camera.set_temperature, setTemp["degC"])
        finally:
            print("releasing: {}".format(self.set_temperature.__name__))
            self.lock.release()

    @setting(4, "Set Cooler On", returns="")
    def set_cooler_on(self, c):
        """Turns Cooler On"""
        print("acquiring: {}".format(self.set_cooler_on.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.set_cooler_on.__name__))
            yield deferToThread(self.camera.set_cooler_on)
        finally:
            print("releasing: {}".format(self.set_cooler_on.__name__))
            self.lock.release()

    @setting(5, "Set Cooler Off", returns="")
    def set_cooler_off(self, c):
        """Turns Cooler On"""
        print("acquiring: {}".format(self.set_cooler_off.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.set_cooler_off.__name__))
            yield deferToThread(self.camera.set_cooler_off)
        finally:
            print("releasing: {}".format(self.set_cooler_off.__name__))
            self.lock.release()

    """
    EMCCD Gain Settings
    """

    @setting(6, "Get EMCCD Gain", returns="i")
    def getEMCCDGain(self, c):
        """Gets Current EMCCD Gain"""
        gain = None
        print("acquiring: {}".format(self.getEMCCDGain.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.getEMCCDGain.__name__))
            gain = yield deferToThread(self.camera.get_emccd_gain)
        finally:
            print("releasing: {}".format(self.getEMCCDGain.__name__))
            self.lock.release()
        if gain is not None:
            returnValue(gain)

    @setting(7, "Set EMCCD Gain", gain="i", returns="")
    def setEMCCDGain(self, c, gain):
        """Sets Current EMCCD Gain"""
        print("acquiring: {}".format(self.setEMCCDGain.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.setEMCCDGain.__name__))
            yield deferToThread(self.camera.set_emccd_gain, gain)
        finally:
            print("releasing: {}".format(self.setEMCCDGain.__name__))
            self.lock.release()
        if c is not None:
            self.gui.set_gain(gain)

    """
    Read mode
    """

    @setting(8, "Get Read Mode", returns="s")
    def getReadMode(self, c):
        return self.camera.get_read_mode()

    @setting(9, "Set Read Mode", readMode="s", returns="")
    def setReadMode(self, c, readMode):
        """Sets Current Read Mode"""
        mode = None
        print("acquiring: {}".format(self.setReadMode.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.setReadMode.__name__))
            yield deferToThread(self.camera.set_read_mode, readMode)
        finally:
            print("releasing: {}".format(self.setReadMode.__name__))
            self.lock.release()
        if mode is not None:
            returnValue(mode)

    """
    Shutter Mode
    """

    @setting(100, "get_shutter_mode", returns="s")
    def get_shutter_mode(self, c):
        return self.camera.get_shutter_mode()

    @setting(101, "set_shutter_mode", shutterMode="s", returns="")
    def set_shutter_mode(self, c, shutterMode):
        """Sets Current Shutter Mode"""
        mode = None
        print("acquiring: {}".format(self.set_shutter_mode.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.set_shutter_mode.__name__))
            yield deferToThread(self.camera.set_shutter_mode, shutterMode)
        finally:
            print("releasing: {}".format(self.set_shutter_mode.__name__))
            self.lock.release()
        if mode is not None:
            returnValue(mode)

    """
    Acquisition Mode
    """

    @setting(10, "Get Acquisition Mode", returns="s")
    def getAcquisitionMode(self, c):
        """Gets Current Acquisition Mode"""
        return self.camera.get_acquisition_mode()

    @setting(11, "Set Acquisition Mode", mode="s", returns="")
    def setAcquisitionMode(self, c, mode):
        """Sets Current Acquisition Mode"""
        print("acquiring: {}".format(self.setAcquisitionMode.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.setAcquisitionMode.__name__))
            yield deferToThread(self.camera.set_acquisition_mode, mode)
        finally:
            print("releasing: {}".format(self.setAcquisitionMode.__name__))
            self.lock.release()
        self.gui.set_acquisition_mode(mode)

    """
    Trigger Mode
    """

    @setting(12, "Get Trigger Mode", returns="s")
    def getTriggerMode(self, c):
        """Gets Current Trigger Mode"""
        return self.camera.get_trigger_mode()

    @setting(13, "Set Trigger Mode", mode="s", returns="")
    def setTriggerMode(self, c, mode):
        """Sets Current Trigger Mode"""
        print("acquiring: {}".format(self.setTriggerMode.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.setTriggerMode.__name__))
            yield deferToThread(self.camera.set_trigger_mode, mode)
        finally:
            print("releasing: {}".format(self.setTriggerMode.__name__))
            self.lock.release()
        self.gui.set_trigger_mode(mode)

    """
    Exposure Time
    """

    @setting(14, "Get Exposure Time", returns="v[s]")
    def getExposureTime(self, c):
        """Gets Current Exposure Time"""
        time = self.camera.get_exposure_time()
        return WithUnit(time, "s")

    @setting(15, "Set Exposure Time", expTime="v[s]", returns="v[s]")
    def setExposureTime(self, c, expTime):
        """Sets Current Exposure Time"""
        print("acquiring: {}".format(self.setExposureTime.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.setExposureTime.__name__))
            yield deferToThread(self.camera.set_exposure_time, expTime["s"])
        finally:
            print("releasing: {}".format(self.setExposureTime.__name__))
            self.lock.release()
        # need to request the actual set value because it may differ from the request when the request is not possible
        time = self.camera.get_exposure_time()
        if c is not None:
            self.gui.set_exposure(time)
        returnValue(WithUnit(time, "s"))

    """
    Image Region
    """

    @setting(16, "Get Image Region", returns="*i")
    def getImageRegion(self, c):
        """Gets Current Image Region"""
        return self.camera.get_image()

    @setting(
        17,
        "Set Image Region",
        horizontalBinning="i",
        verticalBinning="i",
        horizontalStart="i",
        horizontalEnd="i",
        verticalStart="i",
        verticalEnd="i",
        returns="",
    )
    def setImageRegion(
        self,
        c,
        horizontalBinning,
        verticalBinning,
        horizontalStart,
        horizontalEnd,
        verticalStart,
        verticalEnd,
    ):
        """Sets Current Image Region"""
        print("acquiring: {}".format(self.setImageRegion.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.setImageRegion.__name__))
            yield deferToThread(
                self.camera.set_image,
                horizontalBinning,
                verticalBinning,
                horizontalStart,
                horizontalEnd,
                verticalStart,
                verticalEnd,
            )
        finally:
            print("releasing: {}".format(self.setImageRegion.__name__))
            self.lock.release()

    """
    Acquisition
    """

    @setting(18, "Start Acquisition", returns="")
    def startAcquisition(self, c):
        print("acquiring: {}".format(self.startAcquisition.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.startAcquisition.__name__))
            # speeds up the call to start_acquisition
            yield deferToThread(self.camera.prepare_acqusition)
            yield deferToThread(self.camera.start_acquisition)
            # necessary so that start_acquisition call completes even for long kinetic series
            # yield self.wait(0.050)
            yield self.wait(0.1)
        finally:
            print("releasing: {}".format(self.startAcquisition.__name__))
            self.lock.release()

    @setting(19, "Wait For Acquisition", returns="")
    def waitForAcquisition(self, c):
        print("acquiring: {}".format(self.waitForAcquisition.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.waitForAcquisition.__name__))
            yield deferToThread(self.camera.wait_for_acquisition)
        finally:
            print("releasing: {}".format(self.waitForAcquisition.__name__))
            self.lock.release()

    @setting(20, "Abort Acquisition", returns="")
    def abortAcquisition(self, c):
        if c is not None and self.gui.live_update_running:
            yield self.gui.stop_live_display()
        print("acquiring: {}".format(self.abortAcquisition.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.abortAcquisition.__name__))
            yield deferToThread(self.camera.abort_acquisition)
        finally:
            print("releasing: {}".format(self.abortAcquisition.__name__))
            self.lock.release()

    @setting(21, "Get Acquired Data", num_images="i", returns="*i")
    def getAcquiredData(self, c, num_images=1):
        """Get the acquired images"""
        print("acquiring: {}".format(self.getAcquiredData.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.getAcquiredData.__name__))
            image = yield deferToThread(self.camera.get_acquired_data, num_images)
        finally:
            print("releasing: {}".format(self.getAcquiredData.__name__))
            self.lock.release()
        returnValue(image)

    @setting(33, "Get Summed Data", num_images="i", returns="*i")
    def getSummedData(self, c, num_images=1):
        """Get the counts with the vertical axis summed over."""

        print("acquiring: {}".format(self.getAcquiredData.__name__))
        yield self.lock.acquire()
        try:
            print("acquired: {}".format(self.getAcquiredData.__name__))
            images = yield deferToThread(self.camera.get_acquired_data, num_images)
            hbin, vbin, hstart, hend, vstart, vend = self.camera.get_image()
            x_pixels = int((hend - hstart + 1.0) / hbin)
            y_pixels = int(vend - vstart + 1.0) / vbin
            images = np.reshape(images, (num_images, y_pixels, x_pixels))
            images = images.sum(axis=1)
            images = np.ravel(images, order="C")
            images = images.tolist()
        finally:
            print("releasing: {}".format(self.getAcquiredData.__name__))
            self.lock.release()
        returnValue(images)

    """
    General
    """

    @setting(22, "Get Camera Serial Number", returns="i")
    def getCameraSerialNumber(self, c):
        """Gets Camera Serial Number"""
        return self.camera.get_camera_serial_number()

    @setting(23, "Get Most Recent Image", returns="*i")
    def getMostRecentImage(self, c):
        """Get all Data"""
        #         print('acquiring: {}'.format(self.getMostRecentImage.__name__))
        yield self.lock.acquire()
        try:
            #             print('acquired : {}'.format(self.getMostRecentImage.__name__))
            image = yield deferToThread(self.camera.get_most_recent_image)
        finally:
            #             print('releasing: {}'.format(self.getMostRecentImage.__name__))
            self.lock.release()
        returnValue(image)

    @setting(24, "Start Live Display", returns="")
    def startLiveDisplay(self, c):
        """Starts live display of the images on the GUI"""
        yield self.gui.start_live_display()

    @setting(25, "Is Live Display Running", returns="b")
    def isLiveDisplayRunning(self, c):
        return self.gui.live_update_running

    @setting(26, "Get Number Kinetics", returns="i")
    def getNumberKinetics(self, c):
        """Gets Number Of Scans In A Kinetic Cycle"""
        return self.camera.get_number_kinetics()

    @setting(27, "Set Number Kinetics", numKin="i", returns="")
    def setNumberKinetics(self, c, numKin):
        """Sets Number Of Scans In A Kinetic Cycle"""
        print("acquiring: {}".format(self.setNumberKinetics.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.setNumberKinetics.__name__))
            yield deferToThread(self.camera.set_number_kinetics, numKin)
        finally:
            print("releasing: {}".format(self.setNumberKinetics.__name__))
            self.lock.release()

    # UPDATED THE TIMEOUT. FIX IT LATER
    @setting(28, "Wait For Kinetic", timeout="v[s]", returns="b")
    def waitForKinetic(self, c, timeout=WithUnit(1, "s")):
        """Waits until the given number of kinetic images are completed"""
        request_calls = int(timeout["s"] / 0.050)  # number of request calls
        for i in range(request_calls):
            print("acquiring: {}".format(self.waitForKinetic.__name__))
            yield self.lock.acquire()
            try:
                print("acquired : {}".format(self.waitForKinetic.__name__))
                status = yield deferToThread(self.camera.get_status)
                # useful for debugging of how many iterations have been completed in case of missed trigger pulses
                a, b = yield deferToThread(self.camera.get_series_progress)
                print(a, b)
                print(status)
            finally:
                print("releasing: {}".format(self.waitForKinetic.__name__))
                self.lock.release()
            if status == "DRV_IDLE":
                returnValue(True)
            yield self.wait(0.050)
        returnValue(False)

    @setting(31, "Get Detector Dimensions", returns="ww")
    def get_detector_dimensions(self, c):
        print("acquiring: {}".format(self.get_detector_dimensions.__name__))
        yield self.lock.acquire()
        try:
            print("acquired : {}".format(self.get_detector_dimensions.__name__))
            dimensions = yield deferToThread(self.camera.get_detector_dimensions)
        finally:
            print("releasing: {}".format(self.get_detector_dimensions.__name__))
            self.lock.release()
        returnValue(dimensions)

    @setting(32, "getemrange", returns="(ii)")
    def getemrange(self, c):
        # emrange = yield self.camera.get_camera_em_gain_range()
        # returnValue(emrange)
        return self.camera.get_camera_em_gain_range()

    def wait(self, seconds, result=None):
        """Returns a deferred that will be fired later"""
        d = Deferred()
        reactor.callLater(seconds, d.callback, result)
        return d

    def stop(self):
        self._stopServer()

    @inlineCallbacks
    def stopServer(self):
        """Shuts down camera before closing"""
        try:
            if self.gui.live_update_running:
                yield self.gui.stop_live_display()
            print("acquiring: {}".format(self.stopServer.__name__))
            yield self.lock.acquire()
            print("acquired : {}".format(self.stopServer.__name__))
            self.camera.shut_down()
            print("releasing: {}".format(self.stopServer.__name__))
            self.lock.release()
        except Exception:
            # not yet created
            pass

    @setting(201, returns="")
    def start_signal_loop(self, c):
        """Start the loop sending images to remote clients"""
        self.live_update_loop = LoopingCall(
            self.update_signal_loop
        )  # loop to send images to remote clients
        self.last_image = None  # the last retrived image
        self.live_update_loop.start(
            0.1
        )  # a reasonable interval considering the Network speed,
        # setting it shorter should not negatively influence the performance

    @setting(202, returns="")
    def stop_signal_loop(self, c):
        """Stop the loop sending images to remote clients"""
        self.live_update_loop.stop()

    @inlineCallbacks
    def update_signal_loop(self):
        data = yield self.getMostRecentImage(None)
        # if there is a new image since the last update, send a signal to the clients
        if data != self.last_image:
            self.last_image = data
            yield self.image_updated(data)


if __name__ == "__main__":
    from labrad import util

    util.runServer(AndorServer())
