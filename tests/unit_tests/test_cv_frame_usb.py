# Copyright (c) 2022 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""

"""

__author__ = "Kyle Vitautas Lopin"

# standard libraries
import unittest
from unittest import mock

# local files
import cv_frame
import graph_properties
import properties


class TestCVFrameUSB(unittest.TestCase):
    @mock.patch("cv_frame.CVFrame.make_graph_area")
    def test_get_and_display_data(self, mocked_graph):
        mocked_root = mock.Mock()
        mocked_root.frames = [mock.Mock()]
        mocked_root.device_params = properties.DeviceParameters()
        # print(f"device params: {dir(mocked_root.device_params.cv_settings)}")
        # print(f"start voltage: {mocked_root.device_params.cv_settings.start_voltage}")
        # print(f"end voltage: {mocked_root.device_params.cv_settings.end_voltage}")
        # print(f"use_swv: {mocked_root.device_params.cv_settings.use_swv}")
        # print(f"swv inc: {mocked_root.device_params.cv_settings.swv_inc}")
        # print(f"swv height: {mocked_root.device_params.cv_settings.swv_height}")
        # mocked_root.device_params = mock.Mock()
        graph_props = graph_properties.GraphProps()
        _cv_frame = cv_frame.CVFrame(mocked_root, None, graph_props)
        _cv_frame.device.run_button = mock.Mock()
        print(f"run button: {_cv_frame.device.run_button}")
        mocked_canvas = mock.Mock()
        _cv_frame.device.get_and_display_data(mocked_canvas)
        print(f"calls: {mocked_canvas.update_data.call_args}")
        print(f'use swv: {}')

