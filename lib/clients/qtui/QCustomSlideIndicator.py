#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class SlideIndicator(QWidget):

    def __init__(self, limits):
        super(SlideIndicator, self).__init__()
        self.set_rails(limits)
        self.value = None
        self.init_ui()

    def init_ui(self):
        self.setGeometry(0, 0, 200, 30)
        self.setMaximumHeight(60)
        self.setMinimumHeight(30)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setWindowTitle("Slide Indicator")
        self.show()

    def paintEvent(self, e):

        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw_grid(qp)
        self.draw_pointer(qp)
        qp.end()

    def draw_grid(self, qp):

        pen = QPen(Qt.gray, 2, QtCore.Qt.PenStyle.SolidLine)
        brush = QBrush(Qt.white)
        qp.setPen(pen)
        qp.setBrush(brush)
        qp.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 5, 5)

        pen = QPen(Qt.gray, 1, QtCore.Qt.PenStyle.DashLine)
        qp.setPen(pen)
        qp.drawLine(int(self.width() / 4), 1, int(self.width() / 4), self.height() - 2)
        qp.drawLine(int(self.width() / 2), 1, int(self.width() / 2), self.height() - 2)
        qp.drawLine(
            int(3 * self.width() / 4), 1, int(3 * self.width() / 4), self.height() - 2
        )

        # qp.drawLine(0, self.height() - 3, self.width(), self.height() - 3)

    def draw_pointer(self, qp):
        pen = QtGui.QPen(
            Qt.red, 4, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap
        )
        qp.setPen(pen)
        if self.value is not None:
            xpos = int((self.value - self.minvalue) / self.span * self.width())
            qp.drawLine(xpos, int(self.height() * 0.2), xpos, self.height())

    def set_rails(self, rails):
        self.minvalue = rails[0]
        self.maxvalue = rails[1]
        self.span = self.maxvalue - self.minvalue
        self.repaint()

    def update_slider(self, value):
        if value >= self.maxvalue:
            value = self.maxvalue
        elif value <= self.minvalue:
            value = self.minvalue
        self.value = value
        self.repaint()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon = SlideIndicator([-5.0, 5.0])
    icon.show()
    app.exec_()
