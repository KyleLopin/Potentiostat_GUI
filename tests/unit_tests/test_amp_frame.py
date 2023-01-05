# Copyright (c) 2022-23 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License


"""
Unit test methods and functions in amp_frame.py
"""

__author__ = "Kyle Vitautas Lopin"

# standard libraries
import unittest
from unittest import mock

# local files
import amp_frame
import graph_properties
import properties


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

    def test_save_data(self):
        device = mock.Mock()
        device.time = [1, 2, 3]
        device.data = [11, 12, 13]
        self.amp_frame.save_data(device)
