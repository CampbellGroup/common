# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 10:39:47 2014

@author: Andrew Jayich
"""


# TODO: change this import when class is moved to multiplexerclient.py
import common.lib.clients.Multiplexer.wlm_client_config as wm_config


def test():
    """
    This function runs all the tests available for the tested module.

    The return value is counterintuitve, 1 if the test fails, but this allows
    us to easily track the number of failures over all modules.

    Returns
    -------
    test_value: int, 0 if test passes, 1 if test fails

    """

    debug = False   
    test_errors = 0
    test_value = 0

    test_errors = test_multiplexer_config(test_errors, debug)
    test_errors = test_ChannelSettings(test_errors, debug)
    #test_errors = test_channelFloatConvert(test_errors, debug)



    if test_errors == 0 :
        print "Passed multixplerclient_test.test()."
        pass
    else:
        test_value = 1
        print "multiplexerclient_test.test() had", test_errors, "errors."




    return test_value



#### Test multiplexer_config() class

def test_multiplexer_config(test_errors, debug):
    """
    Test the multiplexer_config class.
    
    """


    val = {'Repump':     (1, '320.', (0,1), True),
            'Pebbles':    (3, '321.', (0,0), False),
            'Bamm-Bamm':  (4, '350.', (1,0), True),
            }
    
    mp_conf = wm_config.multiplexer_config(test_flag=True)
    
    #if val == multiplexer_config.info :
    if val == mp_conf.info :
        pass
    else:
        test_errors += 1
        print "FAILED original class test"

    test_errors = test_makeTupleDict(test_errors, debug)



    return test_errors
    
    
def test_makeTupleDict(test_errors, debug):
    """
    """

    mp_conf = wm_config.multiplexer_config(test_flag=True)


    val = {'Repump':     (1, '320.', (0,1), True),
            'Pebbles':    (3, '321.', (0,0), False),
            'Bamm-Bamm':  (4, '350.', (1,0), True),
            }    

    if debug : print "mp_conf.info_3=", mp_conf.info
 
    if val == mp_conf.info :
        pass
    else:
        test_errors += 1
        print "FAILED test_makeTupleDict()"




    return test_errors   
    

#def test_channelFloatConvert(test_errors, debug):
#    """
#    
#    """
#    
#        
#    mp_conf = wm_config.multiplexer_config(test_flag=True)
#
#    
#    val = ('Repump', (1, '320.', (0,1), True))
#
#    ch_val = ('Repump', (1.0, '320.', (0.0,1.0), True))
#    
#    ch_val = mp_conf.channelFloatConvert(ch_val)
#             
#    if val == ch_val :
#        pass
#    else:
#        test_errors += 1
#        print "FAILED test_channel_floats_to_ints()"
#        
#    return test_errors
    
### Test ChannelSettings() class

def test_ChannelSettings(test_errors, debug):
    """
    Test the ChannelSettings class.

    Parameters
    ----------
    test_errors: int, track the number of errors
    debug: bool, for debugging

    Returns
    -------
    test_errors
    """
    
    test_errors = test_ChannelSettings_default(test_errors, debug)     
    test_errors = test_ChannelSettings_args(test_errors, debug)

        
    return test_errors



def test_ChannelSettings_default(test_errors, debug):
    """
    Test the default settings of ChannelSettings
    """
    
    chSet = wm_config.ChannelSettings()
    flag = True
    
    ### Test default values of ChannelSettings    
    
    val = "Repump"
    if val == chSet.name :
        pass
    else:
        test_errors += 1
        print "FAILED default name"
        flag = False        
        
    val = 1
    if val == chSet.ch_number :
        pass
    else:
        test_errors += 1
        print "FAILED default ch_number"
        flag = False

    val = '320.'
    if val == chSet.freq_guess :
        pass
    else:
        test_errors += 1
        print "FAILED default freq_guess"
        flag = False 
        
        
    val = [0, 1]
    if val == chSet.gui_position :
        pass
    else:
        test_errors += 1
        print "FAILED default gui_position"        
        flag = False

    val = True
    if val == chSet.stretch :
        pass
    else:
        test_errors += 1
        print "FAILED default stretch"      
        flag = False

    if debug : 
        if flag : print "PASSED test_ChannelSettings_default()"        
    
        
    return test_errors



def test_ChannelSettings_args(test_errors, debug):
    """
    Test ChannelSettings with non-default arguments
    """
    chSet = wm_config.ChannelSettings(name="Pebbles", ch_number=3, freq_guess='321.', gui_position=[0,0], stretch=False)
    flag = True
    
    ### Test default values of ChannelSettings    
    
    val = "Pebbles"
    if val == chSet.name :
        pass
    else:
        test_errors += 1
        print "FAILED args name"
        flag = False        
        
    val = 3
    if val == chSet.ch_number :
        pass
    else:
        test_errors += 1
        print "FAILED args ch_number"
        flag = False

    val = [0, 0]
    if val == chSet.gui_position :
        pass
    else:
        test_errors += 1
        print "FAILED args gui_position"
        flag = False
        

    val = '321.'
    if val == chSet.freq_guess :
        pass
    else:
        test_errors += 1
        print "FAILED args freq_guess"
        flag = False 

    val = False
    if val == chSet.stretch :
        pass
    else:
        test_errors += 1
        print "FAILED args stretch"      
        flag = False

    if debug : 
        if flag : print "PASSED test_ChannelSettings_args()"      
        
        
    return test_errors
    
    
    
    
    
    