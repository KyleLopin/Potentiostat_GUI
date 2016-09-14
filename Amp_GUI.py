# standard libraries
import logging
import Tkinter as tk
import ttk
import csv
import tkFileDialog
import traceback
# local files
import option_menu
import pyplot_data_class as data_class
import usb_comm
import change_toplevel as change_top
import tkinter_canvas_graph
import tkinter_pyplot
import graph_properties
import properties

__author__ = 'Kyle Vitautas Lopin'
# this shold be obsolete now
operation_params = {'low_cv_voltage': -500,  # units: mv
                    'high_cv_voltage': 500,  # units: mv
                    'sweep_rate': 1.0,  # units: V/s
                    'TIA_resistor': 20,  # units: k ohms
                    'PIDAC_resistor': 9.8,  # kilo ohms
                    'ADC_gain': 1,  # unitless
                    'number_IN_ENDPOINTS': 1,  # how many IN ENDPOINTS to connect to
                    'number_OUT_ENDPOINTS': 1,  # how many IN ENDPOINTS to connect to
                    'smallest_increment_pidac': 1./8.,  # the smallest increment the PIDAC is increased by
                    'clk_freq_isr_pwm': 24000000,  # frequency of the clock that is driving the PWM that triggers isrs
                    'virtual_ground_shift': 1024,  # mv shift in
                    'bits_PIDAC': 11,  # number of bits of the PIDAC
                    'adc_channel': 0,  # which adc channel to get
                    'PWM_period': 30000,  # value in the timing PWM period register
                    'PWM_compare': 15000,  # value in the timing PWM period register
                    'should_process': False,  # variable if the program should export the raw adc numbers or convert it
                    'user_sets_labels_after_run': True}  # lets the user set the data label and make a note after a run

options_background = 'LightCyan4'


class AmpGUI(tk.Tk):
    """
    Graphical User Interface to interact with the PSoC electrochemical device
    Notes:
    self.data is a pyplot_data_class object and handles all the data to be saved, loaded, displayed, etc.  look in
    pyplot_data_class for documentation about self.data
    """
    def __init__(self, parent=None):

        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(module)s %(lineno)d: %(message)s")
        self.data_save_type = "Converted"
        self.device = None  # no device connected yet
        self.data = data_class.PyplotData()

        # self.operation_params = operation_params
        self.device_params = properties.DeviceParameters()
        self.display_type = check_display_type()
        tk.Tk.__init__(self, parent)
        self.parent = parent
        self.device = usb_comm.AmpUsb(self, self.device_params)

        """Make Notebooks to separate the CV and amperometry methods"""
        self.notebook = ttk.Notebook(self)
        amp_frame = ttk.Frame(self.notebook)
        cv_frame = ttk.Frame(self.notebook)
        self.notebook.add(cv_frame, text="Cyclic Voltammetry")
        self.notebook.add(amp_frame, text="Amperometry")

        self.init(amp_frame, cv_frame)

    def init(self, amp_frame, cv_frame):
        """
        make all the widget elements in this method
        :return:
        """
        graph_props = graph_properties.GraphProps()
        self.update_param_dict()
        bottom_frame = self.make_bottom_frames()
        self.make_connect_button(bottom_frame[1])

        """ Add the cyclic voltammetry graph, first decide how to make the graph and then display it
        NOTE: THE canvas_graph_embed DOES NOT WORK RIGHT NOW"""
        if self.display_type == 'matplotlib':
            current_lim = 1.2 * 1000. / self.device_params.TIA_resistor  # calculate the max current measurable
            low_voltage = self.device_params.low_cv_voltage
            high_voltage = self.device_params.high_cv_voltage
            amp_graph = tkinter_pyplot.PyplotEmbed(self,
                                                   bottom_frame[0],
                                                   graph_props.amp_plot,
                                                   amp_frame,
                                                   current_lim, low_voltage, high_voltage)
            cv_graph = tkinter_pyplot.PyplotEmbed(self,
                                                  bottom_frame[0],
                                                  graph_props.cv_plot,
                                                  cv_frame,
                                                  current_lim, low_voltage, high_voltage)
        else:  # NOT WORKING
            amp_graph = tkinter_canvas_graph.canvas_graph_embed(master=amp_frame, properties=graph_props.amp_canvas)
            cv_graph = tkinter_canvas_graph.canvas_graph_embed(master=cv_frame, properties=graph_props.cv_canvas)
        cv_graph.pack(side='left', expand=True, fill=tk.BOTH)
        self.graph = cv_graph
        """ call a routine to make all the components to put in the notebook for cyclic voltammetry """
        self.build_cv_notebook(cv_graph, cv_frame)
        amp_graph.pack(expand=True, fill=tk.BOTH)

        """ make a button to display connection settings and allow user to try to reconnect """

        self.notebook.pack(side='top', expand=True, fill=tk.BOTH)

        """make the option menu"""
        # self.build_option_menu()
        option_menu.OptionMenu(self)

    def set_data_type(self, _type):
        self.data_save_type = _type

    def build_cv_notebook(self, cv_graph, cv_frame):
        """
        Make all the components in the notebook to display the cyclic voltammetry data

        :param cv_graph: graph that will display the cyclic voltammetry data
        :param cv_frame: ttk.Frame (the main frame inserted into ttk.notebook) where all the cyclic voltammetry
        settings and data are displayed
        :return:
        """
        """Make frames to put the options and settings for the CV scans """
        cv_options_frame = tk.Frame(cv_frame, bg=options_background, bd=3)
        cv_options_frame.pack(side='left', fill=tk.Y)
        cv_settings_frame = tk.Frame(cv_options_frame)
        cv_settings_frame.pack(side='top')

        """ make a label that displays the low voltage, high voltage and frequency settings for the
        cyclic voltammetry frame """
        self.make_cv_settings_display(cv_settings_frame)
        self.make_cv_option_frame_buttons(cv_options_frame, cv_graph)

        """ make a button to change the cyclic voltammetry settings """
        tk.Button(cv_settings_frame,
                  text="Change Settings",
                  command=lambda: self.change_cv_settings(cv_graph)).pack(side='bottom', fill=tk.BOTH)

    def make_cv_option_frame_buttons(self, _frame, cv_graph):
        """
        Make and pack all the buttons needed to perform cyclic voltammetry.  These are all the options but what
        the waveform looks like (which is made in the make_cv_settings_display)

        :param _frame: tk frame to make all the buttons in
        :param cv_graph: graph where the cyclic voltammetry data will be displayed in (needed to put in the button
        function calls)
        :return:
        """
        # make a button to run a cyclic voltammetry scan
        tk.Button(_frame,
                  text="Run CV Scan",
                  command=lambda: self.device.run_scan(cv_graph, self)
                  ).pack(side='bottom', fill=tk.BOTH)
        """Make a button to allow the user to export the data"""
        tk.Button(_frame,
                  text="Save data",
                  command=lambda: self.save_all_data()
                  ).pack(side='bottom', fill=tk.BOTH)

        # make button to change data labels
        tk.Button(_frame,
                  text="Change data style",
                  command=lambda: self.change_data_labels()
                  ).pack(side='bottom', fill=tk.BOTH)

        # make a button to delete some of the data
        tk.Button(_frame,
                  text="Delete Data",
                  command=lambda: self.user_select_delete_some_data()
                  ).pack(side='bottom', fill=tk.BOTH)

        # make a button to allow the user to view the toolbar
        toolbar_button = tk.Button(_frame,
                                   text="Add toolbar",
                                   command=lambda: cv_graph.toolbar_toggle())
        toolbar_button.pack(side='bottom', fill=tk.BOTH)

    def make_cv_settings_display(self, _frame):
        """
        Make a display for the parameters the CV is set to

        :param _frame: tk Frame to put display the values in
        :return: None
        """
        """Make String variables to hold the strings that state the parameters; bind them to self so they are easy
        to pass between functions"""
        self.low_voltage_varstr = tk.StringVar()
        self.high_voltage_varstr = tk.StringVar()
        self.freq_varstr = tk.StringVar()
        self.current_varstr = tk.StringVar()

        """Make Labels to display the String variables """
        cv_low_voltage_label = tk.Label(textvariable=self.low_voltage_varstr, master=_frame)
        cv_high_voltage_label = tk.Label(textvariable=self.high_voltage_varstr, master=_frame)
        cv_freq_label = tk.Label(textvariable=self.freq_varstr, master=_frame)
        cv_current_range_label = tk.Label(textvariable=self.current_varstr, master=_frame)

        """Call a function to update all the parameters, this function is used to update display whenever changes
        are made"""
        self.cv_label_update()

        """Display the labels """
        cv_low_voltage_label.pack()
        cv_high_voltage_label.pack()
        cv_freq_label.pack()
        cv_current_range_label.pack()

    def make_connect_button(self, _frame):
        """
        Make a button that will allow the user to connect to the amperometry device if it is available
        This checks if a device is already connected (in which case it does nothing) and attempts to connect if a device
        is not already attached [see method connect for more details]
        The button will be red if no device is connected and green if it is connected, except on mac devices as there
        tcl (or something) does not allow the buttons to be colored

        :param _frame: tk frame to put the button in
        :return:
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
        change_top.ChangeDataLegend(self)

    def open_data(self):
        """
        Open a csv file that has the data saved in it, in the same format as this program
        saves the data.

        _data_hold - holds the data as its being pulled from the file with the structure
        _data_hold = [ [x-data-array], [y1-data-array], [y2-data-array], .., [yn-data] ]

        :return:
        """
        print "TODO: open data"
        logging.error("opendata here")
        _file_name = self.open_file('open')  # get a filename
        """ Confirm that the user supplied a file """
        if _file_name:
            print "insert function here"
            logging.info("a file named %s opened", _file_name)
            with open(_file_name, 'rb') as _file:
                _reader = csv.reader(_file)  # create reader from file

                first_array = _reader.next()  # get the first line that has the data labels
                _data_hold = []  # create a list to hold the data
                """ Make lists to hold the voltage and data arrays """
                for i in range(len(first_array)):  # make as many list as there columns in the csv file
                    _data_hold.append([])

                for row in _reader:
                    for i, data in enumerate(row):
                        _data_hold[i].append(float(data))
            _file.close()

            self.graph.update_data(_data_hold[0], _data_hold[1])
            try:
                """ Make the data structure and display the data """
                self.graph.update_data(_data_hold[0], _data_hold[1])
                pass

            except Exception as e:
                logging.error("%s - exception called", e)
                pass

    def save_all_data(self):
        logging.debug("saving all data")
        if self.data.index == 0:  # no data to save
            logging.info("No data to save")
            return

        """ ask the user for a filename to save the data in """
        _file = open_file('saveas')

        """ Confirm that the user supplied a file """
        if _file:
            """ make a csv writer, go through each data point and save the voltage and current at each point, then
            close the file """
            try:
                writer = csv.writer(_file, dialect='excel')
                # make the first line of the file with the data labels
                l = ["voltage"]  # first line will be the voltages
                for i in range(self.data.index):
                    l.append(self.data.label[i])
                writer.writerow(l)
                print dir(self.data.current_data)
                length = len(self.data.current_data[0])
                width = self.data.index

                # the second row are the notes
                l = [" "]  # first line is voltages so it has no notes
                for i in range(self.data.index):
                    l.append(self.data.notes[i])
                writer.writerow(l)

                # check to see what type of data the user wants to save
                if self.data_save_type == "Converted":
                    _data_array = self.data.current_data
                elif self.data_save_type == "Raw Counts":
                    _data_array = self.data.y_raw_dat
                # go through each data point and save the a list l that is saved in the file with writerow
                for i in range(length):
                    l[0] = self.data.voltage_data[0][i]  # this is only take the voltage of the first run
                    for j in range(width):
                        l[j + 1] = _data_array[j][i]
                    writer.writerow(l)

                _file.close()
            except Exception as e:
                logging.error("failed saving")
                logging.error(e)
                traceback.print_exc()
                _file.close()

    def save_selected_data(self):
        print "TODO: save selected data"
        logging.error("save selected data here")

    def user_select_delete_some_data(self):
        change_top.UserSelectDataDelete(self)

    def delete_some_data(self, list_of_index_to_delete):
        for index in reversed(list_of_index_to_delete):
            self.graph.delete_a_line(index)

    def delete_all_data_user_prompt(self):
        change_top.UserDeleteDataWarning(self)

    def delete_all_data(self):
        """
        Delete all the data collected so far and clear the lines from the plot area
        :return:
        """
        """ Clear data """
        # self.plotted_lines
        logging.debug("len self.data.values: %i", self.data.index)
        """ Delete all displayed lines """
        self.graph.delete_all_lines()
        self.data = data_class.PyplotData()

    def quit(self):
        self.destroy()

    def cv_label_update(self):
        """
        Update the user's display of what the parameters of the cyclic voltammetry  scan are set to
        :return:
        """
        self.low_voltage_varstr.set('Start voltage: ' + str(self.device_params.low_cv_voltage) + ' mV')
        self.high_voltage_varstr.set('End voltage: ' + str(self.device_params.high_cv_voltage) + ' mV')
        self.freq_varstr.set('Sweep rate: ' + str(self.device_params.sweep_rate) + ' V/s')
        self.current_varstr.set(u'Current range: \u00B1' + str(1000 / self.device_params.TIA_resistor) + u' \u00B5A')

    def set_adc_channel(self, _channel):
        self.device_params.adc_channel = _channel

    def change_cv_settings(self, cv_graph):
        """
        Make a dialog window to allow the user to change the cyclic voltammetry sweep parameters
        For now, this just calls the SettingChanges class in change_toplevel
        note that self here is the main window

        :param cv_graph: graph where the data is displayed (needed so that the routine can change the axis scales)
        :return:
        """
        change_top.SettingChanges(self, cv_graph)  # self will become the master of the toplevel

    def connect(self, button=None):
        """
        Function the connect button is attached to, to try to connect a amperometry PSoC device and display if the
        device is connected or not
        :param button: button the user clicks to try to connect the device
        :return:
        """
        logging.debug("trying connecting")

        if self.device.connected:
            logging.info("device is connected")
            pass  # If a device is already connected and someone hits the button, ignore it
        else:
            logging.debug("attempting to connect")
            self.device = usb_comm.AmpUsb(self, self.device_params)  # If no device then try to connect
            if self.device.working:  # If a device was just found then change the button's appearance

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
        To pack the matplotlib toolbar and connect button in a nice layout make a frame along the bottom of
        the GUI and fill it with 3 'evenly' spaced frames on the bottom of the GUI to put toolbar and connect button
        NOTE: if you fill the frames you can see they are not evenly space, but it looks ok so meh
        :return:
        """
        """ make frame to line the bottom of the GUI """
        main_bottom = tk.Frame(self)
        main_bottom.pack(side='bottom', fill=tk.X)
        """ make a list to fill with the 3 frames and pack them """
        bottom_frame = []
        for i in range(3):
            bottom_frame.append(tk.Frame(main_bottom, width=220, height=35))  # this works, not sure why though
            bottom_frame[i].pack(side='left', fill=tk.X, expand=1)
        return bottom_frame

    def update_param_dict(self):
        """
        update how many data points (dac voltage changes and adc voltage reads) are on each 'side' of the cyclic
        voltammetry scan ["length_side"] and how many data points total there are
        (dac voltage changes and adc voltage reads)

        :return: none, just update the global device_params
        """
        self.device_params.length_side = self.device_params.high_cv_voltage - self.device_params.low_cv_voltage
        self.device_params.data_pts = 2 * (self.device_params.length_side + 1)


def open_file(_type):
    """
    Make a method to return an open file or a file name depending on the type asked for
    :param _type:
    :return:
    """
    """ Make the options for the save file dialog box for the user """
    file_opt = options = {}
    options['defaultextension'] = ".csv"
    options['filetypes'] = [('All files', '*.*'), ("Comma separate values", "*.csv")]
    if _type == 'saveas':
        """ Ask the user what name to save the file as """
        _file = tkFileDialog.asksaveasfile(mode='wb', **file_opt)
    elif _type == 'open':
        _filename = tkFileDialog.askopenfilename(**file_opt)
        return _filename
    return _file


def get_data_from_csv_file(_filename):
    with open(_filename, 'rb') as _file:
        _reader = csv.reader(_file)  # create reader from file

        first_array = _reader.next()  # get the first line that has the data labels
        _data_hold = []  # create a list to hold the data
        """ Make lists to hold the voltage and data arrays """
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
