# labRAD server tutorial example using the RIGOL DG1022.  This is a relatively
# inexpensive two channel signal generator based on DDS technology.



# TODO: Need a healthy description of the special docstring below.

# "### BEGIN NODE INFO"  - TODO: write this up, labRAD blah blah to signify
# the start of node info.  

# TODO:  description of whatever the heck a node in labRAD is.

# "name" - will be the name of this server on labRAD, with the 
# space replaced by an underscore and capital letters made
# lowercase, so it will read: cxn.rigol_dg1022  (after running cxn = labrad.connect())

# "version" - TODO: write this up

# "description" - TODO: write this up

# "[startup]" - TODO: write this up

# "cmdline"  - TODO: write this up

# first "timeout" - TODO: write this up

# "[shutdown]" - TODO: write this up

# "message" - special labRAD shutdown message, hence the countdown 9876...

# second "timeout" - TODO: write this up

### "END NODE INFO  - TODO: write this up, labRAD blah blah to signify the end
# of the node info


"""
### BEGIN NODE INFO
[info]
name = Rigol DG1022
version = 1.0
description = 

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""


# Describe the imports here...  Need a comment for each line

from labrad.server import setting

# Import the two classes that will be subclassed below
from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper

# This provides commonly used functions from twisted that allow
# for asynchronous communcation with devices.
from twisted.internet.defer import inlineCallbacks, returnValue

# Why import T and WithUnit?  what is the difference and what do they do?
from labrad.units import WithUnit
from labrad import types as T



# TODO: track hardware Errors from the device



class RigolDG1022Wrapper(GPIBDeviceWrapper):
    """
    Wrapper for the RIGOL DG1022.  The user does not see these commands, but 
    instead interacts with the server.  The wrapper is the place to store the
    low level commands.  The server can be designed to intelligently interact
    with these low level device commands.
    
    Syntax - the command names given below should closely follow the GPIB
    commands that are issued to the instrument.
    """
    
    # We include this debug line so that debug statements print if
    # we are trying to debug this device wrapper.
    debug = False
    
    # Probably should inclue channel variable here to track which channel is active
    # or in the server

    # Server set this value to elect a channel to get and set values of
    # The variable is saved and called throughout the code below
    # to issue the correct commands
    selectedChannel = None


    ### FUNCtion Commands

    @inlineCallbacks
    def getFunction(self):
        """
        Get function output of the selected channel, set as self.selectedChannel
        """
        
        # Check here to see if the selected channel is channel one
        # Get whatever function channel 1 is set to output        
        if self.selectedChannel == 1:
            val = yield self.query('FUNCtion?')
        
        # Check here to see if the selected channel is channel two,
        # Get whatever function channel 2 is set to output        
        elif self.selectedChannel == 2:
            val = yield self.query('FUNCtion:CH2?')


        # Handle error in not having a selected channel
        else :
            print "Neither channel 1 nor channel 2 in the wrapper has been set."
            
            # TODO:
            val = None  # Perhaps return something intelligent here, error 
                        # code for channel not selected.  Woudl be great
            
            
        # When using asynchronous communication we use the special return, 
        # returnValue, I think this returns a deferred, need to detail this
        # in the tutorial.
        returnValue(val)


    @inlineCallbacks
    def setFunction(self, val='RAMP'):
        """
        Set function output of the selected channel, set as self.selectedChannel

        val - str, valid values are 'SINusoid', 'SQUare', 'RAMP', 'PULSe', 
            'NOISe', 'DC',  not programmed in yet: 'USER', default(val, 'RAMP')
            

        """

        # TODO: error checking on valid arguments.  Or better, handling
        # GPIB errors that are returned.

        
        # Check here to see if the selected channel is channel one
        # Get whatever function channel 1 is set to output        
        if self.selectedChannel == 1:
            
            command = "FUNCtion " + val
            yield self.write(command)
        
        # Check here to see if the selected channel is channel two,
        # Get whatever function channel 2 is set to output        
        elif self.selectedChannel == 2:
            command = "FUNCtion:CH2 " + val
            yield self.query(command)


        # Handle error in not having a selected channel
        else :
            print "Neither channel 1 nor channel 2 in the wrapper has been set."
            
            # TODO:
            val = None  # Perhaps return something intelligent here, error 
                        # code for channel not selected.  Woudl be great
            




        
    @inlineCallbacks
    def getVoltage(self):
        """
        Get the self.channel's output voltage.  Measured at the device.
        """
        voltage = yield self.query('MEAS:VOLT:DC?').addCallback(float)
        voltage = WithUnit(voltage,'V')
        if self.debug : print "getVoltage, voltage =", voltage
        returnValue(voltage)

        
        
    @inlineCallbacks
    def setVoltage(self, voltage):
        yield self.write('VOLT {}'.format(voltage['V']))
        #self.voltages[self.chanNumber]= voltage   # Set the voltage in the voltages dictionary,
        # This tracks the active channel



        
    @inlineCallbacks
    def getCurrent(self):
        """
        Get the output current.
        """
        current = yield self.query('MEAS:CURR:DC?').addCallback(float)
        current = WithUnit(current,'A')
        returnValue(current)



    @inlineCallbacks
    def setCurrent(self, current):
        yield self.write('CURR {}'.format(current['A']))
        # This is the only the "set" current or voltage value, not the real value
        #self.currents[self.chanNumber] = current    

    

    
    @inlineCallbacks
    def setOutput(self, output):
        # TODO: line below needs to be fixed to actually change the output
        if self.debug : print "setOutput argument output =", output
        
        # Warning, double quotes below seem to be the difference maker     
        # STILL not working
        # TODO: get the below working
        # consider using gpib_write()
        if output == True :
            yield self.write("OUTput ON")
        elif output == False:
            yield self.write("OUTput OFF")
        
        #if self.debug : print "setOutput command =", command
        #yield self.write(command)
        #yield self.write('OUTPut {}'.format(int(output)))

        # TODO: deprecate this line eventually
        #self.output = output
        
        
        #self.outputs[self.chanNumber] = output     

    @inlineCallbacks
    def getOutput(self):
        state = yield self.query('OUTPut?').addCallback(int).addCallback(bool)
        returnValue(state)

#
#    @inlineCallbacks
#    def getOutputs(self):
#        """
#        Get output status for both channels, populate outputs dictionary.
#        
#        Intended as an internal intialization function.
#        
#        2014-01-29 - Andrew Jayich
#        """
#        originalChannel = self.chanNumber   # Save the active channel, to be reset at the end
#        
#        # Channel 1
#        channel = 1
#        yield self.setChannel(channel)
#        self.outputs[channel] = yield self.getOutput()  # Include value in dictionary
#        
#        # Channel 2
#        channel = 2
#        yield self.setChannel(channel)
#        self.outputs[channel] = yield self.getOutput()  # Include value in dictionary        
#        
#        # Reset to original channel
#        yield self.setChannel(originalChannel)




    @inlineCallbacks
    def getChannel(self):
        """
        Get the device's active channel.  
        
        returns 1 or 2
        
        Andrew Jayich 2014-01-24
        """
        #current = yield self.query('MEAS:CURR:DC?').addCallback(float)
        #current = WithUnit(current,'A')
        #returnValue(current)


        #if self.debug : print "Start of getChannel"
        
        #val = yield self.query('INST:NSEL?').addCallback(float)
        #val = yield self.query('INSTrument:NSELect?').addCallback(int)#.addCallback(bool)

        val = yield self.query('INSTrument:SELect?')

        #if self.debug : print "getChannel val=", val
        #val = T.Int(val)   # Convert to labrad Integer type
        if self.debug : print "val just before returnValue(val), =", val    
        if val == 'OUTP1' :
            val = 1
        elif val == 'OUTP2' :
            val = 2
        #self.chanNumber = val
        returnValue(val)
            


    @inlineCallbacks
    def setChannel(self, chan):
        """
        Set the device's active channel (1 or 2).  
        
        Andrew Jayich 2014-01-24
        """

        set_ch = 'INSTrument:NSELect ' + str(chan)
        yield self.write(set_ch)
        #self.chanNumber = chan





class RigolDG1022Server(GPIBManagedServer):
    """
    These functions are accessed by the user and provide an interface to the 
    RIGOL DG1022 dual channel frequency generator.
    
    This class provides high level commands that interface with the low-level
    commands of the RigolDG1022Wrapper.
    
    There are multiple options for how to handle devices.  We try here to make
    the interface mimic the physical interface with the system. One example of 
    this is that Ch1 or Ch2 is selected, using a function, and then once
    selected one accesses voltage and frequency settings of that particular
    channel without specifying the channel again unless one wants to switch
    channels.
    
    Note: Alternatively we could have setup the server so that functions all take a
    channel argument, in addition to whatever value of the specified channel
    is being changed.
    
    2014-03-31 - Andrew Jayich
    """
    
    # Check, this name might need to match the NODE INFO given above.
    
    # A debug variable for the convenience of debuggin the server.
    debug = False
    #selectedChannel = None   # Select a channel to get and set values of
    
    #It is important to get variable deviceName to match the response from *IDN? 
    # If you don't the gpib device manager will not be able to connect the server
    # See the tutorial for how this device name was found.  
    # TODO: include one line or two line note here on how to find the deviceName
    name = 'Rigol DG1022'
    deviceName = 'RIGOL TECHNOLOGIES DG1022A'
    deviceWrapper = RigolDG1022Wrapper

    def initContext(self, c):
        """
        TODO: big description here.  Is this overloading something, etc.
        
        """
        if self.debug : print "First line of initContext."
        c['dict'] = {}


    # @setting values that are already taken by the superclass object
    # 1 - List Devices
    # 2 - Select Device
    # 3 - Deselect Device

    # First @setting needs a healthy description...
    # The first number is the number for the setting.  This needs to be unique
    # across all server functions.  Make them increase linearly as you move 
    # downwards.
    @setting(4, 'channel', channel=['i'], returns=[''])
    def channel(self, c, channel=None):
        """
        TODO: properly format this for labRAD output
        Haeffner lab has no examples of this to my knowledge
        
        This sets the self.selectedChannel and will be used in all functions
        to set voltages, frequencies, functions of the selected channel
        in all the server functions.  
        
        Note there is a functional difference between channel 1 and 2.  This
        needs to be accounted for in this device server and wrapper.

        c - context dictionary.  For handling multipled RIGOL DG1022 devices
        connected to the same computer
            
        channel - int, select a channel, None returns the selected channel
        
        """
        dev = self.selectedDevice(c)        
        
        
        if channel == None:
            returnValue(dev.selectedChannel)

        elif channel == 1: # Select channel one
            dev.selectedChannel = channel
        elif channel == 2: # Select channel two         
            dev.selectedChannel = channel

        else:  # Return an error message
            print "Channel == 1, 2 or None, not:", channel            
        
        
        
        
    @setting(5, 'Function', function=['s'], returns=['s'])
    def function(self, c, function=None):
        """
        Set the function of the selected channel.
        
        function - str, valid values are 'SINusoid', 'SQUare', 'RAMP', 'PULSe', 
            'NOISe', 'DC',  not programmed in yet: 'USER'

        """
        dev = self.selectedDevice(c)
    
        if function == None:
            val = yield dev.getFunction()
            returnValue(val)

        else:
            dev.setFunction(val = function)



    @setting(10, 'Voltage', voltage=['v[V]'], returns=['v[V]'])
    def voltage(self, c, voltage=None):
        """
        Get or set the active channel's voltage.
        
        
        
         - Andrew Jayich
        """
        if self.debug : print "in Wrapper voltage, c =", c
        dev = self.selectedDevice(c)
        
        if voltage is not None:
            if self.debug : print "voltage, setting to voltage =", voltage
            yield dev.setVoltage(voltage)
            
        currentVoltage = yield dev.getVoltage()
        #dev.voltages[dev.chanNumber] = currentVoltage
        
        if self.debug : print "voltage() currentVoltage =", currentVoltage
        #print "out from dev.voltages[dev.Channel] =", dev.voltages[dev.chanNumber]
        returnValue(currentVoltage)

    



    @setting(11, 'Current', current=['v[A]'], returns=['v[A]'])
    def current(self, c, current=None):
        """
        Get or set the active channel's current."
        
        2013-01-27 - Andrew Jayich
        """
        dev = self.selectedDevice(c)

        if self.debug : print "in Wrapper current, c =", c


        if self.debug : print "Inside Wrapper current, current =", current        
        
        if current is not None:
            yield dev.setCurrent(current)

        currentCurrent = yield dev.getCurrent()            
        #dev.currents[dev.chanNumber] = currentCurrent        
        
        returnValue(currentCurrent)


    @setting(12, 'Output', output=['b'], returns=['b'])
    def output_state(self, c, output=None):
        """Get or set the output status."""
        dev = self.selectedDevice(c)

        #if self.debug : print "Server output_state, dev.chanNumber =", dev.chanNumber        
        if self.debug : print "in Wrapper output_state c =", c


        if output is not None:
            if self.debug : print "Server output_state, output =", output
            yield dev.setOutput(output)
            
        outVal = yield dev.getOutput()
        
        returnValue(outVal)


    # Why lists for these items?
    # '?' for channel breaks code
    # '_' doesn't work with for example T.Int(2)
    # Crucial to set default function argument to None in the function line
    @setting(13, 'Channel', ch=['i'], returns=['i'])        
    def devChannel(self, c, ch=None):
        """
        Set or get the device channel.  When the channel number is set
        voltage and current functions will apply to this channel.
        
        channel - 1, 2 or None
        
        returns 1 or 2
        
        Andrew Jayich 2014-01-24
        """
        if self.debug : print "in Wrapper devChannel ch =", ch
        if self.debug : print "in Wrapper devChannel c =", c
        if self.debug : print "in Wrapper devChannel c.ID = ", c.ID

        # TODO: somehow the context is getting changed here at selectedDevice, but not
        # in other functions.
        dev = self.selectedDevice(c)

        if self.debug : print "in Wrapper devChannel after self.selectedDevice(c), c =", c
        if self.debug : print "in Wrapper devChannel c.ID = ", c.ID

            
        if ch is not None : # set the channel
            # TODO: handle input where 1 or 2 is not specified (User error at this point)
            #yield dev.setChannel(T.Int(channel))
            yield dev.setChannel(ch)

            
        chanVal = yield dev.getChannel().addCallback(int)
        if self.debug : print "devChannel() dev.chanNumber =", chanVal        
        
        returnValue(chanVal)




__server__ = RigolDG1022Server()


if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
