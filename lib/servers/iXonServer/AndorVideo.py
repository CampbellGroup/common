from config.andor_config import andor_config as config
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
import numpy as np
import pyqtgraph as pg
import datetime as datetime
from datetime import datetime
import os


class AndorVideo(QWidget):
    def __init__(self, server):
        super(AndorVideo, self).__init__()
        from labrad.units import WithUnit

        self.WithUnit = WithUnit
        self.server = server
        self.setup_layout()
        self.live_update_loop = LoopingCall(self.live_update)
        self.connect_layout()
        self.saved_data = None
        self.buffer = list()

        self.save_images_state = False
        self.image_path = config.image_path

        try:
            self.save_in_sub_dir = config.save_in_sub_dir
        except Exception as e:
            self.save_in_sub_dir = False
            print("save_in_sub_dir not found in config")
        try:
            self.save_format = config.save_format
        except Exception as e:
            self.save_format = "tsv"
            print("save_format not found in config")
        try:
            self.save_header = config.save_header
        except Exception as e:
            self.save_header = False
            print("save_header not found in config")

    #        emrange= yield self.server.getemrange(None)
    #        self.emccdSpinBox.setMinimum(emrange[0])
    #        self.emccdSpinBox.setMaximum(emrange[1])
    @inlineCallbacks
    def setup_layout(self):
        self.setWindowTitle("Andor")
        # layout
        layout = QGridLayout()
        self.plt = plt = pg.PlotItem()
        self.img_view = pg.ImageView(view=self.plt)
        plt.showAxis("top")
        plt.hideAxis("bottom")
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
        self.exposureSpinBox.setSuffix(" s")
        layout.addWidget(
            exposure_label,
            1,
            4,
        )
        layout.addWidget(self.exposureSpinBox, 1, 5)
        # EMCCD Gain
        emccd_label = QLabel("EMCCD Gain")
        emccd_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.emccdSpinBox = QSpinBox()
        self.emccdSpinBox.setSingleStep(1)
        # emrange= yield self.server.getemrange(None)
        self.emrange = yield self.server.getemrange(None)
        mingain, maxgain = self.emrange
        self.emccdSpinBox.setMinimum(mingain)  # mingain)
        self.emccdSpinBox.setMaximum(maxgain)  # maxgain)
        print(maxgain)
        self.emccdSpinBox.setKeyboardTracking(False)
        layout.addWidget(
            emccd_label,
            2,
            4,
        )
        layout.addWidget(self.emccdSpinBox, 2, 5)
        # Live Video Button
        self.live_button = QPushButton("Live Video")
        self.live_button.setCheckable(True)
        layout.addWidget(self.live_button, 1, 0)
        # set image region button
        self.set_image_region_button = QPushButton("Set Image Region")
        layout.addWidget(self.set_image_region_button, 2, 0)
        # save images
        self.save_images = QCheckBox("Save Images")
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
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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

    def mouse_clicked(self, event):
        """
        draws the cross at the position of a double click
        """
        pos = event.pos()
        if self.plt.sceneBoundingRect().contains(pos) and event.double():
            # only on double clicks within bounds
            mousePoint = self.plt.vb.mapToView(pos)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    @inlineCallbacks
    def connect_layout(self):
        # self.emrange= yield self.server.getemrange(None)
        # mingain, maxgain = self.emrange
        # self.emccdSpinBox.setMinimum(0)
        # self.emccdSpinBox.setMaximum(4096)
        self.set_image_region_button.clicked.connect(self.on_set_image_region)
        self.plt.scene().sigMouseClicked.connect(self.mouse_clicked)
        exposure = yield self.server.getExposureTime(None)
        self.exposureSpinBox.setValue(exposure["s"])
        self.exposureSpinBox.valueChanged.connect(self.on_new_exposure)
        gain = yield self.server.getEMCCDGain(None)
        self.emccdSpinBox.setValue(gain)
        trigger_mode = yield self.server.getTriggerMode(None)
        self.trigger_mode.setText(trigger_mode)
        acquisition_mode = yield self.server.getAcquisitionMode(None)
        self.acquisition_mode.setText(acquisition_mode)
        self.emccdSpinBox.valueChanged.connect(self.on_new_gain)
        self.live_button.clicked.connect(self.on_live_button)
        self.auto_levels_button.clicked.connect(self.on_auto_levels_button)
        self.view_all_button.clicked.connect(self.on_auto_range_button)
        self.save_images.stateChanged.connect(
            lambda state=self.save_images.isChecked(): self.save_image_data(state)
        )

    def save_image_data(self, state):
        if state >= 1:
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
        if self.live_update_loop.running:
            yield self.on_live_button(False)
            yield self.server.setExposureTime(None, self.WithUnit(exposure, "s"))
            yield self.on_live_button(True)
        else:
            yield self.server.setExposureTime(None, self.WithUnit(exposure, "s"))

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
        yield self.server.setEMCCDGain(None, gain)

    def set_gain(self, gain):
        self.emccdSpinBox.blockSignals(True)
        self.emccdSpinBox.setValue(gain)
        self.emccdSpinBox.blockSignals(False)

    @inlineCallbacks
    def on_live_button(self, checked):
        if checked:
            yield self.server.setTriggerMode(None, "Internal")
            yield self.server.setAcquisitionMode(None, "Run till abort")
            yield self.server.set_shutter_mode(None, "Open")
            yield self.server.startAcquisition(None)
            self.binx, self.biny, self.startx, self.stopx, self.starty, self.stopy = (
                yield self.server.getImageRegion(None)
            )
            self.pixels_x = (self.stopx - self.startx + 1) / self.binx
            self.pixels_y = (self.stopy - self.starty + 1) / self.biny
            yield self.server.waitForAcquisition(None)
            self.live_update_loop.start(0)
        else:
            yield self.live_update_loop.stop()
            yield self.server.abortAcquisition(None)
            yield self.server.set_shutter_mode(None, "Close")

    @inlineCallbacks
    def live_update(self):
        data = yield self.server.getMostRecentImage(None)
        image_data = np.reshape(data, (self.pixels_y, self.pixels_x))

        self.buffer.append(image_data.transpose())
        if len(self.buffer) > 5:
            self.buffer.pop()

        self.img_view.setImage(
            self.buffer,  # image_data.transpose(),
            autoRange=False,
            autoLevels=False,
            pos=[self.startx, self.starty],
            scale=[self.binx, self.biny],
            autoHistogramRange=False,
        )

        if self.save_images_state == True:
            self.save_image(image_data)

    def get_image_header(self):
        header = ""
        shutter_time = self.exposureSpinBox.value()
        header += "shutter_time " + str(shutter_time) + "\n"
        em_gain = self.emccdSpinBox.value()
        header += "em_gain " + str(em_gain)
        return header

    def save_image(self, image_data):
        if not np.array_equal(image_data, self.saved_data):
            self.saved_data = image_data
            saved_data_in_int = self.saved_data.astype("int16")
            time_stamp = "-".join(self.datetime_to_str_list())
            if self.save_in_sub_dir:
                path = self.check_save_path_exists()
                path = os.path.join(path, time_stamp)
            else:
                path = os.path.join(self.image_path, time_stamp)
            if self.save_header:
                header = self.get_image_header()
            else:
                header = ""
            if self.save_format == "tsv":
                np.savetxt(path + ".tsv", saved_data_in_int, fmt="%i", header=header)
            elif self.save_format == "csv":
                np.savetxt(
                    path + ".csv",
                    saved_data_in_int,
                    fmt="%i",
                    delimiter=",",
                    header=header,
                )
            elif self.save_format == "bin":
                saved_data_in_int.tofile(path + ".dat")
            else:
                np.savetxt(path + ".tsv", saved_data_in_int, fmt="%i", header=header)

    def datetime_to_str_list(self):
        dt = datetime.now()
        dt_str = [
            str(dt.year).rjust(4, "0"),
            str(dt.month).rjust(2, "0"),
            str(dt.day).rjust(2, "0"),
            str(dt.hour).rjust(2, "0"),
            str(dt.minute).rjust(2, "0"),
            str(dt.second).rjust(2, "0"),
            str(int(dt.microsecond / 1000)).rjust(3, "0"),
        ]
        return dt_str

    def str_datetime_to_path(self, str_datetime):
        year = str_datetime[0]
        month = str_datetime[1]
        day = year + "_" + month + "_" + str_datetime[2]
        return (year, month, day)

    def check_save_path_exists(self):
        folders = self.str_datetime_to_path(self.datetime_to_str_list())
        path = self.image_path
        for sub_dir in folders:
            path = os.path.join(path, sub_dir)
            if not os.path.isdir(path):
                os.makedirs(path)
        return path

    @inlineCallbacks
    def start_live_display(self):
        self.live_button.setChecked(True)
        yield self.on_live_button(True)

    @inlineCallbacks
    def stop_live_display(self):
        self.live_button.setChecked(False)
        yield self.on_live_button(False)

    @property
    def live_update_running(self):
        return self.live_update_loop.running

    def closeEvent(self, event):
        self.server.stop()


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
    def set_image_region(
        self, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver
    ):
        yield self.server.set_image_region(
            bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver
        )

    @inlineCallbacks
    def setupLayout(self):
        self.hor_max, self.ver_max = yield self.server.get_detector_dimensions(None)
        self.hor_min, self.ver_min = [1, 1]
        (
            cur_bin_hor,
            cur_bin_ver,
            cur_start_hor,
            cur_stop_hor,
            cur_start_ver,
            cur_stop_ver,
        ) = yield self.server.getImageRegion(None)
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
                yield self.server.setImageRegion(
                    None, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver
                )
            except Exception as e:
                yield self.parent.on_live_button(True)
            else:
                yield self.parent.on_live_button(True)
                self.close()
        else:
            try:
                yield self.server.setImageRegion(
                    None, bin_hor, bin_ver, start_hor, stop_hor, start_ver, stop_ver
                )
            except Exception as e:
                pass
            else:
                self.close()

    def on_cancel(self, clicked):
        self.close()
