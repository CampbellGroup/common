"""

Designed to be a simple GUI for controlling both DDS boxes on the molecule
experiment

"""



from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks

#app = QtGui.QApplication(sys.argv)

class DDS(QtGui.QWidget):
    debug = True

    def __init__(self, reactor, parent=None):
        super(DDS,self).__init__(parent)

        self.server    = None  # Device server
        self.regctx    = None  # labRAD Registry context

        self.numChannels = 4   # This is a hardware depedent value, so far the first 2 boxes have 4 channels
        self.numBoxes = 1  # Later this expands to 2, etc.

        self.address = 'COM4'  # Coach_K

        self.minFreq = 0.0   # MHz
        self.maxFreq = 500.0 # MHz

        # TODO: This should be done in a future, more intelligent implementation.
        #self.ctxBox1 = None     # Hold the context of the given box
        #self.ctxBox2 = None

        self.reactor = reactor

        #self.makeGUI()
        # I think there should be a yield in front of connect..., but can't have a generator in __init__
        self.connect()  # At the end this calls makeGUI() and initialize()
        if self.debug : print "Just before self.makeGUI()"
        self.makeGUI()
        if self.debug : print "Just before self.initialize()"

        # I think we need the yield below, but it is not in the BIAS_FIELD_CURRENT_CONTROL
        self.connectLabrad()

        # Important note: reactor doesn't start running until after this, so
        # you can make meaningful calls to processEvents for example until after __init__



    @inlineCallbacks      # This is necessary here.   Not sure why yet
    def connectLabrad(self):
        """
        Function to fill out intial values on the GUI.  Values are stored in
        the LabRAD Registry.
        """
        if self.debug : print "Start of initialize()"

        from labrad.wrappers import connectAsync

        self.cxn = yield connectAsync(name='DDS_CTRL_BOX2')
        reg = yield self.cxn.registry
        self.regctx = yield self.cxn.context()

        # Change directory to relevant keys
        yield reg.cd(['Clients','DDS_Box', 'Box2'], True, context=self.regctx)  # True creates the directory if it doesn't exist

        #if self.debug : print "initialize() self.numChannels =", self.numChannels
        for kk in xrange(self.numChannels):
            channel = kk + 1
            if self.debug : print "initialize() channel =", channel


            self.onOffButtons[kk].clicked.connect(self.setOnOffButton)
            # By default turn On all channels
            if self.debug : print "initialize() before setting server amplitude"
            yield self.server.amplitude(channel, True)
            self.onOffButtons[kk].setChecked(True)
            if self.debug : print "initialize() after setting server amplitude"
            amp = True

            if amp : # If amplitude is true, then turn on this channel
                yield self.onOffButtons[kk].click()
                #QtGui.QPushButton.cli



            freqStrKey = 'freq_ch%s' %channel
            if self.debug : print "initialize freqStrKey =", freqStrKey
            #ampHEXStrKey  = 'ampHEX_ch%s' %channel

            frequency = yield reg.get(freqStrKey, context=self.regctx)
            if self.debug : print "initialize() channel", channel, "frequency =", frequency
            self.freqBoxes[kk].setValue(frequency)
            self.freqBoxes[kk].valueChanged.connect(self.setFreq)
            self.server.frequency(channel, frequency)



            chFuncKey = 'function_ch%s' %channel
            chFunc = yield reg.get(chFuncKey, context=self.regctx)
            self.chLineEdits[kk].setText(chFunc)

        # Not sure how to get around the initialization problems.  This is just terrible code...

        yield self.initButton.clicked.connect(self.initHACK)




    @inlineCallbacks
    def initHACK(self, pressed):
        # Init Button Hack
        source = self.sender()
        if self.debug : print "Inside initHACK())"

        for kk in xrange(self.numChannels):
            channel = kk + 1
            #yield self.server.amplitude(channel, True)

            frequency = self.freqBoxes[kk].value()


            #yield self.server.frequency(source.channel, self.T.Value(source.value(), 'MHz'))
            if self.debug : print "initHACK() channel =", channel
            self.onOffButtons[kk].click()

            # Hack to set the frequency without changing its value.
            self.freqBoxes[kk].stepBy(1)
            #a.processEvents()  # Processing events is necessary, otherwise the two calls cancel each other.
            self.freqBoxes[kk].stepBy(-1)

            # I don't know why the two lines below are required to make this work, but they are necessary!!
            self.freqBoxes[kk].stepUp()
            self.freqBoxes[kk].stepDown()


        source.setText("Fully Initialized, don't press")




    def makeGUI(self):

        layout      = QtGui.QGridLayout()  # Create a grid to place widgets on
        superLayout = QtGui.QGridLayout()  # Create another grid to place widgets on
        groupboxLayout = QtGui.QGridLayout()  # Create yet another grid to place widgets on

        groupbox    = QtGui.QGroupBox('Box 1')  # Frame with a title


        # Perhaps multiple by self.numBoxes to generate the proper number of buttons.
        # Lists to hold ON/OFF buttons and the frequency spinboxes
        self.onOffButtons = [None] * self.numChannels  # List to hold status Buttons, Is the even on or off?
        self.freqBoxes    = [None] * self.numChannels  # List to hold time spinboxes, Set the event time
        self.chLineEdits  = [None] * self.numChannels  # Line edits to hold strings for channel functionality

        # TODO, add amplitude as suggested below
        #self.ampBoxes = [None] * self.numChannels  # List to hold amplitude values

        # TODO: Outer for loop to hold the number of DDS boxes

        # Create the controls
        for kk in xrange(self.numChannels):
            channel = kk + 1
            self.onOffButtons[kk] = self.QOnOffButton()
            self.onOffButtons[kk].channel = channel
            #if self.debug : print "makeGUI() self.address =", self.address
            self.onOffButtons[kk].address = self.address

            self.freqBoxes[kk] = self.QFreqSpinBox()
            self.freqBoxes[kk].channel = channel
            self.freqBoxes[kk].address = self.address

            # TODO: get amplitude working
            #self.ampBoxes[kk] = QtimeSpinBox()

            self.chLineEdits[kk] = QtGui.QLineEdit()
            self.chLineEdits[kk].channel = channel
            self.chLineEdits[kk].address = self.address
            self.chLineEdits[kk].setMinimumWidth(200)



        superLayout.addLayout(layout,0,0)
        layout.addWidget(groupbox,0,0)


        # Title line for the controls
        groupboxLayout.addWidget(QtGui.QLabel('Channel'),0,0)
        groupboxLayout.addWidget(QtGui.QLabel('Channel is...'),    0,1)
        groupboxLayout.addWidget(QtGui.QLabel('Frequency [MHz]'),  0,2)
        groupboxLayout.addWidget(QtGui.QLabel('Amplitude [dBm]'),  0,3)
        groupboxLayout.addWidget(QtGui.QLabel('Ch. Function'),     0,4)  # Description of what this channel does

        # Hack button to run the initialize() function once everything is set
        self.initButton = QtGui.QPushButton()
        self.initButton.setText('re-initialize')
        groupboxLayout.addWidget(self.initButton, 0, 5)



        # Place the controls on the GUI
        for kk in range(self.numChannels):
            labelStr = "Ch%s.)" %(kk+1)
            #if self.debug : print "makeGUI labelStr =", labelStr
            groupboxLayout.addWidget(QtGui.QLabel(labelStr), kk+1,0)
            groupboxLayout.addWidget(self.onOffButtons[kk],  kk+1,1)
            groupboxLayout.addWidget(self.freqBoxes[kk],     kk+1,2)
            #groupboxLayout.addWidget(self.ampBoxes[kk],      kk+1,3)
            groupboxLayout.addWidget(self.chLineEdits[kk],   kk+1,4)


        groupbox.setLayout(groupboxLayout)
        self.setLayout(superLayout)



    @inlineCallbacks
    def connect(self):
        from labrad.wrappers import connectAsync
        from labrad.types import Error
        from labrad import types as T
        self.T = T
        self.cxn = yield connectAsync()
        self.server = yield self.cxn.dds_box_server

        try:
            # By default start by connecting to Box2
            yield self.server.select_device(self.address)

        except Error:
            self.setEnabled(False)
            return



    @inlineCallbacks
    def setOnOffButton(self, pressed):
        """
        """

        source = self.sender()
        state = source.isChecked()
        if self.debug : print "setOnOffButton() state =", state
        if self.debug : print "setOnOffButton() source.channel = ", source.channel


        if state:  # If the button is pressed, the event is on
            source.setText('On')
            source.setStyleSheet('background-color: green; color: black; font: bold 14px')

        else:
            source.setText('Off')
            source.setStyleSheet('background-color: red; color: black; font: bold 14px')

        yield self.server.amplitude(source.channel, state)



    @inlineCallbacks
    def setFreq(self, pressed):
        """
        Set the frequency of DDS box's channel
        """
        source = self.sender()

        if self.debug : print "setFreq source.channel =", source.channel
        if self.debug : print "setFreq source.address =", source.address


        #yield self.server.select_device(source.address)


        yield self.server.frequency(source.channel, self.T.Value(source.value(), 'MHz'))



    def closeEvent(self, x):
        self.reactor.stop()




    class QOnOffButton(QtGui.QPushButton):
        """
        Custom status button, is an event On or Off?
        """
        #def __init__(self, initState='Off', channel=None, server=None, parent=None):
        def __init__(self, initState='Off', channel=None, address=None, parent=None):
            """
            initState - str for initial state of device default('Off')
            channel - int, define channel that button interacts with, default(None)
            addresss - str, COM port of the device
            server - DDS Box device server, default(None)
            """


            super(QtGui.QPushButton,self).__init__(parent)
            self.setText(initState)
            self.setCheckable(True)
            #self.clicked[bool].connect(self.setButton)
            self.setStyleSheet('background-color: red; \
                                color: black; \
                                font: bold 14px')

            self.channel = channel   # Track a channel variable for the set button event
            self.address = address   # Track COM port of DDS Box

    #    @inlineCallbacks
    #    def setButton(self, pressed):
    #        """
    #        Change the status buttons color and text when pressed.
    #        """
    #
    #        source = self.sender()
    #        state = source.isChecked()
    #        #if debug : print "state =", state
    #
    #        if state:  # If the button is pressed, the event is on
    #            source.setText('On')
    #            source.setStyleSheet('background-color: green; color: black; font: bold 14px')
    #
    #        else:
    #            source.setText('Off')
    #            source.setStyleSheet('background-color: red; color: black; font: bold 14px')
    #
    #        yield self.server.amplitude(self.channel, state)



    class QFreqSpinBox(QtGui.QDoubleSpinBox):
        """
        Double spin box for setting Frequency (MHz)

        2014-02-28 - Andrew Jayich
        """
        def __init__(self, channel=None, address=None, parent=None):
            """

            channel - int, define channel that button interacts with, default(None)
            addresss - str, COM port of the device, default(None)

            2014-02-27 - Andrew Jayich
            """
            super(QtGui.QDoubleSpinBox,self).__init__(parent)
            self.setRange(0,500)   # Frequency range 0 to 500 MHz, need to double check what this really is.
            self.setDecimals(6)     # Can set Hertz precision
            self.setSingleStep(1.0) # 1 MHz step size

            self.channel = channel   # Track a channel variable for frequency
            self.address = address   # Track COM port of DDS Box


    #    @inlineCallbacks
    #    def setFreq(self, pressed):
    #        """
    #        Set the frequency of DDS box's channel
    #
    #        2014-02-28 - Andrew Jayich
    #        """
    #
    #        freq_MHz = self.value()
    #        freq_MHz = _u.WithUnit(freq_MHz, 'MHz')   # Assuming value is in MHz
    #
    #        yield self.server.frequency(self.channel, freq_MHz)
    #






class DDS_CONTROL(QtGui.QMainWindow):
    debug = True

    def __init__(self, reactor, parent=None):

        super(DDS_CONTROL, self).__init__(parent)
        self.reactor = reactor
        W = self.buildW(reactor)
        widget = QtGui.QWidget()
        gridLayout = QtGui.QGridLayout()
        gridLayout.addWidget(W, 1, 0)
        self.setWindowTitle('DDS Box Control')
        widget.setLayout(gridLayout)
        self.setCentralWidget(widget)


    def buildW(self, reactor):

        W = QtGui.QWidget()
        subLayout = QtGui.QGridLayout()
        if self.debug : print "DDS_CONTROL, buildW(), before adding DDS"
        subLayout.addWidget(DDS(reactor), 1, 0)
        W.setLayout(subLayout)
        if self.debug : print "DDS_CONTROL, buildW(), after adding DDS"
        return W


    # TODO: Figure out what the 'x' is doing below
    def closeEvent(self, x):
        self.reactor.stop()






if __name__=="__main__":
    print "First line of __main__"
    a = QtGui.QApplication( [] )  # Why is this started with an empty list?
    import common.lib.qt4reactor as qt4reactor
    qt4reactor.install()  # What does this module do?
    from twisted.internet import reactor
    DDS_CONTROL = DDS_CONTROL(reactor)
    DDS_CONTROL.show()
    print "__main__ before reactor.run()"
    reactor.run()
    print "End of __main__"
