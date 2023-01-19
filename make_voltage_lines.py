# Copyright (c) 2022 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""
Make voltage profiles for electrochemical profiles.  Currently works for
Cyclic Voltammetry and Linear sweep.  Can start at the equilibrium voltage
or at 0 Volts and can impose a square wave over the profile.

Call make_voltage_profile, it will use the other functions to make the specified
voltage profile
"""

__author__ = "Kyle Vitatus Lopin"

# standard libraries
import logging
import unittest


def make_voltage_profile(start: int, end: int, increment: int,
                         sweep_type="CV", start_volt_type="Zero",
                         swv_height=None):
    """
    Make a voltage profile with the specified parameters.  This should be the
    only function called in this file.

    Args:
        start (int): voltage to start at, or first voltage to go to when starting at 0V
        end (int): voltage to go to at the end, or before going back to 0V
        increment (int): increment to change the voltage
        sweep_type (str): sweep type to preform, can be "CV" for cyclic voltammertry,
        or "LS" for a linear sweep
        start_volt_type (str): where to start a cyclic voltammetry experiment at, can
        be "Start" to use the start voltage in the beginning or "Zero" to start at 0 V
        swv_height (int): height of the pulse to use for square wave voltammetry (swv),
        if None or 0, no swv pulses will be used
        TODO: this swv_height way of controlling the swv waveform needs fixing

    Returns (list): list of the voltages for the specified parameters

    """
    if sweep_type == "CV" and start_volt_type == "Zero":
        return make_x_line_zero_cv(start, end, increment, swv_height)
    if sweep_type == "LS":  # for linear sweep ignore what the user inputted for start_volt_type
        return make_x_line_linear(start, end, increment, swv_height)
    if sweep_type == "CV" and start_volt_type == "Start":
        return make_x_line_triangle(start, end, increment, swv_height)
    logging.error(f"make x line got a bad type: {sweep_type}, {start_volt_type}")
    raise NotImplementedError


def make_x_line_linear(start: int, end: int, inc: int,
                       swv_height: int) -> list:
    """
    Make the voltages to associate with the current data for a
    linear sweep that goes from start to end
    Args:
        start (int): starting voltage of the protocol
        end (int): last voltage of the protocol
        inc (int): voltage step size
        swv_height: voltage of the square wave voltage pulse, if 0 or None, not used

    Returns: list of voltages

    """
    side_maker = _make_side
    if swv_height:
        side_maker = _make_swv_side
    return side_maker(start, end, inc, swv_height)


def make_x_line_zero_cv(start, end, inc, swv_height):
    """
    Make a cyclic voltammetry voltage profle that starts 0 V, go to the
    start voltage, then the end voltage, and then to 0 V
    Args:
        start (int): first voltage the device goes to in the CV protocol
        end (int): second voltage the device goes to
        inc (int): the voltage step size
        swv_height: voltage of the square wave voltage pulse, if 0 or None, not used

    Returns: list of voltages

    """
    side_maker = _make_side
    if swv_height:
        side_maker = _make_swv_side
    _line = []
    _line.extend(side_maker(0, start, inc, swv_height))
    next_start = _line[-2]
    if swv_height:  # if a swv, the next start has to be modified
        next_start = _line[-5] + int(swv_height / 2)
    _line.extend(side_maker(next_start, end, inc, swv_height))
    next_start = _line[-2]
    if swv_height:  # if a swv, the next start has to be modified
        next_start = _line[-5] + int(swv_height / 2)
    _line.extend(side_maker(next_start, 0, inc, swv_height))
    return _line


def make_x_line_triangle(start, end, inc, swv_height):
    """
    Make a voltage profile that goes from the start voltage to the end voltage
    and then back to the start voltage again for a cyclic voltammetry (CV) experiment.
    If swv_height is set, a square wave will be superimposed on the CV profile
    Args:
        start (int): voltage the cyclic voltammetry starts and ends at
        end (int): voltage the cyclic voltammetry goes to in the
        middle of the experiment
        inc (int): voltage step of the protocol
        swv_height:  voltage of the square wave voltage pulse, if 0 or None, not used

    Returns:  list of voltages for the cyclic / square wave voltammetry experiment

    """
    side_maker = _make_side
    if swv_height:
        side_maker = _make_swv_side
    _line = []
    _line.extend(side_maker(start, end, inc, swv_height))
    # use line[-2] because line[-1] is the peak, so start on the next on
    # eg. [..., 58, 59, 60]; 60 is the peak so the next voltage should be 59 not 60
    next_start = _line[-2]
    if swv_height:  # if a swv, the next start has to be modified
        next_start = _line[-5] + int(swv_height / 2)
    _line.extend(side_maker(next_start, start, inc, swv_height))
    return _line


def _make_side(start, end, increment, *args):
    """
    Helper function to make the voltages for the voltage axis (x)
    for cyclic voltammetry and linear sweep experiments.
    Increment does not have to be negative.
    Args:
        start (int):  value to start at
        end (int):  value to end
        increment (int):  step size
        *args:  used to keep this and _make_swv_side interchangeable, should not be used

    Returns: list of voltages from start to end in increment steps

    """
    increment = abs(increment)
    lut = []
    if start < end:
        while start <= end:
            lut.append(start)
            start += increment
    else:
        while start >= end:
            lut.append(start)
            start -= increment
    return lut


def _make_swv_side(start, end, increment, pulse_height):
    """
    Helper function to make the voltages for the voltage axis (x)
    for cyclic voltammetry and linear sweep experiments with a square wave pulse
    superimposed.  Increment does not have to be negative.
    Args:
        start (int):  value to start at
        end (int):  value to end
        increment (int):  step size
        pulse_height (int):  height of square wave

    Returns:list of voltages from start to end in increment steps
    with a square wave superimposed

    """
    increment = abs(increment)
    lut = []
    half_pulse = int(pulse_height / 2)
    if start <= end:
        while start <= end:
            lut.extend(2 * [(start + half_pulse)])
            lut.extend(2 * [(start - half_pulse)])
            start += increment
    elif start > end:
        while start >= end:
            lut.extend(2 * [(start + half_pulse)])
            lut.extend(2 * [(start - half_pulse)])
            start -= increment
    # print(f"returning swv line: {lut}")
    return lut


def check_inc_corrrect(start: int, end: int, increment: int) -> int:
    """
    #TODO: remove this cleanly
    Check that the sign of the increment is correct to go from start voltage
    to end voltage and not go on forever
    Args:
        start (int):  voltage the line will start with
        end (int):  voltage the line will end with
        increment (int):  voltage step to go from start to end

    Returns (int):  the increment variable with the proper sign to go from start to end

    """
    if 1 >= increment >= -1:
        raise Exception(f"Increment can not be less than 1, increment is {increment}")
    if increment >= 1 and start > end:  # start low and go high
        return -increment  # switch increment sign
    if increment <= 1 and end > start:  # start high and go low
        return -increment  # switch increment sign
    # else increment is ok without changing
    return increment


class TestProfiles(unittest.TestCase):
    """
    Test if the voltage profiles are being made correctly
    TODO: move this to testing folder and files
    """
    def test_make_swv_side1(self):
        """
        Test if going from 0 to -50 in increments of 20 and a swv height of 50 works
        """
        line = _make_swv_side(0, -60, 20, 50)
        correct_line = [25, 25, -25, -25, 5, 5, -45, -45, -15,
                        -15, -65, -65, -35, -35, -85, -85]
        self.assertListEqual(line, correct_line,
                             msg="_make_swv_line not returning the correct list "
                                 "going from 0 to -50")

    def test_make_swv_side2(self):
        """
        Test if going from -60 to 40 in increments of 20 and a swv height of 50 works
        """
        line = _make_swv_side(-60, 40, 20, 50)
        correct_line = [-35, -35, -85, -85, -15, -15, -65, -65, 5, 5, -45,
                        -45, 25, 25, -25, -25, 45, 45, -5, -5, 65, 65, 15, 15]
        self.assertListEqual(line, correct_line,
                             msg=f"_make_swv_line not returning correct list for"
                                 "going from 60 to 40 in 20 increments")

    def test_make_side_1(self):
        """
        Test if going from -60 to 40 in increments of 20 and a swv height of 50 works
        """
        line = _make_side(-60, 40, 20)
        correct_line = [-60, -40, -20, 0, 20, 40]
        self.assertListEqual(line, correct_line,
                             msg=f"_make_line not returning correct list for"
                                 "going from -60 to 40 in 20 increments")

    def test_make_side_2(self):
        """
        Test if going from 60 to -100 in increments of 20 and a swv height of 50 works
        """
        line = _make_side(60, -100, 20)
        correct_line = [60, 40, 20, 0, -20, -40, -60, -80, -100]
        self.assertListEqual(line, correct_line,
                             msg=f"_make_line not returning correct list for"
                                 "going from 60 to -100 in 20 increments")

    def test_make_cv_1(self):
        """ Test if cyclic voltammetry profile is correct """
        line = make_voltage_profile(-60, 20, 20, sweep_type="CV",
                                    start_volt_type="Start")
        correct_line = [-60, -40, -20, 0, 20, 0, -20, -40, -60]
        self.assertListEqual(line, correct_line,
                             msg=f"CV profile not correct going "
                                 f"from 60 to -60 in 20 increments")

    def test_make_cv_2(self):
        """ Test if cyclic voltammetry profile is correct """
        line = make_voltage_profile(20, -60, 20, sweep_type="CV",
                                    start_volt_type="Start")
        correct_line = [20, 0, -20, -40, -60, -40, -20, 0, 20]
        self.assertListEqual(line, correct_line,
                             msg=f"CV profile not correct going "
                                 f"from 60 to -60 in 20 increments")

    def test_make_cv_zero_1(self):
        """ Test if cyclic voltammetry profile is correct starting at 0 V """
        line = make_voltage_profile(-60, 20, 20, sweep_type="CV",
                                    start_volt_type="Zero")
        correct_line = [0, -20, -40, -60, -40, -20, 0, 20, 0]
        self.assertListEqual(line, correct_line,
                             msg=f"CV profile starting at 0 V is not correct going "
                                 f"from 60 to -60 in 20 increments")

    def test_make_cv_zero_2(self):
        """ Test if cyclic voltammetry profile is correct starting at 0 V """
        line = make_voltage_profile(40, -60, 20, sweep_type="CV",
                                    start_volt_type="Zero")
        correct_line = [0, 20, 40, 20, 0, -20, -40, -60, -40, -20, 0]
        self.assertListEqual(line, correct_line,
                             msg=f"CV profile starting at 0 V not correct going "
                                 f"from 60 to -60 in 20 increments")

    def test_make_ls_1(self):
        """ Test if linear sweep profile is correct """
        line = make_voltage_profile(-60, 20, 10, sweep_type="LS",
                                    start_volt_type="Start")
        correct_line = [-60, -50, -40, -30, -20, -10, 0, 10, 20]
        self.assertListEqual(line, correct_line,
                             msg=f"LS profile not correct going "
                                 f"from 60 to -60 in 10 increments")

    def test_make_ls_2(self):
        """ Test if linear sweep profile is correct """
        line = make_voltage_profile(20, -60, 10, sweep_type="LS",
                                    start_volt_type="Zero")
        correct_line = [20, 10, 0, -10, -20, -30, -40, -50, -60]
        self.assertListEqual(line, correct_line,
                             msg=f"LS profile not correct going "
                                 f"from 60 to -60 in 10 increments")

    def test_make_cv_swv_1(self):
        """ Test if cyclic voltammetry with a square wave profile is correct """
        line = make_voltage_profile(-60, 20, 20, sweep_type="CV",
                                    start_volt_type="Start", swv_height=50)
        correct_line = [-35, -35, -85, -85, -15, -15, -65, -65, 5, 5, -45, -45,
                        25, 25, -25, -25, 45, 45, -5, -5, 25, 25, -25, -25, 5, 5,
                        -45, -45, -15, -15, -65, -65, -35, -35, -85, -85]
        self.assertListEqual(line, correct_line,
                             msg=f"CV profile with square wave pulses not "
                                 f"correct going from 60 to -60 in 20 increments")

    def test_make_cv_swv_2(self):
        """ Test if cyclic voltammetry with a square wave profile is correct """
        line = make_voltage_profile(20, -60, 20, sweep_type="CV",
                                    start_volt_type="Start", swv_height=50)
        correct_line = [45, 45, -5, -5, 25, 25, -25, -25, 5, 5, -45, -45, -15,
                        -15, -65, -65, -35, -35, -85, -85, -15, -15, -65, -65,
                        5, 5, -45, -45, 25, 25, -25, -25, 45, 45, -5, -5]
        self.assertListEqual(line, correct_line,
                             msg=f"CV profile with square wave pulses not "
                                 f"correct going from 60 to -60 in 20 increments")

    def test_make_cv_zero_swv_1(self):
        """ Test if cyclic voltammetry with a square wave profile
        is correct starting at 0 V """
        line = make_voltage_profile(-60, 20, 20, sweep_type="CV",
                                    start_volt_type="Zero", swv_height=50)
        correct_line = [25, 25, -25, -25, 5, 5, -45, -45, -15, -15, -65, -65,
                        -35, -35, -85, -85, -15, -15, -65, -65, 5, 5, -45, -45,
                        25, 25, -25, -25, 45, 45, -5, -5, 25, 25, -25, -25]

        self.assertListEqual(line, correct_line,
                             msg=f"CV profile starting at 0 V is not correct going "
                                 f"from 60 to -60 in 20 increments with swv")

    def test_make_cv_zero_swv_2(self):
        """ Test if cyclic voltammetry with a square wave profile
        is correct starting at 0 V """
        line = make_voltage_profile(40, -60, 20, sweep_type="CV",
                                    start_volt_type="Zero", swv_height=50)
        correct_line = [25, 25, -25, -25, 45, 45, -5, -5, 65, 65, 15, 15, 45, 45, -5, -5,
                        25, 25, -25, -25, 5, 5, -45, -45, -15, -15, -65, -65, -35, -35,
                        -85, -85, -15, -15, -65, -65, 5, 5, -45, -45, 25, 25, -25, -25]
        self.assertListEqual(line, correct_line,
                             msg=f"CV profile starting at 0 V not correct going "
                                 f"from 60 to -60 in 20 increments with swv")

    def test_make_ls_swv_1(self):
        """ Test if linear sweep profile is correct """
        line = make_voltage_profile(-60, 20, 20, sweep_type="LS",
                                    start_volt_type="Start", swv_height=50)
        correct_line = [-35, -35, -85, -85, -15, -15, -65, -65, 5, 5, -45, -45,
                        25, 25, -25, -25, 45, 45, -5, -5]
        self.assertListEqual(line, correct_line,
                             msg=f"LS profile not correct going "
                                 f"from 60 to -60 in 10 increments with swv")

    def test_make_ls_swv_2(self):
        """ Test if linear sweep profile is correct """
        line = make_voltage_profile(20, -60, 20, sweep_type="LS",
                                    start_volt_type="Zero", swv_height=50)
        correct_line = [45, 45, -5, -5, 25, 25, -25, -25, 5, 5, -45, -45, -15,
                        -15, -65, -65, -35, -35, -85, -85]
        self.assertListEqual(line, correct_line,
                             msg=f"LS profile not correct going "
                                 f"from 60 to -60 in 10 increments with swv")


if __name__ == "__main__":
    unittest.main()
