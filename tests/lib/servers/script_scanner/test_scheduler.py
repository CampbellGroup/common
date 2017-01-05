"""
Test experiment.py.
"""
import unittest as _ut
import common.lib.servers.script_scanner.scheduler as _sch


class Test_experiment(_ut.TestCase):

    def setUp(self):
        self.scheduler = _sch.scheduler()

    def tearDown(self):
        self.scheduler = None
        del self.scheduler
