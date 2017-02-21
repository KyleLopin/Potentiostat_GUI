# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" tkinter frame to hold all buttons and plotting area for cyclic voltammetry experiments
"""
# standard libraries
import logging
import time
import tkFileDialog
import Tkinter as tk
import ttk
# local files
import change_toplevel as change_top
import tkinter_pyplot

__author__ = 'Kyle Vitautas Lopin'

OPTIONS_BACKGROUND = 'LightCyan4'

COMPLETE_MESSAGE = "Done"
USB_IN_BYTE_SIZE = 64
FAIL_COUNT_THRESHOLD = 2
FAILURE_DELAY = 500

class CVFrame(ttk.Frame):
    """ Frame to hold all the widgets and information to perform cyclic voltammetry experiments
    """

    def __init__(self, master, parent_notebook, graph_properties):
        """ Make a ttk frame to hold all the info for cyclic voltammetry, frame is split in 2,
        for graph area and buttons
        :param master: tk.Tk overall master program
        :param parent_notebook: ttk.Notebook that this frame is embedded
        :param graph_properties: properties for the graph
        """
        ttk.Frame.__init__(self, parent_notebook)
        self.master = master
        self.graph = self.make_graph_area(master, graph_properties)
        self.graph.pack(side='left', expand=True, fill=tk.BOTH)
        options_frame = tk.Frame(self, bg=OPTIONS_BACKGROUND, bd=3)
        options_frame.pack(side='left', fill=tk.BOTH)
        buttons_frame = tk.Frame(options_frame)
        buttons_frame.pack(side='bottom', fill=tk.X)

        self.device = self.USBHandler(self.graph, master.device, master)
        self.cv_settings_frame = self.CVSettingDisplay(master, options_frame,
                                                       self.graph, master.device_params,
                                                       self.device)
        self.cv_settings_frame.pack(side="top", fill=tk.X)
        self.device.send_cv_parameters()
        # self.make_cv_buttons(buttons_frame, self.graph, master.device)
        self.make_cv_buttons(buttons_frame, self.graph, self.device)

    def make_graph_area(self, master, graph_props):
        """ Make the graph area to display the cyclic voltammetry data.  Use matplotlib if it is
        available or else plot in a tk Canvas
        TODO: add canvas option
        :param master: tk.Tk overall master of the program
        :param graph_props: dictionary fo properties on how the graph looks
        :return: the graph object, currently a PyplotEmbed class from tkinter_pyplot
        :::::::::::::::: UPdate when canvas is implemented
        """
        if check_display_type() == 'matplotlib':
            current_lim = 1.2 * 1000. / master.device_params.adc_tia.tia_resistor
            low_voltage = master.device_params.cv_settings.low_voltage
            high_voltage = master.device_params.cv_settings.high_voltage
            graph = tkinter_pyplot.PyplotEmbed(master,
                                               master.frames[1],
                                               # frame to put the toolbar in NOTE: hack, fix this
                                               graph_props.cv_plot,
                                               self,
                                               current_lim, low_voltage, high_voltage)
        else:
            graph = None  # TODO: implement for canvas
        return graph

    def make_cv_buttons(self, _frame, cv_graph, device):
        """ Make and pack all the buttons needed to perform cyclic voltammetry.  These are
        all the options but what the waveform looks like (which is made in the
        make_cv_settings_display)
        :param _frame: tk frame to make all the buttons in
        :param cv_graph: graph where the cyclic voltammetry data will be displayed in
        (needed to put in the button function calls)
        :param device: usb_comm AmpUsb device to send commands too
        """
        # make a button to run a cyclic voltammetry scan
        self.run_button = tk.Button(_frame, text="Run CV Scan",
                                    command=lambda: device.run_scan(cv_graph,
                                                                    self.run_button))
        self.run_button.pack(side='bottom', fill=tk.BOTH)

        # Make a button to allow the user to export the data
        tk.Button(_frame,
                  text="Save data",
                  command=self.save_all_data).pack(side='bottom', fill=tk.BOTH)

        # make button to change data labels
        tk.Button(_frame,
                  text="Change data style",
                  command=self.change_data_labels).pack(side='bottom', fill=tk.BOTH)

        # make a button to delete some of the data
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
        #           text="Calibrate",
        #           command=device.calibrate).pack(side='bottom',
        #                                          fill=tk.BOTH)
        # tk.Button(_frame,
        #           text="Read Message",
        #           command=lambda: self.print_usb_message(device)).pack(side='bottom',
        #                                                                fill=tk.BOTH)
        tk.Button(_frame,
                  text="Chronoamp",
                  command=lambda: self.chrono_hack(device)).pack(side='bottom',
                                                                 fill=tk.BOTH)

    def chrono_hack(self, device):
        self.master.device.usb_write("Q|1024|1524|02399")
        device.params.cv_settings.delay_time = 5000
        device.run_chrono = True
        self.graph.resize_x(0, 4000)

    def print_usb_message(self, device):
        """ For developing, check if a message is waiting in the usb
        :param device:  usb device to read
        """
        print device.usb_read_message(1)

    def change_data_labels(self):
        """ Call a toplevel to allow the user to change data labels in the legend
        """
        change_top.ChangeDataLegend(self.master, self.graph)

    def save_all_data(self):
        """ Save all the data displayed, allow the user to choose the filename
        """
        logging.debug("saving all data")
        if len(self.master.data.current_data) == 0:  # no data to save
            logging.info("No data to save")
            return

        # ask the user for a filename to save the data in
        _file = open_file('saveas')

        # Confirm that the user supplied a file
        if _file:
            self.master.data.save_all_data(_file, self.master.data_save_type)

    def user_select_delete_some_data(self):
        """ The user wants to delete some of the data, call a top level to handle this
        """
        change_top.UserSelectDataDelete(self)

    class USBHandler(object):
        """ NOTE: self.device is the AMpUSB class and device.device is the pyUSB class
        """

        def __init__(self, graph, device, master):
            self.graph = graph
            self.device = device  # bind master device to self
            self.master = master
            self.params = master.device_params
            self.settings = master.device_params.cv_settings
            self.usb_packet_count = 0
            self.run_chrono = False
            self.run_button = None  # placeholder, the first run will assign it

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
            # convert the values into the values the device needs
            # this part is done on the computer side to save MCU code length
            # minus sign is needed because the device sets the common electrode to the voltage and
            # assumes the working electrode is ground, but voltammetry has the voltage on the
            # working electrode compared to the common electrode
            formatted_low_volt, low_dac_value = \
                self.format_voltage(-self.settings.low_voltage)
            formatted_high_volt, high_dac_value = \
                self.format_voltage(-self.settings.high_voltage)
            formatted_freq_divider, pwm_period = \
                self.format_divider(self.settings.sweep_rate)

            self.params.PWM_period = pwm_period

            # send those values to the device in the proper format for the PSoC amperometry device
            to_amp_device = '|'.join(["S", formatted_low_volt,
                                      formatted_high_volt, formatted_freq_divider])
            # save how many data points should be recieved back from the usb
            packet_count = (2 * (- high_dac_value + low_dac_value + 1)
                            / (float(USB_IN_BYTE_SIZE) / 2.0))  # data is 2 bytes long
            # round up
            self.usb_packet_count = int(packet_count) + (packet_count % USB_IN_BYTE_SIZE > 0)
            # calculate what the actual voltage the device will make.  This will be slightly different
            # from the user input because of the VDAC's resolution
            self.params.actual_low_volt = (- low_dac_value + low_dac_value
                                           % self.params.dac.voltage_step_size)
            time.sleep(0.5)
            self.device.usb_write(to_amp_device)
            time.sleep(0.01)
            # Write to the timing PWM compare register so the dac adc timing is correct
            compare_value = pwm_period / 2
            self.device.write_timer_compare(compare_value)

        def run_scan(self, canvas, run_button):
            """ This will run a cyclic voltammetry scan. To do this it follows the steps
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
            self.run_button = run_button
            self.run_button.config(state='disabled')
            self.device.usb_write('R')  # step 1
            if self.device.working:
                logging.debug("device reading")
                # amount of time to wait for the data to be collected before getting it
                # give a 200 ms buffer to the calculated delay time
                _delay = int(2000 + self.params.cv_settings.delay_time)
                # print 'delay: ', _delay
                self.master.after(_delay, lambda: self.run_scan_continue(canvas))  # step 2
            else:
                logging.debug("Couldn't find out endpoint to send message to run")
                # master.attempt_reconnection()

        def run_scan_continue(self, canvas, fail_count=0):
            """ The callback for run_scan.  This is called after the device should be done with the scan
            and is readyto export the data.   The parts of the run cyclic voltammetry scan this
            functions run is part 3-5 listed in run_scan.
            :param canvas: the widget that is called to display the data
            :param fail_count: int, running count of how many attempts have been tried
            :return:
            """
            check_message = self.device.usb_read_message()  # step 3

            if check_message == COMPLETE_MESSAGE:
                self.get_and_display_data(canvas)
            else:
                # wait a little longer and retry, after a certain amount of time, timeout
                if fail_count < FAIL_COUNT_THRESHOLD:  # retry step 2
                    self.master.after(FAILURE_DELAY,
                                      lambda: self.run_scan_continue(canvas, fail_count + 1))
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
            if not raw_data:  # if something is wrong just return
                return
            # call function to convert the raw ADC values into the current that passed
            # through the working electrode
            data = self.device._process_data(raw_data)
            self.master.current_data = data

            x_line = make_x_line(self.params.cv_settings.low_voltage,
                                 self.params.cv_settings.high_voltage,
                                 self.params.dac.voltage_step_size)
            # Send data to the canvas where it will be saved and displayed

            if self.run_chrono:
                x_line = range(4001)

            # canvas.update_data(x_line, data, raw_data)
            canvas.update_data(x_line, data, raw_data)
            self.run_button.config(state='active')

        def format_divider(self, _sweep_rate):
            """ Take in the users desired sweet rate and convert it to the number needed to input
            into the PWM used to set the time between the interrupts that change the dac values
            (_sweep_rate * 1000) is used to convert the sweep rate from V/s to mV/s
            :param _sweep_rate: the users desired sweep rate
            :return: integer that is to be put into the interrupt PWM timer that's padded with zeros to
            be 5 integers long to properly send it to the device
            """
            clk_freq = self.params.clk_freq_isr_pwm
            # take the clock frequency that is driving the PWM and divide it by the number of voltage
            # steps per second: this is how many clk ticks between each interrupt
            raw_divider = int(
                round(
                    clk_freq / (_sweep_rate * 1000 / self.params.dac.voltage_step_size)) - 1)
            return '{0:05d}'.format(raw_divider), raw_divider

        def format_voltage(self, _in_volts):
            """ Takes in the voltage (in millivolts) the user wants to apply to the electrode and
            convert it to the integer that represent the value to be put into the pidac
            :param _in_volts: user desired electrode voltage value in millivolts
            :return: integer that is the value to be put into the pidac, padded with zeros to be 4
            values long to be transmitted to the device
            """
            # shift the user's voltage by the amount of the virtual ground
            input_voltage = self.params.virtual_ground_shift + _in_volts  # mV

            # get the value needed (number of increments needed to get desired voltage, ex. desire
            # 500mV with 1 mV increments then put in 500) to put into the dac and pad it with zeros
            dac_value = self.params.dac.get_dac_count(input_voltage)
            return '{0:04d}'.format(dac_value), dac_value

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
            self.low_voltage_var_str = tk.StringVar()
            self.high_voltage_var_str = tk.StringVar()
            self.freq_var_str = tk.StringVar()
            self.current_var_str = tk.StringVar()
            self.device = device

            # Make Labels to display the String variables
            tk.Label(textvariable=self.low_voltage_var_str, master=self).pack(side='top')
            tk.Label(textvariable=self.high_voltage_var_str, master=self).pack(side='top')
            tk.Label(textvariable=self.freq_var_str, master=self).pack(side='top')
            tk.Label(textvariable=self.current_var_str, master=self).pack(side='top')
            # make a button to change the cyclic voltammetry setting
            tk.Button(self,
                      text="Change Settings",
                      command=lambda: self.change_cv_settings(_master, graph)).pack(side='bottom',
                                                                                    fill=tk.BOTH)

            self.cv_label_update(device_params)

        def cv_label_update(self, device_params):
            """ Update the user's display of what the parameters of the cyclic
            voltammetry scan are set to
            :param device_params: device settings
            """
            self.low_voltage_var_str.set('Start voltage: ' +
                                         str(device_params.cv_settings.low_voltage) +
                                         ' mV')
            self.high_voltage_var_str.set('End voltage: ' +
                                          str(device_params.cv_settings.high_voltage) +
                                          ' mV')
            self.freq_var_str.set('Sweep rate: ' +
                                  str(device_params.cv_settings.sweep_rate) +
                                  ' V/s')
            self.current_var_str.set(u'Current range: \u00B1' +
                                     str(1000 / device_params.adc_tia.tia_resistor) +
                                     u' \u00B5A')

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


def make_x_line(start, end, inc):
    start = int(start)
    end = int(end)
    inc = int(inc)
    line = []
    line.extend(make_side(0, start, inc))
    line.extend(make_side(start, end, inc))
    line.extend(make_side(end, 0, inc))
    line.append(0)
    return line


def make_side(start, end, inc):
    if end < start:
        inc *= -1
    return range(start, end, inc)


def make_x_line_triangle(start, end, inc):
    """ Make the voltage's that correspond to the currents measured
    :param start: voltage the cyclic voltammetry starts at
    :param end: voltage the cyclic voltammetry ends at
    :param inc: the voltage step size
    :return: list of numbers
    """
    i = start
    line = []
    while i <= end:
        line.append(i)
        i += inc
    i -= inc  # do the last value twice but i is 1 inc too high here
    while i >= start:
        line.append(i)
        i -= inc
    return line


def open_file(_type):
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
        _file = tkFileDialog.asksaveasfile(mode='wb', **file_opt)
    elif _type == 'open':
        _filename = tkFileDialog.askopenfilename(**file_opt)
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
    except ImportError, _:
        return "canvas"
