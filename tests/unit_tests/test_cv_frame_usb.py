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
import usb_comm


class TestCVFrameUSB(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with mock.patch("cv_frame.CVFrame.make_graph_area") as mocked_graph:
            cls.mocked_root = mock.Mock()
            cls.mocked_root.frames = [mock.Mock()]
            cls.mocked_root.device_params = properties.DeviceParameters()
            cls.mocked_root.device.get_data.return_value = [5, 0, 10, 5, 15, 10, 20, 15, 25, 20,
                                                            20, 15, 15, 10, 10, 5, 5, 0]
            cls.mocked_root.device.process_data.return_value =[
                0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]
            settings = cls.mocked_root.device_params.cv_settings
            settings.start_voltage = 0
            settings.end_voltage = 20
            settings.use_swv = True

            graph_props = graph_properties.GraphProps()
            cls._cv_frame = cv_frame.CVFrame(cls.mocked_root, None, graph_props)
            cls._cv_frame.device.run_button = mock.Mock()


    @mock.patch("cv_frame.CVFrame.make_graph_area")
    def test_get_and_display_data(self, mocked_graph):
        settings = self.mocked_root.device_params.cv_settings
        device = self.mocked_root.device
        print(f" mocked root.device: {self.mocked_root.device}")
        # print(f"device params: {dir(mocked_root.device_params.cv_settings)}")
        print(f"start voltage: {settings.start_voltage}")
        print(f"end voltage: {self.mocked_root.device_params.cv_settings.end_voltage}")
        print(f"use_swv: {self.mocked_root.device_params.cv_settings.use_swv}")
        # print(f"swv inc: {mocked_root.device_params.cv_settings.swv_inc}")
        # print(f"swv height: {mocked_root.device_params.cv_settings.swv_height}")
        # mocked_root.device_params = mock.Mock()

        mocked_canvas = mock.Mock()
        self._cv_frame.device.get_and_display_data(mocked_canvas)
        args = device.process_data.call_args.args
        kwargs = device.process_data.call_args.kwargs
        self.assertEqual(args, ([0, 10, 5, 15, 10, 20, 15, 25, 20, 20, 15, 15, 10, 10, 5, 5, 0], ))
        self.assertEqual({'swv': True}, kwargs)
