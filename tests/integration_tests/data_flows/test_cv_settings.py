# Copyright (c) 2023 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""
Test how data flows for the cv settings, from the saved data file to the cv data structure
in the properties.py CVSettings class, CVSettingsDisplay in cv_frame.py and to the usb serial port
"""

__author__ = "Kyle Vitautas Lopin"

# standard libraries
import tkinter as tk
import unittest
from unittest import mock

# local files
import change_toplevel
import cv_frame
import graph_properties
import properties
import tkinter_pyplot


class TestCVSettingFlow(unittest.TestCase):
    @mock.patch('amp_gui.ElectroChemGUI')
    def setUp(self, mocked_gui) -> None:
        self.gui = tk.Tk()
        # self.gui = mocked_gui
        self.gui.frames = []
        self.gui.device = mock.Mock()
        for i in range(3):
            self.gui.frames.append(mock.Mock())
        self.gui.device_params = properties.DeviceParameters()
        print(dir(self.gui.device_params.cv_settings))
        # self.top_level = change_toplevel.CVSettingChanges(None, self.gui, None, None)
        self.initial_state = self.gui.device_params.cv_settings.use_swv

    def test_change_toplevel_settings(self) -> None:
        """
        Test that the value stored in the change_toplevel.CVSettingsChanges is correct
        """
        self.top_level = change_toplevel.CVSettingChanges(None, self.gui, None, None)
        print(f"test_load_correctly use_swv top_level: {self.top_level.use_swv.get()}")
        self.assertEqual(self.initial_state, self.top_level.use_swv.get())

    # def test_check_button(self):
    #     self.gui.mainloop()

    @mock.patch('tkinter_pyplot.PyplotEmbed')
    def test_cv_settiings(self, mock_graph) -> None:
        """
        Test that the CVSettingsDisplay class in cv_frame.CVFrame is correct
        """
        print(self.gui.device_params.cv_settings)
        graph_props = graph_properties.GraphProps()
        _cv_frame = cv_frame.CVFrame(self.gui, None, graph_props)
        cv_settings_display = cv_frame.CVFrame.CVSettingDisplay(self.gui, tk.Frame(),
                                                                mock.Mock(), mock.Mock(),
                                                                mock.Mock())
        print(cv_settings_display)
        print(cv_settings_display.use_swv_var_str.get())
        print(dir(cv_settings_display))
