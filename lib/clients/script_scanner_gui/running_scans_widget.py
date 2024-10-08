from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtGui import *
from common.lib.clients.script_scanner_gui.qtui import FixedWidthButton, ProgressBar
import logging

logger = logging.getLogger(__name__)


class ScriptStatusWidget(QWidget):

    on_pause = QtCore.pyqtSignal()
    on_continue = QtCore.pyqtSignal()
    on_stop = QtCore.pyqtSignal()

    def __init__(self, reactor, ident, name, font=None, parent=None):
        super(ScriptStatusWidget, self).__init__(parent)
        self.reactor = reactor
        self.ident = ident
        self.name = name
        self.parent = parent
        self.font = QFont(self.font().family(), pointSize=10)
        if self.font is None:
            self.font = QFont()
        self.setup_layout()
        self.connect_layout()
        self.finished = False

    def setup_layout(self):
        layout = QHBoxLayout()
        self.id_label = QLabel("{0}".format(self.ident))
        self.id_label.setFont(self.font)
        self.id_label.setMinimumWidth(30)
        self.id_label.setMinimumHeight(15)
        self.id_label.setAlignment(QtCore.Qt.AlignCenter)
        self.id_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.name_label = QLabel(self.name)
        self.name_label.setFont(self.font)
        self.name_label.setAlignment(QtCore.Qt.AlignLeft)
        self.name_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.name_label.setMinimumWidth(150)
        self.name_label.setMinimumHeight(15)
        self.progress_bar = ProgressBar(self.reactor, self.parent)
        self.pause_button = FixedWidthButton("Pause", (75, 15))
        self.stop_button = FixedWidthButton("Stop", (75, 15))
        layout.addWidget(self.id_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.pause_button)
        layout.addWidget(self.stop_button)
        layout.setSizeConstraint(layout.SetMinimumSize)
        self.setLayout(layout)

    # noinspection PyUnresolvedReferences
    def connect_layout(self):
        self.stop_button.pressed.connect(self.on_user_stop)
        self.pause_button.pressed.connect(self.on_user_pause)

    def on_user_pause(self):
        if self.pause_button.text() == "Pause":
            self.on_pause.emit()
        else:
            self.on_continue.emit()

    def on_user_stop(self):
        self.on_stop.emit()

    def set_paused(self, is_paused):
        if is_paused:
            self.pause_button.setText("Continue")
        else:
            self.pause_button.setText("Pause")

    def set_status(self, status, percentage):
        self.progress_bar.set_status(status, percentage)

    def closeEvent(self, x):
        self.reactor.stop()


class RunningScansList(QTableWidget):

    on_pause = QtCore.pyqtSignal(int, bool)
    on_stop = QtCore.pyqtSignal(int)

    def __init__(self, reactor, font=None, parent=None):
        super(RunningScansList, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.font = font
        if self.font is None:
            self.font = QFont("MS Shell Dlg 2", pointSize=12)
        self.setup_layout()
        self.d = {}
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.mapper_pause = QtCore.QSignalMapper()
        self.mapper_pause.mapped.connect(self.emit_pause)
        self.mapper_continue = QtCore.QSignalMapper()
        self.mapper_continue.mapped.connect(self.emit_continue)
        self.mapper_stop = QtCore.QSignalMapper()
        self.mapper_stop.mapped.connect(self.on_stop.emit)

    def emit_pause(self, ident):
        self.on_pause.emit(ident, True)

    def emit_continue(self, ident):
        self.on_pause.emit(ident, False)

    def setup_layout(self):
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setColumnCount(1)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

    def add(self, ident, name):
        ident = int(ident)
        row_count = self.rowCount()
        self.setRowCount(row_count + 1)
        widget = ScriptStatusWidget(
            self.reactor, parent=self.parent, ident=ident, name=name
        )
        # set up signal mapping
        self.mapper_continue.setMapping(widget, ident)
        widget.on_continue.connect(self.mapper_continue.map)
        self.mapper_stop.setMapping(widget, ident)
        widget.on_stop.connect(self.mapper_stop.map)
        self.mapper_pause.setMapping(widget, ident)
        widget.on_pause.connect(self.mapper_pause.map)
        # insert widget
        self.setCellWidget(row_count, 0, widget)
        self.resizeColumnsToContents()
        self.d[ident] = widget

    def set_status(self, ident, status, percentage):
        try:
            widget = self.d[ident]
        except KeyError:
            logger.error("trying set status of experiment that's not there")
        else:
            widget.set_status(status, percentage)

    def set_paused(self, ident, is_paused):
        try:
            widget = self.d[ident]
        except KeyError:
            logger.error("trying set pause experiment that's not there")
        else:
            widget.set_paused(is_paused)

    def remove(self, ident):
        widget = self.d[ident]
        for row in range(self.rowCount()):
            if self.cellWidget(row, 0) == widget:
                del self.d[ident]
                self.removeRow(row)

    def sizeHint(self):
        width = 0
        for i in range(self.columnCount()):
            width += self.columnWidth(i)
        height = 0
        for i in range(self.rowCount()):
            height += self.rowHeight(i)
        return QtCore.QSize(width, height)

    def finish(self, ident):
        try:
            self.remove(ident)
        except KeyError:
            logger.error("trying remove experiment {0} that's not there".format(ident))

    def closeEvent(self, x):
        self.reactor.stop()


class RunningCombined(QWidget):
    """
    What does this class do?
    Instantiated in the scripting_widget class
    TODO: more descriptive class name
    TODO: rename class with proper syntax
    """

    def __init__(self, reactor, font=None, parent=None):
        """
        Parameters
        ----------
        reactor: Qt reactor?
        font: ?
        parent: ?
        """
        super(RunningCombined, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.font = font
        if self.font is None:
            self.font = QFont("MS Shell Dlg 2", pointSize=12)
        self.setupLayout()

    def clear_all(self):
        self.scans_list.clear()

    def setupLayout(self):
        layout = QGridLayout()
        title = QLabel("Running", font=self.font)
        title.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        title.setAlignment(QtCore.Qt.AlignLeft)
        self.scans_list = RunningScansList(self.reactor, self.parent)
        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(self.scans_list, 1, 0, 3, 3)
        self.setLayout(layout)

    def add(self, ident, name):
        """
        Parameters
        ----------
        ident: ?
        name: ?
        """
        self.scans_list.add(ident, name)

    def set_status(self, ident, status, percentage):
        self.scans_list.set_status(ident, status, percentage)

    def paused(self, ident, is_paused):
        self.scans_list.set_paused(ident, is_paused)

    def finish(self, ident):
        self.scans_list.finish(ident)

    def closeEvent(self, x):
        self.reactor.stop()
