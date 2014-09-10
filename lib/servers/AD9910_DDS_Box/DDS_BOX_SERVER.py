"""
### BEGIN NODE INFO
[info]
name = DDS Box Server
version = 1.0
description =
instancename = DDS Box Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20

### END NODE INFO
"""

from common.lib.servers.serialdeviceserver import SerialDeviceServer, setting, inlineCallbacks, SerialDeviceError, SerialConnectionError
import labrad.types as T
from twisted.internet.defer import returnValue
import labrad.units as _u

import sys
# Should specify this with respect to the current direct, not an absolute path
sys.path.append(r'C:\Users\Campbell Lab\Dropbox\Campbell_Group\Molecules\Programming\Git Repositories\Python\Magic Repository')

# These functions should perhaps be directly incorporated into the server?
#from lib._wc_functions import DDS_freq_to_HEX
#from lib._wc_functions import DDS_HEX_to_freq




class DDS_Box_Channel(object):

    def __init__(self, number, **kwargs):
        """
        Object to define a channel for a DDS box device

        number = int for the channel number, currently 1,2,3, or 4.

        kwargs:
        frequency - labrad units type frequency (preferably in MHz), default(_u.WithUnit(0.0, 'MHz'))
        ampHEX    - string for hex value of amplitude (COM language), default('0000')
        rawInfo   - string of raw info about a channel, default(None)

        2014-02-27 - Andrew Jayich
        """

        self.number = number   # Channel number (for a DDS box device)

        if not kwargs.has_key('frequency'): kwargs['frequency'] = _u.WithUnit(0.0, 'MHz')
        self.frequency = kwargs['frequency']

        if not kwargs.has_key('ampHEX'): kwargs['ampHEX'] = '0000' # set amplitude to zero by default
        self.ampHEX = kwargs['ampHEX']

        if not kwargs.has_key('amp'): kwargs['amp'] = None # To be used for amplitude in dBm in the future, now just 1 and 0 indicating ON/OFF
        self.amp = kwargs['amp']

        if not kwargs.has_key('rawInfo'): kwargs['rawInfo'] = None # default(None)
        self.rawInfo = kwargs['ampHEX']

    def __str__(self):
        """
        Print returns this information
        """

        return "DDX_Box_Channel object, channel " + `self.number` + ", freqeuncy=" + `self.frequency` + ", ampHEX=" + `self.ampHEX` + ", rawInfo=" + `self.rawInfo`



class DDS_Box_Server(SerialDeviceServer):

    debug = True

    name = 'DDS Box Server'
    serNode = 'coach_k'  # This should be the correct value

    # TODO: make this a list of valid values, or have the key-value pair
    # contain a list of valid values.
    regKey = 'DDS_BOX_2'


    #port = 'COM3'
    # 'COM5' is Magic's port for DDS Box 1, 'COM3' is for DDS box 2.
    # Okay, not specifing a port here was crucial to getting the server up and running
    port = None  # This should likely be assigned to it when a device is connected?
    #port = 'COM3'
    #regKey = 'port_DDS_Box2'  # Trying adding this in.
    baudrate = 9600
    timeout = T.Value(1., 's')   # Read timeout value

    numChannels = 4  # Hardware dependent, currently all boxes have 4 channels

    stopbits = 1



    # For some reason I can't access initServer even though it has an inlineCallback dressing...
    @inlineCallbacks
    def initServer(self):

        if self.debug : print "initServer just before createDict()"
        self.createDict()
        #if self.debug : print "initServer just before populateDict()"
        #self.populateDict()
        if not self.regKey or not self.serNode:
            raise SerialDeviceError('Must define regKey and serNode attributes')
        self.queue = []   # For handling read/write events (somehow)

        port = yield self.getPortFromReg(self.regKey)
        port = self.port

        #if self.debug: print "Inside initServer, port=", port

#        try:
#            serStr = yield self.findSerial(self.serNode)
#            if self.debug : print "initServer serStr =", serStr
#            #if self.debug: print "serStr=", serStr
#
#            # Not sure what this does, might reset a lot of values
#            self.initSerial( serStr, port )
#            #if self.debug : print "Inside initServer, before except"
#        except SerialConnectionError, e:
#            self.ser = None
#            if e.code == 0:
#                print 'Could not find serial server for node: %s' % self.serNode
#                print 'Please start correct serial server'
#            elif e.code == 1:
#                print 'Error opening serial connection'
#                print 'Check set up and restart serial server'
#            else: raise

        #if self.debug : print "End of initServer."


        #self.populateDict()


# TODO: apparently the code below is all that needs to be overwritten to
# get this to work properly with context, etc.
# Looking through gpib.py and findDevices(), and _findDevicesForSever()
# I think this should return something like
#[(name, (srv, address1)), (name, (srv, address2)), etc.]

#    def findDevices(self):
#        """Return a list of found devices.
#
#        The result should be a list of (name, args, kw) tuples
#        where args and kw are the arguments tuple and keyword dict
#        that will be used to call the device's connect function.
#        """
#        return []





    @inlineCallbacks
    def checkQueue( self ):
        """
        When timer expires, check queue for values to write
        """
        if self.queue:
            print 'clearing queue...(%d items)' % len( self.queue )
            yield self.writeToSerial( self.queue.pop( 0 ) )
        else:
            print 'queue free for writing'
            self.free = True





    # Dictionary to handle information that can't wait around for Deferred's
    # TODO: Is there a better way to do this?
    def createDict(self):
        d = {}
        d['state'] = None # state is a


        for kk in xrange(self.numChannels):
            number = kk + 1
            chStr = 'ch%s' %number
            d[chStr] = DDS_Box_Channel(number=number)


#        d['ch1raw']  = None # string with raw information about channel 1
#        d['ch1freq'] = None # should end up being a labrad value with units of MHz
#        d['ch1amp']  = None # should be a labrad value, calibrate to get units in dBm?
#
#        d['ch2raw']  = None # string with raw information about channel 1
#        d['ch2freq'] = None # should end up being a labrad value with units of MHz
#        d['ch2amp']  = None # should be a labrad value, calibrate to get units in dBm?
#
#        d['ch3raw']  = None # string with raw information about channel 1
#        d['ch3freq'] = None # should end up being a labrad value with units of MHz
#        d['ch3amp']  = None # should be a labrad value, calibrate to get units in dBm?
#
#        d['ch4raw']  = None # string with raw information about channel 1
#        d['ch4freq'] = None # should end up being a labrad value with units of MHz
#        d['ch4amp']  = None # should be a labrad value, calibrate to get units in dBm?


        # TODO: get real values for the min and max frequency range
        d['freqrange'] = (0.1, 500.)  # Frequency range in MHz

        self.DDSDict = d


    @inlineCallbacks   # Not sure if I need this line
    def populateDict(self):
        """
        Read in current values of the different channels and populate the
        dictionary based on these initial values
        """
        # TODO: perhaps inserting a wait here would help this work?
        if self.debug : print "Inside populateDict"

        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync()
        self.context = yield self.cxn.context()



        # Manually setting dictionary values upon initialization
        for kk in xrange(self.numChannels):
            number = kk + 1
            chStr = 'ch%s' %number

            if self.debug : print "populateDict chStr =", chStr


            # TODO: c=self.context doesn't make any sense here.
            self.DDSDict[chStr].frequency = yield self.getFreq(c=self.context, channel=number)
            # TODO: fix the below to NOT set each value automatically to its max value
            self.DDSDict[chStr].ampHEX    = 'ffff'


            # 0 dBm is close to the max output of the device
            self.DDSDict[chStr].amp_dBm   = _u.WithUnit(0., 'dBm')

#
#        channel = 1
#        dictString = 'ch' + str(channel) + 'freq'
#        self.DDSDict[dictString] = 101.  # Initial frequency in MHz
#        dictString = 'ch' + str(channel) + 'amp'
#        self.DDSDict[dictString] = 1     # 1 is ON (full amplitude), 0 is OFF
#
#        channel = 2
#        dictString = 'ch' + str(channel) + 'freq'
#        self.DDSDict[dictString] = 161.  # Initial frequency in MHz
#        dictString = 'ch' + str(channel) + 'amp'
#        self.DDSDict[dictString] = 1     # 1 is ON (full amplitude), 0 is OFF
#
#        channel = 3
#        dictString = 'ch' + str(channel) + 'freq'
#        self.DDSDict[dictString] = 50.  # Initial frequency in MHz
#        dictString = 'ch' + str(channel) + 'amp'
#        self.DDSDict[dictString] = 1     # 1 is ON (full amplitude), 0 is OFF
#
#        channel = 4
#        dictString = 'ch' + str(channel) + 'freq'
#        self.DDSDict[dictString] = 172.  # Initial frequency in MHz
#        dictString = 'ch' + str(channel) + 'amp'
#        self.DDSDict[dictString] = 1     # 1 is ON (full amplitude), 0 is OFF



        # TODO: Make this an elegant loop
#        chList = [1,2,3,4]
#        for kk in xrange(len(chList)) :
#            channel = chList[kk]
#            if self.debug : print "In populateDict channel=", channel
#
#
#            freq = yield self._GetFreq2(channel=channel)
#
#
#            dictString = 'ch' + str(channel) + 'freq'
#            self.DDSDict[dictString] = freq




    @setting(6, "initialize all channels")
    def initializeChannels(self, accepts='?', returns='?'):
        """
        Initialize all 4 channels based on the populateDict values above.
        """

        chList = [1,2,3,4]
        for kk in xrange(len(chList)) :
            channel = chList[kk]
            if self.debug : print "In initializeChannels, channel=", channel

            dictString = 'ch' + str(channel) + 'freq'
            if self.debug : print "dictString =", dictString
            val = self.DDSDict[dictString]
            if self.debug : print "val = ", val

            val = _u.WithUnit(val, 'MHz')  # Convert to a labrad type with units
            if self.debug : print "after units val =", val

            #freq = yield self.frequency(channel, val)
            yield self.frequency(channel, val)



            dictString = 'ch' + str(channel) + 'amp'
            val = self.DDSDict[dictString]

            #amp = yield self.amplitudeON_OFF(channel, val)
            yield self.amplitudeON_OFF(channel, val)


#    @setting(7, "channel")
#    def select_channel(self, c, channel='i', returns='i'):
#        """
#        If argument is None returns the current active channel, if channel
#        is specified, switches to that channel
#
#        channel - channel number, 1-4
#
#        2014-02-27 - Andrew Jayich
#        """








# TODO: get this to work on intializiation.
# TODO: probably need to get a config file involved here
#    @inlineCallbacks
#    def populateDict(self):
#        state = yield self._GetState()
#        freq = yield self._GetFreq()
#        power = yield self._GetPower()
#        self.DDSDict['state'] = bool(state)
#        self.DDSDict['power'] = float(power)
#        self.DDSDict['freq'] = float(freq)






    @inlineCallbacks
    def writeToSerial(self, message):
        """
        Write value through serial connection.

        Convert message to DDS Box syntax.


        #@param channel: Channel to write to
        @param message: message to write/send

        @raise SerialConnectionError: Error code 2.  No open serial connection.
        """
        self.checkConnection()

        self.ser.flushinput()  # This is necessary for the DDS Boxes.
                               # You want the buffer to be clear.

        if self.debug : print "writeToSerial, message=", message

        # TODO:  fix this complete hack, no idea why I have to write the command twice
        yield self.ser.write( message )
        yield self.ser.write( message )

        #self.ser.write( message )
        #self.ser.write( message )




    #@setting(1, "get raw Channel Info", channel = 'i', returns = 's')
    @inlineCallbacks
    def channelInfoRaw(self, c, channel):
        """
        Returns raw read of channel information via serial command
        '/I1R0f', '/I2R0f', etc.

        c       - context object, a ~dictionary, needs to come after self.
        @param channel - channel number, 1-4, to communicate with.

        2014-01-14 - Andrew Jayich
        """
        preString = self.channelString(channel=channel)


        message = preString + 'R0f'


        #self.ser.write(string)
        # TODO: might not need the yield below, try without
        #yield self.writeToSerial(message)
        yield self.writeToSerial(message)

        #yield writeIt

        #val = yield self.ser.readline()     # Should ouptut '>Read Mode\n'
        #info = yield self.ser.readline()     # Valuable information
        val = yield self.ser.readline().addCallback(str)     # Should ouptut '>Read Mode\n'
        info = yield self.ser.readline().addCallback(str)     # Valuable information
        yield self.ser.flushinput()   # Clear the buffer

        if self.debug : print "\n"

        #if self.debug==True: print "type(val1):", type(val)
        if self.debug==True: print "In channelInfoRaw val:", val
        if self.debug==True: print "In channelInfoRaw info:", info

        # Put raw data into dictionary.
        chStr = 'ch' + str(channel)

        self.DDSDict[chStr].rawInfo = info
        if self.debug : print "In channelInfoRaw, self.DDSDict[chStr].rawInfo =", self.DDSDict[chStr].rawInfo

        returnValue(info)





#    @inlineCallbacks   # Not sure how to dress this function
    def channelString(self, channel=1):
        """
        Returns useful channel string for interacting with the device,
        '/I1', /I2', etc.

        channel - channel number, 1-4

        2013-09-19 - Andrew Jayich
        """

        #string = '/I' + str(channel)
        string = 'I' + str(channel)

        return string

    ### @setting's functions


    @setting(2, "get Frequency", channel = 'i', returns = 'v')
    #@inlineCallbacks
    def getFreq(self, c, channel=1):
        """
        Returns channel frequency in MHz

        c       - Context dictionary
        channel - channel number, 1-4

        TODO: rename this function so that both names are consistent,
        eliminate the @setting name.

        2013-09-19 - Andrew Jayich
        """
        rawInfo = yield self.channelInfoRaw(c, channel).addCallback(str)
        #rawInfo.addCallback(str)
        #rawInfo = self.channelInfoRaw(c, channel)
        #yield self.channelInfoRaw(c, channel)

        chStr = 'ch' + str(channel)
        if self.debug : print "In getFreq() chStr =", chStr

        if self.debug : print "In getFreq() self.DDSDict[chStr]", self.DDSDict[chStr]
        #rawString = str(self.DDSDict[chStr].rawInfo)
        self.DDSDict[chStr].rawInfo = rawInfo
        if self.debug : print "getFreq() rawInfo from dictionary =", rawInfo

        #if self.debug : print "rawString[-12:]:", rawString[-12:]

        # Get last 12 places in string
        lastPart = rawInfo[-11:]

        # Remove whitespace from string
        lastPart = lastPart.replace(" ", "")
        if self.debug : print "getFreq() lastPart=", lastPart

        # Convert all uppercase characters in string to lowercase
        simpleHex = [x.lower() for x in [lastPart]][0]
        if self.debug : print "getFreq() simpleHex=", simpleHex

        # Make proper hex string for Python
        HEX = '0x' + simpleHex
        if self.debug : print "HEX:", HEX
        freq_Hz = DDS_HEX_to_freq(HEX=HEX)

        freq_MHz = 1e-6 * freq_Hz # Conversion: Hz ---> MHz

        # Convert to labRAD with units value
        freq = _u.WithUnit(freq_MHz, 'MHz')

        returnValue(freq)

#
#    @setting(3, "GetFreqTEST", channel='i', returns='s')
#    #def identify(self, c):
#    #@inlineCallbacks
#    def _GetFreqTEST(self, c, channel=1):
#        """
#        Internal function for initially populating the DDS dictionary
#        """
#        command = self.FreqReqStr(channel = channel)
#        yield self.ser.write(command)
#        #yield self.ForceRead() #expect a reply from instrument
#        line1 = yield self.ser.readline()
#        line2 = yield self.ser.readline()
#        line3 = yield self.ser.readline()
#
#        lastPart = line2[-12:]
#
#        # Remove whitespace from string
#        lastPart = lastPart.replace(" ", "")
##        if self.debug==True: print "lastPart:", lastPart
##
#        # Convert all uppercase characters in string to lowercase
#        simpleHex = [x.lower() for x in [lastPart]][0]
##        if self.debug==True: print "simpleHex:", simpleHex
#
##
#        # Make proper hex string for Python
#        HEX = '0x' + simpleHex
##        if self.debug==True: print "HEX:", HEX
#        freq_Hz = DDS_HEX_to_freq(HEX=HEX)
##
##
##        return 1e-6 * freq_Hz # Conversion: Hz ---> MHz
#
#
#        # works fine if returns = 's', and we don't use value.
#
#        freq = float(freq_Hz)
#        freq = str((freq) / 10.0**6) #state is in MHz
#
#        returnValue(freq)

    @inlineCallbacks
    def _GetFreq2(self, channel=1):
        """
        Internal function for initially populating the DDS dictionary
        """
        command = self.FreqReqStr(channel = channel)
        yield self.ser.write(command)
        #yield self.ForceRead() #expect a reply from instrument
        line1 = yield self.ser.readline().addCallback(str)
        line2 = yield self.ser.readline().addCallback(str)
        line3 = yield self.ser.readline().addCallback(str)

        lastPart = line2[-12:]

        # Remove whitespace from string
        lastPart = lastPart.replace(" ", "")
#        if self.debug==True: print "lastPart:", lastPart
#
        # Convert all uppercase characters in string to lowercase
        simpleHex = [x.lower() for x in [lastPart]][0]
#        if self.debug==True: print "simpleHex:", simpleHex
#
        # Make proper hex string for Python
        HEX = '0x' + simpleHex
#        if self.debug==True: print "HEX:", HEX
        if self.debug : print "Inside _GetFreq2, HEX =", HEX
        freq_Hz = DDS_HEX_to_freq(HEX=HEX)
#
#
#        return 1e-6 * freq_Hz # Conversion: Hz ---> MHz


        # works fine if returns = 's', and we don't use value.

        freq = float(freq_Hz)
        freq = str((freq) / 10.0**6) #state is in MHz

        returnValue(freq)


    @setting(9, 'Select Device', port='s')
    def select_device(self, c, port='COM3'):
        """
        Select the DDS box device by COM port.  Options on Magic at the moment are

        COM5 - DDS Box 1
        COM3 - DDS Box 2

        port - string, COM port to select default('COM3'), set to this default for testing purposes

        2014-02-28 - Andrew Jayich
        """
        self.port = port
        try:
            serStr = yield self.findSerial(self.serNode)
            if self.debug : print "initServer serStr =", serStr
            #if self.debug: print "serStr=", serStr

            # Not sure what this does, might reset a lot of values
            self.initSerial( serStr, port )
            #if self.debug : print "Inside initServer, before except"
        except SerialConnectionError, e:
            self.ser = None
            if e.code == 0:
                print 'Could not find serial server for node: %s' % self.serNode
                print 'Please start correct serial server'
            elif e.code == 1:
                print 'Error opening serial connection'
                print 'Check set up and restart serial server'
            else: raise

        #self.populateDict()


    # TODO: reincorporate channel selection
    #@setting(4, 'Frequency', f=['v[MHz]'], channel='i', returns=['v[MHz]'])
    #@setting(4, 'Frequency', f='v[MHz]', channel='i', returns='?')
    @setting(10, 'Frequency', channel='i', f='v[MHz]', returns='?')
    def frequency(self, c, channel = 1, f = None):
        """
        Get or set channels' frequency.

        Parameters
        ----------
        f: WithUnits frequency, frequency to set
        channel: int, (1-4), default(1)
        returns the current frequency of channel if f is None
        """
        #channel = 1
        chStr = 'ch' + str(channel)


        if f is not None :

            freq_MHz = f.inUnitsOf('MHz')  # Force conversion to MHz
            freq_MHz = freq_MHz.value   # Eliminate labRad type here
            self.FreqCheck(freq_MHz)

            command = self.FreqSetStr(freq_MHz, channel)

            if self.debug : print "frequency() command =", command
            yield self.ser.write(command)

            # TODO: need to purge the buffer here


            self.DDSDict[chStr].frequency =  f

        returnValue( self.DDSDict[chStr].frequency )


    # Note, you don't pass in channel and amplitude by channel=x or amplitude=True on the front end of the server, arguments are just positional.
    @setting(8, 'Amplitude', channel=['i'], amplitude=['b'], returns=['b'])
    def amplitude(self, c, channel=1, amplitude=True):
        """
        Hack function at this point, as you can only turn the amplitude ON/OFF.

        2014-02-27 - Andrew Jayich
        """
        chStr = 'ch' + str(channel)

        if amplitude is not None :

            command = self.AmpSetStr(amplitude, channel)

            yield self.ser.write(command)

            self.DDSDict[chStr].amp = amplitude


        returnValue(self.DDSDict[chStr].amp)




    #TODO: make a function that allows you to set the amplitude over a range
    # using meaningful values, such as dBm.
    @setting(5, 'Channel State', channel='i', amp='b', returns='?')
    def channel_State(self, c, channel = 1, amp = None):
        """
        Hack fucntion to turn a channel on or off.  Sets the amplitude to the
        max value or to zero.

        channel: int channel (1-4) to set amplitude to max or zero
        amp    : b, value for amplitude, ON or OFF, default(None)

        returns the current state of channel, on or off
        """
        #channel = 1
        # We are ultimately setting this dictionary value
        chStr = 'ch' + str(channel)


        if amp is not None:

            command = self.AmpSetStr(amp, channel)

            yield self.ser.write(command)

            # TODO: need to purge the buffer here ????


            #if self.debug : print "dictString =", dictString
            self.DDSDict[chStr].amp =  amp

        returnValue( self.DDSDict[chStr].amp )



    @setting(11, "Identify", returns='s')
    def identify(self, c):
        '''Ask instrument to identify itself'''
        command = self.IdenStr()
        yield self.ser.write(command)
        #self.ForceRead() #expect a reply from instrument
        line1 = yield self.ser.readline()
        if line1 == '>Read Mode\n' :
            print "line1 hit Read Mode value"
        line2 = yield self.ser.readline()

        line3 = yield self.ser.readline()

        #returnValue(answer[:-1])

        answer = line1 + '\n' + line2 + '\n' + line3
        returnValue(answer)




    # TODO: This should replace the amplitude function eventually
    @setting(12, channel=['i'], amplitude='v[dBm]', returns='v[dBm]')
    def amplitude_dbm(self, c, channel=1, amplitude=None):
        """
        Set channel's output in dBm.

        TODO: This needs to be accurately calibrated.
        TODO: Account for frequency dependence in calibration

        Parameters
        ----------
        channel: int, 1-4 default(1)
        amplitude: WithUnits dBm type, default(None)

        Returns
        -------
        labrad.units.dBm
        """
        chStr = 'ch' + str(channel)

        if amplitude is not None :

            command = self.AmpSetStr(amplitude, channel)

            yield self.ser.write(command)

            self.DDSDict[chStr].amp = amplitude


        returnValue(self.DDSDict[chStr].amp)




    # TODO: This is a utility function to understand how to work with the
    # device.  Useful for testing purposes.
    @setting(13, channel=['i'], amplitude=['s'], returns=['s'])
    def amplitude_hex(self, c, channel=1, amplitude=None):
        """
        Set channel's output using a hex string.

        amplitude needs to be a four character string.

        Parameters

        ----------

        channel: int, 1-4 default(1)
        amplitude: str, HEX value from '0000' to 'ffff'

        Returns

        -------

        str, HEX value
        """
        chStr = 'ch' + str(channel)

        if amplitude is not None :

            command = self.AmpSetStr_HEX(channel, amplitude)

            if self.debug : print "amplitude_hex command=", command

            yield self.ser.write(command)

            self.DDSDict[chStr].ampHEX = amplitude


        returnValue(self.DDSDict[chStr].ampHEX)



#    # TODO: make sure this function works
#    @setting(12, 'list devices', returns=['s'])
#    def list_devices(self, c):
#        """
#
#
#        """
#
#        return ['COM3', 'COM5']

    ### Server Utility Functions


    def AmpSetStr(self, amp, channel):
        """
        Returns string command to set channel's amplitude

        Parmaeters
        ----------
        amp: bool, currently in binary mode
        channel: int, DDS channel to set (1-4)

        Returns
        -------
        str
        """
        chStr = self.channelString(channel=channel)

        if amp is True:
            HEX = 'ffff'   # Max amplitude
        else :
            HEX = '0000'   # Min amplitude/OFF

        return chStr + 'A' + HEX + '\n'



    def AmpSetStr_dBm(self, channel, amp):
        """
        Returns string command to set channel's amplitude

        Parmaeters
        ----------
        channel: int, DDS channel to set (1-4)
        amp: labrad.units.dBm

        Returns
        -------
        str
        """

        chStr = self.channelString(channel=channel)

        # Make sure amp is in units of dBm
        # We are going to work with the dBm value
        # as a float for conversion purposes
        amp = amp.inUnitsOf('dBm')

        # Convert amp to a float
        amp = amp.value

        HEX = DDS_dBm_to_HEX(amp)

        if amp is True:
            HEX = 'ffff'   # Max amplitude
        else :
            HEX = '0000'   # Min amplitude/OFF

        return chStr + 'A' + HEX + '\n'




    def AmpSetStr_HEX(self, channel, amp):
        """
        Returns string command to set channel's amplitude.

        The amplitude is set with 14 bits of precision.  This corresponds
        to hex values from 0x0000 to 0x3fff.

        Parmaeters
        ----------
        channel: int, DDS channel to set (1-4)
        amp: Hex string from '0000' to '3fff'

        Returns
        -------
        str
        """

        chStr = self.channelString(channel=channel)

        HEX = amp

        return chStr + 'A' + HEX + '\n'



    def FreqCheck(self, freq):
        MIN,MAX = self.DDSDict['freqrange']
        if not MIN <= freq <= MAX:
            raise Exception('Frequency Out of Allowed Range')



    def FreqReqStr(self, channel=1):
        """
        String to request the current frequency of a channel
        """
        chStr = self.channelString(channel=channel)
        return chStr + 'R0f' + '\n'


    def FreqSetStr(self, freq_MHz, channel):
        """
        String command to set a channel's frequency

        freq_MHz - frequency in MHz, labrad Value type
        channel - channel of DDS to set (1-4)
        """

        chStr = self.channelString(channel=channel)

        #freq_Hz = freq_MHz.inUnitsOf('MHz')   # Conversion: MHz ---> Hz
        freq_Hz = freq_MHz  * 1e6   # Conversion: MHz ---> Hz


        HEX = DDS_freq_to_HEX(freq = freq_Hz)
        # Need to strip off "0x" from front of HEX
        HEX = HEX[2:]

        return chStr + 'F' + HEX + '\n'




    def IdenStr(self):
        """
        Get basic device information
        """
        return '?'+'\n'

#
#    @inlineCallbacks
#    def ForceRead(self):
#       command = self.ForceReadStr()
#       yield self.ser.write(command)
#
#    def TraceReqStr(self):
#        return 'TAA?' + '\n'
#
#    def SetTraceFormatStr(self, format):
#        return 'FORM' + str(format) + '\n'
#
#    # string to force read
#    def ForceReadStr(self):
#        return '++read eoi' + '\n'
#
#    # string for prologix to request a response from instrument, wait can be 0 for listen / for talk
#    def WaitRespStr(self, wait):
#        return '++auto '+ str(wait) + '\n'


    ### Utility Functions


def DDS_freq_to_HEX(freq=160e6):
    """
    Get Hexadecimal code for a frequency "freq" in Hz
    that you want to output from the DDS board

    freq: float, frequency in Hz, default(160e6)

    """

    dec = freq * 4294967295 * 1e-9
    integer = int(dec)

    #return hex(integer)

    # The line below does awesome formatting for DDS commands.
    return "0x%0.8x" % integer



def DDS_HEX_to_freq(HEX='0x4fc3a5'):
    """
    Get frequency in Hz from hexadecmial string HEX.

    HEX: str, representation of hexadecimal number, default('0x4fc3a5')
    MUST begin iwth '0x'.  Maybe do something smart here... whatever.
    TODO: check above line

    """

    #SOooo nice:
    #print "{0:08d}".format(234555)
    integer = int(HEX, 0)   # Convert hex value to a base 10 integer

    # Do the inverse of DDS_freq_to_HEX
    freq = integer * 1e9 * (1./4294967295)

    return freq


def DDS_dBm_to_HEX(amp):
    """
    Get Hexadecimal value that is approximately equalt to the amplitude we
    want to write to the DDS in dBm.

    Parameters
    ----------
    amp: labrad.units.dBm type, default(None)

    Returns
    -------
    str, HEX value
    """



    return None


if __name__ == "__main__":
    from labrad import util
    util.runServer(DDS_Box_Server())
