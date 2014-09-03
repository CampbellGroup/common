"""

"""

from twisted.trial.unittest import TestCase

import labrad

class TestDDS_BOX_SERVER(TestCase):
    
    debug = False
 
    def setUp(self):
        """
        Connect to labrad
        """
        self.cxn = labrad.connect() #host='localhost')
        
    
    def tearDown(self):
        """
        Disconnect from labrad
        """        
        self.cxn.disconnect()


    def _get_tester(self):
        """
        Connect to DDS_BOX_SERVER.  Check that the labrad connection
        has this servers attribute.
        
        Returns
        -------
        cxn.dds_box_server: labrad server
        """
        self.assert_(hasattr(self.cxn, 'dds_box_server'))
        return self.cxn.dds_box_server
    

    def test_echo(self):
        """
        Test that server has basic function echo
        """
        
        server = self._get_tester()
        self.assert_(hasattr(server, 'echo'))


    def test_list_devices(self):
        """
        Hardware dependent test that checks list devices.
        
        A DDS box must be connected for this to work.
        
        TODO: somehow replace device with a mock device that provides this 
        information
        """        
        server = self._get_tester()
        
        resp = server.list_devices()
        
        # TODO: get correct value for this.
        expected_resp = ['50-0503317586']
        self.assertEquals(resp, expected_resp)
        
        
    def test_get_frequency(self):
        """
        
        """
        server = self._get_tester()

        resp = server.get_frequency()

        expected_resp = ['50-0503317586']
        self.assertEquals(resp, expected_resp)       
 

    def test_identify(self):
        server = self._get_tester()

        resp = server.identify()

        expected_resp = '50-0503317586'
        self.assertEquals(resp, expected_resp)         
       

    def test_name(self):
        """
        Test server name
        """
        server = self._get_tester()
        
        resp = server.name
        expected_resp = 'DDS Box Server'
        self.assertEquals(resp, expected_resp)  
        


# Hmmm... This is basically synchronous testing, or should just be tested 
# when working with the server?        
#class test_DDS_Box_Channel()
        


        