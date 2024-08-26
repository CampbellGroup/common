import sys
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QPushButton,
    QWidget,
    QAction,
    QTabWidget,
    QVBoxLayout,
    QLabel,
)
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QGroupBox,
    QDialog,
    QVBoxLayout,
    QGridLayout,
)
import os
from PyQt5 import uic


import os

basepath = os.path.dirname(__file__)
path = os.path.join(basepath, "..", "..", "Views", "EventEditor.ui")
base, form = uic.loadUiType(path)


class EventEditor(base, form):
    def __init__(self, parent=None):
        super(EventEditor, self).__init__(parent)
        self.setupUi(self)
        self._dataMapper = QDataWidgetMapper(self)
        self.connect_layout()

    def connect_layout(self):
        self.uiBool.clicked.connect(self.on_check)
        self.uiChan.valueChanged.connect(self.on_chan_changed)
        self.uiTime.valueChanged.connect(self.on_time_changed)

    def on_check(self):
        self._dataMapper.itemDelegate().commitData.emit(self.uiBool)

    def on_chan_changed(self):
        self._dataMapper.itemDelegate().commitData.emit(self.uiChan)

    def on_time_changed(self):
        self._dataMapper.itemDelegate().commitData.emit(self.uiTime)

    def on_new_decimals(self, decimals):
        for widget in [self.uiTime]:
            widget.setSingleStep(10**-decimals)
            widget.setDecimals(decimals)

    def set_suffix(self, suffix):
        for widget in [self.uiTime]:
            widget.setSuffix(suffix)

    def set_minimum(self, value):
        for widget in [self.uiTime]:
            widget.setMinimum(value)

    def set_maximum(self, value):
        for widget in [self.uiTime]:
            widget.setMaximum(value)

    def setModel(self, proxyModel):
        self._proxyModel = proxyModel
        self._dataMapper.setModel(proxyModel.sourceModel())
        self._dataMapper.addMapping(self.uiName, 0)
        self._dataMapper.addMapping(self.uiCollection, 2)
        self._dataMapper.addMapping(self.uiBool, 3)
        self._dataMapper.addMapping(self.uiChan, 4)
        self._dataMapper.addMapping(self.uiTime, 5)
        self._dataMapper.addMapping(QWidget(self), 8)

    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)
