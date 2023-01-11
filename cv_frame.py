# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike
# 3.0 (CC BY-SA 3.0 US) License

""" tkinter frame to hold all buttons and plotting area for cyclic voltammetry experiments
"""
# standard libraries
import logging
import time
import tkinter.font
from tkinter import filedialog
import tkinter as tk
from tkinter import ttk
import unittest
from unittest import mock
# local files
import change_toplevel as change_top
import make_voltage_lines
import properties
import pyplot_data_class as data_class
import tkinter_pyplot

__author__ = 'Kyle Vitautas Lopin'

OPTIONS_BACKGROUND = 'LightCyan4'

COMPLETE_MESSAGE = "Done"
USB_IN_BYTE_SIZE = 64
FAIL_COUNT_THRESHOLD = 2
FAILURE_DELAY = 500


class CVFrame(ttk.Frame):
    """
    Frame to hold all the widgets and information to perform
    cyclic voltammetry experiments
    """

    def __init__(self, master, parent_notebook, graph_properties, bg=OPTIONS_BACKGROUND,
                 initialize=True):
        """ Make a ttk frame to hold all the info for cyclic voltammetry, frame
        is split in 2, one for graph area and another for the buttons
        :param master: tk.Tk overall master program
        :param parent_notebook: ttk.Notebook that this frame is embedded in
        :param graph_properties (graph_properties.GraphProps): properties for the graph
        :param bg: color to make the background frame
        """
        ttk.Frame.__init__(self, parent_notebook)
        self.master = master
        # TODO: put device_params and graph params all in 1 place
        self.settings = master.device_params.cv_settings
        print(f"settings: {self.settings}")
        self.data = data_class.PyplotData()
        self.graph = self.make_graph_area(master, graph_properties)  # make graph
        self.graph.pack(side='left', expand=True, fill=tk.BOTH)
        options_frame = tk.Frame(self, bg=bg, bd=3)
        options_frame.pack(side='left', fill=tk.BOTH)
        buttons_frame = tk.Frame(options_frame)
        buttons_frame.pack(side='bottom', fill=tk.X)
        # assign device to special handler for CV protocols
        self.device = self.USBHandler(self.graph, master.device, master, self.data)
        # make area to show the CV settings with a custom class
        self.cv_settings_frame = self.CVSettingDisplay(master, options_frame,
                                                       self.graph, master.device_params,
                                                       self.device)
        self.cv_settings_frame.pack(side="top", fill=tk.X)
        # initialize the device so the user can hit the run button
        if initialize:
            time.sleep(0.4)  # give time for the calibration data to be processed
            self.device.send_cv_parameters()
            time.sleep(0.1)
            master.device.usb_write("L|3")
            time.sleep(0.1)
        # make the buttons the user can use in the CV experiments
        # make a button to run a cyclic voltammetry scan
        self.run_button = tk.Button(
            buttons_frame, text="Run CV Scan",
            command=lambda: self.device.run_scan(self.graph,
                                                 self.run_button))
        self.run_button.pack(side='bottom', fill=tk.BOTH)
        # use a separate function to make the generic buttons
        # that don't need to be bound to self
        self.make_cv_buttons(buttons_frame, self.graph)

    def make_graph_area(self, master, graph_props):
        """ Make the graph area to display the cyclic voltammetry data.
        Use matplotlib if it is available or else plot in a tk Canvas
        TODO: add canvas option
        :param master: tk.Tk overall master of the program
        :param graph_props: dictionary fo properties on how the graph looks
        :return: the graph object, currently a PyplotEmbed class from tkinter_pyplot
        """
        if check_display_type() == 'matplotlib':
            # current_lim = 1.2 * 1000. / master.device_params.adc_tia.tia_resistor
            current_lim = master.device_params.adc_tia.current_lims
            low_voltage = self.settings.low_voltage
            high_voltage = self.settings.high_voltage
            graph = tkinter_pyplot.PyplotEmbed(master.frames[0],
                                               # frame to put the toolbar in NOTE: hack, fix this
                                               graph_props.cv_plot,
                                               self,
                                               current_lim, low_voltage, high_voltage)
        else:
            # TODO: implement for canvas
            raise NotImplementedError
        return graph

    def make_cv_buttons(self, _frame, cv_graph):
        """ Make and pack all the buttons needed to perform cyclic voltammetry.  These are
        all the options the user can use, except for what the waveform looks like
        (which is made in the make_cv_settings_display)
        :param _frame: tk frame to make all the buttons in
        :param cv_graph: graph where the cyclic voltammetry data will be displayed in
        (needed to put in the button function calls)
        :param device: USBHandler class in this file
        """
        # Make a button to allow the user to export the data
        tk.Button(_frame,
                  text="Save data",
                  command=self.save_all_data).pack(side='bottom', fill=tk.BOTH)

        # make button to change data labels
        tk.Button(_frame,
                  text="Change data style",
                  command=self.change_data_labels).pack(side='bottom', fill=tk.BOTH)

        # make a button to delete some data
        tk.Button(_frame,
                  text="Delete Data",
                  command=self.user_select_delete_some_data).pack(side='bottom',
                                                                  fill=tk.BOTH)

        # make a button to allow the user to view the toolbar
        toolbar_button = tk.Button(_frame,
                                   text="Add toolbar",
                                   command=cv_graph.toolbar_toggle)
        toolbar_button.pack(side='bottom', fill=tk.BOTH)
        # tk.Button(_frame,
        #           text="Read Message",
        #           command=lambda: self.print_usb_message(device)).pack(side='bottom',
        #                                                                fill=tk.BOTH)
        # experimental button to try chronoamperometry experiments
        # tk.Button(_frame,
        #           text="Chronoamp",
        #           command=lambda: self.chrono_hack(device)).pack(side='bottom',
        #                                                          fill=tk.BOTH)

    def chrono_hack(self, device):
        """ Hack to get a chronoamperometry experiment to run, inactivate the
        button when released
        :param device: USBHandler to handle device communications
        """
        self.master.device.usb_write("Q|1024|1524|02399")
        device.params.cv_settings.delay_time = 5000
        device.run_chrono = True
        self.graph.resize_x(0, 4000)

    @staticmethod
    def print_usb_message(device):
        """ For developing, check if a message is waiting in the usb
        :param device:  usb device to read
        """
        print(device.usb_read_message())

    def change_data_labels(self):
        """ Call a toplevel to allow the user to change data labels in the legend
        """
        change_top.ChangeDataLegend(self, self.graph)

    def delete_some_data(self, list_of_index_to_delete):
        """ The user wants to delete some data traces
        :param list_of_index_to_delete: index of the data to delete
        """
        for index in reversed(list_of_index_to_delete):
            self.graph.delete_a_line(index)

    def save_all_data(self):
        """ Save all the data displayed, allow the user to choose the filename
        """
        logging.debug("saving all data")
        if self.data.index == 0:  # no data to save
            logging.info("No data to save")
            return

        # ask the user for a filename to save the data in
        _file = open_file('saveas')

        # Confirm that the user supplied a file
        if _file:
            self.data.save_all_data(_file, self.master.data_save_type)

    def delete_all_data(self):
        """ Clear all the lines in the graph and reset the data
        :return:
        """
        self.graph.delete_all_lines()
        self.data = data_class.PyplotData()

    def user_select_delete_some_data(self):
        """ The user wants to delete some data, call a top level to handle this
        """
        change_top.UserSelectDataDelete(self)

    def open_data(self, csv_reader_file, first_line):
        """ Open a csv file that has the data saved in it, in the same
        format as this program saves the data.
        NOTE:
        _data_hold - holds the data as its being pulled from the file with the structure
        _data_hold = [ [x-data-array], [y1-data-array], [y2-data-array], .., [yn-data] ]
        :param csv_reader_file: csv reader object with the data in it
        :param first_line: first line read from the csv reader
        """
        logging.debug("opening data in cv frame")
        _data_hold = []  # buffer to hold the data we read from the file

        for i in range(len(first_line)):
            _data_hold.append([])  # add a list to store the column data

        _ = csv_reader_file.next()  # dump the line with notes

        for row in csv_reader_file:
            for i, data in enumerate(row):
                _data_hold[i].append(float(data))
        # go through each data line and add it to self.data
        for i in range(1, len(first_line)):
            self.graph.update_data(_data_hold[0], _data_hold[i], label=first_line[i])

    def set_tia_current_lim(self, _value, current_limit):
        self.cv_settings_frame.set_current_var_str(_value)
        self.graph.resize_y(current_limit)

    class USBHandler(object):
        """ NOTE: self.device is the AMpUSB class and device.device is the pyUSB class
        """
        def __init__(self, graph, device, master, data):
            """ Class to handle all the usb calls to perform cyclic voltammetry experiments
            :param graph: tkinter_pyplot - graph the data is displayed in
            :param device: usb_comm.AmpUSB device to send calls with
            :param master: root tk.TK
            :param data: pyplot_data_class.PyplotData - class data is stored in
            """
            self.graph = graph
            self.device = device  # bind master device to self
            self.master = master
            self.data = data
            self.params = master.device_params
            self.settings = master.device_params.cv_settings
            self.usb_packet_count = 0  # how many usb reading to make
            self.run_chrono = False  # Hack for testing chrono amperometry experiments
            self.run_button = None  # placeholder, the first run will assign it

        def send_cv_parameters(self):
            """ Send the parameters that the amperometric device should use to perform a
            cyclic voltammetry sweep
            the data needed to calculate the values are
            device.params.low_cv_voltage which is the lowest voltage (in mV)
            device.params.high_cv_voltage which is the highest voltage (in mV)
            device.params.sweep_rate - the speed (in V/s) that the voltage should be
            changed

            Note: the values sending to the device have to be padded with 0's,
            so they are the proper size for the device to interpret

            :return: will update to the device.params the following values
            usb_packet_count; which is how many data packets to expect
            actual_low_volt the lowest voltage the device will give to the electrode,
            depending on the DAC used can be different from the user value
            actual_high_volt the highest voltage the device will give to the electrode
            """
            logging.debug("sending cv params here")
            # convert the values into the values the device needs
            # this part is done on the computer side to save MCU code length
            formatted_start_volt, start_dac_value = \
                self.format_voltage_with_gnd(self.settings.start_voltage)
            formatted_end_volt, end_dac_value = \
                self.format_voltage_with_gnd(self.settings.end_voltage)
            formatted_freq_divider, pwm_period = \
                    self.format_divider(self.settings.sweep_rate)

            self.params.PWM_period = pwm_period

            # figure out what voltage protocol to give the device
            sweep_type_to_send = self.settings.sweep_type[0] + \
                                 self.settings.sweep_start_type[0]

            if self.settings.use_swv:
                formatted_inc, increment = self.format_voltage(self.settings.swv_inc)
                formatted_swv_height, swv_height = \
                    self.format_voltage(self.settings.swv_height)
                #TODO: put all the different letter commands in seperate file
                to_amp_device = '|'.join(["G", formatted_start_volt, formatted_end_volt,
                                          formatted_inc, formatted_swv_height,
                                          formatted_freq_divider, sweep_type_to_send])
            else:
                # send those values to the device in the proper format for the PSoC
                to_amp_device = '|'.join(["S", formatted_start_volt,
                                          formatted_end_volt, formatted_freq_divider,
                                          sweep_type_to_send])
                increment = 1
            print(end_dac_value, start_dac_value, increment)
            # save how many data packets should be received back from the usb
            packet_count = ((2 * abs(end_dac_value - start_dac_value + 1) / increment)
                            / (float(USB_IN_BYTE_SIZE) / 2.0))  # data is 2 bytes long

            # round up the packet count
            self.usb_packet_count = int(packet_count) + \
                                    (packet_count % USB_IN_BYTE_SIZE > 0)
            # calculate what the actual voltage the device will make.
            # This might be slightly different from the user input because of the
            # VDAC's resolution
            # TODO: figure out if this is working
            self.params.actual_low_volt = (- start_dac_value + start_dac_value
                                           % self.params.dac.voltage_step_size)
            time.sleep(0.5)
            self.device.usb_write(to_amp_device)
            time.sleep(0.01)
            # Write to the timing PWM compare register so the dac adc timing is correct
            compare_value = pwm_period / 2
            print("test2")
            self.device.write_timer_compare(compare_value)
            return 1

        def update_adc_setting(self):
            pass

        def run_scan(self, canvas, run_button, _delay=None):
            """ This will run a cyclic voltammetry scan. To do this it follows the steps
            1) sent 'R' to the microcontroller to run the scan and collect the data
            2) wait for the scan to run and poll the amperometry device to see
            if its ready for data
            3) Check if the device is done by receiving the correct message back
            4) sent 'EX' to the device, this make the amperometry device export
            the data in chunks (size defined in USB_IN_BYTE_SIZE (IN, as 'in' the
            computer) from the channel number described use in X.
            NOTE: the X is a string of an int so '0', '1', '2', or '3' works
            5) read the IN_ENDPOINT until all the data is sent to this program

            :param canvas: canvas to display data on
            :param run_button: run button that was pressed to start the scan
            :param _delay: int
            :return: binds the data to the master instead of returning anything
            """
            if self.device.last_experiment != "CV":  # the look-up table is not correct
                self.send_cv_parameters()
                self.device.set_last_run = "CV"
            # bind button to self, so it can be put active again
            self.run_button = run_button
            # inactive the button so the user can't hit it twice
            self.run_button.config(state='disabled')
            self.device.usb_write('R')  # step 1
            if self.device.working:
                logging.debug("device reading")
                # amount of time to wait for the data to be collected before getting it
                # give a 200 ms buffer to the calculated delay time

                if not _delay:
                    _delay = int(200 + self.params.cv_settings.delay_time)
                # step 2
                self.master.after(int(_delay), lambda: self.run_scan_continue(canvas))
            else:
                logging.debug("Couldn't find out endpoint to send message to run")
                # master.attempt_reconnection()

        def run_scan_continue(self, canvas, fail_count=0):
            """ The callback for run_scan.  This is called after the device
            should be done with the scan and is ready to export the data.
            The parts of the run cyclic voltammetry scan this functions run
            is part 3-5 listed in run_scan.
            param canvas: the widget that is called to display the data
            param fail_count: int, running count of how many attempts have been tried
            """
            check_message = self.device.usb_read_message()  # step 3
            print(f"got check message: {check_message}")
            if check_message == COMPLETE_MESSAGE:
                self.get_and_display_data(canvas)
            else:
                # wait a little longer and retry
                if fail_count < FAIL_COUNT_THRESHOLD:  # retry step 2
                    self.master.after(FAILURE_DELAY,
                                      lambda: self.run_scan_continue(canvas,
                                                                     fail_count + 1))
                logging.error("Failed to run the scan")

        def get_and_display_data(self, canvas, _channel=None):
            """ Get the data from the device and display it on the pyplot display
            :param canvas: where the data is to be displayed
            :param _channel: which adc channel to read
            """
            if not _channel:
                # if no channel sent, use the one saved in parameters dict
                _channel = self.params.adc_tia.adc_channel

            # the correct complete message was received so attempt to collect the data
            self.device.usb_write('E' + str(_channel))  # step 4

            # Get the raw data from the ADC.
            # this has to be modified to get the actual current values
            if self.run_chrono:
                self.usb_packet_count = 125
            raw_data = self.device.get_data(self.usb_packet_count)
            print(f'raw data got {self.usb_packet_count} packets')
            print(f"raw data: {raw_data}")
            raw_data.pop(0)
            self.run_button.config(state='active')
            if not raw_data:  # if something is wrong just return
                return
            # call function to convert the raw ADC values into the current that passed
            # through the working electrode
            self.data = self.device.process_data(raw_data)  # bind data to cv_frame master
            # print("get and display data: ", self.params.cv_settings.sweep_type)
            # if self.params.cv_settings.sweep_type == "DPV":
            #     # hack the data
            #     print(self.data)
            #     index = 0
            #     new_data = []
            #     while index <= len(self.data):
            #         new_data.append(self.data[index]-self.data[index+1])
            #         print('new data: ', new_data)
            #     self.data = new_data

            # make the voltages for the x-axis that correspond to the currents read

            x_line = make_voltage_lines.make_voltage_profile(
                self.params.cv_settings.start_voltage, self.params.cv_settings.end_voltage,
                self.params.dac.voltage_step_size, self.params.cv_settings.sweep_type,
                self.params.cv_settings.sweep_start_type, self.params.asv_settings.pulse_inc)
            if self.run_chrono:  # HACK to test chronoamp experiments
                x_line = range(4001)
            # Send data to the canvas where it will be saved and displayed
            canvas.update_data(x_line, self.data, raw_data)  # send raw data for testing purposes

        def format_divider(self, _sweep_rate):
            """ Take in the users desired sweet rate and convert it to the number needed to input
            into the PWM used to set the time between the interrupts that change the dac values
            (_sweep_rate * 1000) is used to convert the sweep rate from V/s to mV/s
            :param _sweep_rate: the users desired sweep rate
            :return: integer that is to be put into the interrupt PWM timer that's padded with
            zeros to be 5 integers long to properly send it to the device
            """
            clk_freq = self.params.clk_freq_isr_pwm
            cv_params = self.params.cv_settings
            if cv_params.use_swv:
                # use 2000 in denominator to convert from ms to secs and change the
                # dac twice during each step for the square wave
                raw_divider = int(clk_freq / (2000 / cv_params.swv_period)) - 1
            else:
                # take the clock frequency that is driving the PWM and divide it by the number of
                # voltage steps per second: this is how many clk ticks between each interrupt
                raw_divider = int(round(clk_freq /
                                        (_sweep_rate * 1000 / self.params.dac.voltage_step_size)) - 1)
            return '{0:05d}'.format(raw_divider), raw_divider

        def format_voltage(self, _in_volts):
            """ Takes in the voltage (in milli volts) the user wants to apply to step the electrode
            for the pulse voltammetry techniques

            :param _in_volts: user desired electrode voltage **step** value in milli volts
            :return: integer that is the dac is to be stepped with, padded with zeros to be 4
            values long to be transmitted to the device
            """
            dac_value = self.params.dac.get_dac_count(_in_volts)

            if dac_value == 0:
                dac_value = 1
            print(f"formated dac to {dac_value}, from {_in_volts}")
            return '{0:04d}'.format(dac_value), dac_value

        def format_voltage_with_gnd(self, _in_volts):
            """ Takes in the voltage (in millivolts) the user wants to apply to the electrode and
            convert it to the integer that represent the value to be put into the dac
            :param _in_volts: user desired electrode voltage value in millivolts
            :return: integer that is the value to be put into the dac, padded with zeros to be 4
            values long to be transmitted to the device
            """
            # shift the user's voltage by the amount of the virtual ground
            input_voltage = self.params.virtual_ground_shift - _in_volts  # mV
            # get the value needed (number of increments needed to get desired voltage, ex. desire
            # 500mV with 1 mV increments then put in 500) to put into the dac and pad it with zeros
            dac_value = self.params.dac.get_dac_count(input_voltage)
            return '{0:04d}'.format(dac_value), dac_value

        def set_adc_tia(self, *args):
            self.device.set_adc_tia(*args)

        def usb_read_message(self):
            """ For development, check if device wants to speak """
            return self.device.usb_read_message()

    class CVSettingDisplay(tk.Frame):
        """ Class that makes a frame displaying the settings for a cyclic voltammetry experiment
        """
        def __init__(self, _master, _frame, graph, device_params, device):
            """
            :param _master: the root application
            :param _frame: the tk.Frame this frame is placed in
            :param graph:  the pyplot graph area
            :param device_params:  device parameters
            """
            tk.Frame.__init__(self, master=_frame)
            # Make String variables to hold the strings that state the parameters; bind them to self
            # so they are easy to pass between functions
            self.start_voltage_var_str = tk.StringVar()
            self.end_voltage_var_str = tk.StringVar()
            self.freq_var_str = tk.StringVar()
            self.current_var_str = tk.StringVar()

            self.swv_pulse_var_str = tk.StringVar()
            self.swv_inc_var_str = tk.StringVar()
            self.swv_period_var_str = tk.StringVar()

            self.device = device

            tk.Label(self, text="Cyclic Voltammetry settings:"
                     ).pack(side='top', pady=5)
            # Make Labels to display the String variables
            for var_str in [self.start_voltage_var_str, self.end_voltage_var_str,
                            self.freq_var_str, self.current_var_str]:
                tk.Label(textvariable=var_str, master=self).pack(side='top')

            ttk.Separator(self, orient=tk.HORIZONTAL).pack(side=tk.TOP, pady=5, fill=tk.X)

            # make dpv frame
            swv_frame = tk.Frame(self)
            tk.Label(swv_frame, text="Square Wave\nVoltammetry settings:"
                     ).pack(side='top', pady=5)
            for var_str in [self.swv_pulse_var_str, self.swv_inc_var_str,
                            self.swv_period_var_str]:
                tk.Label(swv_frame, textvariable=var_str).pack(side='top')

            swv_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

            # make a button to change the cyclic voltammetry setting
            tk.Button(self,
                      text="Change Settings",
                      command=lambda: self.change_cv_settings(_master, graph)).pack(side='bottom',
                                                                                    fill=tk.BOTH)

            self.cv_label_update(device_params)

        def set_current_var_str(self, tia_value):
            self.current_var_str.set(u'Current range: {0}'
                                     .format(tia_value))

        def cv_label_update(self, device_params):
            """ Update the user's display of what the parameters of the cyclic
            voltammetry scan are set to
            :param device_params: device settings from properties.DeviceParameters
            """
            self.start_voltage_var_str.set(f'Start voltage: '
                                           f'{device_params.cv_settings.start_voltage} mV')
            self.end_voltage_var_str.set(f'End voltage: '
                                         f"{device_params.cv_settings.end_voltage} mV")
            self.freq_var_str.set(f"Sweep rate: "
                                  f"{device_params.cv_settings.sweep_rate} V/s")
            self.current_var_str.set(f'Current range: \u00B1 '
                                     f'{device_params.adc_tia.current_lims:.1f} \u00B5A')

            self.swv_pulse_var_str.set(f"Pulse height: "
                                       f"{device_params.cv_settings.swv_height} mv")
            self.swv_inc_var_str.set(f"Step Increment: "
                                     f"{device_params.cv_settings.swv_inc} mv")
            self.swv_period_var_str.set(f"Puulse Period: "
                                        f"{device_params.cv_settings.swv_period} ms")

        def change_cv_settings(self, master, graph):
            """ Make a dialog window to allow the user to change the cyclic voltammetry sweep
            parameters. For now, this just calls the SettingChanges class in change_toplevel
            note that self here is the main window
            :param master: root tkinter application
            :param graph: graph where the data is displayed (needed so that the routine can
            change the axis scales)
            """
            change_top.CVSettingChanges(self, master, graph,
                                        self.device)  # bind toplevel to the root tk.tk


def open_file(_type, tkFileDialog=None):
    """ Make a method to return an open file or a file name depending on the type asked for
    :param _type: what type of file dialog to use
    :return: the filename
    """
    # Make the options for the save file dialog box for the user
    file_opt = options = {}
    options['defaultextension'] = ".csv"
    options['filetypes'] = [('All files', '*.*'), ("Comma separate values", "*.csv")]
    if _type == 'saveas':
        # Ask the user what name to save the file as
        _file = filedialog.asksaveasfile(mode='w', **file_opt)
    elif _type == 'open':
        _filename = filedialog.askopenfilename(**file_opt)
        return _filename
    return _file


def check_display_type():
    """ Check if matplotlib graph can be used,
    :return: type that can be used to make display graph, matplotlib or canvas as a string
    """
    try:
        import matplotlib
        import matplotlib.pyplot
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        return "matplotlib"
    except ImportError:
        return "canvas"
