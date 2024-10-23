
from ast import literal_eval
from PyQt5.QtWidgets import QWidget
from twisted.internet.defer import inlineCallbacks

from config.signal_config import signal_config
from common.lib.clients.connection import Connection
from common.lib.clients.status_bar.ui_status_bar import Ui_StatusBar


class StatusBar(QWidget, Ui_StatusBar):
    def __init__(self, reactor, cxn=None):
        super().__init__()
        self.reactor = reactor
        self.setupUi(self)
        self.cxn = cxn
        self.c_boxes = [eval(f'self.c{i}{j}', {'self': self}) for i in range(2) for j in range(5)]

        self.signals = sorted(signal_config.keys())
        self.servers = {}
        self.id_boxes = {signal_config.get_id(signal): [] for signal in self.signals}
        self.id_servers = {signal_config.get_id(signal): signal[:signal.find('__')] for signal in self.signals}
        self.signals.insert(0, '')
        self.connect()

    @inlineCallbacks
    def connect(self):
        from labrad import types as t
        self.T = t
        if self.cxn is None:
            self.cxn = Connection(name='StatusBar Client')
            yield self.cxn.connect()
        self.init_ui()
        for c in self.c_boxes:
            c.currentIndexChanged.connect(lambda index, _c=c: self.set_signal(_c))

    def init_ui(self):
        for c in self.c_boxes:
            c.addItems(self.signals)

    @inlineCallbacks
    def add_listener(self, _id):
        yield eval(f'self.servers[_id].{signal_config.signal[_id].replace(self.id_servers[_id], "signal")}(_id)',
                   {'self': self, '_id': _id})
        yield self.servers[_id].addListener(listener=self.update_status, source=None, ID=_id)

    @inlineCallbacks
    def remove_listener(self, _id):
        yield self.servers[_id].removeListener(listener=self.update_status, source=None, ID=_id)

    @inlineCallbacks
    def set_signal(self, c):
        signal = c.currentText()
        id_set = signal_config.get_id(signal)

        for _, c_list in self.id_boxes.items():
            try:
                c_list.remove(c)
            except ValueError:
                pass
        self.id_boxes[id_set].append(c)

        if signal and self.servers.get(id_set, None) is None:
            self.servers[id_set] = yield self.cxn.get_server(self.id_servers[id_set])
            yield self.add_listener(id_set)

        for _id in self.servers.keys():
            if not self.id_boxes[_id]:
                del self.servers[_id]
                yield self.remove_listener(_id)

    def update_status(self, signal=None, value=None):
        print(signal, value)
        if signal is None or value is None:
            return

        for c in self.id_boxes[signal.target]:
            c.setStyleSheet(f'background-color: {"green" if value > 6 else "red"};')
            c.repaint()
