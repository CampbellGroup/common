# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 10:24:27 2014

@author: Campbell Lab
"""

from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui

class recieverWidget(QtGui.QWidget):

    ID = 654321
#this is an ID for the client to register to the server

    def __init__(self, reactor, parent=None):
        super(recieverWidget, self).__init__(parent)
        self.reactor = reactor
        self.setupLayout()
        self.connect()

    def setupLayout(self):
        #setup the layout and make all the widgets
        self.setWindowTitle('Reciever Widget')
        #create a horizontal layout
        layout = QtGui.QHBoxLayout()
        #create the text widget 
        self.textedit = QtGui.QTextEdit()
        self.textedit.setReadOnly(True)
        layout.addWidget(self.textedit)
        self.setLayout(layout)

    @inlineCallbacks
    def connect(self):
        #make an asynchronous connection to LabRAD
        from labrad.wrappers import connectAsync
        cxn = yield connectAsync(name = 'Signal Widget')
        self.server = cxn.emitter_server
        #connect to emitter server 
        yield self.server.signal__emitted_signal(self.ID)
        #connect to signal from server (note the method is named from parsed 
        #text of the in the server emitter name)
        yield self.server.addListener(listener = self.displaySignal, 
                source = None, ID = self.ID) 
        #This registers the client as a listener to the server and assigns a 
        #slot (function) from the client to the signal emitted from the server
        #In this case self.displaySignal

    def displaySignal(self, cntx, signal):
        self.textedit.append(signal)

    def closeEvent(self, x):
        #stop the reactor when closing the widget
        self.reactor.stop()

if __name__ == "__main__":
    a = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = recieverWidget(reactor)
    widget.show()
    reactor.run()
