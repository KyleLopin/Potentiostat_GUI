from __future__ import division

__author__ = 'Kyle Vitautas Lopin'

ADC_VREF = 2048  # mV
ADC_BITS = 12

class DeviceParameters(object):
    """
    class to hold all the properties and parameters of the PSoC amperometry device
    """

    def __init__(self):
        # constant parameters
        self.number_IN_ENDPOINTS = 1  # how many IN ENDPOINTS to connect to
        self.number_OUT_ENDPOINTS = 1  # how many IN ENDPOINTS to connect to

        self.dac = DAC("8-bit DAC", voltage_range=4080)
        # self.smallest_increment_vdac = 4  # mV if the device is configured to use the VDAC instead of the PIDAC
        # change in voltage made by a 1 bit change in the models dac
        # self.voltage_step = 16  # mV assume the 8-bit VDAC at 1V range to start
        self.clk_freq_isr_pwm = 240000.  # frequency of the clock that is driving the PWM that triggers isr
        self.virtual_ground_shift = 1024.  # mv shift in ground the device uses

        # variable parameters
        self.low_cv_voltage = -500.  # mV
        self.high_cv_voltage = 500.  # mV
        self.length_side = self.high_cv_voltage - self.low_cv_voltage
        self.data_pts = 2 * (self.length_side + 1)
        self.sweep_rate = 1.0  # V/s
        self.PWM_period_value = self.calculate_pwm_period()
        self.PWM_compare = int(self.PWM_period_value / 2)
        self.adc_tia = ADC_TIA()
        self.adc_channel = 0  # the PSoC has different adc channels that can be read
        self.usb_count = 0  # this will be set when the device is initialized
        self.user_sets_labels_after_run = True  # should be moved

    def calculate_pwm_period(self):
        """ take the clock frequency that is driving the PWM and divide it by the number of voltage steps per second:
        this is how many clk ticks between each interrupt """
        voltage_step_size = self.dac.voltage_step_size
        pwm_period_value = int(round(self.clk_freq_isr_pwm / (self.sweep_rate * 1000 / voltage_step_size)))
        return pwm_period_value

    def set_dac(self, _type):
        _voltage_range = self.dac.range
        self.dac = DAC(_type, _voltage_range)

class UserParameters(object):
    def __init__(self):
        # variable if the program should export the raw adc numbers or convert it
        self.should_process = False
        # lets the user set the data label and make a note after a run
        # self.user_sets_labels_after_run = True


class DAC(object):
    """
    Class that provides the information of the DAC being used
    """

    def __init__(self, _type, voltage_range=4080.0):
        self.source = _type
        print 'properties: ', self.source
        if _type == "8-bit DAC":
            self.bits = 8  # bits of resolution

        elif _type == "DVDAC":
            self.bits = 12  # bits of resolution

        # (mV) the full voltage step the DAC can take, NOTE: is programmable
        self.range = voltage_range
        self.voltage_step_size = self.set_step_size()  # set the voltage step

    def set_bits(self):
        """ Set the number of bits of the DAC """
        if self.source == "8-bit DAC":
            self.bits = 8  # bits of resolution
        elif self.source == "DVDAC":
            self.bits = 12  # bits of resolution

    def set_step_size(self):
        """
        Calculate the step size (in mV) the dac will take
        :return:  voltage step, i.e. the amount the DAC changes for an 1 bit increase in digital
        code
        """
        return self.range / (2 ** self.bits)

    def get_dac_count(self, _input_voltage):
        """ Get the digital value the dac needs to product the input voltage
        :param _input_voltage: float of the desired voltage
        :return: int of the digital value that should be inputted  """
        return int(round(_input_voltage / self.voltage_step_size))

    def set_source(self, _source):
        """ Set the source of the voltage sources, either 8-bit VDAC of dithering VDAC
        :param _source: string of either "VDAC" or "DVDAC" for which source to set the DAC to
        :return:
        """
        if _source == self.source:
            return  # want to set to what it is already set to
        self.source = _source
        self.set_bits()
        self.voltage_step_size = self.set_step_size()


class ADC_TIA(object):
    """
    Class to represent the ADC and TIA current sensing block
    """

    def __init__(self, tia_resistor=20, adc_gain=1, bits=ADC_BITS):
        self.tia_resistor = tia_resistor
        self.adc_gain = adc_gain
        self.bits = bits
        self.counts_to_current = self.calc_counts_to_current_ua()

    def calc_counts_to_current_ua(self):
        """
        Calculate the number that you multiple the ADC count by to get the current in micro amps
        :return: float
        """
        # what to multiply adc counts by to get voltage in mV
        counts_to_volts = float(ADC_VREF) / (2 ** self.bits)
        volts_to_current = 1.0 / self.tia_resistor
        return counts_to_volts * volts_to_current

    def set_value(self, new_tia_value, new_adc_gain_value):
        self.tia_resistor = new_tia_value
        self.adc_gain = new_adc_gain_value
        self.counts_to_current = self.calc_counts_to_current_ua()
