from common.clients.qtui.multiplexerchannel import QCustomWavemeterChannel
from twisted.internet.defer import inlineCallbacks, returnValue
from common.clients.connection import connection
from PyQt4 import QtGui
from wlm_client_config import multiplexer_config

    

SIGNALID1 = 445566
SIGNALID2 = 143533
SIGNALID3 = 111221
#this is the signal for the updated frequencys
    
class wavemeterclient(QtGui.QWidget):
    


    def __init__(self, reactor, parent = None):
        """initializels the GUI creates the reactor 
            and empty dictionary for channel widgets to 
            be stored for iteration. also grabs chan info
            from wlm_client_config file 
        """ 
        super(wavemeterclient, self).__init__()
        self.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.reactor = reactor     
        self.d = {} 
        self.chaninfo = multiplexer_config.info     
        self.connect()
        
    @inlineCallbacks
    def connect(self):
        """Creates an Asynchronous connection to the wavemeter computer and
        connects incoming signals to relavent functions
        
        """
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync('169.232.156.230')
        self.server = yield self.cxn.multiplexerserver
        
        yield self.server.signal__frequency_changed(SIGNALID1)
        yield self.server.signal__selected_channels_changed(SIGNALID2)
        yield self.server.signal__update_exp(SIGNALID3)
        
        yield self.server.addListener(listener = self.updateFrequency, source = None, ID = SIGNALID1) 
        yield self.server.addListener(listener = self.toggleMeas, source = None, ID = SIGNALID2)
        yield self.server.addListener(listener = self.updateexp, source = None, ID = SIGNALID3)
        
        self.initializeGUI()
        
    @inlineCallbacks
    def initializeGUI(self):  
    
        layout = QtGui.QGridLayout()
        for chan in self.chaninfo:
            port = self.chaninfo[chan][0]
            hint = self.chaninfo[chan][1]
            stretched = self.chaninfo[chan][3]
            
            widget = QCustomWavemeterChannel(chan, hint, stretched)  
            import RGBconverter as RGB  
            RGB = RGB.RGBconverter()
            color = int(2.998e8/(float(hint)*1e3))
            color = RGB.wav2RGB(color)
            color = tuple(color)

            widget.spinFreq.setValue(float(hint))

            widget.currentfrequency.setStyleSheet('color: rgb' + str(color))

            widget.spinExp.valueChanged.connect(lambda exp = widget.spinExp.value(), port = port : self.expChanged(exp, port))
            initvalue = yield self.server.get_exposure(port)
            widget.spinExp.setValue(initvalue)
            initmeas = yield self.server.get_switcher_signal_state(port)
            initmeas = initmeas
            widget.measSwitch.setChecked(bool(initmeas))
            widget.measSwitch.toggled.connect(lambda state = widget.measSwitch.isDown(), port = port  : self.changeState(state, port))         
            widget.spinFreq.valueChanged.connect(lambda freq = widget.spinFreq.value(), port = port : self.freqChanged(freq, port))

            self.d[port] = widget
            layout.addWidget(self.d[port])
        self.setLayout(layout)
        yield None


    
    @inlineCallbacks
    def expChanged(self, exp, chan):
        #these are switched, dont know why
        exp = int(exp)
        yield self.server.set_exposure_time(chan,exp)
        
    
    def updateFrequency(self , c , signal):     
        chan = signal[0]
        if chan in self.d : 
            freq = signal[1]
            
            if self.d[chan].measSwitch.isDown():
                self.d[chan].currentfrequency.setText('Not Measured')                       
            elif freq == -3.0:
                self.d[chan].currentfrequency.setText('Under Exposed')
            elif freq == -4.0:
                self.d[chan].currentfrequency.setText('Over Exposed')
            else:
                self.d[chan].currentfrequency.setText(str(freq)[0:10])
                
    def toggleMeas(self, c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d :
            self.d[chan].measSwitch.setChecked(value)
            
    def updateexp(self,c, signal):
        chan = signal[0]
        value = signal[1]
        if chan in self.d :
            self.d[chan].spinExp.setValue(value)

    @inlineCallbacks
    def changeState(self, state, chan):
        yield self.server.set_switcher_signal_state(chan, state)
        if state == False:  self.d[chan].currentfrequency.setText('Not Measured') 
     
    @inlineCallbacks   
    def freqChanged(self,freq, port):
        yield self.server.set_pid_course(port, freq)

    def closeEvent(self, x):
        self.reactor.stop()
        
        
        
if __name__=="__main__":
    a = QtGui.QApplication( [] )
    from common.clients import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    wavemeterWidget = wavemeterclient(reactor)
    wavemeterWidget.show()
    reactor.run()