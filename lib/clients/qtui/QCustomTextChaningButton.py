from PyQt4 import QtGui, QtCore


class TextChangingButton(QtGui.QPushButton):
    """Button that changes its text to ON or OFF and colors when it's pressed.
    """
    def __init__(self, labels=None, addtext=None, parent=None):
        """
        NOTE: when both labels and addtext are not None, labels take
        precedence.

        Parameters
        ----------
        labels: 2-tuple, the first entry corresponds to text when the button is
            "ON", and the second entry corresponds to text when the button is
            "OFF".
        addtext: str, text gets added before "ON" or "OFF" if it's not None.
        """
        super(TextChangingButton, self).__init__(parent)
        self.labels = labels
        self.addtext = addtext
        self.setCheckable(True)
        self.setFont(QtGui.QFont('MS Shell Dlg 2', pointSize=10))
        self.setSizePolicy(QtGui.QSizePolicy.Minimum,
                           QtGui.QSizePolicy.Minimum)
        # connect signal for appearance changing
        self.toggled.connect(self.setAppearance)
        self.setAppearance(self.isDown())

    def setAppearance(self, down):
        on_text, off_text = self._set_button_texts()
        if down:
            self.setText(on_text)
            self.setPalette(QtGui.QPalette(QtCore.Qt.darkGreen))
        else:
            self.setText(off_text)
            self.setPalette(QtGui.QPalette(QtCore.Qt.black))

    def _set_button_texts(self):
        """Return button texts when they are on or off."""
        if self.labels is not None:
            on_text = self.labels[0]
            off_text = self.labels[0]
        elif self.addtext is not None:
            on_text = self.add_text + "   On"
            off_text = self.add_text + "   Off"
        else:
            on_text = "On"
            off_text = "Off"
        return on_text, off_text

    def sizeHint(self):
        return QtCore.QSize(37, 26)
