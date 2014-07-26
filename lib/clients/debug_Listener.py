# -*- coding: utf-8 -*-
"""
Client for debugging server signals.  Comment/uncomment signals as necessary
"""

from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui


IMAGE_AVAILABLE_SIGNAL = 102181
READY_4_TTL_SIGNAL     = 103810

class recieverWidget(QtGui.QWidget):

    debug = False

    # This is an ID for the client to register to the server
    ID  = 654321
    ID3 = 572957
    

    def __init__(self, reactor, parent=None):
        super(recieverWidget, self).__init__(parent)
        
        self.reactor = reactor
        
        self.makeGUI()
        self.connectLabrad()


    def makeGUI(self):
        """
        
        """
        self.setWindowTitle('Signal Listener')

        # Create a grid layout
        layout = QtGui.QGridLayout()

        
        # Create the text widget 
        self.textedit = QtGui.QTextEdit()
        self.textedit.setReadOnly(True)
        layout.addWidget(self.textedit, 1,0)

        
        
        
        self.setLayout(layout)


    @inlineCallbacks
    def connectLabrad(self):
        """
        Make an asynchronous connection to LabRAD
        """
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name = 'Debug Signals Client')

        # Connect to emitter server 
        #self.server = self.cxn.interactive_emitter_server
        self.avt_server = self.cxn.avt_indy_server
        
        ### Signals        
        
#        # Connect to signal from server (note the method is named from parsed 
#        # text of the in the server emitter name)        
#        yield self.server.signal__emitted_signal(self.ID)
#        
#        # This registers the client as a listener to the server and assigns a 
#        # slot (function) from the client to the signal emitted from the server
#        # In this case self.displaySignal
#        yield self.server.addListener(listener = self.displaySignal, 
#                source = None, ID = self.ID) 

                
                
        # Image is ready for retrieval
        yield self.avt_server.signal__image_available(IMAGE_AVAILABLE_SIGNAL)
                                  
        yield self.avt_server.addListener(listener=self.displaySignal, 
                                          source=self.avt_server.ID,
                                          ID=IMAGE_AVAILABLE_SIGNAL)


        # Camera is prepared for TTL input
        yield self.avt_server.signal__waiting_for_ttl(READY_4_TTL_SIGNAL)

        yield self.avt_server.addListener(listener=self.displaySignal, 
                                          source=self.avt_server.ID,
                                          ID=READY_4_TTL_SIGNAL)



    def displaySignal(self, cntx, signal):
        
        if self.debug : print "displaySignal called()"
        self.textedit.append(signal)


    def closeEvent(self, x):
        
        self.cxn.disconnect()

        # Need to expire the listener context
        #self.        
        
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