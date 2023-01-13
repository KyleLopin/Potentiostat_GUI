# Copyright (c) 2022 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""
Unit test the functions of the SerialComm class in usb_comm.py
"""

__author__ = "Kyle Vitautas Lopin"

# standard libraries
import os
import unittest
from unittest import mock

# local files
import usb_comm

mock_data1 = b'\xc8\x00d\x00\x00\x00d\x00\xc8\x00\xd5\x01\xea\x00\xfb\xff\x0b\xff \xfe'

class TestSerialComm(unittest.TestCase):
    @mock.patch('usb_comm.SerialComm.auto_find_com_port_windows')
    @mock.patch('usb_comm.SerialComm.auto_find_com_port_mac')
    def setUp(self, mock_serial_win, mock_serial_mac) -> None:
        if os.name == 'nt':
            self.mock_serial = mock_serial_mac
        elif os.name == 'posix':
            self.mock_serial = mock_serial_win
        self.serial_comm = usb_comm.SerialComm()

    @mock.patch('serial.Serial')
    def test_read_data(self, mock_serial):
        self.mock_serial.return_value.read.return_value = mock_data1
        data = self.serial_comm.read_data(20, 'int16')
        print(f"data: {data}")
        self.assertListEqual(data, [200, 100, 0, 100, 200, 469, 234, -5, -245, -480])
