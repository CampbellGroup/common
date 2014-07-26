# -*- coding: utf-8 -*-

import numpy as _n
from twisted.trial.unittest import TestCase

import labrad
from labrad.types import LazyList
import labrad.units as _u

class Test_TypesServer(TestCase):
    """
    Test Types Server.  Check against different pylabrad branches.
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
        self.assert_(hasattr(self.cxn, 'types_server'))
        return self.cxn.types_server


    def test_serverInServers(self):
        """
        Test that BasicServer is in servers
        """
        servers = self.cxn.servers
        self.assert_('types_server' in servers)


    def test_AreThereServers(self):
        """
        Test that there are servers
        """
        servers = self.cxn.servers
        self.assert_(len(servers.keys()) > 0)        


    def test_echoExists(self):
        """
        Test that server has basic function echo
        """
        
        server = self._get_tester()

        self.assert_(hasattr(server, 'echo'))


    def test_return_boolExists(self):
        """
        Test that server has function return_bool
        """
        
        server = self._get_tester()

        # make sure we can access the setting by both allowed methods
        self.assert_(hasattr(server, 'return_bool'))


    def test_return_boolType(self):
        """
        Test type of server.return_bool response
        """
        
        server = self._get_tester()
        resp = server.return_bool()
        val = type(resp)
        
        exp_val = type(True)
        self.assertEqual(val, exp_val)                


    def test_return_intType(self):
        """
        Test type of server.return_int response
        """
        
        server = self._get_tester()
        resp = server.return_int()
        val = type(resp)
        
        exp_val = type(int(45))
        self.assertEqual(val, exp_val)                


    def test_return_int(self):
        """
        Test type of server.return_int response
        """
        
        server = self._get_tester()
        resp = server.return_int()
        
        exp_resp = 23
        self.assertEqual(resp, exp_resp)      



    def test_return_uintType(self):
        """
        Test type of server.return_iunt response
        """
        
        server = self._get_tester()
        resp = server.return_uint()
        val = type(resp)
        
        exp_val = type(long(45))
        self.assertEqual(val, exp_val)                


    def test_return_uint(self):
        """
        Test type of server.return_uint response
        """
        
        server = self._get_tester()
        resp = server.return_uint()
        
        exp_resp = 86
        self.assertEqual(resp, exp_resp)      


    def test_return_v_unitType(self):

        server = self._get_tester()
        resp = server.return_v_unit()
        val = type(resp)
        
        exp_val = type(_u.WithUnit(4., 'Hz'))
        self.assertEqual(val, exp_val)                


    def test_return_v_unit(self):

        server = self._get_tester()
        resp = server.return_v_unit()
        
        exp_resp = _u.WithUnit(60., 'Hz')
        self.assertEqual(resp, exp_resp)      


    def test_return_v_bracketsType(self):

        server = self._get_tester()
        resp = server.return_v_brackets()
        val = type(resp)
        
        exp_val = type(57.0)
        self.assertEqual(val, exp_val)                


    def test_return_v_brackets(self):

        server = self._get_tester()
        resp = server.return_v_brackets()
        
        exp_resp = 127.1
        self.assertEqual(resp, exp_resp)  

    def test_return_c_unitType(self):

        server = self._get_tester()
        resp = server.return_c_unit()
        val = type(resp)
        
        exp_val = type(_u.WithUnit(9.+1j*8., 'Hz'))
        self.assertEqual(val, exp_val)                


    def test_return_c_unit(self):

        server = self._get_tester()
        resp = server.return_c_unit()
        
        exp_resp = _u.WithUnit(9.+1j*3., 'Hz')
        self.assertEqual(resp, exp_resp)  


    def test_return_c_bracketsType(self):

        server = self._get_tester()
        resp = server.return_c_brackets()
        val = type(resp)
        
        exp_val = type(3. + 1j * 4.)
        self.assertEqual(val, exp_val)                


    def test_return_c_brackets(self):

        server = self._get_tester()
        resp = server.return_c_brackets()
        
        exp_resp = 1. + 1j * 4.
        self.assertEqual(resp, exp_resp)  



    def test_return_star_v_bracketsType(self):

        server = self._get_tester()
        resp = server.return_star_v_brackets()
        val = type(resp)
        
        exp_val = type(_n.ndarray([4., 4., 2.]))
        self.assertEqual(val, exp_val)                


    def test_return_star_v_brackets(self):

        server = self._get_tester()
        resp = server.return_star_v_brackets()
        
        exp_resp = _n.ndarray([4., 36., 2.])
        self.assertEqual(resp, exp_resp)  





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


    def test_return_npArray3DUnflatten(self):
        """
        Test unflattening of an array that will look 
        like camera output
        """
        server = self._get_tester()                        
        
        # This resturns a LazyList, which we
        resp = server.return_npArray3D()
        
        val = resp._unflattenArray()

        # Arguments given might not make sense, 
        # but they give the correct type.
        exp_val = _n.empty( (492, 656, 1) )

        self.assertTrue(_n.array_equal(val, exp_val) )


