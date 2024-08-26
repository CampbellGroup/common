import AndorConfig as config
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
import numpy as np
import pyqtgraph as pg
import datetime as datetime
from datetime import datetime
import socket
import os

config = config.AndorConfig()

IMAGE_UPDATED_SIGNAL = 125125


class AndorClient(QWidget):
    def __init__(self, reactor, parent=None):
        super(AndorClient, self).__init__()
        from labrad.units import WithUnit
        self.reactor = reactor
        self.WithUnit = WithUnit
        self.connect()

    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection to the wavemeter computer and
        connects incoming signals to relavent functions

        """
        self.name = socket.gethostname() + ' Andor Client'
        from labrad.wrappers import connectAsync
        self.cameraIP = config.camera_ip
        self.password = os.environ['LABRADPASSWORD']
        self.cxn = yield connectAsync(self.cameraIP,
                                      name=self.name,
                                      password=self.password)
        self.server = yield self.cxn.andor_server

        yield self.server.signal__image_updated(IMAGE_UPDATED_SIGNAL)

        yield self.server.addListener(listener=self.image_updated, source=None, ID=IMAGE_UPDATED_SIGNAL)

        self.save_images_state = False
        self.is_live_update_running = False
        self.image_path = config.image_path
        self.setup_layout()

    @inlineCallbacks
    def setup_layout(self):
        self.setWindowTitle("Andor")
        # layout
        layout = QGridLayout()
        self.plt = plt = pg.PlotItem()
        self.img_view = pg.ImageView(view = self.plt)
        plt.showAxis('top')
        plt.hideAxis('bottom')
        plt.setAspectLocked(True)
        layout.addWidget(self.img_view, 0, 0, 1, 6)
        self.img_view.getHistogramWidget().setHistogramRange(0, 1000)
        exposure_label = QLabel("Exposure")
        exposure_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.exposureSpinBox = QDoubleSpinBox()
        self.exposureSpinBox.setDecimals(3)
        self.exposureSpinBox.setSingleStep(0.001)
        self.exposureSpinBox.setMinimum(0.0)
        self.exposureSpinBox.setMaximum(10000.0)
        self.exposureSpinBox.setKeyboardTracking(False)
        self.exposureSpinBox.setSuffix(' s')
        layout.addWidget(exposure_label, 1, 4,)
        layout.addWidget(self.exposureSpinBox, 1, 5)
        # EMCCD Gain
        emccd_label = QLabel("EMCCD Gain")
        emccd_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.emccdSpinBox = QSpinBox()
        self.emccdSpinBox.setSingleStep(1)
        # emrange= yield self.server.getemrange(None)
        self.emrange= yield self.server.getemrange(None)
        mingain, maxgain = self.emrange
        self.emccdSpinBox.setMinimum(mingain)  # mingain)
        self.emccdSpinBox.setMaximum(maxgain)  # maxgain)
        self.emccdSpinBox.setKeyboardTracking(False)
        layout.addWidget(emccd_label, 2, 4,)
        layout.addWidget(self.emccdSpinBox, 2, 5)
        # Live Video Button
        self.live_button = QPushButton("Live Video")
        self.live_button.setCheckable(True)
        layout.addWidget(self.live_button, 1, 0)
        # set image region button
        self.set_image_region_button = QPushButton("Set Image Region")
        layout.addWidget(self.set_image_region_button, 2, 0)
        # save images
        self.save_images = QCheckBox('Save Images')
        layout.addWidget(self.save_images, 3, 0)


        # controlling the display buttons
        self.view_all_button = QPushButton("View All")
        layout.addWidget(self.view_all_button, 1, 1)
        self.auto_levels_button = QPushButton("Auto Levels")
        layout.addWidget(self.auto_levels_button, 2, 1)
        # display mode buttons
        self.trigger_mode = QLineEdit()
        self.acquisition_mode = QLineEdit()
        self.trigger_mode.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.acquisition_mode.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.trigger_mode.setReadOnly(True)
        self.acquisition_mode.setReadOnly(True)
        label = QLabel("Trigger Mode")
        label.setAlignment(Qt.AlignRight| Qt.AlignVCenter)
        layout.addWidget(label, 1, 2)
        label = QLabel("Acquisition Mode")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label, 2, 2)
        layout.addWidget(self.trigger_mode, 1, 3)
        layout.addWidget(self.acquisition_mode, 2, 3)
        # add lines for the cross
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        plt.addItem(self.vLine, ignoreBounds=True)
        plt.addItem(self.hLine, ignoreBounds=True)
        # set the layout and show
        self.setLayout(layout)
        self.show()

        self.connect_layout()

    def mouse_clicked(self, event):
        """
        draws the cross at the position of a double click
        """
        pos = event.pos()
        if self.plt.sceneBoundingRect().contains(pos) and event.double():
            # only on double clicks within bounds
            mouse_point = self.plt.vb.mapToView(pos)
            self.vLine.setPos(mouse_point.x())
            self.hLine.setPos(mouse_point.y())

    @inlineCallbacks
    def connect_layout(self):
        # self.emrange= yield self.server.getemrange(None)
        # mingain, maxgain = self.emrange
        # self.emccdSpinBox.setMinimum(0)
        # self.emccdSpinBox.setMaximum(4096)
        self.set_image_region_button.clicked.connect(self.on_set_image_region)
        self.plt.scene().sigMouseClicked.connect(self.mouse_clicked)
        exposure = yield self.server.get_exposure_time(None)
        self.exposureSpinBox.setValue(exposure['s'])
        self.exposureSpinBox.valueChanged.connect(self.on_new_exposure)
        gain = yield self.server.get_emccd_gain(None)
        self.emccdSpinBox.setValue(gain)
        trigger_mode = yield self.server.get_trigger_mode(None)
        self.trigger_mode.setText(trigger_mode)
        acquisition_mode = yield self.server.get_acquisition_mode(None)
        self.acquisition_mode.setText(acquisition_mode)
        self.emccdSpinBox.valueChanged.connect(self.on_new_gain)
        self.live_button.clicked.connect(self.on_live_button)
        self.auto_levels_button.clicked.connect(self.on_auto_levels_button)
        self.view_all_button.clicked.connect(self.on_auto_range_button)
        self.save_images.stateChanged.connect(lambda state = \
                self.save_images.isChecked() : self.save_image_data(state))

    def save_image_data(self, state):
        if state >=1:
            self.save_images_state = True
        elif state == 0:
            self.save_images_state = False

    def on_set_image_region(self, checked):
        # displays a non-modal dialog
        dialog = image_region_selection_dialog(self, self.server)
        one = dialog.open()
        two = dialog.show()
        three = dialog.raise_()

    def on_auto_levels_button(self, checked):
        self.img_view.autoLevels()

    def on_auto_range_button(self, checked):
        self.img_view.autoRange()

    @inlineCallbacks
    def on_new_exposure(self, exposure):
        if self.is_live_update:
            yield self.on_live_button(False)
            yield self.server.set_exposure_time(self.WithUnit(exposure,'s'))
            yield self.on_live_button(True)
        else:
            yield self.server.set_exposure_time(self.WithUnit(exposure,'s'))

    def set_exposure(self, exposure):
        self.exposureSpinBox.blockSignals(True)
        self.exposureSpinBox.setValue(exposure)
        self.exposureSpinBox.blockSignals(False)

    def set_trigger_mode(self, mode):
        self.trigger_mode.setText(mode)

    def set_acquisition_mode(self, mode):
        self.acquisition_mode.setText(mode)

    @inlineCallbacks
    def on_new_gain(self, gain):
        yield self.server.set_emccd_gain(None, gain)

    def set_gain(self, gain):
        self.emccdSpinBox.blockSignals(True)
        self.emccdSpinBox.setValue(gain)
        self.emccdSpinBox.blockSignals(False)

    def image_updated(self, c, signal): # callback of image updated signal
        image_data = np.reshape(signal, (self.pixels_y, self.pixels_x))
        self.img_view.setImage(image_data.transpose(), autoRange=False, autoLevels=False, pos=[self.startx, self.starty], scale=[self.binx, self.biny], autoHistogramRange=False)

        if self.save_images_state == True:
            dt = datetime.now()
            time_stamp = str(dt.year)+str(dt.month)+str(dt.day)+str(dt.hour)\
            +str(dt.minute)+str(dt.second)+str(dt.microsecond)+'.csv'
            np.savetxt(self.image_path+time_stamp,image_data)

    @inlineCallbacks
    def on_live_button(self, checked):
        if checked:
            yield self.server.set_trigger_mode('Internal')
            yield self.server.set_acquisition_mode('Run till abort')
            yield self.server.set_shutter_mode('Open')
            yield self.server.start_acquisition(None)
            self.binx, self.biny, self.startx, self.stopx, self.starty, self.stopy = yield self.server.get_image_region(None)
            self.pixels_x = (self.stopx - self.startx + 1) / self.binx
            self.pixels_y = (self.stopy - self.starty + 1) / self.biny
            yield self.server.wait_for_acquisition()
            yield self.server.start_signal_loop()  # start the server loop
            self.is_live_update_running = True
        else:
            self.is_live_update_running = False
            yield self.server.stop_signal_loop()  # stop the server loop
            yield self.server.abort_acquisition()
            yield self.server.set_shutter_mode('Close')
    
    @inlineCallbacks
    def start_live_display(self):
        self.live_button.setChecked(True)
        yield self.on_live_button(True)

    @inlineCallbacks
    def stop_live_display(self):
        self.live_button.setChecked(False)
        yield self.on_live_button(False)

    @inlineCallbacks
    def closeEvent(self, event):
        if self.is_live_update_running:
            self.is_live_update_running = False
            yield self.server.stop_loop() # stop the server loop
            yield self.server.abort_acquisition()
            yield self.server.set_shutter_mode('Close')

        self.reactor.stop()   
            

class image_region_selection_dialog(QDialog):
    def __init__(self, parent, server):
        super(image_region_selection_dialog, self).__init__(parent)
        self.server = server
        self.parent = parent
        self.setWindowTitle("Select Region")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setupLayout()

    def sizeHint(self):
        return QSize(300, 120)

    @inlineCallbacks
    def set_image_region(self, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver):
        yield self.server.set_image_region(bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)

    @inlineCallbacks
    def setupLayout(self):
        self.hor_max, self.ver_max =  yield self.server.get_detector_dimensions(None)
        self.hor_min, self.ver_min = [1, 1]
        cur_bin_hor, cur_bin_ver, cur_start_hor, cur_stop_hor, cur_start_ver, cur_stop_ver = yield self.server.get_image_region(None)
        layout = QGridLayout()
        default_button = QPushButton("Default")
        start_label = QLabel("Start")
        stop_label = QLabel("Stop")
        bin_label = QLabel("Bin")
        hor_label = QLabel("Horizontal")
        ver_label = QLabel("Vertical")
        self.start_hor = QSpinBox()
        self.stop_hor = QSpinBox()
        self.bin_hor = QSpinBox()
        for button in [self.start_hor, self.stop_hor, self.bin_hor]:
            button.setRange(self.hor_min, self.hor_max)
        self.start_hor.setValue(cur_start_hor)
        self.stop_hor.setValue(cur_stop_hor)
        self.bin_hor.setValue(cur_bin_hor)
        self.start_ver = QSpinBox()
        self.stop_ver = QSpinBox()
        self.bin_ver = QSpinBox()
        for button in [self.start_ver, self.stop_ver, self.bin_ver]:
            button.setRange(self.ver_min, self.ver_max)
        self.start_ver.setValue(cur_start_ver)
        self.stop_ver.setValue(cur_stop_ver)
        self.bin_ver.setValue(cur_bin_ver)
        layout.addWidget(default_button, 0, 0)
        layout.addWidget(start_label, 0, 1)
        layout.addWidget(stop_label, 0, 2)
        layout.addWidget(bin_label, 0, 3)
        layout.addWidget(hor_label, 1, 0)
        layout.addWidget(self.start_hor, 1, 1)
        layout.addWidget(self.stop_hor, 1, 2)
        layout.addWidget(self.bin_hor, 1, 3)
        layout.addWidget(ver_label, 2, 0)
        layout.addWidget(self.start_ver, 2, 1)
        layout.addWidget(self.stop_ver, 2, 2)
        layout.addWidget(self.bin_ver, 2, 3)
        submit_button = QPushButton("Submit")
        layout.addWidget(submit_button, 3, 0, 1, 2)
        cancel_button = QPushButton("Cancel")
        layout.addWidget(cancel_button, 3, 2, 1, 2)
        default_button.clicked.connect(self.on_default)
        submit_button.clicked.connect(self.on_submit)
        cancel_button.clicked.connect(self.on_cancel)
        self.setLayout(layout)

    def on_default(self, clicked):
        self.bin_hor.setValue(1)
        self.bin_ver.setValue(1)
        self.start_hor.setValue(self.hor_min)
        self.stop_hor.setValue(self.hor_max)
        self.start_ver.setValue(self.ver_min)
        self.stop_ver.setValue(self.ver_max)

    @inlineCallbacks
    def on_submit(self, clicked):
        bin_hor = self.bin_hor.value()
        bin_ver = self.bin_ver.value()
        start_hor = self.start_hor.value()
        stop_hor = self.stop_hor.value()
        start_ver = self.start_ver.value()
        stop_ver = self.stop_ver.value()
        yield self.do_submit(bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)

    @inlineCallbacks
    def do_submit(self, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver):
        if self.parent.live_update_loop.running:
            yield self.parent.on_live_button(False)
            try:
                yield self.server.get_image_region(None, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)
            except Exception as e:
                yield self.parent.on_live_button(True)
            else:
                yield self.parent.on_live_button(True)
                self.close()
        else:
            try:
                yield self.server.get_image_region(None, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver)
            except Exception as e:
                pass
            else:
                self.close()

    def on_cancel(self, clicked):
        self.close()


if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    andorClient = AndorClient(reactor)
    andorClient.show()
    reactor.run()