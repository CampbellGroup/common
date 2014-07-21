# -*- coding: utf-8 -*-
"""
Created on Sat Jul 19 10:24:27 2014

@author: Campbell Lab
"""

from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui

class recieverWidget(QtGui.QWidget):

    debug = False

    # This is an ID for the client to register to the server
    ID  = 654321
    ID3 = 572957

    def __init__(self, reactor, parent=None):
        super(recieverWidget, self).__init__(parent)
        
        self.reactor = reactor
        
        self.makeGUI()
        self.connectWidgets()
        self.connectLabrad()


    def makeGUI(self):
        """
        
        """
        self.setWindowTitle('Interactive Signal Widget')

        # Create a grid layout
        layout = QtGui.QGridLayout()

        
        # Create the text widget 
        self.textedit = QtGui.QTextEdit()
        self.textedit.setReadOnly(True)
        layout.addWidget(self.textedit, 1,0)

        
        # Button for triggering a signal from the interactive emitter server
        self.trigger_button = QtGui.QPushButton("Trigger Server Signal")
        layout.addWidget(self.trigger_button, 1, 1)
        
        
        self.setLayout(layout)


    @inlineCallbacks
    def connectLabrad(self):
        """
        Make an asynchronous connection to LabRAD
        """
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name = 'Interactive Signal Client')

        # Connect to emitter server 
        self.server = self.cxn.interactive_emitter_server
        
        
        ### Signals        
        
        # Connect to signal from server (note the method is named from parsed 
        # text of the in the server emitter name)        
        yield self.server.signal__emitted_signal(self.ID)
        yield self.server.signal__efs(self.ID3)
        
        # This registers the client as a listener to the server and assigns a 
        # slot (function) from the client to the signal emitted from the server
        # In this case self.displaySignal
        yield self.server.addListener(listener = self.displaySignal, 
                source = None, ID = self.ID) 
        yield self.server.addListener(listener = self.displayFloat, 
                source = None, ID = self.ID3) 

                

    @inlineCallbacks
    def connectWidgets(self):
        """
        Make button connections, so that specific actions are
        performed when they are pressed.
        """    

        yield self.trigger_button.clicked.connect(self.triggerTheServer)


    @inlineCallbacks
    def triggerTheServer(self, x):
        """
        Trigger the server to emit a signal.        
        
        Parameters
        ---------
        x: 
        TODO: figure out what x is.
        """
        
        yield self.server.trigger_signal()
        

    def displaySignal(self, cntx, signal):
        
        if self.debug : print "displaySignal called()"
        self.textedit.append(signal)


    @inlineCallbacks
    def displayFloat(self, cntx, signal):
        
        if self.debug : print "displayFloat cntx=", cntx
        if self.debug : print "displayFloat signal=", signal
        
        value = yield self.server.float_data()
        
        # Convert the value to a string so the text can be appended
        value = str(value)
        self.textedit.append(value)



    def closeEvent(self, x):
        
        self.cxn.disconnect()
        
        # Stop the reactor when closing the widget
        self.reactor.stop()
        



if __name__=="__main__":
    #join Qt and twisted event loops
    a = QtGui.QApplication( [] )
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = recieverWidget(reactor)
    widget.show()
    reactor.run()