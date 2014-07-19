# -*- coding: utf-8 -*-

import numpy as _n
from twisted.trial.unittest import TestCase

import labrad
from labrad.types import LazyList

class Test_InteractiveServer(TestCase):
    """
    Test Basic Server
    """

    
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
        Connect to BasicServer
        """
        self.assert_(hasattr(self.cxn, 'interactive_emitter_server'))
        return self.cxn.interactive_emitter_server


    def test_ServerInServers(self):
        """
        Test that Server is in servers list
        """
        servers = self.cxn.servers
        self.assert_('interactive_emitter_server' in servers)


#        self.assert_(len(servers.keys()) > 0)
#        self.assert_('manager' in servers)

#        self._get_manager()
#        self._get_tester()
#        
#        self._get_manager()
#        self._get_tester()


    def test_AreThereServers(self):
        """
        Test that there are servers
        """
        servers = self.cxn.servers
        self.assert_(len(servers.keys()) > 0)        


    def test_echo(self):
        """
        Test that server has basic function echo
        """
        
        pts = self._get_tester()

        # make sure we can access the setting by both allowed methods
        self.assert_(hasattr(pts, 'echo'))



    def test_return_float(self):
        """
        Check that specific hard-coded value is returned.
        """
        server = self._get_tester()                        
        
        resp = server.return_float()
        exp_resp = 6.626
        self.assertEquals(resp, exp_resp)                


 

