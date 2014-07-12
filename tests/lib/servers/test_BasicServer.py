# -*- coding: utf-8 -*-

import numpy as _n
from twisted.trial.unittest import TestCase

import labrad
from labrad.types import LazyList

class Test_BasicServer(TestCase):
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
        self.assert_(hasattr(self.cxn, 'basic_server'))
        return self.cxn.basic_server


    def test_BasicServerInServers(self):
        """
        Test that BasicServer is in servers
        """
        servers = self.cxn.servers
        self.assert_('basic_server' in servers)


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


    def test_faux_echoExists(self):
        """
        Test that server has function  faux_echo
        """
        
        pts = self._get_tester()

        # make sure we can access the setting by both allowed methods
        self.assert_(hasattr(pts, 'faux_echo'))
                

    def test_faux_echoResponse(self):
        """
        Test that fuax_echo responds appropriately
        """
        pts = self._get_tester()                        
        
        # single setting, named explicitly
        resp = pts.faux_echo('faux_echo string test')
        self.assertEquals(resp, 'faux_echo string test')


    def test_return_float(self):
        """
        Check that specific hard-coded value is returned.
        """
        server = self._get_tester()                        
        
        resp = server.return_float()
        exp_resp = 137.036
        self.assertEquals(resp, exp_resp)                

    def test_return_floatyield(self):
        """
        Check when looking for a yield output it works.
        """
        server = self._get_tester()                        
        
        resp = yield server.return_float()
        exp_resp = 137.036
        self.assertEquals(resp, exp_resp)  
        

    def test_return_floatList(self):
        server = self._get_tester()                        
        
        resp = server.return_floatList()
        exp_resp = [87.04, 0.001, -1.09, 1e-5, 2.]
        self.assertEquals(resp, exp_resp)          

    def test_return_npArray1D(self):
        server = self._get_tester()                        
        
        resp = server.return_npArray1D()
        exp_resp = _n.array([1., 2., 1e-5, 237])
        #self.assertEquals(resp, exp_resp)  
        self.assertTrue(_n.array_equal(exp_resp, resp))


    def test_return_npArray2D(self):
        server = self._get_tester()                        
        
        resp = server.return_npArray2D()
        exp_resp = _n.array([[1., 4.6, 1e-5], [45, -1, 1./45.]])
        self.assertTrue(_n.array_equal(exp_resp, resp) )


    def test_return_npArray2DType(self):
        """
        Test output type.
        """
        server = self._get_tester()                        
        
        resp = server.return_npArray2D()

        # Arguments given might not make sense, 
        # but they give the correct type.
        exp_resp = type(LazyList(None, 's', None))

        self.assertEquals(type(resp), exp_resp)


    def test_return_npArray2DUnflatten(self):
        """
        Test unflattening of array output.
        """
        server = self._get_tester()                        
        
        # This resturns a LazyList, which we
        resp = server.return_npArray2D()
        
        val = resp._unflattenArray()

        # Arguments given might not make sense, 
        # but they give the correct type.
        exp_val = _n.array([[1., 4.6, 1e-5], [45, -1, 1./45.]])

        self.assertTrue(_n.array_equal(val, exp_val) )




