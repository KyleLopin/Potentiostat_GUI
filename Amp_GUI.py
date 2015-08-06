__author__ = 'Kyle Vitautas Lopin'

import Tkinter as tk
import amp_usb
import ttk
import change_toplevel as change_top
import tkinter_canvas_graph
import tkinter_pyplot
import csv
import tkFileDialog
import DataDisplay

operation_params = {'low_cv_voltage': -500, # units: mv
                    'high_cv_voltage': 750, # units: mv
                    'sweep_rate': 1.0,  # units: V/s
                    'TIA_resistor': 20}  # units: k ohms
options_background = 'LightCyan4'


class AmpGUI(tk.Tk):

    def __init__(self, parent=None):

        self.operation_params = operation_params
        self.display_type = self.check_display_type()
        tk.Tk.__init__(self, parent)
        self.parent = parent
        self.device = amp_usb.amp_usb(self, operation_params)
        self.init()


    def init(self):
        """
        make all the widget elements in this method
        :return:
        """
        """Make Notebooks to separate the CV and amperometry methods"""
        self.notebook = ttk.Notebook(self)
        amp_frame = ttk.Frame(self.notebook)
        cv_frame = ttk.Frame(self.notebook)
        self.notebook.add(cv_frame, text="Cyclic Voltammetry")
        self.notebook.add(amp_frame, text="Amperometry")

        """Make and pack the canvases to display the data
         TODO: make this so if the user has matplotlib installed, it will use that method instead"""
        amp_plot_properties = {'xlabel' : "'time'",
                               'ylabel' : "'current'",
                               'xlim' : "[0, 200]",
                               'ylim' : "[-.1,1]",
                               'title': "'Amperometry time course'",
                               'subplots_adjust': "bottom=0.15, left=0.12"}
        CV_plot_properties = {'xlabel' : "'voltage (mV)'",
                              'ylabel' : "'current'",
                              'title': "'Cyclic Voltammetry'",
                              'subplots_adjust': "bottom=0.15, left=0.12"}
        CV_canvas_properties = {'xlabel' : "voltage (mV)",
                                'ylabel' : "current",
                                'width' : 600,
                                'height' : 300,
                                'xlim' : [-500, 500],
                                'ylim' : [-1, 1],
                                'title': "Cyclic Voltammetry"}
        amp_canvas_properties = {'xlabel' : "time",
                                'ylabel' : "current",
                                'width' : 600,
                                'height' : 300,
                                'xlim' : [000, 200],
                                'ylim' : [-1, 1],
                                'title': "Amperometry time course"}

        self.update_param_dict()

        if self.display_type == 'matplotlib': # debug on
            amp_graph = tkinter_pyplot.pyplot_embed(amp_plot_properties, amp_frame, operation_params)
            cv_graph = tkinter_pyplot.pyplot_embed(CV_plot_properties, cv_frame, operation_params)
        elif self.display_type == 'canvas': # debug on
            amp_graph = tkinter_canvas_graph.canvas_graph_embed(master=amp_frame, properties=amp_canvas_properties)
            cv_graph = tkinter_canvas_graph.canvas_graph_embed(master=cv_frame, properties=CV_canvas_properties)

        self.build_cv_notebook(cv_graph, cv_frame)
        amp_graph.pack(expand=True, fill=tk.BOTH)

        # amp_canvas = tk.Canvas(master=amp_frame, width=600, height=300)

        # amp_canvas.pack(side='top')
        self.notebook.pack(side='top', expand=True, fill=tk.BOTH)

        # make a button to display connection settings and allow user to try to reconnect
        self.make_connect_button()

    def build_cv_notebook(self, cv_graph, cv_frame):
        cv_graph.pack(side='left', expand=True, fill=tk.BOTH)
        # cv_canvas = tk.Canvas(master=cv_frame, width=600, height=300)
        # cv_canvas.pack(side='left', expand=True, fill=tk.BOTH)
        """Make frames to put the options and settings for the CV scans """
        CV_options_frame = tk.Frame(cv_frame, bg=options_background, bd=3)
        CV_options_frame.pack(side='left', fill=tk.Y, expand=True)
        CV_settings_frame = tk.Frame(CV_options_frame)
        CV_settings_frame.pack(side='top')
        # make a label that displays the low voltage, high voltage and frequency settings for the
        # cyclic voltammetry frame
        self.make_cv_settings_display(CV_settings_frame)
        # make a button to run a cyclic voltammetry scan
        tk.Button(CV_options_frame,
                  text="Run CV Scan",
                  command=lambda: self.device.run_scan(cv_graph)).pack(side='bottom', fill=tk.BOTH)
        """Make a button to allow the user to export the data"""
        tk.Button(CV_options_frame,
                  text="Save data",
                  command=lambda: self.save_data()).pack(side='bottom', fill=tk.BOTH)

        # make a button to allow the user to view the toolbar
        toolbar_button = tk.Button(CV_options_frame,
                                   text="Add toolbar",
                                   command=lambda: cv_graph.toolbar_toggle())
        toolbar_button.pack(side='bottom', fill=tk.BOTH)

        # make a button to change the cyclic voltammetry settings
        tk.Button(CV_settings_frame,
                  text="Change Settings",
                  command=lambda: self.change_cv_settings(cv_graph)).pack(side ='bottom', fill=tk.BOTH)

    def check_display_type(self):
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
        cv_low_voltage_label = tk.Label(textvariable=self.low_voltage_varstr, master= _frame)
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

    def update_param_dict(self):
        operation_params["length_side"] = operation_params["high_cv_voltage"] - operation_params["low_cv_voltage"]
        operation_params["data_pts"] = 2*(operation_params["length_side"]+1)

    def make_connect_button(self):
        """
        Make a button that will allow the user to connect to the ampereometry device if it is available
        This checks if a device is already connected (in which case it does nothing) and attempts to connect if a device
        is not already attached [see method connect for more details]
        The button will be red if no device is connected and green if it is connected, except on mac devices as there
        tcl (or something) does not allow the buttons to be colored
        :return:
        """
        self.connect_button = tk.Button(self, command=lambda: self.connect())
        if self.device.connected:
            self.connect_button["text"] = "Connected"
            self.connect_button.config(bg='green')
        else:
            self.connect_button["text"] = "Not Connected"
            self.connect_button.config(bg='red')

        self.connect_button.pack(side='bottom')

    def save_data(self):
        file_opt = options = {}
        options['defaultextension'] = ".csv"
        options['filetypes'] = ".csv"
        if hasattr(self, "data"):
            _file = tkFileDialog.asksaveasfile(mode='wb', defaultextension='.csv')
            writer = csv.writer(_file, dialect='excel')
            # print type(self.data)
            # print self.data
            for element in self.data:
                writer.writerow([element])
            _file.close()
        else:
            print 'no data'

    def cv_label_update(self):
        """
        Update the user's display of what the parameters of the CV scan are set to
        :return:
        """
        self.low_voltage_varstr.set('Start voltage: '+str(operation_params['low_cv_voltage'])+' mV')
        self.high_voltage_varstr.set('End voltage: '+str(operation_params['high_cv_voltage'])+' mV')
        self.freq_varstr.set('Sweep rate: '+str(operation_params['sweep_rate'])+' V/s')
        self.current_varstr.set(u'Current range: \u00B1'+str(1000/operation_params['TIA_resistor'])+u' \u00B5A')

    def change_cv_settings(self, cv_graph):  # note that self here is the main window
        change_top.setting_changes(self, cv_graph)  # self will become the master of the toplevel


    def connect(self):

        if self.device:
            pass  # If a device is already connected and someone hits the button, ignore it
        else:
            self.device = amp_usb.connect_usb()  # If no device then try to connect
            if self.device:  # If a device was just found then change the button's appearance
                self.connect_button["text"] = 'Connected'
                self.connect_button.config(bg='green')
            else:
                print "No Device detected"  # If still no device detected, warn the user

if __name__ == '__main__':

    app = AmpGUI()
    app.title("Amperometry Device")
    app.geometry("800x400")
    app.mainloop()
