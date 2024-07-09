import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QAction, QTabWidget, QVBoxLayout, QLabel
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout
import os
from PyQt5 import uic

import os

basepath =  os.path.dirname(__file__)
path = os.path.join(basepath,"..","..","Views", "ScanSensitivity.ui")
base, form = uic.loadUiType(path)

class spectrum_sensitivity_editor(base, form):
    def __init__(self, parent=None):
        super(spectrum_sensitivity_editor, self).__init__(parent)
        self.setupUi(self)
        self._dataMapper = QDataWidgetMapper(self)

    def setModel(self, proxyModel):
        self._proxyModel = proxyModel
        self._dataMapper.setModel(proxyModel.sourceModel())
        self._dataMapper.addMapping(self.uiName, 0)
        self._dataMapper.addMapping(self.uiCollection, 2)
        self._dataMapper.addMapping(self.uiSpan, 3)
        self._dataMapper.addMapping(self.uiResolution, 4)
        self._dataMapper.addMapping(self.uiDuration, 5)
        self._dataMapper.addMapping(self.uiAmplitude, 6)

    def setSelection(self, current):
        parent = current.parent()
        self._dataMapper.setRootIndex(parent)
        self._dataMapper.setCurrentModelIndex(current)
