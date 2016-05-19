"""
Test experiment.py.
"""
import unittest as _ut
import sys
from common.tests.mocks.modules.mock_labrad import MockLabrad
sys.modules['labrad'] = MockLabrad()
import common.lib.servers.abstractservers.script_scanner.experiment as _exp


class Test_experiment(_ut.TestCase):

    def setUp(self):
        self.experiment = _exp.experiment()

    def tearDown(self):
        self.experiment = None
        del self.experiment

    def test_execute(self):
        self.experiment.execute(ident='test_experiment')

    def test_required_parameters_default(self):
        self.assertEqual(self.experiment.required_parameters, [])

    def test_name_default(self):
        self.assertEqual(self.experiment.name, '')

    def test_initialize(self):
        self.experiment.initialize(None, None, None)

    def test__connect(self):
        self.experiment._connect()
