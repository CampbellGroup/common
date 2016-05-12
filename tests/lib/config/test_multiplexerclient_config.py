# -*- coding: utf-8 -*-
"""
Test the multiplexerclient.
"""
import unittest as _ut
import common.lib.config.multiplexerclient_config as _mc_config


class TestMultiplexerConfig(_ut.TestCase):

    def setUp(self):
        self.default_config = _mc_config.multiplexer_config()

    def tearDown(self):
        self.default_config = None
        del self.default_config

    def test_laser_1_port(self):
        expected_value = 1
        value = self.default_config.info['Laser 1'][0]
        self.assertEqual(expected_value, value)

    def test_laser_1_hint(self):
        expected_value = '461.251000'
        value = self.default_config.info['Laser 1'][1]
        self.assertEqual(expected_value, value)

    def test_laser_1_display_location(self):
        expected_value = (0, 1)
        value = self.default_config.info['Laser 1'][2]
        self.assertEqual(expected_value, value)

    def test_laser_1_stretched(self):
        expected_value = True
        value = self.default_config.info['Laser 1'][3]
        self.assertEqual(expected_value, value)

    def test_laser_1_display_pid(self):
        expected_value = False
        value = self.default_config.info['Laser 1'][4]
        self.assertEqual(expected_value, value)

    def test_laser_1_dac(self):
        expected_value = 1
        value = self.default_config.info['Laser 1'][5]
        self.assertEqual(expected_value, value)

    def test_laser_1_dac_rails(self):
        expected_value = [-10, 10]
        value = self.default_config.info['Laser 1'][6]
        self.assertEqual(expected_value, value)
