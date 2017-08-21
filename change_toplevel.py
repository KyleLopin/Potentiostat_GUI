# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

"""Top levels for the user to change different aspects of the device
"""
# standard libraries
import logging
import os
import sys
import time
import Tkinter as tk
import tkFont
import ttk
# local files
import cv_frame
import globals as _globals
import tkinter_pyplot

__author__ = 'Kyle Vitautas Lopin'

# TIA_RESISTOR_VALUES = [20, 30, 40, 80, 120, 250, 500, 1000]
# CURRENT_LIMIT_VALUES = [50, 33, 25, 12.5, 8.4, 4, 2, 1, 0.5, 0.25, 0.125]
COLOR_CHOICES = ['black', 'gray', 'red', 'green', 'blue', 'orange', 'magenta']

TIA_RESISTOR_VALUES = _globals.TIA_RESISTOR_VALUES
CURRENT_LIMIT_VALUES = _globals.CURRENT_LIMIT_VALUES
CURRENT_OPTION_LIST = _globals.CURRENT_OPTION_LIST


class CVSettingChanges(tk.Toplevel):
    """ A modified tkinter toplevel that allows the user to input new voltage ranges to measure
    and to set the frequency
    """

    def __init__(self, cv_display, _master, cv_graph, device):
        """ Initialize the window
        :paran cv_display: cv_frame.CVSettingDisplay: tk.Frame that displays the cyclic voltammertry info
        :param _master: tk.Frame, the main window
        :param cv_graph: tkinter_pyplot.PyplotEmbed: embedded graph that needs to be updated if limits change
        :param device: usb.comm.AmpUsb: USB device being communicated with
        """
        tk.Toplevel.__init__(self, master=_master)
        # Initialize values needed later
        self.master = _master
        self.graph = cv_graph
        self.start_volt = tk.DoubleVar()
        self.end_volt = tk.DoubleVar()
        self.entry_delay = None  # variable to bind the after calls to

        self.freq = tk.DoubleVar()
        self._current_range = ""
        self.device = device
        self.data = None  # placeholder for voltage protocol to be held in, for tkinter_pyplot
        self.geometry("300x300")

        self.title("Change Cyclic Voltammetry Settings")
        # make labels and an entry widget for a user to change the starting
        # voltage of the triangle wave
        self.preview_frame = tk.Frame(self)
        self.options_frame = tk.Frame(self)
        self.options_frame.pack(side='right')

        tk.Label(self.options_frame, text="Starting Voltage: ",
                 padx=10, pady=10
                 ).grid(row=0, column=0)
        # entry widget for the user to change the voltage
        tk.Entry(self.options_frame, textvariable=self.start_volt).grid(row=0, column=1)
        # put the current value in the entry widget
        self.start_volt.set(_master.device_params.cv_settings.start_voltage)
        tk.Label(self.options_frame, text="mV", padx=10, pady=10).grid(row=0, column=3)

        # make labels and an entry widget for a user to change the ending voltage
        #  of the triangle wave
        tk.Label(self.options_frame, text="Ending Voltage: ",
                 padx=10, pady=10
                 ).grid(row=1, column=0)
        # spinbox for the user to change the voltage
        tk.Entry(self.options_frame, textvariable=self.end_volt).grid(row=1, column=1)
        # put the current value in the entry widget
        self.end_volt.set(_master.device_params.cv_settings.end_voltage)
        tk.Label(self.options_frame, text="mV", padx=10, pady=10).grid(row=1, column=3)

        # make labels and an entry widget for a user to change the sweep rate of the triangle wave
        tk.Label(self.options_frame, text="Sweep Rate: ", padx=10, pady=10).grid(row=2, column=0)
        # entry widget for the user to change the voltage
        tk.Entry(self.options_frame, textvariable=self.freq).grid(row=2, column=1)
        # put the current value in the entry widget
        self.freq.set(_master.device_params.cv_settings.sweep_rate)

        tk.Label(self.options_frame, text="V/s", padx=10, pady=10).grid(row=2, column=3)

        # make labels and option menu for the user to change current range the device detects
        tk.Label(self.options_frame, text="Current Range: ", padx=10, pady=10).grid(row=3, column=0)
        self.current_options = tk.StringVar(self.options_frame)
        # there are sometimes problems with encoding with this
        self.current_option_list = CURRENT_OPTION_LIST

        # if _master.device_params.adc_tia.tia_resistor in TIA_RESISTOR_VALUES:
        #     current_option_list_index = TIA_RESISTOR_VALUES.index(
        #         _master.device_params.adc_tia.tia_resistor)
        #     self.current_options.set(self.current_option_list[current_option_list_index])

        self.current_options.set(self.current_option_list[_master.device_params.adc_tia.current_option_index])
        current = tk.OptionMenu(self.options_frame, self.current_options,
                                *self.current_option_list)
        current.grid(row=3, column=1)

        self.make_buttons(self.options_frame)

        # make a button that will take the entry values and call a function to properly convert
        # them and send the correct values to the amperometry microcontroller
        tk.Button(self.options_frame,
                  text='Save Changes',
                  command=lambda: self.save_cv_changes(self.current_options.get(),
                                                       _master, cv_graph,
                                                       cv_display)
                  ).grid(row=9, column=0)

        # make a button to exit the toplevel by destroying it
        tk.Button(self.options_frame,
                  text='Exit',
                  command=self.destroy).grid(row=9, column=1)

        # set varaible traces
        self.end_volt.trace("w", self.trace_delay)
        self.start_volt.trace("w", self.trace_delay)
        self.freq.trace("w", self.trace_delay)

    def make_buttons(self, frame):
        # TODO: think these can be removed
        self.preview_var = tk.IntVar()
        self.sweep_type = tk.StringVar()
        self.sweep_type.set(self.master.device_params.cv_settings.sweep_type)

        self.start_voltage_type = tk.StringVar()
        self.start_voltage_type.set(self.master.device_params.cv_settings.sweep_start_type)

        tk.Label(frame, text="Voltage Sweep type: "
                 ).grid(row=4, column=0, columnspan=2, sticky='w')
        tk.Radiobutton(frame, text="Cyclic Voltammetry", variable=self.sweep_type,
                       value="CV", command=self.set_sweep_type
                       ).grid(row=5, column=0, sticky='w')
        tk.Radiobutton(frame, text="Linear Sweep", variable=self.sweep_type,
                       value="LS", command=self.set_sweep_type
                       ).grid(row=5, column=1, sticky='w')

        tk.Label(frame, text="Start voltage: "
                 ).grid(row=6, column=0, columnspan=2, sticky='w')
        tk.Radiobutton(frame, text="0 V", variable=self.start_voltage_type,
                       value="Zero", command=self.set_sweep_type
                       ).grid(row=7, column=0, sticky='w')
        tk.Radiobutton(frame, text="Start Voltage", variable=self.start_voltage_type,
                       value="Start", command=self.set_sweep_type
                       ).grid(row=7, column=1, sticky='w')

        preview_option = tk.Checkbutton(frame, text="Preview voltage protocol",
                                        var=self.preview_var, command=self.preview)
        preview_option.grid(row=8, column=0, columnspan=2)

    def trace_delay(self, *args):
        """ Trace callback, add a small delay to changing the voltage line so the user can finish
        """
        self.entry_delay = self.after(300, self.set_sweep_type)

    def set_sweep_type(self, *args):
        if not self.preview_var.get():
            return  # there is not graph displayed so exit
        if self.entry_delay:
            self.after_cancel(self.entry_delay)  # if user types multiple numbers,
            # trace will be called multiple times, just update the graph once
            self.entry_delay = None
        if self.sweep_type.get() == 'LS':
            pass
        self.update_graph(self.start_voltage_type.get(), self.sweep_type.get())

    def preview(self):
        if self.preview_var.get():
            sweep_type = self.sweep_type.get()
            start_place = self.start_voltage_type.get()
            type = (start_place, sweep_type)
            self.make_graph(sweep_type, start_place)
        else:
            self.geometry("300x300")

    def make_graph(self, sweep_type, start_volt_type):
        """ Make a graph of what the voltage versus time protocol looks like
        :param sweep_type: str - 'LS' or 'CV' for a linear sweep or cyclic voltammetry
        :param start_volt_type: str - 'Zero' or 'Start' for starting the protocol at zero volts or the starting voltage
        """
        self.geometry("700x300")
        blank_frame = tk.Frame()  # holder for toolbar that is not needed
        try:
            start_volt = int(float(self.start_volt.get()))
            end_volt = int(float(self.end_volt.get()))
            rate = float(self.freq.get())
        except:
            return -1
        low_voltage = min([start_volt, end_volt])
        high_volt = max([start_volt, end_volt])
        voltage_step = self.master.device_params.dac.voltage_step_size
        ylims = [low_voltage, high_volt]

        # make the voltage protocol, use the functions used by the cv_frame
        self.data = cv_frame.make_x_line(start_volt,
                                         end_volt, voltage_step, sweep_type, start_volt_type)
        steps_per_second = rate * float(voltage_step)
        total_time = len(self.data) * steps_per_second
        time = [x * steps_per_second for x in range(len(self.data))]

        plt_props = {'xlabel': "'time (msec)'",
                     'ylabel': "'voltage (mV)'",
                     'title': "'Voltage profile'",
                     'subplots_adjust': "bottom=0.15, left=0.12"}
        self.graph = tkinter_pyplot.PyplotEmbed(blank_frame, plt_props, self, ylims, 0,
                                                total_time)
        self.graph.pack(side='left')
        self.graph.simple_update_data(time, self.data)

    def update_graph(self, start_voltage_type, sweep_type):
        """ Update the graph displaying the voltage protocol
        :param start_voltage_type: str - 'LS' or 'CV' for a linear sweep or cyclic voltammetry
        :param sweep_type: str - 'Zero' or 'Start' for starting the protocol at zero volts or the starting voltage
        :return:
        """
        try:
            start_volt = int(float(self.start_volt.get()))
            end_volt = int(float(self.end_volt.get()))
            rate = float(self.freq.get())
        except:  # if crap input just leave
            return -1

        low_voltage = min([start_volt, end_volt])
        high_volt = max([start_volt, end_volt])

        ylims = [low_voltage, high_volt]
        # resize the y axis
        self.graph.graph_area.axis.set_ylim(ylims)  # TODO: horrible for encapsulation
        # remake the voltage protocol
        voltage_step = self.master.device_params.dac.voltage_step_size
        self.data = cv_frame.make_x_line(start_volt, end_volt, voltage_step,
                                         sweep_type, start_voltage_type)
        # make a new t-axis data
        steps_per_second = rate / float(voltage_step)
        if steps_per_second <= 0:
            return  # user is not done typing in the varible yet
        total_time = len(self.data) / steps_per_second

        time = [x / steps_per_second for x in range(len(self.data))]
        xlims = [0, total_time]
        # resize the x axis
        self.graph.graph_area.axis.set_xlim(xlims)  # TODO: horrible for encapsulation

        self.graph.voltage_line.set_data(time, self.data)
        self.graph.update_graph()

    def save_cv_changes(self, _range, _master, cv_graph, cv_display):
        """ Commit all changes the user entered
        :param _range: string from self.current_option_list that the user picked
        :param _master: main window of the program, used so that the operational parameters
        of the main window can be changed
        :param cv_graph:  graph area the data is displayed on
        :param cv_display: display frame of the cyclic voltammetry parameters
        :return: the parameters are updated in the main windows operational_params dictionary
        """
        cv_settings = _master.device_params.cv_settings
        # try to convert the voltages to integers and sweep rate to a float and save the voltage
        # and frequency parameters to the current instance so they don't
        # have to passed all the time to the functions
        try:
            self._start_volt = int(float(self.start_volt.get()))  # first voltage of the protocol
            self._end_volt = int(float(self.end_volt.get()))  # second voltage the protocol goes to
            self._freq = float(self.freq.get())
            # don't have to check current range cause it was chosen from an option menu
        except ValueError as error:  # user input values failed
            logging.info("Error in data input format: %s", error)
            # TODO: put a toplevel telling the user about the error

            self.destroy()  # if the inputted data is not correct, just destroy the toplevel so
            # that the program will not try to send bad data to the MCU

            return
        # Update all of the main programs operations_params settings so the User's choices
        # will be remembered and send all the parameters to the MCU
        if self.sweep_param_is_changed(_master.device_params):
            cv_settings.update_settings(self._start_volt, self._end_volt, self._freq,
                                        self.sweep_type.get(), self.start_voltage_type.get())
            cv_display.cv_label_update(_master.device_params)
            self.device.send_cv_parameters()

            # resize the graph to the new voltages
            x_lim_low = cv_settings.low_voltage
            x_lim_high = cv_settings.high_voltage
            cv_graph.resize_x(x_lim_low, x_lim_high)

        # figure out if the current range has changed and update the device if it has
        current_range_index = CURRENT_OPTION_LIST.index(_range)

        if _master.device_params.adc_tia.current_option_index != current_range_index:
            self.device.set_adc_tia(current_range_index)
        _master.device_params.adc_tia.current_option_index = current_range_index

        # destroy the top level now that every is saved and updated
        self.destroy()

    def sweep_param_is_changed(self, _old_params):
        """ Check to see if any of the parameters of the cyclic voltammetry experiments
         have been changed
        :param _old_params:  old parameters
        :return: True or False if the parameters have been changed
        """
        if (self._start_volt != _old_params.cv_settings.low_voltage
            or self._end_volt != _old_params.cv_settings.high_voltage
            or self._freq != _old_params.cv_settings.sweep_rate):

            logging.debug("sweep_param is changed")
            return True
        else:
            logging.debug("sweep param are not changed")
            return False


class ASVSettingChanges(tk.Toplevel):
    def __init__(self, asv_frame, master, graph, device):
        """

        :param display: the CVSettingsDisplay (tk.Frame) in the ASV frame where the
        settings are displayed
        :param master: root application master
        :param graph: tkinter_pyplot graph area
        :param device; asv_frame device handler
        """
        tk.Toplevel.__init__(self, master=master)
        self.title("Change Anode Stripping Voltammetry Settings")
        # Initialize values needed later
        self.asv_frame = asv_frame
        self.master = master
        self.graph = graph
        self.device = device
        self.entry_delay = None  # variable to bind the after calls to
        self.geometry("400x300")

        # make all the variables to fill
        self.clean_volt = tk.DoubleVar()
        self.clean_time = tk.DoubleVar()
        self.plate_volt = tk.DoubleVar()
        self.plate_time = tk.DoubleVar()
        self.end_voltage = tk.DoubleVar()
        self.sweep_rate = tk.DoubleVar()

        self.settings = master.device_params
        self.clean_volt.set(self.settings.asv_settings.clean_volt)
        self.clean_time.set(self.settings.asv_settings.clean_time)
        self.plate_volt.set(self.settings.asv_settings.plate_volt)
        self.plate_time.set(self.settings.asv_settings.plate_time)
        self.end_voltage.set(self.settings.asv_settings.end_voltage)
        self.sweep_rate.set(self.settings.asv_settings.sweep_rate)

        self.options_frame = tk.Frame(self)
        self.options_frame.pack()

        label_strs = ["Cleaning voltage: ", "Cleaning time: ", "Plating voltage: ",
                      "Plating time: ", "Peak voltage: ", "Sweep rate: "]
        entries = [self.clean_volt, self.clean_time, self.plate_volt,
                   self.plate_time, self.end_voltage, self.sweep_rate]
        unit_str = [" mV", "secs", "mV", "secs", "mV", "V/s"]
        for i in range(6):  # framework for making
            self.entry_row(self.options_frame, label_strs[i], entries[i], unit_str[i], i)

        tk.Label(self.options_frame, text="Current Range: ", padx=10, pady=10
                 ).grid(row=7, column=0)

        self.current_range = tk.StringVar()

        if master.device_params.adc_tia.tia_resistor in TIA_RESISTOR_VALUES:
            current_option_list_index = TIA_RESISTOR_VALUES.index(
                master.device_params.adc_tia.tia_resistor)
            self.current_range.set(CURRENT_OPTION_LIST[current_option_list_index])

        tk.OptionMenu(self.options_frame, self.current_range, *CURRENT_OPTION_LIST
                      ).grid(row=7, column=1)

        tk.Button(self, text="Save", width=15, command=self.save
                  ).pack(side='left', expand=True)
        tk.Button(self, text="Exit", width=15, command=self.destroy
                  ).pack(side='left', expand=True)

    def entry_row(self, frame, label_str, entry_variable, unit_str, row):
        tk.Label(frame, text=label_str, padx=10, pady=10
                 ).grid(row=row, column=0)
        tk.Entry(frame, textvariable=entry_variable).grid(row=row, column=1)
        tk.Label(frame, text=unit_str, padx=10, pady=10).grid(row=row, column=2)

    def save(self):
        self.settings.asv_settings.update_settings(self.clean_volt.get(),
                                                   self.clean_time.get(),
                                                   self.plate_volt.get(),
                                                   self.plate_time.get(),
                                                   self.end_voltage.get(),
                                                   self.sweep_rate.get())

        # resize the graph to the new voltages
        x_lim_low = self.settings.asv_settings.low_voltage
        x_lim_high = self.settings.asv_settings.high_voltage
        self.graph.resize_x(x_lim_low, x_lim_high)

        # figure out what the user selected for the current range
        position = CURRENT_OPTION_LIST.index(
            self.current_range.get())  # get user's choice from the option menu
        # the largest setting change the ADC gain but not the TIA value
        adc_config, tia_position, adc_gain_setting = get_tia_settings(position)

        if check_tia_changed(self.settings, adc_gain_setting, tia_position):
            self.device.set_adc_tia(adc_config, tia_position, adc_gain_setting)

        # self.settings.adc_tia.tia_resistor = TIA_RESISTOR_VALUES[position]
        # logging.debug("TIA resistor changed to: %s", self.settings.adc_tia.tia_resistor)

        # Change the value for the current limits displayed to the user and
        # update the graph's scale
        self.master.update_current_range(CURRENT_OPTION_LIST[position],
                                         CURRENT_LIMIT_VALUES[position])

        self.asv_frame.label_update(self.settings)
        self.destroy()


class AmpSettingsChanges(tk.Toplevel):
    """ Toplevel that displays the current amperoemtry settings and allows the user to change
     them """
    def __init__(self, display, master, graph, device):
        """
        :param display: the AmpSettingsDisplay (tk.Frame) where the
        amperometry settings are displayed
        :param master: root application master
        :param graph: tkinter_pyplot graph area
        :param device; amp_frame device handler
        """

        tk.Toplevel.__init__(self, master=master)
        # very similar to CVSettingsChange, can be refactored
        # Initialize values needed later
        self.sample_rate = 0
        self.current_range = ""
        self.title("Change Amperometry Settings")
        self.display = display  # the info window on notebook
        # make labels and an entry widget for a user to change the voltage
        tk.Label(self, text="Voltage: ", padx=10, pady=10).grid(row=0, column=0)
        voltage = tk.Entry(self)  # entry widget for the user to change the voltage
        # put the current value in the entry widget
        voltage.insert(0, str(master.device_params.amp_settings.voltage))
        voltage.grid(row=0, column=1)
        tk.Label(self, text="mV", padx=10, pady=10).grid(row=0, column=3)

        # make labels and an entry widget for a user to change the sampling rate
        # tk.Label(self, text="Sampling rate: ", padx=10, pady=10).grid(row=1, column=0)
        rate = tk.Entry(self)  # entry widget for the user to change the voltage
        # put the current value in the entry widget
        rate.insert(0, str(master.device_params.amp_settings.sampling_rate / 1000))
        # rate.grid(row=1, column=1)
        # tk.Label(self, text="kHz", padx=10, pady=10).grid(row=1, column=3)

        # make labels and option menu for the user to change current range the device detects
        tk.Label(self, text="Current Range: ", padx=10, pady=10).grid(row=2, column=0)
        self.current_options = tk.StringVar(self)
        # there are sometimes problems with encoding with this
        self.current_option_list = CURRENT_OPTION_LIST
        self.current_options.set(self.current_option_list[master.device_params.adc_tia.current_option_index])

        # current_option_list_index = TIA_RESISTOR_VALUES.index(
        #     master.device_params.adc_tia.tia_resistor)
        # self.current_options.set(self.current_option_list[current_option_list_index])
        current = tk.OptionMenu(self, self.current_options, *self.current_option_list)
        current.grid(row=2, column=1)
        tk.Button(self,
                  text='Save Changes',
                  command=lambda: self.save_amp_changes(voltage.get(), rate.get(), device,
                                                        master)
                  ).grid(row=3, column=0)

        # make a button to exit the toplevel by destroying it
        tk.Button(self,
                  text='Exit',
                  command=self.destroy).grid(row=3, column=1)

    def save_amp_changes(self, _voltage, _sampling_rate, device, master):
        """ Save user's entered data to the device
        NOTE: sampling rate is not working currently
        :param _voltage:  int - voltage the user wants to run an amperometry experiment at
        :param _sampling_rate:  int - sampling rate (in kHz) the user wants to sample at
        :param device:  usb_comm.AmpUsb device that will communicate with the device through a USB
        :param master:  master GUI this
        """
        current_range = self.current_options.get()

        try:  # make sure the user entered the correct data format
            voltage = int(float(_voltage))
            sampling_rate = float(_sampling_rate)
            # don't have to check current range cause it was chosen from an option menu
        except ValueError as error:  # user input values failed
            logging.info("Error in data input format: %s", error)

        # check for changes to the voltage and sampling rate,
        # do not bother the amplifier if there is no update
        if self.params_are_changed(master.device_params, voltage, sampling_rate):
            # send the new parameters to the device
            # device.set_sample_rate(sampling_rate)  # not working yet
            device.set_voltage(voltage)

        current_range_index = CURRENT_OPTION_LIST.index(current_range)
        adc_config, tia_position, adc_gain = get_tia_settings(current_range_index)

        if check_tia_changed(master.device_params, adc_config, adc_gain, tia_position):
            device.set_adc_tia(adc_config, tia_position, adc_gain)  # this updates all frames

        self.display.label_update(master.device_params)
        self.destroy()

    @staticmethod
    def params_are_changed(old_params, new_voltage, new_rate):
        """ Check to see if any of the parameters of the amperometry experiments have been changed
        :param old_params:  properties.DeviceParameters() what the device is currently set to
        :param new_voltage:  int - new voltage the user wants
        :params new_rate:  int - new sampling rate the user wants
        :return: True or False if the parameters have been changed
        """
        if (new_voltage != old_params.amp_settings.voltage
            or new_rate != old_params.amp_settings.sampling_rate):

            logging.debug("amperometry parameters changed")
            return True
        else:
            logging.debug("amperometry parameters not changed")
            return False


class ChangeCompareValue(tk.Toplevel):
    """ Allow the user to change the compare value of the PWM, for testing, sets when the
    ADC goes after the DAC is changes
    """
    def __init__(self, _master):
        tk.Toplevel.__init__(self, _master)
        self.title("Change PWM timing compare value")

        tk.Label(self, text="Enter value to place in timing PWM compare register").pack(side='top')
        tk.Label(self, text="Value must be between 500 and "
                            + str(_master.device_params.PWM_period)).pack(side='top')
        tk.Label(self, text="Current value is "
                            + str(_master.device_params.PWM_compare)).pack(side='top')
        value_varstring = tk.StringVar()
        value_varstring.set(_master.device_params.PWM_compare)
        value_box = tk.Entry(self, textvariable=value_varstring)
        value_box.pack(side='top')

        button_frame = tk.Frame(self)
        button_frame.pack(side='top')

        tk.Button(button_frame, text="Quit", command=self.destroy).pack(side='left')

        tk.Button(button_frame, text="Send",
                  command=lambda: self.compare_reg_change(_master,
                                                          value_varstring.get())).pack(side='left')

        logging.error("put in here something to check if the number for compare is correct")

    def compare_reg_change(self, master, _value):
        """ Write the value the user entered to the device
        :param master: where to find the device, the device is bound to master
        :param _value: value to set PWM to
        """
        master.device.write_timer_compare(_value)
        self.destroy()


class UserDeleteDataWarning(tk.Toplevel):
    """ Warning to the user that they are selecting to delete all the data
    """
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.title("Delete all data")

        warning_frame = tk.Frame(self)
        tk.Label(warning_frame,
                 text="Do you really want to delete all recorded data?").pack(side='top')

        buttons_frame = tk.Frame(self)
        tk.Button(buttons_frame, text="Delete Data",
                  command=lambda: self.call_delete_data(master)).pack(side='left', padx=10)

        tk.Button(buttons_frame, text="Don't Delete",
                  command=self.destroy).pack(side='left', padx=10)
        warning_frame.pack(side='top')
        buttons_frame.pack(side='top', pady=10)

    def call_delete_data(self, master):
        """ The user confirmed they want to delete all the data, so delete all the data and close
        the top level
        :param master: root tk, has a routine to delete all the data
        """
        master.delete_all_data()
        self.destroy()


class UserSetDataLabel(tk.Toplevel):
    """
    Pop up for the user to enter the lable for the data just read, and to make notes that will
    be saved with the data
    """
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.title("Save data options")

        label_frame = tk.Frame(self)
        label_frame.pack(side='top')
        tk.Label(label_frame, text="Data label: ").pack(side='left')
        _label = tk.StringVar()
        label_box = tk.Entry(label_frame, textvariable=_label)
        label_box.pack(side='left')

        tk.Label(self, text="Notes:").pack(side='top')

        user_notes = tk.Text(self, width=20, height=5, wrap=tk.WORD)

        user_notes.pack(side='top')

        buttons_frame = tk.Frame(self)
        buttons_frame.pack(side='bottom', fill=tk.X, expand=1, pady=10)

        # master is the instance of tkinter_pyplot calling this
        tk.Button(buttons_frame,
                  text="Save",
                  command=lambda:
                  self.save_user_input(master, _label.get(),
                                       user_notes.get("1.0", 'end-1c'))).pack(side='left',
                                                                              fill=tk.X,
                                                                              expand=1,
                                                                              padx=10)

        tk.Button(buttons_frame,
                  text="Quit",
                  command=self.destroy).pack(side='left', fill=tk.X, expand=1, padx=10)

    def save_user_input(self, master_pyplot, label, notes):
        """ Save the label to the data that the user entered
        :param master_pyplot: the pyplot the data is displayed on
        :param label: the string the user whats to use as a label
        :param notes: notes to save with the data
        """
        master_pyplot.change_label(label)
        master_pyplot.add_notes(notes)
        self.destroy()


class UserSelectDataDelete(tk.Toplevel):
    """
    Allow the user to select some data to delete from the display
    """
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        big_font = tkFont.Font(family="Helvetica", size=14)
        small_font = tkFont.Font(family="Helvetica", size=12)
        size = len(master.data.label)
        length = 50 * size
        self.geometry("200x{0}".format(length))
        self.title("Select data to delete")
        tk.Label(self,
                 text="Select data to delete",
                 font=big_font).pack(side='top')
        frames = []
        choices = []
        index = 0
        print master.data.label
        for _label in master.data.label:
            frames.append(tk.Frame(self))
            choices.append(tk.IntVar())
            tk.Checkbutton(frames[index],
                           text=_label,
                           font=small_font,
                           variable=choices[index]).pack(padx=5)

            frames[index].pack(side='top', fill=tk.X, expand=1)
            index += 1

        tk.Label(self, text="Delete on selected data?")

        button_frame = tk.Frame(self)
        tk.Button(button_frame,
                  text="Yes",
                  width=10,
                  command=lambda: self.send_delete_selection(master, choices)
                  ).pack(side='left', padx=10, fill=tk.X, expand=1)

        tk.Button(button_frame,
                  text="No",
                  width=10,
                  command=self.destroy
                  ).pack(side='left', padx=10, fill=tk.X, expand=1)

        button_frame.pack(side='top', fill=tk.X, expand=1)

    def send_delete_selection(self, master, picks):
        """ Decode the check boxes the user selected and send the list to master to delete the data
        :param master: root application
        :param picks: list of the checkboxes the user choose from
        """
        _list = []
        _index = 0
        for pick in picks:
            if pick.get() == 1:
                _list.append(_index)
            _index += 1
        master.delete_some_data(_list)
        self.destroy()


class ChangeDataLegend(tk.Toplevel):
    """ Make a toplevel that will allow the user to change the color of the data in the legend
    """

    def __init__(self, _master, graph):

        tk.Toplevel.__init__(self, master=_master)
        self.legend_entries = []
        self.color_picks = []
        tk.Label(self, text="Configure Data Legend").pack(side="top")
        # make a section to modify each line plotted so far
        for i in range(_master.data.index):
            horizontal_frame = tk.Frame(self)
            horizontal_frame.pack(side="top")
            tk.Label(horizontal_frame, text="Chose color:").pack(side='left')
            self.color_picks.append(tk.StringVar())
            self.color_picks[i].set(_master.data.colors[i])
            drop_menu = tk.OptionMenu(horizontal_frame,
                                      self.color_picks[i],
                                      *COLOR_CHOICES)
            drop_menu.pack(side='left')
            tk.Label(horizontal_frame,
                     text="Change data label:").pack(side='left')
            self.legend_entries.append(tk.StringVar())
            self.legend_entries[i].set(_master.data.label[i])
            tk.Entry(horizontal_frame,
                     textvariable=self.legend_entries[i]).pack(side="left")
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(side='bottom')
        tk.Button(bottom_frame,
                  text='Save',
                  width=10,
                  command=lambda: self.save(_master, graph)).pack(side='left', padx=10,
                                                                  fill=tk.X, expand=1)
        tk.Button(bottom_frame,
                  text='Exit',
                  width=10,
                  command=self.destroy).pack(side='left', padx=10, fill=tk.X, expand=1)

    def save(self, _master, graph):
        """  The user wants to save changes to the data style and legend, impliment it here
        :param _master: master where the data is stored
        :param graph: graph area
        """
        i = 0
        for pick in self.color_picks:
            _master.data.colors[i] = pick.get()
            graph.change_line_color(pick.get(), i)
            _master.data.label[i] = self.legend_entries[i].get()
            i += 1
        graph.update_legend()

        self.destroy()


class EnterLoggingInfo(tk.Toplevel):
    """ Allow the user to enter a line into the logging file at the INFO level
    """
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.title("Logging info")
        tk.Label(self, text="Enter information to log").pack(side='top')
        entry = tk.Text(self, width=30, height=6, wrap=tk.WORD)
        entry.pack(side='top')

        button_frame = tk.Frame(self)
        tk.Button(button_frame,
                  text='Save',
                  width=10,
                  command=lambda: self.save(entry.get("1.0", 'end-1c'))
                  ).pack(side='left', padx=10, fill=tk.X, expand=1)
        tk.Button(button_frame,
                  text='Exit',
                  width=10,
                  command=self.destroy).pack(side='left', padx=10, fill=tk.X, expand=1)
        button_frame.pack(side='top')

    def save(self, message):
        """ There user wants to save data into the logging file
        :param message: message to enter into the logging file
        """
        logging.info("User entered the following message")
        logging.info(message)
        self.destroy()


class EnterCustomTIAResistor(tk.Toplevel):
    """ Allow the user to use a custom resistor for the transimpedance amplifier
    NOTE: Note confirmed this works, will cause voltage error in the working electrode
    """
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        self.title("Use a custom TIA resistor")
        tk.Label(self,
                 text="Enter the custom resistor value used and the channel it is connected to"
                 ).pack(side='top')

        top_frame = tk.Frame(self)
        top_frame.pack(side='top')
        tk.Label(top_frame, text="enter custom resistor value used (in kohms):").pack(side='left')
        _tia_resistor_value = tk.StringVar()
        resistor_value_enter = tk.Entry(top_frame, textvariable=_tia_resistor_value)
        resistor_value_enter.pack(side='left')

        middle_frame = tk.Frame(self)
        middle_frame.pack(side='top')
        # tk.Label(middle_frame, text="enter channel used (0 or 1):").pack(side='left')
        # _channel_value = tk.StringVar()
        # channel_value_entry = tk.Entry(middle_frame, textvariable=_channel_value)
        # channel_value_entry.pack(side='left')

        # tk.Label(self, text="channel 0 is between P0[4] and p6[0]").pack(side='top')
        # tk.Label(self, text="channel 1 is between P0[5] and p6[0]").pack(side='top')

        button_frame = tk.Frame(self)
        button_frame.pack(side='top')
        tk.Button(button_frame,
                  text='Save',
                  width=10,
                  command=lambda: self.save(master, resistor_value_enter.get())
                  # resistor_value_enter.get("1.0", 'end-1c'))  #,
                  # channel_value_entry.get("1.0", 'end-1c'))
                  ).pack(side='left', padx=10, fill=tk.X, expand=1)
        tk.Button(button_frame,
                  text='Exit',
                  width=10,
                  command=self.destroy).pack(side='left', padx=10, fill=tk.X, expand=1)

    def save(self, master, resistor_value):
        """ Save user entered information
        :param master: overall master
        :param resistor_value: resistor values used
        """
        # master.device.set_custom_resistor_channel(channel_value)
        resistor_value = float(resistor_value)
        master.device_params.adc_tia.set_value(resistor_value)
        master.device.set_custom_resistor_channel('0')
        current_limit = 1200.0 / resistor_value
        master.cv.graph.resize_y(current_limit)
        self.destroy()


class VoltageSourceSelect(tk.Toplevel):
    """ Toplevel for the user to select what voltage souce to use
    """

    def __init__(self, master, current_value):
        tk.Toplevel.__init__(self, master=master)
        self.geometry("300x200")
        self.source_selected = None
        self.master = master
        logging.debug('current value: {0}'.format(current_value))
        if current_value == 0:  # no choice has been made yet
            _label = "No voltage selected yet"
        else:
            _label = "Default"

        tk.Label(self, text=_label).pack(side='top')
        tk.Button(self, text="No capacitor installed", width=20,
                  command=lambda: self.send_selection("VDAC")).pack(side='top')
        tk.Button(self, text="DAC capacitor installed", width=20,
                  command=lambda: self.send_selection("DVDAC")).pack(side='top')
        tk.Button(self, text="Not sure (default)", width=20,
                  command=lambda: self.send_selection("default")).pack(side='top')
        tk.Label(self, text="Program needs to restart after selection").pack(side='top')

        self.lift()
        self.attributes("-topmost", True)

    def send_selection(self, source_selected):
        logging.info('source: {0}'.format(source_selected))

        if source_selected == 'VDAC':
            self.master.device.select_voltage_source("8-bit DAC")  # hack
        elif source_selected == "DVDAC":
            self.master.device.select_voltage_source(source_selected)
        else:  # user selected they do not know
            pass

        self.source_selected = source_selected
        self.destroy()


class MasterDestroyer(tk.Toplevel):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master=master)
        self.geometry("300x300")
        self.lift()
        self.attributes("-topmost", True)
        tk.Label(self, text="Program needs to be restarted").pack(side='top')
        tk.Label(self, text="to implement changes").pack(side='top')
        # tk.Button(self, text="Close", width=40, command=lambda: master.destroy()).pack(side='top')
        master.device.destroy()
        os.execl(sys.executable, sys.executable, *sys.argv)
        tk.Button(self, text="Close", width=40, command=lambda: self.destroy()).pack(side='top')
