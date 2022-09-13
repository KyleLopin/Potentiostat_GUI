# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" Graphical user interface to control PSoC electrochemical device main file
"""

from __future__ import division

import logging

import globals as _globals

__author__ = 'Kyle Vitautas Lopin'

ADC_VREF = _globals.ADC_VREF  # mV
ADC_BITS = _globals.ADC_BITS
PWM_FREQ = _globals.PWM_FREQ
VIRTUAL_GROUND = _globals.VIRTUAL_GROUND

DEFAULT_CV_SETTINGS = {'start_dac_value': 159, 'start_voltage': -900, 'end_voltage': 900,
                       'sweep_start_type': 'Start', 'end_dac_value': 78,
                       'sweep_type': 'CV', 'sweep_rate': 0.2,
                       'delay_time': 1400.0, 'pwm_period_value': 3840,
                       'swv_height': 100, 'swv_inc': 5, 'swv_period': 100,
                       'use_swv': False}
# 'low_voltage': 200, 'high_voltage': 900,
SWEEP_TYPE_OPTIONS = ['CV', 'LS']
SWEEP_START_TYPE_OPTIONS = ['Start', 'Zero']

START_VOLTAGE_CV = -900.
END_VOLTAGE_CV = 900.
SWEEP_RATE = 0.5

# Amperometry properties
DEVICE_SAMPLING_RATE = 1000
DOWN_SAMPLING = 50

# Anode stripping voltammetry properties
CLEAN_VOLTAGE_ASV = 800  # mV
CLEAN_TIME = 2  # seconds
PLATING_VOLTAGE = -1500  # mV
PLATING_TIME = 5  # seconds
END_ASV_VOLTAGE = 500  # mV
# DPV in ASV
PULSE_HEIGHT = 100  # mV
PULSE_INCREMENT = 10  # mV
PULSE_WIDTH = 20  # msec

SAVED_SETTINGS_FILE = "settings.txt"


class DeviceParameters(object):
    """ Class to hold all the properties and parameters of the PSoC amperometry device
    """

    def __init__(self):
        # constant parameters
        self.number_in_endpoints = 1  # how many IN ENDPOINTS to connect to
        self.number_out_endpoints = 1  # how many OUT ENDPOINTS to connect to

        # frequency of the clock that is driving the PWM that triggers isr
        self.clk_freq_isr_pwm = PWM_FREQ
        self.virtual_ground_shift = VIRTUAL_GROUND  # mv shift in ground the device uses

        # create instances for all the important components of the device
        self.dac = DAC("8-bit DAC", voltage_range=4080)
        self.adc_tia = ADC_TIA()
        self.cv_settings = CVSettings(self.dac)
        self.amp_settings = AmpSettings(self.clk_freq_isr_pwm, self.dac)
        self.asv_settings = ASVSettings(self.clk_freq_isr_pwm, self.dac)

        # variable parameters
        self.pwm_period_value = self.calculate_pwm_period()
        self.pwm_compare = int(self.pwm_period_value / 2)

        self.usb_count = 0  # this will be set when getting data from the device
        self.user_sets_labels_after_run = True  # should be moved
        self.last_run = 'cv'  # keep track of what the device is programmed for

    def calculate_pwm_period(self):
        """ Take the clock frequency that is driving the PWM and divide it by the number of voltage
        steps per second: this is how many clk ticks between each interrupt """
        voltage_step_size = self.dac.voltage_step_size
        pwm_period_value = int(round(self.clk_freq_isr_pwm /
                                     (self.cv_settings.sweep_rate * 1000 / voltage_step_size)))
        return pwm_period_value

    def set_dac(self, _type):
        """ Set the type of dac to use
        :param _type: "VDAC" or "DVDAC", string of the type of dac used
        :return:
        """
        _voltage_range = self.dac.range
        self.dac = DAC(_type, _voltage_range)


class CVSettings(object):
    """ Class to hold the important parameters for running a cyclic voltammetry scan
    """

    def __init__(self, dac):
        """
        :param dac: DAC instance
        """
        # try to open settings file
        try:
            with open("settings.txt", 'r') as _file:
                for line in _file.readlines():
                    # print(line)
                    attribute, value = line.split('=')
                    attribute = attribute.strip(' ')
                    value = value.strip()
                    # convert the string read from the file to the proper data type
                    valid_value = self.check_valid_value(attribute, value)
                    if valid_value:
                        setattr(self, attribute, valid_value)

        except Exception as e:
            logging.debug("Load error: ", e)
            # with open("settings.txt", "w") as _file:
            #     pass  # make the file if it is not there
        for key in DEFAULT_CV_SETTINGS:
            if not hasattr(self, key):
                setattr(self, key, DEFAULT_CV_SETTINGS[key])

        self.delay_time = 2 * abs(self.start_voltage - self.end_voltage) / self.sweep_rate
        self.low_voltage = min([self.start_voltage, self.end_voltage])
        self.high_voltage = max([self.start_voltage, self.end_voltage])
        self.start_dac_value = None  # init holder
        self.end_dac_value = None  # init holder
        self.calc_dac_values(dac)

    @staticmethod
    def check_valid_value(attribute, value):
        """ Check if value entered is valid for the attribute it wants to be assigned to.
        Cross-reference the DEFAULT_CV_SETTINGS dict to make sure types are consistent
        :param attribute: str - class attribute to assign a value to
        :param value: str - value to convert to the proper type and assign to the attribute
        :return: properly typed value or False if the data type couldn't be converted
        """
        if attribute in DEFAULT_CV_SETTINGS:
            # YOU HAVE TO CHECK BOOL FIRST, THEY ARE ALSO INTS
            if isinstance(DEFAULT_CV_SETTINGS[attribute], bool):
                try:
                    return bool(value)
                except:
                    return False

            elif isinstance(DEFAULT_CV_SETTINGS[attribute], int):
                # try to convert the string to int
                try:
                    return int(value)
                except:
                    return False
            elif isinstance(DEFAULT_CV_SETTINGS[attribute], float):
                try:
                    return float(value)
                except:
                    return False

            elif attribute == 'sweep_start_type':
                if value in SWEEP_START_TYPE_OPTIONS:
                    return value
                else:
                    return False
            elif attribute == 'sweep_type':
                if value in SWEEP_TYPE_OPTIONS:
                    return value
                else:
                    return False
        else:
            return False

    def calc_dac_values(self, dac):
        """ TODO: Depreated??
        :param dac:
        :return:
        """
        self.start_dac_value = dac.get_dac_count(self.start_voltage, shift=True)
        self.end_dac_value = dac.get_dac_count(self.end_voltage, shift=True)

    def calculate_pwm_period(self, clk_freq, dac):
        """ Take the clock frequency that is driving the PWM and divide it by the number of voltage
        steps per second: this is how many clk ticks between each interrupt
        :param clk_freq: int, the clock frequency feeding the PWM timer
        :param dac: instance of a DAC that has the voltage step size
        """
        pwm_period_value = int(round(clk_freq / (self.sweep_rate * 1000 / dac.voltage_step_size)))
        return pwm_period_value

    def update_settings(self, start_voltage, end_voltage,
                        sweep_rate,  sweep_type, start_type,
                        swv_height, swv_inc, swv_period,
                        use_swv):
        """ Update the CV settings
        :param start_voltage: mV, voltage the user wants to start at
        :param end_voltage: mV, voltage the user wants to end the cyclic voltammetry at
        :param sweep_rate: V/s, rate of change of the cyclic voltammetry
        """
        self.start_voltage = start_voltage
        self.end_voltage = end_voltage
        self.low_voltage = min([self.start_voltage, self.end_voltage])  # not dry, in init
        self.high_voltage = max([self.start_voltage, self.end_voltage])
        self.sweep_rate = sweep_rate
        self.delay_time = 2 * abs(self.start_voltage - self.end_voltage) / self.sweep_rate
        self.sweep_type = sweep_type
        self.sweep_start_type = start_type
        self.swv_height = swv_height
        self.swv_inc = swv_inc
        self.swv_period = swv_period
        self.use_swv = use_swv

        try:
            with open(SAVED_SETTINGS_FILE, 'r') as _file:
                old_file = _file.read()

        except Exception as e:
            logging.debug("exception in loading settings file: {0}".format(e))
            pass  # there is no file so skip

        try:
            print(vars(self))
            with open(SAVED_SETTINGS_FILE, 'w') as _file:
                for item in vars(self):
                    _file.write("{0} = {1}\n".format(item, eval("self.{0}".format(item))))

        except Exception as e:
            logging.debug("exception in loading settings file: {0}".format(e))
            pass  # there is no file so skip


class AmpSettings(object):
    """ Class to hold the important parameters for running an amperometry experiment
    Note: this interacts with CVSettings to keep the sample rate / sweep rate connected
    """
    def __init__(self, clock_freq, dac):
        self.voltage = 500  # mV, start with basic parameters
        self.raw_sampling_rate = DEVICE_SAMPLING_RATE  # Hz
        self.down_sample = DOWN_SAMPLING
        self.sampling_rate = self.raw_sampling_rate
        self.pwm_period_value = self.calculate_pwm_period(clock_freq)

    def calculate_pwm_period(self, clk_freq):
        """ Calculate the PWM period needed to achieve the desired sampling rate
        :param clk_freq: clock frequency feeding the timing PWM
        :return: int, to send to pwm to put as its period
        """
        pwm_period_value = int(round(clk_freq / self.sampling_rate))
        return pwm_period_value

    def update_settings(self, voltage, rate):
        """ Update the amperometry settings
        :param voltage: new voltage to set the device at
        :param rate: new sampling rate (in kHz) to set the sample
        """
        self.voltage = voltage
        self.sampling_rate = rate


class ASVSettings(CVSettings):
    def __init__(self, clock_freq, dac):
        CVSettings.__init__(self, dac)
        self.sweep_type = "LS"
        self.clean_volt = CLEAN_VOLTAGE_ASV
        self.clean_time = CLEAN_TIME
        self.plate_volt = PLATING_VOLTAGE
        self.plate_time = PLATING_TIME
        self.end_voltage = END_ASV_VOLTAGE
        self.low_voltage = self.plate_volt
        self.high_voltage = self.end_voltage
        self.sweep_rate = SWEEP_RATE
        self.delay_time = 500 + abs(self.end_voltage -
                                    self.plate_volt) / self.sweep_rate
        self.pulse_height = PULSE_HEIGHT
        self.pulse_inc = PULSE_INCREMENT
        self.pulse_width = PULSE_WIDTH

    def update_settings(self, clean_voltage, clean_time, electroplate_voltage,
                        plating_time, end_voltage, sweep_rate, sweep_type=0,
                        pulse_height=50, pulse_inc=10, pulse_width=100):
        """ Update the CV settings
        :param clean_voltage: int - mV, voltage to hold the working electrode at to remove plated ions
        :param clean_time: int - seconds, time to use the cleaning voltage
        :param electroplate_voltage: int - mV, voltage to hold the working electrode
        at to have the metal ions plate onto the electrode
        :param plating_time: int - seconds, time to hold the electrode at the plating potential
        :param end_voltage: int - mV, voltage the user wants to end the cyclic voltammetry at
        :param sweep_rate: float - V/s, rate of change of the cyclic voltammetry
        """
        self.clean_volt = clean_voltage
        self.clean_time = clean_time
        self.plate_volt = electroplate_voltage
        self.plate_time = plating_time
        self.end_voltage = end_voltage
        self.low_voltage = self.plate_volt
        self.high_voltage = self.end_voltage
        self.sweep_rate = sweep_rate
        self.delay_time = 500 + abs(self.high_voltage - self.low_voltage) / self.sweep_rate

        self.pulse_height = pulse_height
        self.pulse_inc = pulse_inc
        self.pulse_width = pulse_width

        if sweep_type == 1:
            self.sweep_type = "DPV"
            self.delay_time = (500 + self.pulse_width * abs(self.high_voltage - self.low_voltage)
                               / self.pulse_inc)
        else:
            self.sweep_type = "LS"


class DAC(object):
    """ Class that provides the information of the DAC being used
    """

    def __init__(self, _type, voltage_range=4080.0):
        self.source = _type
        if _type == "8-bit DAC":
            self.bits = 8  # bits of resolution
            self.voltage_step_size = 16

        elif _type == "DVDAC":
            self.bits = 12  # bits of resolution
            self.voltage_step_size = 1

        # (mV) the full voltage step the DAC can take, NOTE: is programmable
        self.range = voltage_range
        self.virtual_ground = VIRTUAL_GROUND

    def set_bits(self):
        """ Set the number of bits of the DAC """
        if self.source == "8-bit DAC":
            self.bits = 8  # bits of resolution
        elif self.source == "DVDAC":
            self.bits = 12  # bits of resolution

    def set_step_size(self):
        """ Calculate the step size (in mV) the dac will take
        :return:  voltage step, i.e. the amount the DAC changes for an 1 bit increase in digital
        code
        """
        if self.source == "8-bit DAC":
            return 16

        elif self.source == "DVDAC":
            return 1
        return  # self.range / ((2**self.bits)-1)

    def get_dac_count(self, _input_voltage, shift=False, actual=False):
        """ Get the digital value the dac needs to product the input voltage
        :param _input_voltage: float of the desired voltage
        :param shift: True / False - should the program shift the voltage to take account of the
        virtual ground
        :return: int of the digital value that should be inputted  """
        if actual:
            return int(round(-_input_voltage + self.virtual_ground) / self.voltage_step_size)

        if shift:
            return int(round((_input_voltage + self.virtual_ground) / self.voltage_step_size))
        else:
            return int(round(_input_voltage / self.voltage_step_size))

    def set_source(self, _source):
        """ Set the source of the voltage sources, either 8-bit VDAC of dithering VDAC
        :param _source: string of either "VDAC" or "DVDAC" for which source to set the DAC to
        """
        if _source == self.source:
            return  # want to set to what it is already set to
        self.source = _source
        self.set_bits()
        self.voltage_step_size = self.set_step_size()


class ADC_TIA(object):
    """ Class to represent the ADC and TIA current sensing block
    """

    def __init__(self, adc_config=1, tia_resistor=20, adc_gain=1, bits=ADC_BITS):
        # config 1 sets the Vref to +-2.048 V and config 2 sets the Vref to +-1.024 V
        self.current_options = _globals.CURRENT_LIMIT_VALUES
        self.current_option_index = 0
        self.adc_config = adc_config
        if self.adc_config == 1:
            self.adc_vref = 4096  # mV, +-2.048 V
        elif self.adc_config == 2:
            self.adc_vref = 2048  # mV, +-1.024 V
        else:
            raise NotImplementedError
        self.tia_resistor = tia_resistor  # kilohms, value of resistor across the TIA opamp
        self.adc_gain = adc_gain
        if adc_gain == 1:
            self.range_index = tia_resistor  # what current range choice to set
        else:
            self.range_index = tia_resistor + adc_gain / 2
        self.bits = bits
        self.counts_to_current = self.calc_counts_to_current_ua()
        self.shift = 0
        self.adc_channel = 0  # the PSoC has different adc channels that can be read
        self.current_lims = self.current_options[self.current_option_index]

    def calc_current_lims(self):
        max_voltage = self.adc_config / 2.0
        max_current = max_voltage / float(self.tia_resistor)
        return max_current

    def calc_counts_to_current_ua(self):
        """ Calculate the number that you multiple the ADC count by to get the current in micro amps
        :return: float that is uA / count
        """
        # what to multiply adc counts by to get voltage in mV
        counts_to_volts = float(ADC_VREF) / (2 ** self.bits)
        volts_to_current = 1.0 / self.tia_resistor
        return counts_to_volts * volts_to_current

    def set_value(self, new_tia_value, new_adc_gain_value, new_adc_config, current_range_index):
        """ The TIA or ADC have changed so update the values
        :param new_tia_value: int - new tia resistor value
        :param new_adc_gain_value: int - new buffer gain for the adc
        :param new_adc_config: int - new adc configuration selected
        :param current_range_index: int - index of the current range from the global.py CURRENT_OPTION_LIST
        """
        self.tia_resistor = new_tia_value
        self.adc_gain = new_adc_gain_value

        self.adc_config = new_adc_config
        self.range_index = current_range_index  # what current range choice to set

        self.counts_to_current = self.calc_counts_to_current_ua()
        # self.current_lims = self.calc_current_lims()
        self.current_option_index = current_range_index
        self.current_lims = self.current_options[self.current_option_index]

    def calibrate(self, data):
        """ Calibrate the TIA ADC with the onboard IDAC and calculate the adc shift gain functions
        :param data: list of ints from the device, the first 5 are IDAC values that
        were tested and the next 5 are the ADC values from those currents.  To get current
        from the IDAC values multiply by 1/8 uA per bit
        :return: set the shift and counts_to_current attributes
        """
        self.shift = data[7]
        lower_count_to_current = (data[0] / 8.0) / (data[5] - data[7])
        upper_count_to_current = (data[4] / 8.0) / (data[7] - data[9])
        self.counts_to_current = (float(lower_count_to_current) + float(
            upper_count_to_current)) / 2.0
        logging.info('adc calibrate, counts to current: {0}'.format(self.counts_to_current))
