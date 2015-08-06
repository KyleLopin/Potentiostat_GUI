# from __future__ import division

__author__ = 'Kyle V. Lopin'

import usb.core
import usb.util
import numpy as np

USB_IN_BYTE_SIZE = 32
packet_size = 32


class amp_usb(object):
    """
    Generic class that deals with the usb communication to an PSOC configured as an amperometric device
    """
    def __init__(self, _master, _params, vendor_id=None, product_id=None):
        """
        Initialize a communication channel to a PSOC with a USBFS module.  The default example for the USBFS HID example
        is set if no vendor or product id are inputted

        :param vendor_id: the USB vendor id, used to identify the proper device connected to the computer
        :param product_id: the USB product id
        :return:
        """
        if not vendor_id:
            vendor_id = 0x04B4
        if not product_id:
            product_id = 0xE177
        self.params = _params
        self.device = self.connect_usb(vendor_id, product_id)
        if self.device:
            print "Initializing run parameters"
            self.send_cv_parameters()
            self.usb_write("A0")
        print self.device
        self.master = _master

    def connect_usb(self, _vendor_id, _product_id):
        """
        Attempt to connect to the PSoC device with a USBFS module
        If the device is not found return None

        This method uses the pyUSB module, see the tutorial example at:
        https://github.com/walac/pyusb/blob/master/docs/tutorial.rst
        for more details

        TODO: print statements to a log file with time stamps

        :return:
        """
        # attempt to find the PSoC amperometry device
        amp_device = usb.core.find(idVendor=_vendor_id, idProduct=_product_id)
        # if no device is found, print a warning to the output
        if amp_device is None:
            print ValueError("Device not found")
            self.connected = False
            return None
        else:  # if a device is found print that it was found
            print "PSoC amp found"
            self.connected = True
        # set the active configuration. the pyUSB module deals with the details
        amp_device.set_configuration()

        # with the device active, get the endpoints.
        # See Cypress's document AN57294 - USB 101: An Introduction to Universal Serial Bus 2.0 for details about
        # general USB protocols
        cfg = amp_device.get_active_configuration()
        intf = cfg[(0, 0)]

        ep_out = usb.util.find_descriptor(intf, custom_match=
                                          lambda e: usb.util.endpoint_direction(e.bEndpointAddress) ==
                                          usb.util.ENDPOINT_OUT)

        ep_in = usb.util.find_descriptor(intf, custom_match=
                                         lambda e: usb.util.endpoint_direction(e.bEndpointAddress) ==
                                         usb.util.ENDPOINT_IN)
        # return the device and endpoints if the exist or None if no device is found
        return amp_device, ep_out, ep_in

    def run_scan(self, canvas):
        """
        This will run a CV scan. To do this it follows the steps
        1) sent 'R' to the microcontroller to run the scan and collect the data
        2) wait for the scan to run and poll the amperometry device to see if its ready for data
        3) Check if the device is done by receiving correct
        4) sent 'E' to the device, this make the amperometry device export the data in chunks (size defined in
        USB_IN_BYTE_SIZE (IN, as in 'in' the computer)
        5) read the IN_ENDPOINT until all the data is send to the this program
        :return: the adc data array from the amperometric device
        """
        running_delay = 2000
        self.usb_write('R')  # step 1
        self.master.after(running_delay, lambda: self.run_scan_continue(canvas))  # step 2

    def run_scan_continue(self, canvas, fail_count=0):
        complete_message = "Done"  # REPLACE WITH MORE GENERAL SOLUTION
        print "complete_message: ", complete_message
        fail_count_threshold = 5  # REPLACE WITH MORE GENERAL SOLUTION
        check_message = self.usb_read()  # step 3
        print "got back message: ", check_message
        if check_message == complete_message:
            # continue
            print "continue to get data"
            self.usb_write('E0')
            raw_data = self.get_data()
            print "got raw data"
            data = self.process_data(raw_data)
            self.master.data = data
            i = self.params['low_cv_voltage']
            # for
                # self.params['']
            x_line = make_x_line(self.params['actual_low_volt'],
                                 self.params['actual_high_volt'],
                                 self.params['volt_increment'])
            canvas.display_data(x_line, data)
            # print raw_data[1:10]
            # print data[1:10]
        else:
            # wait a little longer and retry, after a certain amount of time, timeout
            if fail_count > fail_count_threshold:
                print "Make a time out error here and offer to rerun the scan"
            print "rechecK"
            pass

    def process_data(self, _raw_data):
        # print _raw_data
        number_bits = 12  # resolution of the adc being used
        voltage_range = 2048  # mV
        level_shift = 1024  # mV
        max_bit_value = 2**number_bits
        print voltage_range, max_bit_value, level_shift, self.params['TIA_resistor']
        # pre_voltage = [(voltage_range * (float(x) / max_bit_value)) for x in _raw_data]
        # voltage = [(voltage_range * (float(x) / max_bit_value) - level_shift) for x in _raw_data]  # (V)
        # print voltage
        try:
            print self.params['TIA_resistor']
        except:
            pass
        voltage = [-((voltage_range * (float(x) / max_bit_value) - level_shift)
                   / self.params['TIA_resistor']) for x in _raw_data]  # microAmp (mV / kohms)
        print _raw_data[:20]
        print voltage[:20]
        return voltage

    def get_data(self):
        _device, ep_out, _ = self.device
        print "getting data (in get_data)"
        end_pt = _device[0][(0, 0)][0]
        full_array = []
        # calculate how many packets of data to get from the amp device
        # the usb_count param is how many data points there are
        # packet_size / 2 is because the data is converted to uint8
        # from the uint16 it is acquired in
        number_packets = self.params['usb_count'] / (packet_size / 2)
        # print number_packets
        count = 0
        running = True
        while number_packets+1 > count and running:
            try:
                usb_input = _device.read(end_pt.bEndpointAddress, packet_size)
                _hold = self.convert_int8_int16(usb_input.tolist())
                full_array.extend(_hold)
                count += 1
            except Exception as e:
                print "end of ENDPOINT"
                print e
                running = False
        while full_array[-1] == 0:
            full_array.pop()
        return full_array

    def convert_int8_int16(self, _array):
        new_array = [0]*(len(_array)/2)
        for i in range(len(_array)/2):
            new_array[i] = _array.pop(0)*256 + _array.pop(0)
        return new_array

    def send_cv_parameters(self):
        formatted_low_volt, low_dac_value = self.format_voltage(self.params['low_cv_voltage'])
        formatted_high_volt, high_dac_value = self.format_voltage(self.params['high_cv_voltage'])
        formatted_freq_divider = self.format_divider(self.params['sweep_rate'])
        to_amp_device = '|'.join(["S", formatted_low_volt, formatted_high_volt, formatted_freq_divider])
        self.params['usb_count'] = 2*(high_dac_value - low_dac_value+1)
        print to_amp_device
        PIDAC_resistor = 8.200  # kiloohms - resistor used to convert the current DAC to a voltage DAC
        bits_PIDAC = 11
        max_DAC_value = 2**bits_PIDAC  # max value needed to get max current out of PIDAC
        max_I_from_PIDAC = 255. + (7./8)  # max value out of the PIDAC if all bits_PIDAC are set to 1
        low_PIDAC_i_output = max_I_from_PIDAC * (low_dac_value / float(max_DAC_value))
        self.params['actual_low_volt'] = low_PIDAC_i_output * PIDAC_resistor

        high_PIDAC_i_output = max_I_from_PIDAC * (high_dac_value / float(max_DAC_value))
        self.params['actual_high_volt'] = high_PIDAC_i_output * PIDAC_resistor

        PIDAC_increment = max_I_from_PIDAC * (1 / float(max_DAC_value))
        self.params['volt_increment'] = PIDAC_increment * PIDAC_resistor

        print "self.params:"
        print self.params
        self.usb_write(to_amp_device)

    def format_divider(self, _sweep_rate):
        """
        (_sweep_rate * 1000) is used to convert the sweep rate from V/s to mV/s
        :param _sweep_rate:
        :return:
        """
        clk_freq = 24000000 # Hz of clock going into the PWM driving the adc and dac isrs
        PIDAC_resistor = 8.200  # kiloohms - resistor used to convert the current DAC to a voltage DAC
        smallest_inc_PIDAC = 1./8. # microamps - what a 1 bit increase into PIDAC will cause the PIDAC to increase
        # its output current
        voltage_step_size = smallest_inc_PIDAC * PIDAC_resistor  # millivolts (kohms * microamps) increase in output
        # print voltage_step_size
        # voltage for a 1 bit increase in PIDAC
        change_freq = ((_sweep_rate * 1000) / voltage_step_size)
        # change_freq = (voltage_step_size / (_sweep_rate/1000))
        # print change_freq
        raw_divider = int(round(clk_freq / (_sweep_rate * 1000 / voltage_step_size)))
        # print raw_divider
        return '{0:05d}'.format(raw_divider)

    def format_voltage(self, _in_volts):
        # REFACTOR THIS
        virtual_ground_volts = 1024  # mV - the shift in virtual ground from the Vssa
        shift_voltage = virtual_ground_volts + (_in_volts)
        #  'shift_voltage: ', shift_voltage
        PIDAC_resistor = 8.200  # kiloohms - resistor used to convert the current DAC to a voltage DAC
        desired_current = shift_voltage / PIDAC_resistor  # mV / k ohms = microamps (uA)
        # print desired_current
        bits_PIDAC = 11
        max_DAC_value = 2**bits_PIDAC  # max value needed to get max current out of PIDAC
        max_I_from_PIDAC = 255. + (7./8)  # max value out of the PIDAC if all bits_PIDAC are set to 1
        PIDAC_value = int(round(max_DAC_value*(desired_current / max_I_from_PIDAC)))
        # print PIDAC_value
        return '{0:04d}'.format(PIDAC_value), PIDAC_value

    def usb_write(self, message, endpoint=1):
        """

        :param message:
        :param endpoint: which OUT_ENDPOINT to use to send the message in the case there are more than 1 OUT_ENDPOINTS
        :return:
        """
        if not self.device:
            print "Device not connected"
        elif len(message) > 32:
            print "Message is too long"
        else:
            print "writing message: " + message
            _, ep_out, _ = self.device  # seperate OUTENDPOINT needed
            ep_out.write(message)

    def usb_read(self, endpoint=1):
        _device, ep_out, _ = self.device
        end_pt = _device[0][(0, 0)][0]
        try:
            print "getting message in usb_read"
            usb_input = _device.read(end_pt.bEndpointAddress, packet_size)
            _hold = usb_input.tolist()
            str_message = self.convert_uint8_to_string(_hold)
            print "message received: " + str_message
            return str_message
        except Exception as e:
            _full = False
            print "No IN ENDPOINT"
            print e

    def convert_uint8_to_string(self, _uint8_list):
        i = 0
        _string = ""
        while _uint8_list[i] != 0:
            _string += chr(_uint8_list[i])
            i+=1
        return _string

    def convert_int8_int16(self, _array):
        new_array = [0]*int(len(_array)/2)
        for i in range(int(len(_array)/2)):
            new_array[i] = _array.pop(0)*256 + _array.pop(0)
        return new_array

def make_x_line(start, end, inc):
    print "MAKE X LINE IS A HACK FIX    "
    i = start
    line = []
    while i < end:
        line.append(i - 1024)
        i += inc

    line.append(i - 1024)

    while i > start:
        line.append(i - 1024)
        i -= inc

    return line
