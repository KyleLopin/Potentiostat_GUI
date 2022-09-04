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


    Returns (list): list of the voltages for the specified parameters

    """
    print('make x line, make_voltage_lines')
    print(sweep_type, start, end, increment, start_volt_type, swv_height)
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
    _line.extend(side_maker(_line[-2], end, inc, swv_height))
    _line.extend(side_maker(_line[-2], 0, inc, swv_height))
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
    _line.extend(side_maker(_line[-1], start, inc, swv_height))
    return _line


def _make_side(start, end, increment, *args):
    """
    Helper function to make the voltages for the voltage axis (x)
    for cyclic voltammetry and linear sweep experiments.  Will autocorrect
    and error in the increment sign.
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
    print(f"returning lut: {lut}")
    return lut


def _make_swv_side(start, end, inc, pulse_height):
    inc = abs(inc)
    lut = []
    print(f"making swv side with start: {start}, end: {end}, increment: {inc}")
    half_pulse = int(pulse_height / 2)
    if start < end:
        while start <= end:
            lut.extend(2 * [(start + half_pulse)])
            lut.extend(2 * [(start - half_pulse)])
            start += inc
    elif start > end:
        while start >= end:
            lut.extend(2 * [(start + half_pulse)])
            lut.extend(2 * [(start - half_pulse)])
            start -= inc
    print(f"returning swv line: {lut}")
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

    """

    # TODO: put this in the correct place later
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
        line = _make_swv_side(-60, 40, 20, 50)
        correct_line = [-35, -35, -85, -85, -15, -15, -65, -65, 5, 5, -45,
                        -45, 25, 25, -25, -25, 45, 45, -5, -5, 65, 65, 15, 15]
        self.assertListEqual(line, correct_line,
                             msg=f"_make_swv_line not returning correct list for"
                                 "going from 60 to 40 in 20 increments")


if __name__ == "__main__":
    unittest.main()
