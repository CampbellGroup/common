'''
Created on May 18, 2016

@author: Anthony Ransford
'''

from PyQt4 import QtCore, QtGui
from twisted.internet.defer import inlineCallbacks
from common.lib.clients.connection import connection
from Cython.Plex.Regexps import Empty

SIGNALID = 546431

class node_client(QtGui.QWidget):

    def __init__(self, reactor, cxn=None):

        super(node_client, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.connect()

    @inlineCallbacks
    def connect(self):

        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(name='Node Client')
        self.mg = yield self.cxn.manager
        serverlist = yield self.mg.servers()
        self.nodeserverlist = []

        for server in serverlist:
            if server[1].find('node') == 0:
                server = server[1].replace(' ', '_')
                server = getattr(self.cxn, server)
                self.nodeserverlist.append(server)

        yield self.nodeserverlist[0].signal__log(SIGNALID)
        yield self.nodeserverlist[0].addListener(listener=self.update_log, source=None, ID=SIGNALID)
        self.initialize_gui()

    def initialize_gui(self):

        self.setWindowTitle('LabRAD QT Node Client')
        layout = QtGui.QGridLayout()

        stopbutton = QtGui.QPushButton('Stop Server')
        startbutton = QtGui.QPushButton('Start Server')
        startautobutton = QtGui.QPushButton('Start Auto Servers')
        stopallbutton = QtGui.QPushButton('Stop All')

        availablelabel = QtGui.QLabel('Available')
        runninglabel = QtGui.QLabel('Running')

        self.availablelist = QtGui.QListWidget()
        self.runninglist = QtGui.QListWidget()

        self.availablelist.customContextMenuRequested.connect(self.avail_pop_up_menu)
        self.availablelist.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.runninglist.customContextMenuRequested.connect(self.run_pop_up_menu)
        self.runninglist.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)        

        self.availablelist.doubleClicked.connect(self.start_server)

        stopbutton.pressed.connect(self.stop_server)
        startbutton.pressed.connect(self.start_server)
        startautobutton.pressed.connect(self.start_auto_servers)
        stopallbutton.pressed.connect(self.stop_all)

        self.update_nodes()
        layout.addWidget(stopbutton,         0, 0, 1, 1)
        layout.addWidget(startbutton,        0, 1, 1, 1)
        layout.addWidget(startautobutton,        0, 2, 1, 1)
        layout.addWidget(stopallbutton,      0, 3, 1, 1)
        layout.addWidget(availablelabel,     1, 0, 1, 2)
        layout.addWidget(runninglabel,       1, 2, 1, 2)
        layout.addWidget(self.availablelist, 2, 0, 1, 2)
        layout.addWidget(self.runninglist,   2, 2, 1, 2)

        self.setLayout(layout)

    @inlineCallbacks
    def update_nodes(self):

        for node in self.nodeserverlist:
            availableservers = yield node.available_servers()
            runningservers = yield node.running_servers()
            autostartservers = yield node.autostart_list()

        self.availablelist.clear()
        self.runninglist.clear()

        runningserverlist = []
        for runningserver in runningservers:
            runningserverlist.append(runningserver[1])
        availableserverlist = list(set(availableservers) - set(runningserverlist))
        availableserverlist.sort()
        self.availablelist.addItems(availableserverlist)
        self.runninglist.addItems(runningserverlist)

        for autostartserver in autostartservers:
            runningmatch = self.runninglist.findItems(autostartserver, QtCore.Qt.MatchExactly)
            availmatch = self.availablelist.findItems(autostartserver, QtCore.Qt.MatchExactly)
            if len(runningmatch) >= 1:
                runningmatch[0].setFont(QtGui.QFont('Helvetica',12, QtGui.QFont.Bold))
            if len(availmatch) >= 1:
                availmatch[0].setFont(QtGui.QFont('Helvetica',12, QtGui.QFont.Bold))

    def update_log(self, c, signal):
        print 'in update'
        print c, signal

    def start_server(self):
        item = self.availablelist.currentItem().text()
        node = self.nodeserverlist[0]
        node.start(str(item))
        self.availablelist.currentItem().setText(str(item) + ' ...')
        self.update_nodes()

    def stop_server(self):
        item = self.runninglist.currentItem().text()
        node = self.nodeserverlist[0]
        node.stop(str(item))
        self.runninglist.currentItem().setText(str(item) + ' ...')
        self.update_nodes()

    def start_auto_servers(self):
        node = self.nodeserverlist[0]
        node.autostart()
        self.update_nodes()

    def stop_all(self):
        node = self.nodeserverlist[0]
        for i in range(self.runninglist.count()):
            node.stop(str(self.runninglist.item(i).text()))
        self.update_nodes()

    def avail_pop_up_menu(self, pos):
        self.availablemenu = QtGui.QMenu()

        item = self.availablelist.itemAt(pos)
        removeautostartaction = self.availablemenu.addAction('Remove from autostart')
        autostartaction = self.availablemenu.addAction('Auto Start Server')
        action = self.availablemenu.exec_(self.mapToGlobal(QtCore.QPoint(0, 30) + pos))

        if action == autostartaction:
            node = self.nodeserverlist[0]
            node.autostart_add(str(item.text()))
        if action == removeautostartaction:
            node = self.nodeserverlist[0]
            node.autostart_remove(str(item.text()))

        self.update_nodes()

    def run_pop_up_menu(self, pos):
        self.runningmenu = QtGui.QMenu()
        width = self.availablelist.width()
        item = self.runninglist.itemAt(pos)
        autostartaction = self.runningmenu.addAction('Auto Start Server')
        stopaction = self.runningmenu.addAction('Stop Server')
        removeautostartaction = self.runningmenu.addAction('Remove from autostart')
        action = self.runningmenu.exec_(self.mapToGlobal(QtCore.QPoint(width, 30) + pos))

        if action == autostartaction:
            node = self.nodeserverlist[0]
            node.autostart_add(str(item.text()))

        if action == removeautostartaction:
            node = self.nodeserverlist[0]
            node.autostart_remove(str(item.text()))

        if action == stopaction:
            self.stop_server()
        self.update_nodes()

if __name__ == '__main__':
    a = QtGui.QApplication([])
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    nodewidget = node_client(reactor)
    nodewidget.show()
    reactor.run()
