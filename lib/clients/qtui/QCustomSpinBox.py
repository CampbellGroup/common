import sys
import os

from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtGui import QFont


# noinspection PyUnresolvedReferences
class QCustomSpinBox(QWidget):
    onNewValues = QtCore.pyqtSignal()

    def __init__(self, level_range: tuple, title: str = None, suffix: str = None, parent=None):
        QWidget.__init__(self, parent)
        # these attributes are set by the UI file, but this makes the linter happy.
        self.title = title
        self.suffix = suffix
        self.level_range = level_range
        self.initialize_gui()
        self.level = 0

    def initialize_gui(self):
        self.layout = QHBoxLayout()
        self.spin_level = QDoubleSpinBox()
        self.spin_level.setRange(*self.level_range)
        self.spin_level.setDecimals(3)
        self.spin_level.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.spin_level.valueChanged.connect(self.spin_level_changed)
        self.spin_level.setFont(QFont("Ubuntu", 14))
        if self.suffix:
            self.spin_level.setSuffix(" " + self.suffix)
        if self.title:
            title = QLabel(self.title)
            title.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.layout.addWidget(title)
        self.layout.addWidget(self.spin_level)
        self.setLayout(self.layout)

    def set_suffix(self, suffix):
        self.spin_level.setSuffix(suffix)

    def set_value(self, level):
        self.disconnect_all()
        self.spin_level.setValue(level)
        self.level = level
        self.connect_all()

    def set_step_size(self, step):
        self.spin_level.setSingleStep(step)

    def set_decimals(self, decimals):
        self.spin_level.setDecimals(decimals)

    def spin_level_changed(self, newlevel):
        oldlevel = self.level
        within_range = self.check_range(newlevel)
        if within_range:
            self.level = newlevel
            self.disconnect_all()
            self.onNewValues.emit()
            self.connect_all()
        else:
            suggested_level = self.suggest_level(newlevel)
            self.spin_level.setValue(suggested_level)

    def suggest_level(self, level):
        # if spin box value selected too high, goes to the highest possible value
        suggestion = None
        if level < self.level_range[0]:
            suggestion = self.level_range[0]
        if level > self.level_range[1]:
            suggestion = self.level_range[1]
        return suggestion

    def check_range(self, val):
        if self.level_range[0] <= val <= self.level_range[1]:
            return True
        else:
            return False

    def check_bounds(self, val):
        if val < self.level_range[0]:
            output = self.level_range[0]
        elif val > self.level_range[1]:
            output = self.level_range[1]
        else:
            output = val
        return output

    def disconnect_all(self):
        self.spin_level.blockSignals(True)

    def connect_all(self):
        self.spin_level.blockSignals(False)

    def set_value_no_signal(self, value):
        self.spin_level.blockSignals(True)
        self.spin_level.setValue(value)
        self.spin_level.blockSignals(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon = QCustomSpinBox((-10.0, 10.0), title="Control")
    icon.show()
    app.exec_()
