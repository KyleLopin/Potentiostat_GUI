# from __future__ import division

__author__ = 'Kyle V. Lopin'

import logging
import usb.core
import usb.util
import amp_usb_helper as usb_helper
import pyplot_data_class as data_class


USB_IN_BYTE_SIZE = 32
packet_size = 32
test_message = "USB Test"


class AmpUsb(object):
    """
    Generic class that deals with the usb communication microcontroller, uses a helper function to deal
    with the specifics of how data should be formatted, timing, etc.
    Idea is to use this as a general class that can be moved to new projects while the helper
    function handles the specifics
    """
    def __init__(self, _master, _params, vendor_id=None, product_id=None):
        """
        Initialize a communication channel to a PSOC with a USBFS module.  Use the default example for the
        USBFS HID example if no vendor or product id are inputted

        :param _master: the master program that is using the usb
        :param _params: a dictionary of any parameters needed for the device to work properly
        :param vendor_id: the USB vendor id, used to identify the proper device connected to the computer
        :param product_id: the USB product id
        :return:
        """
        self.found = False
        self.data_set = data_class.PyplotData()
        if not vendor_id:
            vendor_id = 0x04B4
        if not product_id:
            product_id = 0xE177

        """ attempt to connect the device """
        self.params = _params
        self.master = _master
        logging.info("attempting connection")
        self.device, self.ep_out, self.ep_in = self.connect_usb(vendor_id, product_id)

        """ test the device if it was found to see if it is working properly """
        if self.found:
            self.working = self.connection_test()
        else:
            logging.info("not found")
            return None

        """ If it was found to be working properly initialize the device """
        if self.working:
            self.connected = False
            logging.info("Initializing run parameters")
            usb_helper.initialize(self)
            usb_helper.send_cv_parameters(self)
            self.usb_write("A0")  # set the TIA resistor to 20k ohm on startup
        else:
            logging.info("not working")

    def connection_test(self):
        """
        The device can be found but still not respond correctly, this is to test the connection by sending a message
        and check if the amperometry responses with the proper message
        :return:
        """
        self.working = True  # for usb_write to work it needs the working property to be true
        self.usb_write("I")
        received_message = self.usb_read_message()
        logging.info("I message received: %s", received_message)
        if received_message == test_message:
            logging.info("test working")
            return True
        else:
            logging.info("test failed")
            self.master.failed_connection()
            return False

    def connect_usb(self, _vendor_id, _product_id):
        """
        Attempt to connect to the PSoC device with a USBFS module
        If the device is not found return None

        This method uses the pyUSB module, see the tutorial example at:
        https://github.com/walac/pyusb/blob/master/docs/tutorial.rst
        for more details

        TODO: print statements to a log file with time stamps
        :param _vendor_id: the USB vendor id, used to identify the proper device connected to the computer
        :param _product_id: the USB product id
        :return:
        """
        """ attempt to find the PSoC amperometry device """
        amp_device = usb.core.find(idVendor=_vendor_id, idProduct=_product_id)

        """ if no device is found, print a warning to the output """
        if amp_device is None:
            logging.info("Device not found")
            self.found = False
            return None, None, None
        else:  # if a device is found print that it was found
            logging.info("PSoC amp found")
            self.found = True

        """ set the active configuration. the pyUSB module deals with the details """
        amp_device.set_configuration()

        """ with the device active, get the endpoints.
        See Cypress's document AN57294 - USB 101: An Introduction to Universal Serial Bus 2.0 for details about
        general USB protocols """
        cfg = amp_device.get_active_configuration()
        interface = cfg[(0, 0)]
        """ make a list of out and in ENDPOINTS and fill it with the number specified in the params dict """
        ep_out = []
        ep_in = []
        for i in range(self.params['number_OUT_ENDPOINTS']):
            ep_out.append(usb.util.find_descriptor(interface, custom_match=
                                                   lambda e: usb.util.endpoint_direction(e.bEndpointAddress) ==
                                                             usb.util.ENDPOINT_OUT))

        for i in range(self.params['number_IN_ENDPOINTS']):
            ep_in.append(usb.util.find_descriptor(interface, custom_match=
                                                  lambda e: usb.util.endpoint_direction(e.bEndpointAddress) ==
                                                            usb.util.ENDPOINT_IN))

        """ return the device and endpoints if the exist or None if no device is found """
        return amp_device, ep_out, ep_in

    def send_cv_parameters(device):
        usb_helper.send_cv_parameters(device)

    def run_scan(self, canvas, master):
        """
        Run a cyclic voltammetry scan
        :param canvas: canvas to display data on
        :param master: master GUI
        :return: bind the data to the master instead of returning anything
        """
        usb_helper.run_scan(self, canvas, master)

    def format_divider(self, _sweep_rate):
        """
        Take in the users desired sweet rate and convert it to the number needed to input into the PWM used to set
        the time between the interrupts that change the dac values
        (_sweep_rate * 1000) is used to convert the sweep rate from V/s to mV/s
        :param _sweep_rate: the users desired sweep rate
        :return: integer that is to be put into the interrupt PWM timer that's padded with zeros to be 5 integers long
        to properly send it to the device
        """
        # clk_freq = 24000000  # Hz of clock going into the PWM driving the adc and dac isr
        clk_freq = self.params['clk_freq_isr_pwm']
        pidac_resistor = self.params['PIDAC_resistor']  # kilohms - resistor used to convert the current DAC to a volts

        """what a 1 bit increase into PIDAC will cause the PIDAC to increase its output current and the corresponding
        increase in the voltage"""
        smallest_increment_pidac = self.params['smallest_increment_pidac']  # microamps
        voltage_step_size = smallest_increment_pidac * pidac_resistor  # millivolts (kilohms * microamps)

        """ take the clock frequency that is driving the PWM and divide it by the number of voltage steps per second:
        this is how many clk ticks between each interrupt """
        raw_divider = int(round(clk_freq / (_sweep_rate * 1000 / voltage_step_size)))
        return '{0:05d}'.format(raw_divider)

    def format_voltage(self, _in_volts):
        """
        Takes in the voltage (in millivolts) the user wants to apply to the electrode and convert it to the integer that
        represent the value to be put into the pidac
        :param _in_volts: user desired electrode voltage value in millivolts
        :return: integer that is the value to be put into the pidac, padded with zeros to be 4 values long to be
        transmitted to the device
        """
        """ shift the user's voltage by the amount of the virtual ground """
        voltage_setting = self.params['virtual_ground_shift'] + _in_volts  # mV
        """ calculate incremental voltage that a bit of the PIDAC causes """
        voltage_step_size = self.params['smallest_increment_pidac'] * self.params['PIDAC_resistor']  # mV
        """ get the value needed (number of increments needed to get desired voltage, ex. desire 500mV with 1 mV
        increments then put in 500) to put into the pidac and pad it with zeros """
        pidac_value = int(round(voltage_setting / voltage_step_size))
        return '{0:04d}'.format(pidac_value), pidac_value

    def usb_write(self, message, endpoint=1):
        """

        :param message:
        :param endpoint: which OUT_ENDPOINT to use to send the message in the case there are more than 1 OUT_ENDPOINTS
        :return:
        """
        if not self.working:
            logging.info("Device not connected")
            self.master.failed_connection()
        elif len(message) > 32:
            logging.error("Message is too long")
        else:
            logging.debug("writing message: %s", message)
            try:
                self.ep_out[0].write(message)
                self.connected = True
            except Exception as e:
                logging.error("No OUT ENDPOINT: %s", e)
                self.working = False
                logging.debug("setting device.working to false")
                # self.master.failed_connection()
                # self.master.attempt_reconnect()

    def usb_read_message(self, endpoint=1):
        if not self.working:
            logging.info("not working")
            self.master.failed_connection()
            return None
        end_pt = self.device[0][(0, 0)][0]

        try:
            logging.debug("getting message in usb_read")
            usb_input = self.device.read(end_pt.bEndpointAddress, packet_size)
            _hold = usb_input.tolist()
            str_message = convert_uint8_to_string(_hold)
            logging.info("message received: %s", str_message)
            return str_message
        except Exception as e:
            logging.error("Failed read")
            logging.error("No IN ENDPOINT: %s", e)
            return None

    def attempt_reconnection(self):
        logging.debug("usb_comm reconnection protocol")
        self.master.attempt_reconnection()
        # usb.util.dispose_resources(self.device)
        # self.device.destroy()
        # vendor_id = 0x04B4
        # product_id = 0xE177
        # print "trying to connect to device again"
        # self.device, self.ep_out, self.ep_in = self.connect_usb(vendor_id, product_id)

        # self.connected = False


def make_x_line(start, end, inc):
    print "MAKE X LINE IS A HACK FIX    "
    print "making line start, stop, inc: ", start, end, inc
    i = start
    line = []
    while i < end:
        line.append(i - 1024)
        i += inc

    while i > start:
        line.append(i - 1024)
        i -= inc

    print "x line start and stop: ", line[0], line[len(line)/2], line[-1]
    return line


def convert_int8_int16(_array):
    new_array = [0]*(len(_array)/2)
    for i in range(len(_array)/2):
        new_array[i] = _array.pop(0)*256 + _array.pop(0)
    return new_array


def convert_uint8_to_string(_uint8_list):
    i = 0
    _string = ""
    while _uint8_list[i] != 0:
        _string += chr(_uint8_list[i])
        i += 1
    return _string
