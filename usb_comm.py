# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" Communicate with a USB device for a PSoC electrochemical device
"""
# standard libraries
import logging
import time
# installed libraries
import usb.core
import usb.util
import usb.backend.libusb0
# local files
import amp_usb_helper as usb_helper
import properties
import toplevels

__author__ = 'Kyle V. Lopin'

USB_IN_BYTE_SIZE = 32
USB_TERMINATION_SIGNAL = 255 * 257
PACKET_SIZE = 32
TEST_MESSAGE = "USB Test"
TEST_MESSAGES = {"USB Test": "base",
                 "USB Test - 059": "kit-059",
                 "USB Test - v04": "v04"}
RUNNING_DELAY = 3000
FAIL_COUNT_THRESHOLD = 2
FAILURE_DELAY = 500
COMPLETE_MESSAGE = "Done"


class AmpUsb(object):
    """
    Generic class that deals with the usb communication microcontroller, uses a helper function
    to deal with the specifics of how data should be formatted, timing, etc.
    Idea is to use this as a general class that can be moved to new projects while the helper
    function handles the specifics
    """

    def __init__(self, _master, _device_params, vendor_id=None, product_id=None):
        """
        Initialize a communication channel to a PSoC with a USBFS module.  Use the default example
        for the USBFS HID example if no vendor or product id are inputted

        :param _master: the master program that is using the usb
        :param _device_params: parameters needed for the device to work properly, from the
        properties file
        :param vendor_id: the USB vendor id, used to identify the proper device connected to
        the computer
        :param product_id: the USB product id
        :return:
        """
        self.found = False
        if not vendor_id:
            vendor_id = 0x04B4
        if not product_id:
            product_id = 0xE177

        # attempt to connect the device
        self.device_params = _device_params
        self.master = _master
        self.device_type = None
        logging.info("attempting connection")
        self.device, self.ep_out, self.ep_in = self.connect_usb(vendor_id, product_id)

        # test the device if it was found to see if it is working properly
        if self.found:
            self.working = self.connection_test()
        else:
            logging.info("not found")
            return None

        # If it was found to be working properly initialize the device
        if self.working:
            self.connected = False
            logging.info("Initializing run parameters")

            self.find_voltage_source()
            time.sleep(0.5)
            self.send_cv_parameters()
            self.usb_write("A0|0|F|2")  # set the TIA resistor to 20k ohm on startup
        else:
            logging.info("not working")

    def connection_test(self):
        """
        The device can be found but still not respond correctly, this is to test the connection
        by sending a message and check if the amperometry responses with the proper message
        """
        self.working = True  # for usb_write to work it needs the working property to be true
        self.usb_write("I")
        received_message = self.usb_read_message()
        logging.info("I message received: %s", received_message)
        if received_message in TEST_MESSAGES:
            # self.device_type = test_messages[received_message]
            self.set_device_type(TEST_MESSAGES[received_message])
            logging.info("Device type %s selected", self.device_type)
            return True
        else:
            logging.info("test failed")
            self.device_type = None
            self.master.failed_connection()
            self.attempt_reconnection()
            return False

    def connect_usb(self, _vendor_id=0x04B4, _product_id=0xE177):
        """
        Attempt to connect to the PSoC device with a USBFS module
        If the device is not found return None

        This method uses the pyUSB module, see the tutorial example at:
        https://github.com/walac/pyusb/blob/master/docs/tutorial.rst
        for more details

        TODO: print statements to a log file with time stamps
        :param _vendor_id: the USB vendor id, used to identify the proper device connected to
        sthe computer
        :param _product_id: the USB product id
        :return:
        """
        # attempt to find the PSoC amperometry device
        amp_device = usb.core.find(idVendor=_vendor_id, idProduct=_product_id)

        # if no device is found, print a warning to the output
        if amp_device is None:
            logging.info("Device not found")
            self.found = False
            return None, None, None
        else:  # if a device is found print that it was found
            logging.info("PSoC amp found")
            self.found = True

        # set the active configuration. the pyUSB module deals with the details
        amp_device.set_configuration()

        # with the device active, get the endpoints.
        # See Cypress's document AN57294 - USB 101: An Introduction to Universal Serial Bus 2.0
        # for details about general USB protocols
        cfg = amp_device.get_active_configuration()
        interface = cfg[(0, 0)]
        # make a list of out and in ENDPOINTS and fill it with the number specified
        # in the params dict
        ep_out = []
        ep_in = []
        for out_end_pts in range(self.device_params.number_OUT_ENDPOINTS):
            ep_out.append(usb.util.find_descriptor(interface, custom_match=
                                                   lambda e: usb.util.endpoint_direction(e.bEndpointAddress) ==
                                                             usb.util.ENDPOINT_OUT))

        for in_end_pts in range(self.device_params.number_IN_ENDPOINTS):
            ep_in.append(usb.util.find_descriptor(interface, custom_match=
                                                  lambda e: usb.util.endpoint_direction(e.bEndpointAddress) ==
                                                            usb.util.ENDPOINT_IN))

        # return the device and endpoints if the exist or None if no device is found
        return amp_device, ep_out, ep_in

    def set_device_type(self, _device_type):
        """
        Set what version of the device is attached
        :param _device_type: sting of the version of the device attached
        """
        self.device_type = _device_type

    def find_voltage_source(self):
        """
        Test the device to see if it is using the 8-bit VDAC or the 12-bit DVDAC
        :return:
        """
        self.usb_write("VR")
        time.sleep(1)
        source_input = self.usb_read_data(2)
        if not source_input:
            return
        if source_input[1] == 0:
            volt_source_top = toplevels.VoltageSourceSelect(self.master, source_input[1])
        elif source_input[1] == 1:
            logging.info("VDAC is set in device")
            self.master.set_voltage_source_label(
                "Voltage source: 8-bit VDAC (no capacitor installed")
            self.device_params.dac.set_source("VDAC")
        elif source_input[1] == 2:
            logging.info("DVDAC is voltage source")
            self.master.set_voltage_source_label(
                "Voltage source: Dithering VDAC (capacitor installed)")
            self.device_params.dac.set_source("DVDAC")

    def select_voltage_source(self, source):
        print '183 usb: ', source, self.device_params.dac.source

        if source == self.device_params.dac.source:
            return  # selected source that is already choosen
        if source == "VDAC":
            print 'usb 19o fix this'
            raise NotImplementedError
        elif source == "DVDAC":
            print 'usb 193 fix this'
            # tell the device to set the voltage source as the DVDAC
            self.usb_write("VS2")
            # TODO: set the device dac attribute to DVDAC
            self.device_params.dac.set_source("DVDAC")
            # TODO:  resend the CV prameters with new numbers because the dac changes so the
            # look up table has to be changed too
            self.send_cv_parameters()

    def send_cv_parameters(self):
        """
        Send the parameters that the amperometric device should use to perform a cyclic voltammetry
        sweep the data needed calculate the values to send should be in a dictionary of the form
        device.params.low_cv_voltage which is the lowest voltage (in mV) of the triangle waveform
        device.params.high_cv_voltage which is the highest voltage (in mV) of the triangle waveform
        device.params.sweep_rate which is the speed (in V/s) that the voltage should be changed

        Note: the values sending to the device have to be padded with 0's so they are the
        proper size for the device to interpret

        :param device: device from usb_comm class that is being used to communicate with
        :return: will update to the device.params the following values
        usb_count which is how many data values to expect back into to device when receiving data
        actual_low_volt the lowest voltage the device will give to the electrode
        actual_high_volt the highest voltage the device will give to the electrode
        volt_increment the amount a 1 bit increase in the PIDAC will increase the voltage
        at the electrode
        """
        logging.debug("sending cv params here")
        # convert the values for the params dictionary into the values the device needs;
        # this part is done on the computer side to save MCU code length
        formatted_low_volt, low_dac_value = self.format_voltage(self.device_params.low_cv_voltage)
        formatted_high_volt, high_dac_value = self.format_voltage(self.device_params.high_cv_voltage)
        formatted_freq_divider, pwm_period = self.format_divider(self.device_params.sweep_rate)

        self.device_params.PWM_period = pwm_period

        # send those values to the device in the proper format for the PSoC amperometry device
        to_amp_device = '|'.join(["S", formatted_low_volt,
                                  formatted_high_volt, formatted_freq_divider])

        # save how many data points should be recieved back from the usb """
        self.device_params.usb_count = 2 * (high_dac_value - low_dac_value + 1)

        # calculate what the actual voltage the device will make.  This will be slightly different
        # from the user input because of the VDAC's resolution
        self.device_params.actual_low_volt = (low_dac_value - low_dac_value
                                              % self.device_params.dac.voltage_step_size)

        self.usb_write(to_amp_device)

        # Write to the timing PWM compare register so the dac adc timing is correct
        compare_value = pwm_period / 2
        write_timer_compare(self, compare_value)

    def _write_timer_compare(self, value):
        """
        Write to the device to update the PWM period so it runs at the correct scan rate
        :param value: the value to write in the timer compare
        """
        logging.debug("compare value is %s", value)
        # usb_helper.write_timer_compare(self, value)
        logging.debug("compare value is %s", value)
        self.master.device_params.PWM_compare = int(value)
        _formatted_value = '{0:05d}'.format(int(value))
        self.usb_write('C|' + _formatted_value)

    def run_scan(self, canvas, master):
        """
        This will run a cyclic voltammetry scan. To do this it follows the steps
        1) sent 'R' to the microcontroller to run the scan and collect the data
        2) wait for the scan to run and poll the amperometry device to see if its ready for data
        3) Check if the device is done by receiving the correct message back
        4) sent 'EX' to the device, this make the amperometry device export the data in chunks
        (size defined in USB_IN_BYTE_SIZE (IN, as in 'in' the computer) from the channel number
        described use in X.  NOTE: the X is a string of an int so '0', '1', '2', or '3' works
        5) read the IN_ENDPOINT until all the data is send to the this program

        :param canvas: canvas to display data on
        :param master: master (root) GUI
        :return: binds the data to the master instead of returning anything
        """
        self.usb_write('R')  # step 1
        if self.working:
            logging.debug("device reading")
            self.master.after(RUNNING_DELAY, lambda: self.run_scan_continue(canvas))  # step 2
        else:
            logging.debug("Couldn't find out endpoint to send message to run")
            master.attempt_reconnection()

    def calibrate(self):
        pass

    def run_scan_continue(self, canvas, fail_count=0):
        """
        The callback for run_scan.  This is called after the device should be done with the scan
        and is readyto export the data.   The parts of the run cyclic voltammetry scan this
        functions run is part 3-5 listed in run_scan.
        :param canvas: the widget that is called to display the data
        :return:
        """
        check_message = self.usb_read_message()  # step 3

        if check_message == COMPLETE_MESSAGE:
            self.get_and_display_data_from_export_channel(canvas)
        else:
            # wait a little longer and retry, after a certain amount of time, timeout
            if fail_count < FAIL_COUNT_THRESHOLD:  # retry step 2
                self.master.after(FAILURE_DELAY,
                                  lambda: self.run_scan_continue(canvas, fail_count + 1))
            logging.error("Failed to run the scan")

    def get_and_display_data_from_export_channel(self, canvas, _channel=None):
        """
        Get the data from the device and display it on the pyplot display
        :param canvas: where the data is to be displayed
        :param _channel: which adc channel to read
        """
        if not _channel:
            # if no channel sent, use the one saved in parameters dict
            _channel = self.device_params.adc_channel

        # the correct complete message was received so attempt to collect the data
        self.usb_write('E' + str(_channel))  # step 4

        # Get the raw data from the ADC.  this has to be modified to get the actual current values
        raw_data = self.get_data()
        if not raw_data:  # if something is wrong just return
            return
        # call function to convert the raw ADC values into the current that passed
        # through the working electrode
        data = self._process_data(raw_data)

        logging.info('TODO: still binding data to main and not custom class, fix this')
        self.master.current_data = data
        x_line = make_x_line(self.device_params.low_cv_voltage,
                             self.device_params.high_cv_voltage,
                             self.device_params.dac.voltage_step_size,
                             self.device_params.virtual_ground_shift)

        # Send data to the canvas where it will be saved and displayed
        canvas.update_data(x_line, data, raw_data)

    def get_data(self):
        """
        Get the raw adc counts from the device
        Get the proper amount of data packets from the device
        :return: a list of adc counts
        """
        logging.debug("getting data")
        end_pt = self.device[0][(0, 0)][0]
        full_array = []
        # calculate how many packets of data to get from the amp device the usb_count param is
        # how many data points there are (+2 us for the 0xFFFF sent at the end)
        # packet_size / 2 is because the data is converted to uint8
        # from the uint16 it is acquired in """
        number_packets = (self.device_params.usb_count + 2) / (PACKET_SIZE / 2)
        logging.debug("get %d number of packets", number_packets)
        count = 0
        running = True
        while number_packets + 1 > count and running:
            try:
                logging.debug("getting packet %d", count)
                usb_input = self.device.read(end_pt.bEndpointAddress, PACKET_SIZE)
                _hold = convert_uint8_to_signed_int16(usb_input.tolist())
                print 'hold: ', _hold
                full_array.extend(_hold)
                if _hold[-1] == -16384:
                    full_array.pop()
                    break
                count += 1
            except Exception as error:
                logging.debug("end of ENDPOINT")
                logging.debug(error)
                running = False
        full_array = full_array[:self.device_params.usb_count + 1]
        return full_array

    def _process_data(self, _raw_data):
        """
        Take in the raw adc counts and output the corresponding current values
        :param device: the device that has the data_save_type and TIA_resistor values to
        properly process the data
        :param _raw_data: raw adc count numbers
        :return: current (micro amperes) values of the adc values
        """
        if self.master.data_save_type == "Converted":
            logging.debug("Converting data")
            # Convert the adc number to the current
            count_to_current = self.device_params.adc_tia.counts_to_current
            logging.debug("count to current: %4.4f", count_to_current)
            current = [x * count_to_current for x in _raw_data]
            return current
        elif self.master.data_save_type == "Raw Counts":
            logging.debug("sending raw data back")
            return _raw_data

    def get_export_channel(self, channel=None):
        """
        DEPRECEATED???
        get the data from the device
        :param channel: int, channel number to get, the device may have multiple adc buffer arrays

        """
        canvas = self.master.graph
        usb_helper.get_and_display_data_from_export_channel(self, canvas, channel)

    def set_electrode_config(self, num_electrodes):
        """
        The PSoC can perform either 2 electrode or 3 electrode measurements, send the device the
        command 'L|X' to change its config where X is either 2 or 3 for the # of electrodes to use
        :param _configs:
        :return:
        """
        self.usb_write('L|' + str(num_electrodes))

    def set_custom_resistor_channel(self, channel):
        self.usb_write("A7|0|T|" + channel)
        # the 7 is to set the TIA resistor to 1M to minimize the change it will have on
        # the equivalent resistance

    def format_divider(self, _sweep_rate):
        """
        Take in the users desired sweet rate and convert it to the number needed to input into the
        PWM used to set the time between the interrupts that change the dac values
        (_sweep_rate * 1000) is used to convert the sweep rate from V/s to mV/s
        :param _sweep_rate: the users desired sweep rate
        :return: integer that is to be put into the interrupt PWM timer that's padded with zeros to
        be 5 integers long to properly send it to the device
        """
        clk_freq = self.device_params.clk_freq_isr_pwm

        # take the clock frequency that is driving the PWM and divide it by the number of voltage
        # steps per second: this is how many clk ticks between each interrupt
        raw_divider = int(
            round(clk_freq / (_sweep_rate * 1000 / self.device_params.dac.voltage_step_size)))
        return '{0:05d}'.format(raw_divider), raw_divider

    def format_voltage(self, _in_volts):
        """
        Takes in the voltage (in millivolts) the user wants to apply to the electrode and convert
        it to the integer that represent the value to be put into the pidac
        :param _in_volts: user desired electrode voltage value in millivolts
        :return: integer that is the value to be put into the pidac, padded with zeros to be 4
        values long to be transmitted to the device
        """
        # shift the user's voltage by the amount of the virtual ground
        input_voltage = self.device_params.virtual_ground_shift + _in_volts  # mV

        # get the value needed (number of increments needed to get desired voltage, ex. desire
        # 500mV with 1 mV increments then put in 500) to put into the dac and pad it with zeros
        print self.device_params.dac.voltage_step_size
        dac_value = self.device_params.dac.get_dac_count(input_voltage)
        return '{0:04d}'.format(dac_value), dac_value

    def usb_write(self, message, endpoint=1):
        """
        Write the message to the device
        :param message: message, in bytes, to send
        :param endpoint: which OUT_ENDPOINT to use to send the message in the case there are more
        than 1 OUT_ENDPOINTS
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

    def usb_read_data(self, _size=PACKET_SIZE, endpoint=None, encoding=None):
        """
        Read data from the usb and return it
        :param _size: number of bytes to read
        :param endpoint: the IN ENPOINT numner
        :return: array of the bytes read
        """
        if not self.working:
            logging.info("not working")
            return None
        if not endpoint:
            endpoint = self.device[0][(0, 0)][0]
        try:
            logging.debug("getting data in usb_read_data")
            usb_input = self.device.read(endpoint.bEndpointAddress, _size)
            logging.info("data received: %s", str(usb_input))

        except Exception as error:
            logging.error("Failed read")
            logging.error("No IN ENDPOINT: %s", error)
            return None
        if encoding == 'uint16':
            return convert_int8_int16(usb_input)
        elif encoding == "signed int16":
            print 'check'
            _hold = convert_uint8_to_signed_int16(usb_input)
            print _hold
            return _hold
        else:  # no encoding so just return raw data
            return usb_input

    def usb_read_message(self, _size=PACKET_SIZE, endpoint=1):
        """
        Read any data from the device
        :param endpoint: endpoint number of the IN channel
        :return: data from the device
        """
        if not self.working:
            logging.info("not working")
            self.master.failed_connection()
            return None
        end_pt = self.device[0][(0, 0)][0]

        try:
            logging.debug("getting message in usb_read_message")
            usb_input = self.device.read(end_pt.bEndpointAddress, _size)
            _hold = usb_input.tolist()
            str_message = convert_uint8_to_string(_hold)
            logging.info("message received: %s", str_message)
            return str_message
        except Exception as error:
            logging.error("Failed read")
            logging.error("No IN ENDPOINT: %s", error)
            return None

    def attempt_reconnection(self):
        logging.debug("usb_comm reconnection protocol")
        self.usb_read_data()  # try to clear the data that might be in the queue
        self.connect_usb()


def make_x_line(start, end, inc, shift):
    i = start
    line = []
    while i <= end:
        line.append(i)
        i += inc
    while i >= start:
        line.append(i)
        i -= inc
    return line


def make_x_line_base(start, end, inc, shift):
    print "MAKE X LINE IS A HACK FIX    "
    print "making line start, stop, inc: ", start, end, inc
    i = start
    line = []
    while i < end:
        line.append(i - shift)
        i += inc

    while i > start:
        line.append(i - shift)
        i -= inc

    print "x line start and stop: ", line[0], line[len(line)/2], line[-1]
    return line


def convert_int8_int16(_array):
    new_array = [0]*(len(_array)/2)
    for i in range(len(_array)/2):
        _hold = _array.pop(0) + _array.pop(0) * 256
        if _hold == USB_TERMINATION_SIGNAL:
            new_array[i] = _hold
            break
        new_array[i] = _hold
    return new_array


def convert_uint8_to_signed_int16(_bytes):
    """
    Convert an array of bytes into an array of signed int16
    :param _bytes: array of uint8
    :return: aray of signed int16
    """
    new_array = [0] * (len(_bytes) / 2)
    max_value = 2 ** 16 / 2  # maximum positive value that can be make with signed int16
    for i in range(len(_bytes) / 2):
        _hold = _bytes.pop(0) + _bytes.pop(0) * 256  # combind the individual bytes
        if _hold >= max_value:
            _hold -= (2 * max_value)
        if _hold == USB_TERMINATION_SIGNAL:
            new_array[i] = _hold
            break
        new_array[i] = _hold
    return new_array

def convert_uint8_to_string(_uint8_list):
    i = 0
    _string = ""
    while _uint8_list[i] != 0:
        _string += chr(_uint8_list[i])
        i += 1
    return _string


def write_timer_compare(device, value):
    logging.debug("compare value is %s", value)
    device.master.device_params.PWM_compare = int(value)
    _formatted_value = '{0:05d}'.format(int(value))
    device.usb_write('C|' + _formatted_value)


# TODO: REMOVE CHECK - DEPRECATED
class DeviceParameters32323(object):
    """
    class to hold all the properties and parameters of the PSoC amperometry device
    """

    def __init__(self):
        # constant parameters
        self.number_IN_ENDPOINTS = 1  # how many IN ENDPOINTS to connect to
        self.number_OUT_ENDPOINTS = 1  # how many IN ENDPOINTS to connect to
        # change in voltage made by a 1 bit change in the dac
        self.voltage_step = 16  # mV
        # frequency of the clock that is driving the PWM that triggers isr
        self.clk_freq_isr_pwm = 2400000.
        self.virtual_ground_shift = 1024.  # mv shift in ground the device uses
        self.bits_VDAC = 12  # number of bits of the PIDAC

        # variable parameters
        self.low_cv_voltage = -500.  # mV
        self.high_cv_voltage = 500.  # mV
        self.length_side = self.high_cv_voltage - self.low_cv_voltage
        self.data_pts = 2 * (self.length_side + 1)
        self.sweep_rate = 1.0  # V/s
        self.PWM_period_value = self.calculate_pwm_period()
        self.PWM_compare = int(self.PWM_period_value / 2)
        # kilohms, variable that the resistor of the transimpedance amplifier is set to
        self.TIA_resistor = 20
        self.ADC_gain = 1.  # the PSoC delta sigma ADC has its own gain setting
        # 1/kilohms, varible to store the real gain of the TIA and ADC
        self.current_gain = self.ADC_gain / 20000.

        self.adc_channel = 0  # the PSoC has different adc channels that can be read
        self.usb_count = 0  # this will be set when the device is initialized
        self.user_sets_labels_after_run = True  # should be moved

    def calculate_pwm_period(self):
        """ take the clock frequency that is driving the PWM and divide it by the number of
        voltage steps per second:this is how many clk ticks between each interrupt """
        return int(round(self.clk_freq_isr_pwm / (self.sweep_rate * 1000 / self.voltage_step)))


# TODO: REMOVE CHECK - DEPRECATED
class UserParametersdsdfasfds(object):
    def __init__(self):
        # variable if the program should export the raw adc numbers or convert it
        self.should_process = False
        # lets the user set the data label and make a note after a run
        self.user_sets_labels_after_run = True
