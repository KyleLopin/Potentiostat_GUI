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


class TestCVFrameUSB(unittest.TestCase):
    def test_get_and_display_data(self):
        mocked_root = mock.Mock()
        mocked_root.frames = [mock.Mock()]
        graph_props = graph_properties.GraphProps()
        _cv_frame = cv_frame.CVFrame(mocked_root, None, graph_props)
