# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" Graphical user interface to control PSoC electrochemical device main file
"""
# standard libraries
import csv
import logging
import Tkinter as tk
import traceback
import ttk
# local files
import amp_frame
import change_toplevel as change_top
import cv_frame
import graph_properties
import option_menu
import properties
import pyplot_data_class as data_class
import usb_comm

__author__ = 'Kyle Vitautas Lopin'

OPTIONS_BACKGROUND = 'LightCyan4'


class AmpGUI(tk.Tk):
    """ Graphical User Interface to interact with the PSoC electrochemical device
    """
    def __init__(self, parent=None):

        logging.basicConfig(level=logging.DEBUG,
                            format="%(levelname)s %(module)s %(lineno)d: %(message)s")
        self.data_save_type = "Converted"
        self.device_params = properties.DeviceParameters()
        self.display_type = check_display_type()
        tk.Tk.__init__(self, parent)
        self.parent = parent
        self.voltage_source_label = tk.StringVar()
        self.device = usb_comm.AmpUsb(self, self.device_params)
        graph_props = graph_properties.GraphProps()

        # Make Notebooks to separate the CV and amperometry methods
        self.notebook = ttk.Notebook(self)
        self.frames = self.make_bottom_frames()

        self.cv = cv_frame.CVFrame(self, self.notebook, graph_props)
        self.amp = amp_frame.AmpFrame(self, self.notebook, graph_props)

        self.notebook.add(self.cv, text="Cyclic Voltammetry")
        self.notebook.add(self.amp, text="Amperometry")
        self.notebook.pack(side='top', expand=True, fill=tk.BOTH)
        self.init()

    def init(self):
        """
        make all the widget elements in this method
        :return:
        """

        bottom_frame = self.frames
        tk.Label(bottom_frame[2], textvariable=self.voltage_source_label).pack(
            side='right')
        # make a button to display connection settings and allow user to try to reconnect
        self.make_connect_button(bottom_frame[1])

        # self.notebook.pack(side='top', expand=True, fill=tk.BOTH)
        # make the option menu
        option_menu.OptionMenu(self)

    def set_data_type(self, _type):
        logging.debug('++++++++++++++++FIGURE OUT WHAT THIS DOES')
        self.data_save_type = _type

    def make_connect_button(self, _frame):
        """
        Make a button that will allow the user to connect to the amperometry device if it is
        available. This checks if a device is already connected (in which case it does nothing) and
         attempts to connect if a device is not already attached [see method connect for more
        details].
        The button will be red if no device is connected and green if it is connected, except on
        mac devices as there tcl (or something) does not allow the buttons to be colored
        :param _frame: tk frame to put the button in
        """
        self.connect_button = tk.Button(_frame, command=lambda: self.connect(self.connect_button))
        if not hasattr(self, "device"):  # if the device is not there just pass
            return

        if hasattr(self.device, "found"):
            if self.device.found and self.device.working:
                self.connect_button.config(text="Connected", bg='green')
            elif self.device.found:  # device i
                self.connect_button.config(text="Not Connected", bg='red')
            else:
                self.connect_button.config(text="Device Not Found", bg='red')
        else:
            self.connect_button.config(text="No Device", bg='red')
        self.connect_button.pack(side='bottom')

    def change_data_labels(self):
        """
        Call a toplevel to allow the user to change data labels in the legend
        :return:
        """
        change_top.ChangeDataLegend(self)

    def set_voltage_source_label(self, message):
        self.voltage_source_label.set(message)

    def open_data(self):
        """
        Open a csv file that has the data saved in it, in the same format as this program
        saves the data.
        NOTE:
        _data_hold - holds the data as its being pulled from the file with the structure
        _data_hold = [ [x-data-array], [y1-data-array], [y2-data-array], .., [yn-data] ]
        """
        print "TODO: open data"
        logging.error("open data here")
        _file_name = self.open_file('open')  # get a filename
        # Confirm that the user supplied a file
        if _file_name:
            print "insert function here"
            logging.info("a file named %s opened", _file_name)
            with open(_file_name, 'rb') as _file:
                _reader = csv.reader(_file)  # create reader from file

                first_array = _reader.next()  # get the first line that has the data labels
                _data_hold = []  # create a list to hold the data
                # Make lists to hold the voltage and data arrays
                for i in range(len(first_array)):  # make as many lists as there columns in the file
                    _data_hold.append([])

                for row in _reader:
                    for i, data in enumerate(row):
                        _data_hold[i].append(float(data))
            _file.close()

            self.graph.update_data(_data_hold[0], _data_hold[1])
            try:
                # Make the data structure and display the data
                self.graph.update_data(_data_hold[0], _data_hold[1])

            except Exception as error:
                logging.error("%s - exception called", error)

    def save_selected_data(self):
        print "TODO: save selected data"
        logging.error("save selected data here")

    def user_select_delete_some_data(self):
        change_top.UserSelectDataDelete(self)

    def delete_all_data_user_prompt(self):
        change_top.UserDeleteDataWarning(self)

    def delete_all_data(self):
        """ Delete all the data collected so far and clear the lines from the plot area
        :return:
        """
        # Clear data
        logging.debug("len self.data.values: %i", self.data.index)
        # Delete all displayed lines
        self.graph.delete_all_lines()
        self.data = data_class.PyplotData()

    def quit(self):
        self.destroy()

    def set_adc_channel(self, _channel):
        self.device_params.adc_tia.adc_channel = _channel

    def connect(self, button=None):
        """
        Function the connect button is attached to, to try to connect a amperometry PSoC device
        and display if the device is connected or not
        :param button: button the user clicks to try to connect the device
        :return:
        """
        logging.debug("trying connecting")

        if self.device.connected:
            logging.info("device is connected")
        else:
            logging.debug("attempting to connect")
            self.device = usb_comm.AmpUsb(self, self.device_params)
            # If no device then try to connect
            if self.device.working:
                # If a device was just found then change the button's appearance
                if button:
                    button["text"] = 'Connected'
                    button.config(bg='green')
            else:
                logging.info("No Device detected")  # If still no device detected, warn the user

    def failed_connection(self):  # this is not working now
        logging.info("failed connection")

        # usb.util.dispose_resources()
        if hasattr(self, "device"):
            # self.device.destroy()
            pass
        if hasattr(self, "connect_button"):
            self.connect_button.config(text="Not Connected", bg='red')

    def make_bottom_frames(self):
        """
        To pack the matplotlib toolbar and connect button in a nice layout make a frame along the
        bottom ofthe GUI and fill it with 3 'evenly' spaced frames on the bottom of the GUI to put
        toolbar and connect button
        NOTE: if you fill the frames you can see they are not evenly space, but it looks ok so meh
        :return:
        """
        # make frame to line the bottom of the GUI
        main_bottom = tk.Frame(self)
        main_bottom.pack(side='bottom', fill=tk.X)
        # make a list to fill with the 3 frames and pack them
        bottom_frame = []
        for i in range(3):
            bottom_frame.append(tk.Frame(main_bottom, width=220, height=35))
            bottom_frame[i].pack(side='left', fill=tk.X, expand=1)
        return bottom_frame

    def update_param_dict222(self):
        """
        TODO: deprecate this
        update how many data points (dac voltage changes and adc voltage reads) are on each 'side'
        of the cyclic voltammetry scan ["length_side"] and how many data points total there are
        (dac voltage changes and adc voltage reads)

        :return: none, just update the global device_params
        """
        self.device_params.length_side = (self.device_params.cv_settings.high_voltage -
                                          self.device_params.cv_settings.low_voltage)
        self.device_params.data_pts = 2 * (self.device_params.length_side + 1)

        # class CVSettingDisplay22222(tk.Frame):
        #     """
        #     Class that makes a frame displaying the settings for a cyclic voltammetry experiment
        #     """
        #
        #     def __init__(self, _master, _frame, graph, device_params):
        #         tk.Frame.__init__(self, master=_frame)
        #         # Make String variables to hold the strings that state the parameters; bind them to self
        #         # so they are easy to pass between functions
        #         self.low_voltage_var_str = tk.StringVar()
        #         self.high_voltage_var_str = tk.StringVar()
        #         self.freq_var_str = tk.StringVar()
        #         self.current_var_str = tk.StringVar()
        #
        #         # Make Labels to display the String variables
        #         tk.Label(textvariable=self.low_voltage_var_str, master=self).pack()
        #         tk.Label(textvariable=self.high_voltage_var_str, master=self).pack()
        #         tk.Label(textvariable=self.freq_var_str, master=self).pack()
        #         tk.Label(textvariable=self.current_var_str, master=self).pack()
        #         # make a button to change the cyclic voltammetry settings
        #         tk.Button(self,
        #                   text="Change Settings",
        #                   command=lambda: self.change_cv_settings(_master, graph)).pack(side='bottom',
        #                                                                                 fill=tk.BOTH)
        #
        #         self.cv_label_update(device_params)
        #
        #     def cv_label_update(self, device_params):
        #         """
        #         Update the user's display of what the parameters of the cyclic voltammetry  scan are set to
        #         """
        #         self.low_voltage_var_str.set('Start voltage: ' +
        #                                      str(device_params.cv_settings.low_voltage) +
        #                                      ' mV')
        #         self.high_voltage_var_str.set('End voltage: ' +
        #                                       str(device_params.cv_settings.high_voltage) +
        #                                       ' mV')
        #         self.freq_var_str.set('Sweep rate: ' +
        #                               str(device_params.cv_settings.sweep_rate) +
        #                               ' V/s')
        #         self.current_var_str.set(u'Current range: \u00B1' +
        #                                  str(1000 / device_params.adc_tia.tia_resistor) +
        #                                  u' \u00B5A')
        #
        #     def change_cv_settings(self, master, graph):
        #         """
        #         Make a dialog window to allow the user to change the cyclic voltammetry sweep parameters
        #         For now, this just calls the SettingChanges class in change_toplevel
        #         note that self here is the main window
        #
        #         :param cv_graph: graph where the data is displayed (needed so that the routine can
        #         change the axis scales)
        #         :return:
        #         """
        #         change_top.SettingChanges(master, graph)  # bind toplevel to the root tk.tk


#
# def open_file(_type):
#     """
#     Make a method to return an open file or a file name depending on the type asked for
#     :param _type:
#     :return:
#     """
#     # Make the options for the save file dialog box for the user
#     file_opt = options = {}
#     options['defaultextension'] = ".csv"
#     options['filetypes'] = [('All files', '*.*'), ("Comma separate values", "*.csv")]
#     if _type == 'saveas':
#         # Ask the user what name to save the file as
#         _file = tkFileDialog.asksaveasfile(mode='wb', **file_opt)
#     elif _type == 'open':
#         _filename = tkFileDialog.askopenfilename(**file_opt)
#         return _filename
#     return _file


def get_data_from_csv_file(_filename):
    with open(_filename, 'rb') as _file:
        _reader = csv.reader(_file)  # create reader from file

        first_array = _reader.next()  # get the first line that has the data labels
        _data_hold = []  # create a list to hold the data
        # Make lists to hold the voltage and data arrays
        for i in range(len(first_array)):  # make as many list as there columns in the csv file
            _data_hold.append([])

        for row in _reader:
            for i, data in enumerate(row):
                _data_hold[i].append(float(data))
    _file.close()
    return _data_hold


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

if __name__ == '__main__':

    app = AmpGUI()
    app.title("Amperometry Device")
    app.geometry("850x400")
    app.mainloop()
