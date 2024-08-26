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
from common.lib.clients.script_scanner_gui.experiment_selector_widget import (
    experiment_selector_widget,
)
from twisted.internet.defer import inlineCallbacks


class fixed_width_button(QPushButton):
    def __init__(self, text, size):
        super(fixed_width_button, self).__init__(text)
        self.size = size
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def sizeHint(self):
        return QtCore.QSize(*self.size)


class docstring_widget(QWidget):
    def __init__(self, reactor, font=None, parent=None):
        super(docstring_widget, self).__init__(parent)
        self.reactor = reactor
        self.parent = parent
        self.cxn = self.parent.cxn
        self.font = font
        self.selector = experiment_selector_widget(self.reactor, parent=self)
        self.doc_text = ""
        if self.font is None:
            self.font = QtGui.QFont("MS Shell Dlg 2", pointSize=12)
        self.setupLayout()
        self.connect_layout()

    def on_experiment_selected(self):
        script = str(self.parent.selector.dropdown.currentText())
        self.show_doc(script=script)

    @inlineCallbacks
    def show_doc(self, script):
        try:
            sc = yield self.cxn.get_server("ScriptScanner")
            self.doc_text = yield sc.get_script_docstring(script)
            self.doc_text_widget.setPlainText(self.doc_text)
        except AttributeError as e:
            self.doc_text_widget.setPlainText(
                "There has been an error accessing the docstring: \n" + str(e)
            )

    def setupLayout(self):
        layout = QGridLayout()
        self.doc_text_widget = QPlainTextEdit()
        self.doc_text_widget.setDocumentTitle("Docstring")
        self.doc_text_widget.setReadOnly(True)
        self.doc_text_widget.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.doc_text_widget.setFont(QtGui.QFont("JetBrains Mono", pointSize=12))

        layout.addWidget(self.doc_text_widget, 0, 0, 5, 3)
        self.setLayout(layout)

    def connect_layout(self):
        self.parent.on_experiment_selected.connect(self.on_experiment_selected)

    def closeEvent(self, x):
        self.reactor.stop()


if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor

    qt5reactor.install()
    from twisted.internet import reactor

    widget = docstring_widget(reactor)
    widget.show()
    reactor.run()
