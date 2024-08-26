from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui


class client_shell(QtGui.QWidget):

    def __init__(self, reactor, parent=None):
        """Creates the loop (reactor) for twisted and any other initialization that only
        needs to be run once
        """

        super(
            client_shell, self
        ).__init__()  # here we inherit all the init functions from QWidgets
        self.setSizePolicy(
            QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed
        )  # Fixes the size of the GUI to take minimal space
        self.reactor = reactor  # Creates twisted reactor
        """Here is where you will place any other things that only need to be run once 
        """
        self.connect()  # now we call the connect function

    @inlineCallbacks  # this is needed any time a yield statement is used in a function (asynchronous code)
    def connect(self):
        """Creates an Asynchronous connection to servers and can
        connects incoming signals to relavent functions
        """
        from labrad.wrappers import (
            connectAsync,
        )  # imports the connectAsync function from pyLabRAD

        """
        this is where you connect to whatever computer your device server is on
        the default is the current computer but a connection to the another computer may look like:
        self.cxn = yield connectAsync('10.97.112.13', name = "client_shell"). Multiple computers may also be 
        add, ie 
        self.cxn1 = yield connectAsync(name = "client_shell")
        self.cxn2 = yield connectAsync('10.97.112.13', name = "client_shell")
        """
        self.cxn = yield connectAsync(
            name="client_shell"
        )  # asynchronously connects to the LabRAD manager with the name "client_shell"
        """
        Here is where you will connect to specific device servers on the computer connected to, for example:
        arduino_TTL = self.cxn.arduinottl
        """
        self.initializeGUI()  # now we call the initializeGUI function

    def initializeGUI(self):
        """
            This is where the GUI is made and PyQt4 objects such as QPushButtons and QSpinBox can be instantiated and added to the
            layout gridif __name__=="__main__":
        a = QtGui.QApplication( [] )
        from common.lib.clients import qt4reactor
        qt4reactor.install()
        from twisted.internet import reactor
        switchWidget = switchclient(reactor)
        switchWidget.show()
        reactor.run()

        """
        layout = QtGui.QGridLayout()  # instantiates a PyQt4 layout object
        """
        Here we add items to the layout and set inital values then connect them to functions, for example:
        widget = QPushButton('On and Off Button') #Creates a button with the name 'On and Off Button'
        widget.setChecked(False) #Sets initial value to off
        widget.toggled.connect(self.toggle) #connects button to an as yet uncreated function "toggle"
        layout.addWidget(widget, 3,4) #adds widget to the layout at position row=3, column = 4
        """

        self.setLayout(layout)  # sets the final layout with added widgets

    """
    Here we would add relevant functions that we connected widgets to or other needed functions, remember all functions that use the
    asynchronous commands such as yield require an @inlineCallbacks decorator before the function,

    def function1(self):
        print 'do something'

    @inlineCallbacks
    def function2(self):
        yield print 'do something asynchronous'
    """

    def closeEvent(self, x):
        """
        This function is run upon the GUI being closed all cleanup should be done here such as stopping the reactor
        """
        self.reactor.stop()  # stops the reactor


if __name__ == "__main__":
    """
    This is the function that gets run first if the client python file is run directly, however if this client is imported by another function
    this function will not be run
    """
    a = QtGui.QApplication([])  # Creates a GUI structure and can take sys arguments
    import qt4reactor  # imports the PyQt4 reactor that must be integrated with twisted reactor (this must happen here)

    qt4reactor.install()  # installs the pyqt4 reactor
    from twisted.internet import reactor  # imports the twisted reactor

    client_shellWidget = client_shell(
        reactor
    )  # instantiates a widget with the just imported reactor
    client_shellWidget.show()  # shows the widget
    reactor.run()  # runs the integrated reactor
