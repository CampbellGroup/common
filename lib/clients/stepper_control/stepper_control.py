from common.lib.clients.qtui.QCustomSpinBox import QCustomSpinBox
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui


class StepperControl(QtGui.QWidget):

    def __init__(self, reactor):
        super(StepperControl, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.degree_per_step = 1.8
        self.angle = 0.0
        self.connect()

    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection to stepper server and
        connects incoming signals to relavent functions

        """

        from labrad.wrappers import connectAsync

        self.cxn = yield connectAsync()
        self.server = self.cxn.stepper_motor_server
        self.initializeGUI()

    def initializeGUI(self):
        layout = QtGui.QGridLayout()

        zerowidget = QtGui.QPushButton("Zero")
        self.degreewidget = QCustomSpinBox((-10000, 10000.0), title="Angle")
        self.angle_label = QtGui.QLabel("0.0")
        self.degreewidget.set_step_size(1.8)
        self.degreewidget.spin_level.set_decimals(3)

        self.degreewidget.spin_level.setValue(self.angle)

        self.degreewidget.spin_level.valueChanged.connect(self.change_angle)
        zerowidget.clicked.connect(self.zero_scale)

        layout.addWidget(zerowidget, 0, 0)
        layout.addWidget(self.degreewidget, 0, 1)
        layout.addWidget(self.angle_label, 0, 2)

        self.setLayout(layout)

    def zero_scale(self, state):
        self.angle = 0.0
        self.degreewidget.spin_level.setValue(0.0)

    @inlineCallbacks
    def change_angle(self, angle):
        difference = angle - self.angle
        steps = difference / self.degree_per_step
        steps = int(steps)
        self.angle = self.angle + self.degree_per_step * steps
        self.angle_label.setText(str(self.angle))
        self.degreewidget.spin_level.setValue(angle)
        yield self.server.move_steps(steps)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QtGui.QApplication([])
    import qt4reactor

    qt4reactor.install()
    from twisted.internet import reactor

    stepper_control_Widget = StepperControl(reactor)
    stepper_control_Widget.show()
    reactor.run()
