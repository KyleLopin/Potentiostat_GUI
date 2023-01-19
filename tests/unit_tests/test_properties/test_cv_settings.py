# Copyright (c) 2023 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""
Test that the CVSettings class in the properties file works correctly
"""

__author__ = "Kyle Vitautas Lopin"

# standard libraries
import tkinter as tk
import unittest
from unittest import mock

# local files
import change_toplevel
import properties


class TestCVSettingChanges(unittest.TestCase):
    # @mock.patch('amp_gui.ElectroChemGUI')
    def setUp(self) -> None:
        self.gui = tk.Tk()
        self.gui.device_params = properties.DeviceParameters()
        self.top_level = change_toplevel.CVSettingChanges(None, self.gui, None, None)
        self.initial_state = self.gui.device_params.cv_settings.use_swv

    def test_load_correctly(self):
        print(f"test_load_correctly use_swv top_level: {self.top_level.use_swv.get()}")
        self.assertEqual(self.initial_state, self.top_level.use_swv.get())