# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" tkinter frame to hold all buttons and plotting area for cyclic voltammetry experiments
"""
# standard libraries
import csv
import logging
import Tkinter as tk
import traceback
import ttk
# local files
import change_toplevel as change_top
import tkinter_pyplot

__author__ = 'Kyle Vitautas Lopin'

OPTIONS_BACKGROUND = 'LightCyan4'


class CVFrame(ttk.Frame):
    """
    Frame to hold all the widgets and information to perform cyclic voltammetry experiments
    """

    def __init__(self, master, parent_notebook, graph_properties):
        """
        make a ttk frame to hold all the info for cyclic voltammetry, frame is split in 2, for graph
        area and buttons
        :param master: tk.Tk overall master program
        :param parent_notebook: ttk.Notebook that this frame is embedded
        :param graph_properties:
        """
        ttk.Frame.__init__(self, parent_notebook)
        # self.graph_frame = tk.Frame(self, bg='blue')
        # self.graph_frame.pack(side='left', expand=True, fill=tk.BOTH)

        self.graph = self.make_graph_area(master, graph_properties)
        self.graph.pack(side='left', expand=True, fill=tk.BOTH)
        a = 2
        options_frame = tk.Frame(self, bg=OPTIONS_BACKGROUND, bd=3)
        options_frame.pack(side='left', fill=tk.Y)
        buttons_frame = tk.Frame(options_frame)
        buttons_frame.pack(side='bottom')
        self.make_cv_buttons(buttons_frame, self.graph, master.device)

    def make_graph_area(self, master, graph_props):
        """
        Make the graph area to display the cyclic voltammetry data.  Use matplotlib if it is
        available or else plot in a tk Canvas
        TODO: add canvas option
        :param master: tk.Tk overall master of the program
        :param graph_props: dictionary fo properties on how the graph looks
        :return: the graph object, currently a PyplotEmbed class from tkinter_pyplot
        :::::::::::::::: UPdate when canvas is implemented
        """
        if check_display_type() == 'matplotlib':
            current_lim = 1.2 * 1000. / master.device_params.adc_tia.tia_resistor
            low_voltage = master.device_params.low_cv_voltage
            high_voltage = master.device_params.high_cv_voltage
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
        """
                Make and pack all the buttons needed to perform cyclic voltammetry.  These are all the
                options but what the waveform looks like (which is made in the make_cv_settings_display)

                :param _frame: tk frame to make all the buttons in
                :param cv_graph: graph where the cyclic voltammetry data will be displayed in (needed to
                put in the button function calls)
                :return:
                """
        # make a button to run a cyclic voltammetry scan
        tk.Button(_frame,
                  text="Run CV Scan",
                  command=lambda: device.run_scan(cv_graph, self)).pack(side='bottom',
                                                                        fill=tk.BOTH)
        # Make a button to allow the user to export the data
        logging.debug('buttons lambda functions changed')
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
        logging.debug("developer button added here")
        tk.Button(_frame,
                  text="Custom Button",
                  command=self.custom_button).pack(side='bottom',
                                                   fill=tk.BOTH)

    def change_data_labels(self):
        """
        Call a toplevel to allow the user to change data labels in the legend
        :return:
        """
        change_top.ChangeDataLegend(self)

    def save_all_data(self):
        """
        Save all the data displayed, allow the user to choose the filename
        """
        logging.debug("saving all data")
        if self.data.index == 0:  # no data to save
            logging.info("No data to save")
            return

        # ask the user for a filename to save the data in
        _file = open_file('saveas')

        # Confirm that the user supplied a file
        if _file:
            # make a csv writer, go through each data point and save the voltage and current at
            # each point, then close the file
            try:
                writer = csv.writer(_file, dialect='excel')
                # make the first line of the file with the data labels
                line = ["voltage"]  # first line will be the voltages
                for i in range(self.data.index):
                    line.append(self.data.label[i])
                writer.writerow(line)
                print dir(self.data.current_data)
                length = len(self.data.current_data[0])
                width = self.data.index

                # the second row are the notes
                line = [" "]  # first line is voltages so it has no notes
                for i in range(self.data.index):
                    line.append(self.data.notes[i])
                writer.writerow(line)

                # check to see what type of data the user wants to save
                if self.data_save_type == "Converted":
                    _data_array = self.data.current_data
                elif self.data_save_type == "Raw Counts":
                    _data_array = self.data.y_raw_data
                # go through each data point and save the a list l that is saved
                # in the file with writerow
                for i in range(length):
                    # this is only take the voltage of the first run
                    line[0] = self.data.voltage_data[0][i]
                    for j in range(width):
                        line[j + 1] = _data_array[j][i]
                    writer.writerow(line)

                _file.close()
            except Exception as e:
                logging.error("failed saving")
                logging.error(e)
                traceback.print_exc()
                _file.close()

    def user_select_delete_some_data(self):
        change_top.UserSelectDataDelete(self)

    def custom_button(self):
        self.device.usb_write('B')
        self.after(400, func=self.custom_after)


def check_display_type():
    """
    Check if matplotlib graph can be used,
    :return: type that can be used to make display graph, matplotlib or canvas as a string
    """
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        return "matplotlib"
    except ImportError, e:
        return "canvas"


class CVSettingDisplay(tk.Frame):
    """
    Class that makes a frame displaying the settings for a cyclic voltammetry experiment
    """

    def __init__(self, _master, _frame, graph, device_params):
        tk.Frame.__init__(self, master=_frame)
        # Make String variables to hold the strings that state the parameters; bind them to self
        # so they are easy to pass between functions
        self.low_voltage_var_str = tk.StringVar()
        self.high_voltage_var_str = tk.StringVar()
        self.freq_var_str = tk.StringVar()
        self.current_var_str = tk.StringVar()

        # Make Labels to display the String variables
        tk.Label(textvariable=self.low_voltage_var_str, master=self).pack()
        tk.Label(textvariable=self.high_voltage_var_str, master=self).pack()
        tk.Label(textvariable=self.freq_var_str, master=self).pack()
        tk.Label(textvariable=self.current_var_str, master=self).pack()
        # make a button to change the cyclic voltammetry settings
        tk.Button(self,
                  text="Change Settings",
                  command=lambda: self.change_cv_settings(_master, graph)).pack(side='bottom',
                                                                                fill=tk.BOTH)

        self.cv_label_update(device_params)

    def cv_label_update(self, device_params):
        """
        Update the user's display of what the parameters of the cyclic voltammetry  scan are set to
        """
        self.low_voltage_var_str.set('Start voltage: ' +
                                     str(device_params.low_cv_voltage) +
                                     ' mV')
        self.high_voltage_var_str.set('End voltage: ' +
                                      str(device_params.high_cv_voltage) +
                                      ' mV')
        self.freq_var_str.set('Sweep rate: ' +
                              str(device_params.sweep_rate) +
                              ' V/s')
        self.current_var_str.set(u'Current range: \u00B1' +
                                 str(1000 / device_params.adc_tia.tia_resistor) +
                                 u' \u00B5A')

    def change_cv_settings(self, master, graph):
        """
        Make a dialog window to allow the user to change the cyclic voltammetry sweep parameters
        For now, this just calls the SettingChanges class in change_toplevel
        note that self here is the main window

        :param cv_graph: graph where the data is displayed (needed so that the routine can
        change the axis scales)
        :return:
        """
        change_top.SettingChanges(master, graph)  # bind toplevel to the root tk.tk
