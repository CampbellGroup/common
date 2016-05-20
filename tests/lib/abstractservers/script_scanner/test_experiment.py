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
        self.experiment.execute(ident='test_experiment')

    def tearDown(self):
        self.experiment = None
        del self.experiment

    def test_ident_attribute(self):
        expected_ident = 'test_experiment'
        ident = self.experiment.ident
        self.assertEqual(ident, expected_ident)

    def test_required_parameters_default(self):
        self.assertEqual(self.experiment.required_parameters, [])

    def test_name_default(self):
        self.assertEqual(self.experiment.name, '')

    def test_initialize(self):
        self.experiment.initialize(None, None, None)

    def test__connect(self):
        self.experiment._connect()

    def test_pause_or_stop(self):
        self.experiment.pause_or_stop()

    def test_set_progress_limits(self):
        self.experiment.set_progress_limits(min_progress=0., max_progress=100.)

    def test_make_experiment(self):
        self.experiment.make_experiment(subexprt_cls=_exp.experiment)

    def test_reload_all_parameters(self):
        self.experiment.reload_all_parameters()


class Test_experiment_Exceptions(_ut.TestCase):

    def setUp(self):
        self.experiment = _exp.experiment()
        self.experiment.execute(ident='test_experiment')

    def tearDown(self):
        self.experiment = None
        del self.experiment

    def test_set_parameters_exception(self):
        self.assertRaises(Exception, self.experiment.set_parameters,
                          parameter_dict=None)

    def test__connect_without_scriptscanner(self):
        self.experiment._connect()
        self.experiment.cxn.servers.pop('ScriptScanner', None)
        self.assertRaises(Exception, self.experiment._connect)

    def test__connect_without_parametervault(self):
        self.experiment._connect()
        self.experiment.cxn.servers.pop('ParameterVault', None)
        self.assertRaises(Exception, self.experiment._connect)

    def test_cxn_servers_attribute_type(self):
        self.experiment._connect()
        servers = self.experiment.cxn.servers
        self.assertIsInstance(servers, dict)
