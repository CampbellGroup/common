from PyQt4 import QtGui, uic
from twisted.internet.defer import inlineCallbacks
from common.lib.clients.connection import connection
import os

SIGNALID = 874193


class pmtWidget(QtGui.QWidget):
    def __init__(self, reactor, cxn=None):
        super(pmtWidget, self).__init__()
        self.reactor = reactor
        base_path = os.path.dirname(__file__)
        path = os.path.join(base_path, "pmtfrontend.ui")
        uic.loadUi(path, self)
        self.cxn = cxn
        self.connect()

    @inlineCallbacks
    def connect(self):
        from labrad import types as T
        self.T = T
        if self.cxn is None:
            self.cxn = connection(name='PMT Client')
            yield self.cxn.connect()
        self.server = yield self.cxn.get_server('normalpmtflow')
        yield self.initializeContent()
        yield self.setupListeners()
        # connect functions
        self.pushButton.toggled.connect(self.on_toggled)
        self.newSet.clicked.connect(self.onNewSet)
        self.doubleSpinBox.valueChanged.connect(self.onNewDuration)
        self.comboBox.currentIndexChanged.connect(self.onNewMode)

    @inlineCallbacks
    def setupListeners(self):
        yield self.server.signal__new_count(SIGNALID)
        yield self.server.signal__new_setting(SIGNALID + 1)
        yield self.server.addListener(listener=self.followSignal,
                                      source=None, ID=SIGNALID)
        yield self.server.addListener(listener=self.followSetting,
                                      source=None, ID=SIGNALID + 1)

    @inlineCallbacks
    def initializeContent(self):
        dataset = yield self.server.currentdataset()
        self.lineEdit.setText(dataset)
        running = yield self.server.isrunning()
        self.pushButton.setChecked(running)
        self.setText(self.pushButton)
        duration = yield self.server.get_time_length()
        try:
            ran = yield self.server.get_time_length_range()
        except Exception:
            # not able to obtain
            pass
        else:
            self.doubleSpinBox.setRange(*ran)
        mode = yield self.server.getcurrentmode()
        index = self.comboBox.findText(mode)
        self.comboBox.setCurrentIndex(index)
        self.lcdNumber.display('OFF')

        self.doubleSpinBox.setValue(duration['s'])

    def followSignal(self, signal, value):
        # print signal,value
        self.lcdNumber.display(value)

    def followSetting(self, signal, message):
        setting, val = message
        if setting == "mode":
            index = self.comboBox.findText(val)
            self.comboBox.blockSignals(True)
            self.comboBox.setCurrentIndex(index)
            self.comboBox.blockSignals(False)
        if setting == 'dataset':
            self.lineEdit.blockSignals(True)
            self.lineEdit.setText(val)
            self.lineEdit.blockSignals(False)
        if setting == 'state':
            self.pushButton.blockSignals(True)
            if val == 'on':
                self.pushButton.setChecked(True)
            else:
                self.pushButton.setChecked(False)
                self.lcdNumber.display('OFF')
            self.pushButton.blockSignals(False)
            self.setText(self.pushButton)
        if setting == 'timelength':
            self.doubleSpinBox.blockSignals(True)
            self.doubleSpinBox.setValue(float(val))
            self.doubleSpinBox.blockSignals(False)

    @inlineCallbacks
    def on_toggled(self, state):
        if state:
            yield self.server.record_data()
            new_set = yield self.server.currentdataset()
            self.lineEdit.setText(new_set)
        else:
            yield self.server.stoprecording()
            self.lcdNumber.display('OFF')
        self.setText(self.pushButton)

    @inlineCallbacks
    def onNewSet(self, x):
        new_set = yield self.server.start_new_dataset()
        self.lineEdit.setText(new_set)

    @inlineCallbacks
    def onNewMode(self, mode):
        text = str(self.comboBox.itemText(mode))
        yield self.server.set_mode(text)

    def setText(self, obj):
        state = obj.isChecked()
        if state:
            obj.setText('ON')
        else:
            obj.setText('OFF')

    def onNewData(self, count):
        self.lcdNumber.display(count)

    @inlineCallbacks
    def onNewDuration(self, value):
        value = self.T.Value(value, 's')
        yield self.server.set_time_length(value)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    pmtWidget = pmtWidget(reactor)
    pmtWidget.show()
    reactor.run()
