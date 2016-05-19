"""
Test experiment.py.
"""
import unittest as _ut
import common.lib.servers.abstractservers.script_scanner.experiment as _exp


class Test_experiment(_ut.TestCase):

    def setUp(self):
        self.experiment = _exp.experiment()

    def tearDown(self):
        self.experiment = None
        del self.experiment

    def test_required_parameters_default(self):
        self.assertEqual(self.experiment.required_parameters, [])

    def test_name_default(self):
        self.assertEqual(self.experiment.name, '')
