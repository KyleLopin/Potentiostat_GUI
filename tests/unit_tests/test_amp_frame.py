# Copyright (c) 2022-23 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License


"""
Unit test methods and functions in amp_frame.py
"""

__author__ = "Kyle Vitautas Lopin"

# standard libraries
import filecmp
import os
import unittest
from unittest import mock

# local files
import amp_frame
import graph_properties
import properties

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
SOLN_FILE = os.path.join(FILE_DIR, 'test1_soln.csv')
SAVED_FILE = os.path.join(FILE_DIR, 'test.csv')


class TestAmpFrame(unittest.TestCase):
    @classmethod
    @mock.patch("amp_frame.AmpFrame.make_graph_area")
    def setUpClass(cls, mocked_graph) -> None:
        cls.mocked_root = mock.Mock()
        cls.mocked_root.frames = [mock.Mock(), mock.Mock()]
        cls.mocked_root.device_params = properties.DeviceParameters()
        print(dir(cls.mocked_root))
        graph_props = graph_properties.GraphProps()
        cls.amp_frame = amp_frame.AmpFrame(cls.mocked_root, None, graph_props)

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(SAVED_FILE):
            os.remove(SAVED_FILE)

    def test_save_data(self):
        device = mock.Mock()
        device.time = [1, 2, 3]
        device.data = [11, 12, 13]
        with mock.patch('amp_frame.open_file') as mock_open:
            mock_open.return_value = SAVED_FILE
            self.amp_frame.save_data(device)
            self.assertTrue(filecmp.cmp(SAVED_FILE, SOLN_FILE))
