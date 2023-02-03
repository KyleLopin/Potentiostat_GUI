# Copyright (c) 2023 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""
Unit test methods of the usb_comm.AmpUSB class
"""

__author__ = "Kyle Vitautas Lopin"


# standard libraries
import unittest
from unittest import mock

# local files

import graph_properties
import properties
import usb_comm


class TestAmpUSB(unittest.TestCase):
    def test_process_data(self):
        mocked_root = mock.Mock()
        mocked_root.data_save_type = "Converted"
        device_params = properties.DeviceParameters()
        device_params.adc_tia.shift = 0
        device_params.adc_tia.counts_to_current = 0.05
        usb = usb_comm.AmpUsb(mocked_root, device_params)
        _input = [5, 0, 10, 5, 15, 10, 20, 15, 25, 20,
                  20, 15, 15, 10, 10, 5, 5, 0]
        output = usb.process_data(_input, swv=True)
        correct_output = [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]
        self.assertListEqual(output, correct_output)
