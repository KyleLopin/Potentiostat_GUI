# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" tkinter frame to hold all information, widgets and plotting area for amperometry experiments
NOTE: Can make a parent class
"""
# standard libraries
import csv
import logging
import time
import tkFileDialog
import Tkinter as tk
import ttk
# local files
import change_toplevel
import tkinter_pyplot

__author__ = 'Kyle Vitautas Lopin'

OPTIONS_BACKGROUND = 'LightCyan4'

USB_IN_BYTE_SIZE = 64
USB_UINT16_SIZE = 32


class AmpFrame(ttk.Frame):
    """ Frame to hold widgets and information to perform amperometry experiments,
    also includes the data calls and handles usb commands for amperometry experiments
    NOTE: Make a parent class to hold this and cv_frame
    """

    def __init__(self, master, parent_notebook, graph_properties):
        ttk.Frame.__init__(self, parent_notebook)
        self.data = []
        self.graph = self.make_graph_area(master, graph_properties)
        self.graph.pack(side='left', expand=True, fill=tk.BOTH)
        self.running = False
        options_frame = tk.Frame(self, bg=OPTIONS_BACKGROUND, bd=3)
        options_frame.pack(side='left', fill=tk.BOTH)
        buttons_frame = tk.Frame(options_frame)
        buttons_frame.pack(side='bottom', fill=tk.X)

        device = self.USBHandler(self.graph, master.device, master)
        self.settings_frame = self.AmpSettingsDisplay(master, options_frame,
                                                      self.graph, device,
                                                      master.device_params)
        self.settings_frame.pack(side="top", fill=tk.X)
        self.make_buttons(buttons_frame, self.graph, device)

    def make_graph_area(self, master, graph_props):
        if check_display_type() == 'matplotlib':
            # current_lim = 1.2 * 1000. / master.device_params.adc_tia.tia_resistor
            current_lim = master.device_params.adc_tia.current_lims
            # 1's are not needed, the properties will override this
            graph = tkinter_pyplot.PyplotEmbed(master.frames[1],
                                               graph_props.amp_plot, self,
                                               current_lim, 1, 1)
        else:
            graph = None  # TODO: implement for canvas
        return graph

    def make_buttons(self, frame, graph, device):
        """ Make the buttons needed to perform amperometry experiments.  Basically just start
        and stop, and change the sampling rate
        :param frame: tk frame to make all the buttons in
        :param graph: graph where the data will be displayed in
        :param device: device to send commands too
        """
        # make a button to run a amperometry scan
        self.run_button = tk.Button(frame,
                                    text="Start Amperometry",
                                    command=lambda: self.toggle_amp_run(device, graph))
        self.run_button.pack(side='bottom', fill=tk.BOTH)
        tk.Button(frame,
                  text="Save Data",
                  command=lambda: self.save_data(device)).pack(side='bottom',
                                                               fill=tk.BOTH)

    def toggle_amp_run(self, device, graph):
        if self.running:  # stop reading data and tell the device to stop running
            self.run_button.config(text="Start Amperometry")
            self.running = False
            device.cancel_run()
        else:
            logging.info("starting amperometry run")
            self.run_button.config(text="Stop Amperometry")
            self.running = True
            device.amp_run(graph, self)

    @staticmethod
    def save_data(device):
        if len(device.data) == 0:
            logging.info("No amperometry data to save")
            return

        _file = open_file('saveas')

        if _file:
            writer = csv.writer(_file, dialect='excel')
            writer.writerow(["time", "current"])
            for i in range(len(device.data)):
                writer.writerow([device.time[i], device.data[i]])
            _file.close()

    def set_tia_current_lim(self, _value, current_limit):
        """ The TIA setting has been changed so update the value shown to the user in the
        display frame and resize the graph
        :param _value: str - the current range string to show the user
        :param current_lim: int - the current range to resize the graph to
        """
        self.settings_frame.set_current_var_str(_value)
        self.graph.resize_y(current_limit)

    def change_data_labels(self):
        """ Override parent cv_frame's method to do nothing """
        pass

    class USBHandler(object):
        """ NOTE: self.device is the AMpUSB class and device.device is the pyUSB class
        """

        def __init__(self, graph, device, master):
            self.graph = graph
            self.device = device  # bind master device to self
            self.master = master
            self.settings = master.device_params.amp_settings
            self.running = None
            sampling_rate = self.settings.sampling_rate
            if sampling_rate >= 1000:
                # calculate the number of data points in a usb packets from the sampling rate by
                # dividing by 5 (so that you update the data every 200 ms, i.e. 1s/5)
                self.data_packet_size = int((sampling_rate / 5.0))

            else:
                # if the sampling rate is less than 1 kHz just update every 500 ms
                self.data_packet_size = int(sampling_rate / 2.0)
            # calculate the number of packets of data you should get every 200 ms by adding one
            # to the data packet size to account for the termination code at the end and divide by
            # 32 for the number of data points per packet
            # (packets are 64 bytes - 2 bytes per uint16 data points
            self.number_packets = (int((self.data_packet_size + 1.0) / 32.0)
                                   + ((self.data_packet_size + 1.0) % 32 > 0))  # round the packet up
            self.time_step = 1.0 / self.settings.sampling_rate
            self.endpoint = None  # placeholder, assign it correctly when an amperometry run starts
            self.uint16_array = [0] * 256
            self.t_ptr = -self.time_step
            self.data = []
            self.time = []
            self.first_read_dumbed = False
            self.t_lenght_fixed = False
            self._reader = None
            self.number_packets = 16

        def amp_run(self, graph, amp_frame):
            # reinitialize the data, time and time pointer
            self.t_ptr = -self.time_step
            self.data = []
            self.time = []
            self.running = True
            # set the sampling rate if it is not set correctly
            if (self.device.device_params.pwm_period_value !=
                    self.settings.pwm_period_value):
                self.set_sample_rate(self.settings.sampling_rate)
            # calculate the number to sent do the device to set the DAC for the voltage read
            formatted_packets_size = '{0:04}'.format(self.data_packet_size)
            self.device.usb_write("M|" + self.format_voltage(self.settings.voltage) + '|'
                                  + formatted_packets_size)
            time.sleep(0.1)
            self.endpoint = self.device.device[0][(0, 0)][0].bEndpointAddress  #
            self.master.after(300, self.running_read)

        def running_read(self):
            self._reader = self.master.after(50, self.running_read)
            if self.running:
                get = self.device.usb_read_message()
                if get:
                    logging.debug("getting channel: %s", get[4])
                    self.device.usb_write("F" + get[4])
                    got_data = self.data_try()  # have to read in data packets
                    if got_data:
                        self.graph.update_amp_data(self.time, self.data, 10)

        def data_try(self):
            while True:
                try:
                    usb_input = self.device.get_data_packets(self.endpoint, self.number_packets)
                    data = self.device.process_data(usb_input)
                except Exception as error:
                    logging.error("missed data read: %s", error)
                # dump the first read of the USB incase it is garbate
                # TODO: Check this is still needed
                if not self.first_read_dumbed:
                    self.first_read_dumbed = True
                    return False

                if usb_input:
                    len_input = len(data)
                    # down sampling hack
                    down_sampled_data = []
                    first_index = 0
                    len_sampled = len_input / self.settings.down_sample
                    for i in range(len_sampled):
                        first_index += self.settings.down_sample
                        down_sampled_data.append(sum(data[first_index:first_index + 9]) / self.settings.down_sample)

                    self.data.extend(down_sampled_data)
                    self.time.extend(
                        [x * self.time_step + self.t_ptr for x in range(1, len_sampled + 1)])
                    self.t_ptr += len_input * self.time_step
                    return True

        def cancel_run(self):
            self.running = False
            self.master.after_cancel(self._reader)
            self._reader = None
            self.device.usb_write('X')
            self.device.clear_in_buffer()
            self.first_read_dumbed = False

        def set_sample_rate(self, rate):
            """ Set the sampling rate of the device for amperometric experiments by writing to the
            PWM timer period register
            :param rate: the sampling rate desired (in kHz)
            """
            formatted_period, self.pwm_timer_period_amp = self.format_period(rate)
            self.device.usb_write('T|' + formatted_period)
            self.device.device_params.PWM_period = self.pwm_timer_period_amp

        def set_voltage(self, voltage):
            self.device.device_params.amp_settings.voltage = voltage
            formatted_voltage = self.format_voltage(voltage)
            self.device.usb_write('D|' + formatted_voltage)

        def set_adc_tia(self, *args):
            self.device.set_adc_tia(*args)

        def format_period(self, rate):
            """ Take the users desired sampling rate and convert it to the number to put in the
            PWM used to time the interrupts.
            :param rate: int (kHz) sampling rate the user desires in kHz
            :return:  the int to put in the PWM period register, padded with 0's as the device
            requires
            """
            clk_freq = self.device.device_params.clk_freq_isr_pwm
            # user entered kHz value so convert to Hz
            raw_divider = int(round(clk_freq / (rate))) - 1  # PWM is 0 indexed
            return '{0:05d}'.format(raw_divider), raw_divider

        def format_voltage(self, in_voltage):
            input_voltage = self.device.device_params.virtual_ground_shift - in_voltage  # mV

            dac_value = self.device.device_params.dac.get_dac_count(input_voltage)
            return '{0:04d}'.format(dac_value)

    class AmpSettingsDisplay(tk.Frame):

        def __init__(self, master, frame, graph, device, device_params):
            """
            :param master: root application (master.device) is the usb_comm device
            :param frame: options frame this frame is placed in
            :param graph: graph area
            :param device: usb_handler for the amp_frame
            :param device_params: device parameters
            """
            tk.Frame.__init__(self, master=frame)
            self.master = master
            self.graph = graph
            self.device = device
            # Make String variables to hold the strings that state the parameters; bind them to self
            # so they are easy to pass between functions
            self.voltage_var_str = tk.StringVar()
            self.sampling_rate_var_str = tk.StringVar()
            self.voltage_var_str = tk.StringVar()
            self.current_var_str = tk.StringVar()

            # Make Labels to display the String variables
            tk.Label(textvariable=self.sampling_rate_var_str, master=self).pack(side='top')
            tk.Label(textvariable=self.voltage_var_str, master=self).pack(side='top')
            tk.Label(textvariable=self.current_var_str, master=self).pack(side='top')

            tk.Button(self,
                      text="Change Settings",
                      command=self.change_amp_settings).pack(side='bottom',
                                                             fill=tk.BOTH)
            self.label_update(device_params)

        def set_current_var_str(self, tia_value):
            self.current_var_str.set(u'Current range: {0}'
                                     .format(tia_value))

        def label_update(self, params):
            """ Update the user's display of what the parameters of the amperometry are set to
            :param params: device parameters
            """
            self.voltage_var_str.set('Voltage: ' +
                                     str(params.amp_settings.voltage) +
                                     ' mV')
            self.sampling_rate_var_str.set('Sampling rate: ' +
                                           str(int(params.amp_settings.sampling_rate)) +
                                           ' Hz')
            self.current_var_str.set(u'Current range: \u00B1 {0:.1f} \u00B5A'
                                     .format(params.adc_tia.current_lims))

        def change_amp_settings(self):
            change_toplevel.AmpSettingsChanges(self, self.master, self.graph, self.device)


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
