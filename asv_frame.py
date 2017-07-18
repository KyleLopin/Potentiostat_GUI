# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" tkinter frame to hold all buttons and plotting area for anode stripping
voltammetry experiments
"""
# standard libraries
import logging
import time
import tkFileDialog
import Tkinter as tk
import ttk
# local files
import change_toplevel as change_top
import cv_frame
import pyplot_data_class as data_class
import tkinter_pyplot

__author__ = 'Kyle Vitautas Lopin'

OPTIONS_BACKGROUND = 'lightsteelblue'

COMPLETE_MESSAGE = "Done"
USB_IN_BYTE_SIZE = 64


class ASVFrame(cv_frame.CVFrame):
    """ Frame to hold all the widgets and information to perform anode stripping
    voltammetry experiments
    """

    def __init__(self, *args):
        cv_frame.CVFrame.__init__(self, *args, bg=OPTIONS_BACKGROUND, initialize=False)

        # options_frame = tk.Frame(self, bg=OPTIONS_BACKGROUND, bd=3)
        # TODO: modified below
        self.run_button.config(text="Run ASV",
                               command=lambda: self.device.asv_run(self.graph, self.run_button))

    def make_graph_area(self, master, graph_props):
        """ Make the graph area to display the cyclic voltammetry data.  Use matplotlib if it is
        available or else plot in a tk Canvas
        TODO: Merge this with CV frame so it works better
        :param master: tk.Tk overall master of the program
        :param graph_props: dictionary fo properties on how the graph looks
        :return: the graph object, currently a PyplotEmbed class from tkinter_pyplot
        """
        current_lim = 1.2 * 1000. / master.device_params.adc_tia.tia_resistor
        low_voltage = master.device_params.asv_settings.low_voltage
        high_voltage = master.device_params.asv_settings.high_voltage
        graph = tkinter_pyplot.PyplotEmbed(master,
                                           master.frames[0],
                                           # frame to put the toolbar in NOTE: hack, fix this
                                           graph_props.cv_plot,
                                           self,
                                           current_lim, low_voltage, high_voltage)

        return graph

    class USBHandler(object):
        def __init__(self, graph, device, master, data):
            """ Class to handle all the usb calls to perform anode
            stripping voltammetry experiments
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
            self.settings = master.device_params.asv_settings
            self.usb_packet_count = 0  # how many usb reading to make
            # TODO: bind this in the begining
            self.run_button = None  # placeholder, the first run will assign it

        def send_cv_parameters(self):
            # TODO: send the commands to run a linear sweep at the end of the asv
            logging.debug("sending asv params here")
            formatted_start_volt, start_dac_value = \
                self.format_voltage(self.settings.start_voltage)
            formatted_end_volt, end_dac_value = \
                self.format_voltage(self.settings.end_voltage)
            formatted_freq_divider, pwm_period = \
                self.format_divider(self.settings.sweep_rate)

            self.params.PWM_period = pwm_period

            sweep_type_to_send = "LS"

            # send those values to the device in the proper format for the PSoC amperometry device
            to_amp_device = '|'.join(["S", formatted_start_volt,
                                      formatted_end_volt, formatted_freq_divider,
                                      sweep_type_to_send])

            # save how many data packets should be received back from the usb
            packet_count = (2 * (abs(end_dac_value - start_dac_value) + 1)
                            / (float(USB_IN_BYTE_SIZE) / 2.0))  # data is 2 bytes long
            # round up the packet count
            self.usb_packet_count = int(packet_count) + (packet_count % USB_IN_BYTE_SIZE > 0)
            # calculate what the actual voltage the device will make.  This might be slightly
            # different from the user input because of the VDAC's resolution

            self.device.usb_write(to_amp_device)
            time.sleep(0.01)
            # Write to the timing PWM compare register so the dac adc timing is correct
            compare_value = pwm_period / 2
            self.device.write_timer_compare(compare_value)

        def set_adc_tia(self, *args):
            self.device.set_adc_tia(*args)

        def asv_run(self, graph, run_button):
            # TODO;  when button is pressed have it run an ASV protocol
            # Set the device working electrode to the cleaning voltage
            self.device.start_hardware()

            if not self.run_button:
                self.run_button = run_button

            self.run_button.config(text="Stop ASV", command=self.stop, relief=tk.SUNKEN)

            # device has to start the hardware to set anything
            self.device.start_hardware()

            # Tell the device to hold the Anode at the cleaning voltage
            self.device.set_anode_voltage(self.params.asv_settings.clean_volt)

            # set an after method
            self.after_function = self.master.after(self.params.asv_settings.clean_time * 1000,
                                                    self.change_to_plating_voltage)

        def change_to_plating_voltage(self):
            self.device.set_anode_voltage(self.params.asv_settings.plate_volt)

            self.after_function = self.master.after(self.params.asv_settings.plate_time * 1000,
                                                    self.give_cleaning_step)

        def give_cleaning_step(self):
            self.send_cv_parameters()
            delay_time = self.params.asv_settings.delay_time
            self.run_scan(self.graph, self.run_button, _delay=delay_time)

            self.device.last_experiment = "ASV"  # Let the device know the look up table will
            # be for an ASV run incase they want to run a CV later

        def stop(self):
            # tell the device to stop
            self.run_button.config(text="Run",
                                   command=lambda: self.asv_run(self.graph, self.run_button),
                                   relief=tk.RAISED)
            self.master.after_cancel(self.after_function)
            self.device.reset()

    class CVSettingDisplay(tk.Frame):
        def __init__(self, _master, _frame, graph, device_params, device):
            tk.Frame.__init__(self, master=_frame)
            # Make String variables to hold the strings that state the parameters; bind them to self
            # so they are easy to pass between functions
            self.clean_voltage_var_str = tk.StringVar()
            self.cleaning_time_var_str = tk.StringVar()
            self.plating_voltage_var_str = tk.StringVar()
            self.plating_time_var_str = tk.StringVar();
            self.end_voltage_var_str = tk.StringVar()
            self.freq_var_str = tk.StringVar()
            self.current_var_str = tk.StringVar()
            self.device = device

            # Make Labels to display the String variables
            tk.Label(textvariable=self.clean_voltage_var_str, master=self).pack(side='top')
            tk.Label(textvariable=self.cleaning_time_var_str, master=self).pack(side='top')
            tk.Label(textvariable=self.plating_voltage_var_str, master=self).pack(side='top')
            tk.Label(textvariable=self.plating_time_var_str, master=self).pack(side='top')
            tk.Label(textvariable=self.end_voltage_var_str, master=self).pack(side='top')
            tk.Label(textvariable=self.freq_var_str, master=self).pack(side='top')
            tk.Label(textvariable=self.current_var_str, master=self).pack(side='top')

            # make a button to change the cyclic voltammetry setting
            tk.Button(self,
                      text="Change Settings",
                      command=lambda: self.change_asv_settings(_master, graph)).pack(side='bottom',
                                                                                     fill=tk.BOTH)

            self.label_update(device_params)

        def label_update(self, params):
            self.clean_voltage_var_str.set('Cleaning voltage: {0} mV'
                                           .format(params.asv_settings.clean_volt))
            self.cleaning_time_var_str.set('Cleaning time: {0} secs'
                                           .format(params.asv_settings.clean_time))
            self.plating_voltage_var_str.set('Plating voltage: {0} mV'
                                             .format(params.asv_settings.plate_volt))
            self.plating_time_var_str.set('Cleaning time: {0} secs'
                                          .format(params.asv_settings.plate_time))
            self.end_voltage_var_str.set('Peak voltage: {0} mV'
                                         .format(params.asv_settings.end_voltage))
            self.freq_var_str.set('Sweep rate: {0} V/s'
                                  .format(params.asv_settings.sweep_rate))
            self.current_var_str.set(u'Current range: \u00B1 {0} \u00B5A'
                                     .format(1000 / params.adc_tia.tia_resistor))

        def change_asv_settings(self, master, graph):
            change_top.ASVSettingChanges(self, master, graph, self.device)

        def set_current_var_str(self, tia_value):
            self.current_var_str.set(u'Current range: {0}'
                                     .format(tia_value))
