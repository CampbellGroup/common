"""
Test experiment_info.py.
"""
import unittest as _ut
import common.lib.servers.abstractservers.script_scanner.experiment_info as _ei
import treedict as _td


class Test_experiment_info(_ut.TestCase):
    '''
    holds informaton about the experiment
    '''

    def setUp(self):
        self.experiment_info = _ei.experiment_info()

    def tearDown(self):
        self.experiment_info = None
        del self.experiment_info

    def test_parameters_type(self):
        required = self.experiment_info.parameters
        self.assertIsInstance(required, _td.TreeDict)

    def test_required_parameters_default(self):
        self.assertEqual(self.experiment_info.required_parameters, [])

    def test_name_default(self):
        self.assertEqual(self.experiment_info.name, '')
