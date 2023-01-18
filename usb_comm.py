# Copyright (c) 2015-2023 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" Communicate with a USB device for a PSoC electrochemical device
"""
# standard libraries
import logging
import struct
import time

# installed libraries
import serial
import serial.tools.list_ports

# local files
import cv_frame
import change_toplevel as toplevel
import globals as _globals

# import toplevels

__author__ = 'Kyle V. Lopin'

USB_IN_BYTE_SIZE = 64
USB_TERMINATION_SIGNAL = 255 * 257
USB_OUT_BYTE_SIZE = 32
TEST_MESSAGE = "USB Test"
TEST_MESSAGES = {"USB Test": "base",
                 "USB Test - 059": "kit-059",
                 "USB Test - v04": "v04",
                 b"Naresuan Potentiostat": "v1.5"}
PRODUCT_STRING = "Naresuan Potentiostat"
RUNNING_DELAY = 3000
FAIL_COUNT_THRESHOLD = 2
FAILURE_DELAY = 500
COMPLETE_MESSAGE = "Done"
TERMINATION_CODE = -16384

USB_VENDOR_ID = 0x1D50
USB_PRODUCT_ID = 0x6128
BAUD_RATE = 115200

# device parameter list
TIA_RESISTOR_VALUES = [20, 30, 40, 80, 120, 250, 500, 1000]
CURRENT_OPTION_LIST = _globals.CURRENT_OPTION_LIST
MAX_TIA_SETTING = 7

# CURRENT_LIMIT_VALUES = [50, 33, 25, 12.5, 8.4, 4, 2, 1, 0.5, 0.25, 0.125]
# CURRENT_LIMIT_VALUES = [100, 66, 50, 25, 16, 8, 4, 2, 1, 0.5, 0.25]
CURRENT_LIMIT_VALUES = _globals.CURRENT_LIMIT_VALUES


class AmpUsb(object):
    """
    Generic class that deals with the usb communication microcontroller, uses a helper function
    to deal with the specifics of how data should be formatted, timing, etc.
    Idea is to use this as a general class that can be moved to new projects while the helper
    function handles the specifics
    """

    def __init__(self, _master, _device_params, vendor_id=USB_VENDOR_ID, product_id=USB_PRODUCT_ID):
        """ Initialize a communication channel to a PSoC with a USBUART module.

        :param _master: the master program that is using the usb
        :param _device_params: parameters needed for the device to work properly, from the
        properties file
        :param vendor_id: the USB vendor id, used to identify the proper device connected to
        the computer
        :param product_id: the USB product id
        :return:
        """
        # attempt to connect the device
        self.connected = False
        self.device_params = _device_params
        self.master = _master
        self.device_type = None
        self.last_experiment = "CV"  # keep track of what type of experiment was run last, CV or ASV
        self.samples_to_smooth = 1  # TODO: python 3 use properties to limit its value
        logging.info("attempting connection")
        self.device = SerialComm()

        # If it was found to be working properly initialize the device
        if self.device.connected:
            self.connected = True
            print("Initializing run parameters")
            logging.info("Initializing run parameters")

            self.find_voltage_source()
            time.sleep(0.5)
            # self.send_cv_parameters()
            self.usb_write("A|1|0|0|F|2")  # set the TIA resistor to 20k ohm on startup
            self.calibrate()  # calibrate the TIA settings

    def connection_test(self, fails=0):
        """ The device can be found but still not respond correctly, this is to test the connection
        by sending a message and check if the amperometry responses with the proper message
        """
        # clear the IN BUFFER of the device incase it was stopped or the program was restarted
        self.device.clear_in_buffer()
        self.device.connected = True  # for usb_write to work it needs to be in connected state
        self.usb_write("I")

        received_message = self.usb_read_message()
        # time.sleep(0.5)
        # received_message = self.usb_read_message()
        if received_message in TEST_MESSAGES:
            # self.device_type = test_messages[received_message]
            self.set_device_type(TEST_MESSAGES[received_message])
            logging.info("Device type %s selected", self.device_type)
            return True
        else:
            logging.info("test failed")
            fails = fails + 1
            if fails > 4:

                self.device_type = None
                self.master.failed_connection()
                self.attempt_reconnection()
                return False
            else:
                self.connection_test(fails)

    def set_device_type(self, _device_type):
        """
        Set what version of the device is attached
        :param _device_type: sting of the version of the device attached
        """
        self.device_type = _device_type

    def find_voltage_source(self):
        """ Test the device to see if it is using the 8-bit VDAC or the 12-bit DVDAC
        :return: None, bind voltage source to self.device_params.dac
        """
        self.usb_write("VR")
        time.sleep(0.2)
        source_input = self.usb_read_data(2)
        print(f"source input: {source_input}")
        if not source_input:
            return
        if source_input[1] == 0:
            toplevel.VoltageSourceSelect(self.master, source_input[1])
        elif source_input[1] == 1:
            logging.info("VDAC is set in device")
            self.master.set_voltage_source_label(
                "Voltage source: 8-bit VDAC (no capacitor installed)")
            self.device_params.dac.set_source("8-bit DAC")
        elif source_input[1] == 2:
            logging.info("DVDAC is voltage source")
            self.master.set_voltage_source_label(
                "Voltage source: Dithering VDAC (capacitor installed)")
            self.device_params.dac.set_source("DVDAC")
        else:
            raise IOError

    def select_voltage_source(self, source):
        """ Select which voltage source to use in the device
        :param source:
        :return:
        """
        logging.info('selecting source: {0}'.format(source))
        # if source == self.device_params.dac.source:
        # return  # selected source that is already chosen
        if source == "8-bit DAC":
            # tell the device to set the voltage source as the DVDAC
            self.usb_write("VS1")
            # set the device dac attribute to VDAC
            self.master.set_voltage_source_label(
                "Voltage source: 8-bit VDAC (no capacitor installed)")
            self.device_params.dac.set_source(source)
            # resend the CV prameters with new numbers because the dac changes so the
            self.send_cv_parameters()
        elif source == "DVDAC":
            # tell the device to set the voltage source as the DVDAC
            self.usb_write("VS2")
            # set the device dac attribute to DVDAC
            self.device_params.dac.set_source("DVDAC")
            self.master.set_voltage_source_label(
                "Voltage source: Dithering VDAC (capacitor installed)")
            # resend the CV prameters with new numbers because the dac changes so the
            self.send_cv_parameters()

    def start_hardware(self):
        self.usb_write('H')

    def send_cv_parameters(self):
        """ Make it easier to update the Cyclic Voltammetry frames, send it to the cv usb handler
        """
        self.master.cv.device.send_cv_parameters()

    def write_timer_compare(self, value):
        """ Write to the device to update the PWM compare value to set when the current is measured
        :param value: the value to write in the timer compare
        """
        self.master.device_params.PWM_compare = int(value)
        _formatted_value = '{0:05d}'.format(int(value))
        self.usb_write('C|' + _formatted_value)

    def get_data(self, number_packets=None):
        """ Get the raw adc counts from the device

        :return: a list of adc counts
        """
        full_array = []  # all data will be stored in here
        # calculate how many packets of data to get from the amp device the usb_count param is
        # how many data points there are (+1 us for the 0xC000 sent at the end)
        # packet_size / 2 is because the data is converted to uint8 and minus 1 for 0 indexing
        # from the uint16 it is acquired in
        if not number_packets:
            number_packets = ((self.device_params.usb_count + 1) / (USB_IN_BYTE_SIZE / 2) - 1)

        count = 0
        while number_packets + 1 > count:
            try:
                data_array = self.device.read_data(USB_IN_BYTE_SIZE, 'int16')
                print(f"got usb data: {data_array}, asked for size: {USB_IN_BYTE_SIZE}")
                full_array.extend(data_array)
                if TERMINATION_CODE in data_array:
                    # TODO: Delete the last point that was the TERMINATION code, or find its index?
                    print(f"full array: {full_array}")
                    return full_array[:-1]
                count += 1
            except Exception as _error:
                print(f"Got error reading data: {_error}")
            if self.samples_to_smooth > 1:
                return rolling_mean(data_array, self.samples_to_smooth)
        return full_array

    def process_data(self, _raw_data):
        """ Take in the raw adc counts and output the corresponding current values
        TODO: should put this somewhere, if the amp_frame, cv_frame get a parent class that
        is a good place to put this
        :param device: the device that has the data_save_type and TIA_resistor values to
        properly process the data
        :param _raw_data: raw adc count numbers
        :return: current (micro amperes) values of the adc values
        """
        if self.master.data_save_type == "Converted":
            logging.debug("Converting data")
            # Convert the adc number to the current
            count_to_current = self.device_params.adc_tia.counts_to_current
            shift = self.device_params.adc_tia.shift  # the measured voltage shift of the adc/tia
            logging.debug("count to current: %4.4f", count_to_current)
            current = [(x - shift) * count_to_current for x in _raw_data]

            return current
        elif self.master.data_save_type == "Raw Counts":
            logging.debug("sending raw data back")
            return _raw_data

    def reset(self):
        self.usb_write('X')

    def calibrate(self):
        """ Start calibrating the ADC - TIA module by first sending the proper command to the
        device for it to measure the data, then call _calibrate_data to get the data and send
        it to the adc_tia to be processed
        """
        print(f"calibrating data, connected: {self.connected}")
        if self.connected:
            self.usb_write('B')
            print("setting after")
            # self.master.after(400, func=self._calibrate_data)
            time.sleep(2)  # the after is not working for some reason, fix this when threading is put in
            self._calibrate_data()
            print("done setting after")
            logging.debug("running calibration")

    def _calibrate_data(self):
        """ To be used after the command for the device to measure the calibration data has been
        sent.  Gets the data from the device and sends it to the adc_tia module to be processed
        """
        raw_data = self.usb_read_data(20, encoding='int16')
        print(f"raw data: {raw_data}")
        logging.debug("Calibration data: {0}".format(raw_data))
        print("Calibration data: {0}".format(raw_data))
        self.device_params.adc_tia.calibrate(raw_data)

    def get_export_channel(self, channel=None):
        """ ONLY USED FOR DEVELOPMENT
        get the data from the device from the specified channel
        :param channel: int, channel number to get, the device may have multiple adc buffer arrays

        """
        canvas = self.master.preview_graph
        #TODO fix this
        print("TODO update this")

    def get_look_up_table(self):
        self.usb_write('l|1000')
        look_up_table = self.usb_read_data(2000, encoding='int16')
        print(f"look up table: {look_up_table}")
        return look_up_table

    def set_electrode_config(self, num_electrodes):
        """ The PSoC can perform either 2 electrode or 3 electrode measurements, send the device the
        command 'L|X' to change its config where X is either 2 or 3 for the # of electrodes to use
        :param num_electrodes: int, number of electrodes the user wants to use
        """
        self.usb_write('L|' + str(num_electrodes))  # tell the device
        # update the gui
        self.master.electrode_config_label.set("{0} electrode configuration".format(num_electrodes))

    def set_anode_voltage(self, voltage):
        logging.debug("setting anode voltage to {0} mV".format(voltage))
        formatted_voltage_to_send = self.device_params.dac.get_dac_count(voltage,
                                                                         actual=True)
        # voltage_str = str(formatted_voltage_to_send).zfill(4)
        self.usb_write("D|{0:04d}".format(formatted_voltage_to_send))

    def short_tia_resistor(self):
        """ Short the TIA resistor so the working electrode can short any current """
        logging.debug("Shorting TIA resistor")
        self.usb_write('s')

    def stop_shorting_tia_resistor(self):
        """ Stop shorting the TIA resistor """
        logging.debug("Stop shorting tia resistor")
        self.usb_write('d')

    def set_custom_resistor_channel(self, channel):
        """ Incase the currents are too large and a smaller external TIA resistor is needed
        NOTE: NOT TESTED YET
        NOTE: if a large current is used the parasitic resistance of the analog routing of
        the virtual ground will cause the working electrode voltage to shift significantly
        :param channel:
        """
        self.usb_write("A|2|7|0|T|" + channel)
        # set the adc configuration to 2 for a smaller (1024 mV) Vref,set the TIA resistor to
        # 1M (with the 7) to minimize the change it will have on the equivalent resistance

    def set_adc_tia(self, current_range_index):
        """ The user selected a different current range, tell the device to change the
        impedance of the transimpedance amplifier, update the parameters and all the current
        ranges displayed in the frames
        :param current_range_index: int - index of the current range from the global.py CURRENT_OPTION_LIST
        """
        adc_config, tia_position, adc_gain = get_tia_settings(current_range_index)
        logging.debug('setting tia/adc to position: %s, gain: %s, config: %s', tia_position, adc_gain, adc_config)
        self.usb_write("A|{0}|{1}|{2}|F|0".format(adc_config, tia_position, adc_gain))  # update device
        self.device_params.adc_tia.set_value(TIA_RESISTOR_VALUES[tia_position],
                                             adc_gain, adc_config, current_range_index)  # update params
        logging.debug("TIA resistor changed to: %s", self.device_params.adc_tia.tia_resistor)
        # change current range and current range string in all frames
        current_limit = CURRENT_LIMIT_VALUES[current_range_index]
        self.master.update_current_range(CURRENT_OPTION_LIST[current_range_index], current_limit)
        # run the calibration routine to update the adc counts to current value
        self.calibrate()

    def format_divider(self, _sweep_rate):
        """ Take in the users desired sweet rate and convert it to the number needed to input
        into the PWM used to set the time between the interrupts that change the dac values
        (_sweep_rate * 1000) is used to convert the sweep rate from V/s to mV/s
        :param _sweep_rate: the users desired sweep rate
        :return: integer that is to be put into the interrupt PWM timer that's padded with zeros to
        be 5 integers long to properly send it to the device
        """
        clk_freq = self.device_params.clk_freq_isr_pwm
        # take the clock frequency that is driving the PWM and divide it by the number of voltage
        # steps per second: this is how many clk ticks between each interrupt
        raw_divider = int(
            round(clk_freq / (_sweep_rate * 1000 / self.device_params.dac.voltage_step_size)) - 1)
        return '{0:05d}'.format(raw_divider), raw_divider

    def format_voltage(self, _in_volts):
        """ Takes in the voltage (in millivolts) the user wants to apply to the electrode and
        convert it to the integer that represent the value to be put into the pidac
        :param _in_volts: user desired electrode voltage value in millivolts
        :return: integer that is the value to be put into the pidac, padded with zeros to be 4
        values long to be transmitted to the device
        """
        # shift the user's voltage by the amount of the virtual ground
        input_voltage = self.device_params.virtual_ground_shift + _in_volts  # mV

        # get the value needed (number of increments needed to get desired voltage, ex. desire
        # 500mV with 1 mV increments then put in 500) to put into the dac and pad it with zeros
        dac_value = self.device_params.dac.get_dac_count(input_voltage)
        return '{0:04d}'.format(dac_value), dac_value

    def usb_write(self, message):
        """ Write the message to the device
        :param message: message, in bytes, to send
        """
        if not self.device.connected:
            logging.info("Device not connected")
            self.master.failed_connection()
        else:
            logging.debug("writing message: %s", message)
            try:
                self.device.write_data(message)
            except Exception as error:
                print(f"Error in writing to device: {error}")
                logging.debug(f"Error in writing to device: {error}")
                self.connection_test()

    def usb_read_data(self, _size: int = USB_IN_BYTE_SIZE, encoding: str=None) -> list:
        """
        Abstraction layer of reading from an USB port.
        #TODO: change this to get data when SerialComm is set up as a separate thread

        Args:
            _size (int): size of the data packet to read
            encoding (str): which encoding to use, can be 'int16', or 'str', None defaults to bytes

        Returns: list of data read in the format specified by encoding, else a bytestring is returned

        """
        print("reading data", self.connected)
        if not self.connected:
            logging.info("not working")
            return None
        try:
            return self.device.read_data(_size, encoding=encoding)
        except Exception as error:
            logging.error("Failed read")
            self.connection_test()
            return None

    def usb_read_message_depr(self, _size=USB_IN_BYTE_SIZE):
        """ Alias of usb_read_data for now
        TODO: remove this
        :return: data from the device
        """
        message = self.usb_read_data(_size, encoding='str')
        print(f"usb read message: {message}")
        return message

    def attempt_reconnection(self):
        """ If the device stops working try to reconnect
        NOTE :  NOT WORKING
        TODO: Fix this, though it's mostly working now try a software reset of the device
        """
        logging.debug("usb_comm reconnection protocol")
        self.usb_read_data()  # try to clear the data that might be in the queue
        self.serial_connect()

    def set_last_run(self, run_type):
        self.last_experiment = run_type

    def get_and_display_data_from_export_channel(self, canvas, _channel=None):
        """ For developers to get data from the device.
        Write to the device to let it know to export the data to the computer then call the method
        get_data to get the data, then convert the data to current
        :param canvas: tkinter frame with pyplot canvas to plot to
        :param _channel: int of the adc channel to get from the device
        :return:
        """
        if not _channel:  # if no channel sent, use the one saved in parameters dict
            _channel = self.params.adc_channel

        # the correct complete message was received so attempt to collect the data
        self.usb_write('E'+str(_channel))  # step 4

        # Get the raw data from the ADC
        raw_data = self.get_data()
        if not raw_data:  # if something is wrong just return
            return
        # call function to convert the raw ADC values into the current that passed
        #  through the working electrode
        data = self.process_data(raw_data)

        self.master.current_data = data
        x_line = cv_frame.make_x_line(self.params.actual_low_volt,
                                      self.params.actual_high_volt,
                                      self.params.volt_increment)
        self.master.voltage_data = x_line

        # Send data to the canvas where it will be saved and displayed
        canvas.update_data(x_line, data, raw_data)


class SerialComm:
    def __init__(self):
        self.connected = False
        self.found = False
        self.device = self.auto_find_com_port()
        print(f"Done initializing SerialComm with state: {self.connected}")

    def auto_find_com_port(self):
        available_ports = serial.tools.list_ports
        for port in available_ports.comports():
            if PRODUCT_STRING == port.product:
                print("found device")
                self.found = True
                device = serial.Serial(port.device, BAUD_RATE, timeout=1.0)
                device.write(b"I")
                for i in range(3):
                    _input = device.readline()
                    if b"Naresuan Potentiostat" in _input:
                        self.connected = True
                        print("got device")
                        return device
        return None

    def clear_in_buffer(self):
        if self.device:
            self.device.reset_input_buffer()

    def read_data(self, data_length, encoding=None):
        data = self.device.read(data_length)  # type: bytes
        print(f"read byte data: {data}, lenght asked for: {data_length}")
        if encoding == 'int16':
            size = int(len(data)/2)  # may not be data_length ?
            converted_data = struct.unpack(f"{size}h", data)
            return list(converted_data)
        elif encoding == 'str':
            return data.decode("utf-8")
        elif encoding:  # exclude None
            raise Exception(f"Encoding: '{encoding}' not supported")
        return data

    def write_data(self, message):
        if self.connected:
            if type(message) is str:
                message = message.encode('utf-8')
            print(f"writing data: {message}")
            self.device.write(message)

    def poll_for_data(self):
        if self.device.in_waiting:
            return self.device.read_all()


def get_tia_settings(range_selected):
    # the current limit 100 uA was selected so set the adc Vref to +-2048 mV, TIA resistor to 20k, and adc gain to 1
    if range_selected == 0:
        return 1, 0, 0  # adc_config, TIA resistor value, adc gain
    adc_config = 2  # only the first settings uses the first adc config
    range_selected -= 1  # subtract 1 so the it now maps to the tia resistor setting
    if range_selected > MAX_TIA_SETTING:
        # the last 3 settings increase the adc gain setting
        adc_gain_setting = range_selected % MAX_TIA_SETTING
        # but leaves the TIA setting at the highest setting available
        tia_position = MAX_TIA_SETTING
    else:
        tia_position = range_selected  # the setting to send to the MCU is the same as the index
        adc_gain_setting = 0  # the gain setting is 0 for no gain on the adc
    return adc_config, tia_position, adc_gain_setting


def rolling_mean(array, number_points):
    new_array = []
    for i in range(number_points - 1):
        new_array.append(array[i])
    for i in range(number_points - 1, len(array)):
        new_array.append(float(sum(array[i - number_points + 1:i + 1])) / number_points)
    return new_array


def check_tia_changed22(old_settings, adc_config, adc_gain, tia_position):
    if (old_settings.adc_tia.tia_resistor != TIA_RESISTOR_VALUES[tia_position] or
                old_settings.adc_tia.adc_gain != 2 ** adc_gain or
                old_settings.adc_tia.adc_config != adc_config):
        return True
    return False
