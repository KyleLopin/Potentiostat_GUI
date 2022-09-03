# Copyright (c) 2020 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""

"""

__author__ = "Kyle Vitatus Lopin"

# standard libraries
import logging


def make_x_line(start, end, inc, sweep_type="CV", start_volt_type="Zero",
                swv_height=100, use_swv=False):
    # if type == ("Zero", "CV"):
    print('make x line, make_voltage_lines')
    print(sweep_type, start, end, inc, start_volt_type, swv_height)
    start = int(float(start) / inc) * inc  # fix any issues with the dac being 16 mV / step
    end = int(float(end) / inc) * inc  # always round towards 0 V

    if sweep_type == "CV" and start_volt_type == "Zero":
        # start = int(start/inc) * inc
        return make_x_line_zero_cv(start, end, inc, swv_height, use_swv)
    elif sweep_type == "LS":  # for linear sweep ignore what the user inputted for start_volt_type
        return make_x_line_linear(start, end, inc, swv_height, use_swv)
    elif sweep_type == "CV" and start_volt_type == "Start":
        return make_x_line_triangle(start, end, inc, swv_height, use_swv)
    else:
        logging.error("make x line got a bad type: {0}, {1}".format(sweep_type, start_volt_type))
        raise NotImplementedError


def make_x_line_linear(start: int, end: int, inc: int,
                       swv_height: int, use_swv: bool):
    """ Make the voltages to associate with the current data from a cyclic voltammetry experiments
    Makes a linear sweep that goes from start to end
    :param start:  starting voltage of the protocol
    :param end: last voltage of the protocol
    :param inc: voltage step size
    :param swv_height: voltage of the square wave voltage puslse, if used
    :param use_swv: flag if a square wave should be used
    :return: list of voltages
    """
    # start_mod = 0
    side_maker = make_side
    if use_swv:
        side_maker = make_swv_side
    returner = side_maker(start, end, inc, swv_height)
    # return range(start + start_mod, end + inc, inc)
    return returner


def make_x_line_zero_cv(start, end, inc, swv_height, use_swv):
    """ Make the voltages to associate with the current data from a cyclic voltammetry experiments
    This will start the protocol at 0 V, go to the start voltage, then the end voltage, and then to
    0 V
    TODO: make this less hackish
    :param start: first voltage the device goes to in the CV protocol
    :param end: second voltage the device goes to
    :param inc: the voltage step size the device makes
    :param swv_height: voltage of the square wave voltage puslse, if used
    :param use_swv: flag if a square wave should be used
    :return: list of the voltages to associate with the currents
    """
    side_maker = make_side
    if use_swv:
        side_maker = make_swv_side
    start = int(float(start / inc))
    end = int(float(end / inc))
    inc = int(inc)
    line = []
    line.extend(side_maker(0, start, 1, swv_height))
    line.extend(side_maker(line[-2], end, 1, swv_height))
    line.extend(side_maker(line[-2], 0, 1, swv_height))
    return [x * inc for x in line]


def make_x_line_triangle(start, end, inc, swv_height, use_swv):
    """ Make the voltage's that correspond to the currents measured
    :param start: voltage the cyclic voltammetry starts at
    :param end: voltage the cyclic voltammetry ends at
    :param inc: the voltage step size
    :param swv_height: voltage of the square wave voltage puslse, if used
    :param use_swv: flag if a square wave should be used
    :return: list of numbers
    """
    side_maker = make_side
    if use_swv:
        side_maker = make_swv_side

    start = int(start / inc)
    end = int(end / inc)
    inc = int(inc)
    line = []

    line.extend(side_maker(start, end, 1, swv_height))
    line.extend(side_maker(line[-2], start, 1, swv_height))
    return [x * inc for x in line]


def make_side(start, end, inc, *args):
    """ Helper function to make the voltages for the x-data in a CV experiments
    :param start: value to start at
    :param end: value to end
    :param inc: step size
    :return: list
    """
    lut = []
    if start < end:
        while start <= end:
            lut.append(start)
            start += inc
    else:
        while start >= end:
            lut.append(start)
            start -= inc
    print(f"returning lut: {lut}")
    return lut


def make_swv_side(start, end, inc, pulse_height):
    x = []
    if inc > 0:  # start low and go high
        if start > end:
            raise Exception("Increment is positive, but starting voltage is higher than the end voltage")
        x_current = start
        while x_current < end:
            x.append(x_current)
            x_current += pulse_height
            x.append(x_current)
            x.append(x_current)
            x_current -= (pulse_height - inc)
            x.append(x_current)
    print(f"returning swv line: {x}")
    return x
