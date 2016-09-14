__author__ = 'Kyle Vitautas Lopin'


class DeviceParameters(object):
    """
    class to hold all the properties and parameters of the PSoC amperometry device
    """

    def __init__(self):
        # constant parameters
        self.number_IN_ENDPOINTS = 1  # how many IN ENDPOINTS to connect to
        self.number_OUT_ENDPOINTS = 1  # how many IN ENDPOINTS to connect to
        self.smallest_increment_pidac = 1. / 8.  # the smallest increment the PIDAC is increased by for base model
        self.smallest_increment_vdac = 4  # mV if the device is configured to use the VDAC instead of the PIDAC
        # resistor the PIDAC pushes the current through.  can be a guess as this will be calibrated
        # self.PIDAC_resistor = 9.8  # kilohms
        # change in voltage made by a 1 bit change in the models dac
        self.voltage_step = 16  # mV assume the 8-bit VDAC at 1V range to start
        self.clk_freq_isr_pwm = 2400000.  # frequency of the clock that is driving the PWM that triggers isr
        self.virtual_ground_shift = 1024.  # mv shift in ground the device uses
        self.bits_PIDAC = 11  # number of bits of the PIDAC

        # variable parameters
        self.low_cv_voltage = -500.  # mV
        self.high_cv_voltage = 500.  # mV
        self.length_side = self.high_cv_voltage - self.low_cv_voltage
        self.data_pts = 2 * (self.length_side + 1)
        self.sweep_rate = 1.0  # V/s
        self.PWM_period_value = self.calculate_pwm_period()
        self.PWM_compare = int(self.PWM_period_value / 2)
        self.TIA_resistor = 20  # kilohms, variable that the resistor of the transimpedance amplifier is set to
        self.ADC_gain = 1.  # the PSoC delta sigma ADC has its own gain setting
        self.current_gain = self.ADC_gain / 20000.  # 1/kilohms, varible to store the real gain of the TIA and ADC

        self.adc_channel = 0  # the PSoC has different adc channels that can be read
        self.usb_count = 0  # this will be set when the device is initialized
        self.user_sets_labels_after_run = True  # should be moved

    def calculate_pwm_period(self):
        """ take the clock frequency that is driving the PWM and divide it by the number of voltage steps per second:
        this is how many clk ticks between each interrupt """
        voltage_step_size = self.voltage_step
        pwm_period_value = int(round(self.clk_freq_isr_pwm / (self.sweep_rate * 1000 / voltage_step_size)))
        return pwm_period_value


class UserParameters(object):
    def __init__(self):
        self.should_process = False  # variable if the program should export the raw adc numbers or convert it
        # self.user_sets_labels_after_run = True  # lets the user set the data label and make a note after a run
