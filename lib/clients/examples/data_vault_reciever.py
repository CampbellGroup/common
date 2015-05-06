# -*- coding: utf-8 -*-
"""
Widget to listen for data vault signals
"""
from twisted.internet.defer import inlineCallbacks
from PyQt4 import QtGui


class DataVaultReciever(QtGui.QWidget):

    ID = 752311 # ID for the client to register to the server
    ID_DIR = 214765

    def __init__(self, reactor, parent=None):
        super(DataVaultReciever, self).__init__(parent)
        self.reactor = reactor
        self.setupLayout()
        self.connect()

    def setupLayout(self):
        #setup the layout and make all the widgets
        self.setWindowTitle('Data Vault Reciever')
        #create a horizontal layout
        layout = QtGui.QHBoxLayout()
        #create the text widget 
        self.textedit = QtGui.QTextEdit()
        self.textedit.setReadOnly(True)
        layout.addWidget(self.textedit)
        self.setLayout(layout)

    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        cxn = yield connectAsync(name='Data Vault Reciever')
        self.dv = cxn.data_vault
        yield self.dv.signal__data_available(self.ID)
        # connect to signal from server (note the method is named from parsed 
        # text of the in the server emitter name)
        yield self.dv.addListener(listener=self.display_signal, 
                                      source=None, ID=self.ID) 
        # This registers the client as a listener to the server and assigns a 
        # slot (function) from the client to the signal emitted from the server
        # In this case self.displaySignal
                                      
        yield self.dv.signal__new_dataset_dir(self.ID_DIR)
        yield self.dv.addListener(listener=self.dir_message, 
                                      source=None, ID=self.ID_DIR) 

    def display_signal(self, cntx, signal):
        message = "new data available signal"
        self.textedit.append(message)

    def dir_message(self, cntx, signal):
        self.textedit.append(signal)

    def closeEvent(self, x):
        #stop the reactor when closing the widget
        self.reactor.stop()


if __name__=="__main__":
    #join Qt and twisted event loops
    a = QtGui.QApplication( [] )
    import common.lib.qt4reactor as qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    widget = DataVaultReciever(reactor)
    widget.show()
    reactor.run()
