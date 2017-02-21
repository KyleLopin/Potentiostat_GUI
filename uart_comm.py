# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" Communicate with a USB device for a PSoC electrochemical device through a usb-uart
"""

# standard libraries
import glob
import logging
import sys
import time
# installed libraries
import serial
# local files
import amp_usb_helper as usb_helper
import toplevels

__author__ = 'Kyle V. Lopin'

USB_TERMINATION_SIGNAL = 255 * 257
TEST_MESSAGE = "USB Test"
TEST_MESSAGES = {"USB Test": "base",
                 "USB Test - 059": "kit-059",
                 "USB Test - v04": "v04"}
RUNNING_DELAY = 3000
FAIL_COUNT_THRESHOLD = 2
FAILURE_DELAY = 500
COMPLETE_MESSAGE = "Done"
TERMINATION_CODE = -16384


class AmpUsb(object):
    def __init__(self, master, device_params, address=None, vendor_id=None, product_id=None):
        """
        Leave in vendor and product id to prevent the old code calls from throwing errors
        :param master:
        :param device_params:
        :param address:
        :param vendor_id:
        :param product_id:
        """

        self.found = False
        if not vendor_id:
            vendor_id = 0x04B4
        if not product_id:
            product_id = 0xE177

        self.device_params = device_params
        self.master = master
        self.device_type = None
        logging.info("attempting connection")

        self.device = self.connect_usb(address)

    def connect_usb(self, address):
        if not address:
            return self.autofind()

    def autofind(self):
        """

        list of ports is taken from
        http://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
        :return:
        """

        # get all the possible ports
        if sys.platform.startswith('win'):  # windows computer
            ports = ['COM%s' % (i + 1) for i in range(32)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            ports = glob.glob('dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):  # mac computer
            ports = glob.glob('dev/tty.*')
        else:
            raise EnvironmentError('Unsupported operating system')

        available_ports = []
        for port in ports:
            print port
            try:
                device = serial.Serial(port=port, write_timeout=0.5, inter_byte_timeout=0.1)
                device.write('I')
                bytes_to_read = device.inWaiting()
                print '1: ', bytes_to_read
                print '1: ', device.read(bytes_to_read)
            except (OSError, serial.SerialException) as error:  # port doesn't work
                print error
