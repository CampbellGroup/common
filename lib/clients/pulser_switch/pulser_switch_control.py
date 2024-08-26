from PyQt5.QtWidgets import *

from twisted.internet.defer import inlineCallbacks, returnValue
from common.lib.clients.connection import Connection
import logging
logger = logging.getLogger(__name__)

"""
The Switch Control GUI lets the user control the TTL channels of the Pulser

Version 1.0
"""

SIGNALID = 378902


class SwitchWidget(QFrame):
    def __init__(self, reactor, cxn=None, parent=None):
        super(SwitchWidget, self).__init__(parent=parent)
        self.initialized = False
        self.reactor = reactor
        self.cxn = cxn
        self.connect()

    @inlineCallbacks
    def connect(self):
        if self.cxn is None:
            self.cxn = Connection()
            yield self.cxn.connect()
            from labrad.types import Error
            self.Error = Error
        self.context = yield self.cxn.context()
        try:
            displayed_channels = yield self.get_displayed_channels()
            yield self.initialize_gui(displayed_channels)
            yield self.setup_listeners()
        except Exception as e:
            logger.error(e)
            logger.error('Pulser not available')
            self.setDisabled(True)
        self.cxn.add_on_connect('Pulser', self.reinitialize)
        self.cxn.add_on_disconnect('Pulser', self.disable)

    @inlineCallbacks
    def get_displayed_channels(self):
        """
        get a list of all available channels from the pulser. only show the ones
        listed in the registry. If there is no listing, will display all channels.
        """
        server = yield self.cxn.get_server('Pulser')
        all_channels = yield server.get_ttl_channels(context=self.context)
        all_names = [el[0] for el in all_channels]
        channels_to_display = yield self.registry_load_displayed(all_names)
        if channels_to_display is None:
            channels_to_display = all_names
        channels = [name for name in channels_to_display if name in all_names]
        returnValue(channels)

    @inlineCallbacks
    def registry_load_displayed(self, all_names):
        reg = yield self.cxn.get_server('Registry')
        yield reg.cd(['Clients', 'Switch Control'], True, context=self.context)
        try:
            displayed = yield reg.get('display_channels', context=self.context)
        except self.Error as e:
            if e.code == 21:
                # key error
                yield reg.set('display_channels', all_names, context=self.context)
                displayed = None
            else:
                raise
        returnValue(displayed)

    @inlineCallbacks
    def reinitialize(self):
        self.setDisabled(False)
        server = yield self.cxn.get_server('Pulser')
        if self.initialized:
            yield server.signal__switch_toggled(SIGNALID, context=self.context)
            for name in self.d.keys():
                self.set_state_no_signals(name, server)
        else:
            yield self.initialize_gui()
            yield self.setup_listeners()

    @inlineCallbacks
    def initialize_gui(self, channels):
        """
        Lays out the GUI

        @var channels: a list of channels to be displayed.
        """
        server = yield self.cxn.get_server('Pulser')
        self.d = {}
        # set layout
        layout = QVBoxLayout()
        q_box = QGroupBox('Pulser TTL Control')
        sublayout = QHBoxLayout()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        # get switch names and add them to the layout, and connect their function
        for order, name in enumerate(channels):
            # setting up physical container
            group_box = QWidget()
            group_box_layout = QVBoxLayout()

            button_on = QPushButton('ON')
            button_on.setAutoExclusive(True)
            button_on.setCheckable(True)

            button_off = QPushButton('OFF')
            button_off.setCheckable(True)
            button_off.setAutoExclusive(True)

            button_auto = QPushButton('Auto')
            button_auto.setCheckable(True)
            button_auto.setAutoExclusive(True)

            group_box_layout.addWidget(QLabel(name))
            group_box_layout.addWidget(button_on)
            group_box_layout.addWidget(button_off)
            group_box_layout.addWidget(button_auto)

            group_box.setLayout(group_box_layout)
            # adding to dictionary for signal following
            self.d[name] = {}
            self.d[name]['ON'] = button_on
            self.d[name]['OFF'] = button_off
            self.d[name]['AUTO'] = button_auto
            # setting initial state
            yield self.set_state_no_signals(name, server)
            button_on.clicked.connect(self.button_connection_manual_on(name, server))
            button_off.clicked.connect(self.button_connection_manual_off(name, server))
            button_auto.clicked.connect(self.button_connection_auto(name, server))
            sublayout.addWidget(group_box)  # , 0, 1 + order)
        q_box.setLayout(sublayout)
        layout.addWidget(q_box)
        self.setLayout(layout)
        self.initialized = True

    @inlineCallbacks
    def set_state_no_signals(self, name, server):
        initstate = yield server.get_state(name, context=self.context)
        ismanual = initstate[0]
        manstate = initstate[1]
        if not ismanual:
            self.d[name]['AUTO'].blockSignals(True)
            self.d[name]['AUTO'].setChecked(True)
            self.d[name]['AUTO'].blockSignals(False)
        else:
            if manstate:
                self.d[name]['ON'].blockSignals(True)
                self.d[name]['ON'].setChecked(True)
                self.d[name]['ON'].blockSignals(False)
            else:
                self.d[name]['OFF'].blockSignals(True)
                self.d[name]['OFF'].setChecked(True)
                self.d[name]['OFF'].blockSignals(False)

    def button_connection_manual_on(self, name, server):
        @inlineCallbacks
        def func(state):
            yield server.switch_manual(name, True, context=self.context)

        return func

    def button_connection_manual_off(self, name, server):
        @inlineCallbacks
        def func(state):
            yield server.switch_manual(name, False, context=self.context)

        return func

    def button_connection_auto(self, name, server):
        @inlineCallbacks
        def func(state):
            yield server.switch_auto(name, context=self.context)

        return func

    @inlineCallbacks
    def setup_listeners(self):
        server = yield self.cxn.get_server('Pulser')
        yield server.signal__switch_toggled(SIGNALID, context=self.context)
        yield server.addListener(listener=self.follow_signal, source=None, ID=SIGNALID, context=self.context)

    def follow_signal(self, x, state_tuple):
        (switch_name, state) = state_tuple
        if switch_name not in self.d.keys(): return None
        if state == 'Auto':
            button = self.d[switch_name]['AUTO']
        elif state == 'ManualOn':
            button = self.d[switch_name]['ON']
        elif state == 'ManualOff':
            button = self.d[switch_name]['OFF']
        button.setChecked(True)

    def closeEvent(self, x):
        self.reactor.stop()

    @inlineCallbacks
    def disable(self):
        self.setDisabled(True)
        yield None


if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    triggerWidget = SwitchWidget(reactor)
    triggerWidget.show()
    reactor.run()
