from PyQt5.QtWidgets import *
from PyQt5 import uic

from twisted.internet.defer import inlineCallbacks
from common.lib.clients.connection import Connection
import os
import logging

logger = logging.getLogger(__name__)

SIGNALID = 874193


# noinspection PyUnresolvedReferences
class PMTWidget(QWidget):
    def __init__(self, reactor, cxn=None):
        super(PMTWidget, self).__init__()
        self.reactor = reactor
        base_path = os.path.dirname(__file__)
        path = os.path.join(base_path, "pmtfrontend.ui")
        uic.loadUi(path, self)
        self.cxn = cxn
        self.connect()

    @inlineCallbacks
    def connect(self):
        from labrad import types as t

        self.T = t
        if self.cxn is None:
            self.cxn = Connection(name="PMT Client")
            yield self.cxn.connect()
        self.server = yield self.cxn.get_server("normalpmtflow")
        yield self.initialize_content()
        yield self.setup_listeners()
        # connect functions
        self.pushButton.toggled.connect(self.on_toggled)
        self.newSet.clicked.connect(self.on_new_set)
        self.doubleSpinBox.valueChanged.connect(self.onNewDuration)
        self.comboBox.currentIndexChanged.connect(self.on_new_mode)

    @inlineCallbacks
    def setup_listeners(self):
        yield self.server.signal__new_count(SIGNALID)
        yield self.server.signal__new_setting(SIGNALID + 1)
        yield self.server.addListener(
            listener=self.follow_signal, source=None, ID=SIGNALID
        )
        yield self.server.addListener(
            listener=self.follow_setting, source=None, ID=SIGNALID + 1
        )

    @inlineCallbacks
    def initialize_content(self):
        dataset = yield self.server.current_dataset()
        self.lineEdit.setText(dataset)
        running = yield self.server.is_running()
        self.pushButton.setChecked(running)
        self.setText(self.pushButton)
        duration = yield self.server.get_time_length()
        try:
            ran = yield self.server.get_time_length_range()
        except Exception as e:
            logger.error(e)
        else:
            self.doubleSpinBox.setRange(*ran)
        mode = yield self.server.get_current_mode()
        index = self.comboBox.findText(mode)
        self.comboBox.setCurrentIndex(index)
        self.lcdNumber.display("OFF")

        self.doubleSpinBox.setValue(duration["s"])

    def follow_signal(self, signal, value):
        self.lcdNumber.display(value)

    def follow_setting(self, signal, message):
        setting, val = message
        if setting == "mode":
            index = self.comboBox.findText(val)
            self.comboBox.blockSignals(True)
            self.comboBox.setCurrentIndex(index)
            self.comboBox.blockSignals(False)
        if setting == "dataset":
            self.lineEdit.blockSignals(True)
            self.lineEdit.setText(val)
            self.lineEdit.blockSignals(False)
        if setting == "state":
            self.pushButton.blockSignals(True)
            if val == "on":
                self.pushButton.setChecked(True)
            else:
                self.pushButton.setChecked(False)
                self.lcdNumber.display("OFF")
            self.pushButton.blockSignals(False)
            self.setText(self.pushButton)
        if setting == "timelength":
            self.doubleSpinBox.blockSignals(True)
            self.doubleSpinBox.setValue(float(val))
            self.doubleSpinBox.blockSignals(False)

    @inlineCallbacks
    def on_toggled(self, state):
        if state:
            logger.debug("PMT toggled on")
            yield self.server.record_data()
            new_set = yield self.server.current_dataset()
            self.lineEdit.setText(new_set)
        else:
            logger.debug("PMT toggled off")
            yield self.server.stop_recording()
            self.lcdNumber.display("OFF")
        self.setText(self.pushButton)

    @inlineCallbacks
    def on_new_set(self, x):
        new_set = yield self.server.start_new_dataset()
        self.lineEdit.setText(new_set)

    @inlineCallbacks
    def on_new_mode(self, mode):
        text = str(self.comboBox.itemText(mode))
        yield self.server.set_mode(text)

    def setText(self, obj):
        state = obj.isChecked()
        if state:
            obj.setText("ON")
        else:
            obj.setText("OFF")

    def onNewData(self, count):
        self.lcdNumber.display(count)

    @inlineCallbacks
    def onNewDuration(self, value):
        value = self.T.Value(value, "s")
        yield self.server.set_time_length(value)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor

    qt5reactor.install()
    from twisted.internet import reactor

    pmtWidget = PMTWidget(reactor)
    pmtWidget.show()
    reactor.run()
