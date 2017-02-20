# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" Graphical user interface to control PSoC electrochemical device main file
"""

from __future__ import division

__author__ = 'Kyle Vitautas Lopin'

ADC_VREF = 2048  # mV
ADC_BITS = 12
PWM_FREQ = 2400000.
VIRTUAL_GROUND = 2048.


class DeviceParameters(object):
    """
    class to hold all the properties and parameters of the PSoC amperometry device
    """

    def __init__(self):
        # constant parameters
        self.number_in_endpoints = 1  # how many IN ENDPOINTS to connect to
        self.number_out_endpoints = 1  # how many IN ENDPOINTS to connect to

        # frequency of the clock that is driving the PWM that triggers isr
        self.clk_freq_isr_pwm = PWM_FREQ
        self.virtual_ground_shift = VIRTUAL_GROUND  # mv shift in ground the device uses

        # create instances for all the important components of the device
        self.dac = DAC("8-bit DAC", voltage_range=4080)
        self.cv_settings = CVSettings(self.clk_freq_isr_pwm, self.dac)
        self.amp_settings = AmpSettings(self.clk_freq_isr_pwm, self.dac)

        # variable parameters
        self.pwm_period_value = self.calculate_pwm_period()
        self.pwm_compare = int(self.pwm_period_value / 2)
        self.adc_tia = ADC_TIA()
        # self.adc_channel = 0  # the PSoC has different adc channels that can be read
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

    def __init__(self, clock_freq, dac):
        """
        :param clock_freq: frequency that the DAC is change the voltage
        :param dac: DAC instance
        :return:
        """
        self.low_voltage = -500.  # mV, start with basic parameters
        self.high_voltage = 500.  # mV
        self.sweep_rate = 1.0  # V/s
        self.pwm_period_value = self.calculate_pwm_period(clock_freq, dac)
        self.delay_time = 2 * (self.high_voltage - self.low_voltage) / self.sweep_rate

    def calculate_pwm_period(self, clk_freq, dac):
        """ Take the clock frequency that is driving the PWM and divide it by the number of voltage
        steps per second: this is how many clk ticks between each interrupt
        :param clk_freq: int, the clock frequency feeding the PWM timer
        :param dac: instance of a DAC that has the voltage step size
        """
        pwm_period_value = int(round(clk_freq / (self.sweep_rate * 1000 / dac.voltage_step_size)))
        return pwm_period_value

    def update_settings(self, low_voltage, high_voltage, sweep_rate):
        """ Update the CV settings
        :param low_voltage: mV, voltage the user wants to start at
        :param high_voltage: mV, voltage the user wants to end the cyclic voltammetry at
        :param sweep_rate: V/s, rate of change of the cyclic voltammetry
        :return:
        """
        self.low_voltage = low_voltage
        self.high_voltage = high_voltage
        self.sweep_rate = sweep_rate
        self.delay_time = 2 * (self.high_voltage - self.low_voltage) / self.sweep_rate


class AmpSettings(object):
    """ Class to hold the important parameters for running an amperometry experiment
    Note: this interacts with CVSettings to keep the sample rate / sweep rate connected
    """

    def __init__(self, clock_freq, dac):
        self.voltage = -500  # mV, start with basic parameters
        self.sampling_rate = 1000  # Hz
        self.pwm_period_value = self.calculate_pwm_period(clock_freq)

    def calculate_pwm_period(self, clk_freq):
        """ Calculate the PWM period needed to achieve the desired sampling rate
        :param clk_freq: clock frequecy feeding the timing PWM
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

    def get_dac_count(self, _input_voltage):
        """ Get the digital value the dac needs to product the input voltage
        :param _input_voltage: float of the desired voltage
        :return: int of the digital value that should be inputted  """
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
    def __init__(self, tia_resistor=20, adc_gain=1, bits=ADC_BITS):
        self.tia_resistor = tia_resistor
        self.adc_gain = adc_gain
        self.bits = bits
        self.counts_to_current = self.calc_counts_to_current_ua()
        self.shift = 0
        self.adc_channel = 0  # the PSoC has different adc channels that can be read

    def calc_counts_to_current_ua(self):
        """ Calculate the number that you multiple the ADC count by to get the current in micro amps
        :return: float that is uA / count
        """
        # what to multiply adc counts by to get voltage in mV
        counts_to_volts = float(ADC_VREF) / (2 ** self.bits)
        volts_to_current = 1.0 / self.tia_resistor
        return counts_to_volts * volts_to_current

    def set_value(self, new_tia_value, new_adc_gain_value):
        """ The TIA or ADC have changed so update the values
        :param new_tia_value: new tia resistor value
        :param new_adc_gain_value: new buffer gain for the adc
        :return:
        """
        self.tia_resistor = new_tia_value
        self.adc_gain = new_adc_gain_value
        self.counts_to_current = self.calc_counts_to_current_ua()

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
