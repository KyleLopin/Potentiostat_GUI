__author__ = 'Kyle Vitautas Lopin'


import logging
import Tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NavToolbar
import pyplot_data_class as data_class
import data_legend_toplevel as legend_top


legend_space_ratio = 0.9


class PyplotEmbed(tk.Frame):
    """
    Class that will make a tkinter frame with a matplotlib plot area embedded in the frame
    """

    def __init__(self, root, toolbox_frame, plt_props, _master_frame, _params):
        """
        Initialize the class with a parent of tkinter Frame and embed a pyplot graph in it
        The class also will have a list to hold the data series that is displayed
        :param toolbox_frame: tkinter frame that the toolbox can be shown in
        :param plt_props: properties of the pyplot
        :param _master: the frame that is the master to this frame
        :param _params: parameters needed for setting up the class
        :return:
        """
        tk.Frame.__init__(self, master=_master_frame)  # initialize with the parent class
        self.master = _master_frame
        """ Make an area to graph the data """
        self.graph_area = tk.Frame(self)
        """ Initialize the class to hold the data """

        self.data = data_class.PyplotData()
        root.data = self.data
        """ Create a list to hold the matplotlib lines """
        self.plotted_lines = []

        self.params = _params
        self.legend_displayed = False

        """ initiate the pyplot area """
        self.init_graph_area(plt_props, toolbox_frame)

        self.toolbar_status = False

    def init_graph_area(self, plt_props, toolbox_frame):
        """
        take the tkinter Frame (self) and embed a pyplot figure into it
        :param plt_props: dictionary of properties of the pyplot
        :return: bind figure and axis to this instance
        """
        self.graph_area.figure_bed = plt.figure(figsize=(5, 4))
        self.graph_area.axis = plt.subplot(111)
        self.graph_area.axis.format_coord = lambda x, y: ""  # remove the coordinates in the toolbox
        """ go through the plot properties and apply each one that is listed """
        for key, value in plt_props.iteritems():
            eval("plt." + key + "(" + value + ")")
        """ get the limits of the x axis from the parameters if they are not in the properties """
        if "xlim" not in plt_props:
            plt.xlim(self.params['low_cv_voltage'], self.params['high_cv_voltage'])

        """ calculate the current limit that can be reached, which depends on the resistor value of the TIA
        assume the adc can read +- 1V (1000 mV)"""
        current_limit = 1000 / self.params['TIA_resistor']  # units: (mV/kohms) micro amperes
        plt.ylim(-current_limit, current_limit)
        """ format the graph area, make the canvas and show it """
        self.graph_area.figure_bed.set_facecolor('white')
        self.graph_area.canvas = FigureCanvasTkAgg(self.graph_area.figure_bed, master=self)
        self.graph_area.canvas._tkcanvas.config(highlightthickness=0)
        """ Make a binding for the user to change the data legend """
        self.graph_area.canvas.mpl_connect('button_press_event', self.legend_handler)
        # self.graph_area.canvas.mpl_connect('pick_event', self.artist_onpick)  # not working for some reason
        """ Make the toolbar and then unpack it.  allow the user to display or remove it later """
        self.toolbar = NavToolbar(self.graph_area.canvas, toolbox_frame)
        self.toolbar.pack_forget()

        self.graph_area.canvas.draw()
        self.graph_area.canvas.get_tk_widget().pack(side='top', fill=tk.BOTH, expand=1)

    def artist_onpick(self, event):  # not working for some reason
        picked_item = event.artist
        self.a = 1
        print "picked item: ", picked_item

    def update_data(self, x_data, y_data, _raw_y_data=None, label=None):
        self.data.add_data(x_data, y_data, _raw_y_data, label)
        self.display_data(x_data, y_data, self.data.index-1)

    def display_data(self, x_data, y_data, index):
        """
        Take in a x and y data set and plot them in the self instance of the pyplot
        :param x_data: x axis data
        :param y_data: y axis data
        :return:
        """
        print index
        label = self.data.values[index].label
        x_test = self.data.values[index].x
        y_test = self.data.values[index].y

        print label
        # self.debug_show(x_data, y_data)
        _index = self.data.index  # index of which data series the incoming data is
        """ if this is the first data series to be added the legend has to be displayed also """
        if not self.legend_displayed:
            _box = self.graph_area.axis.get_position()
            self.graph_area.axis.set_position([_box.x0, _box.y0, _box.width * legend_space_ratio, _box.height])
            self.legend_displayed = True
        logging.debug("len test: %d, %d", len(x_data), len(y_data))  # debug if uneven x and y data are being relieved
        """ add the data to the plot area and update the legend """
# this is where the line is added
        l = self.graph_area.axis.plot(x_data, y_data, label="data {}".format(_index))
        self.plotted_lines.append((self.data.index, l))

        self.graph_area.axis.legend(loc='center left',
                                    bbox_to_anchor=(1, 0.5),
                                    title = 'Data series',
                                    prop={'size': 10},
                                    fancybox=True)  # not adding all this screws it up for some reason
        # self.graph_area.axis.legend.get_frame().set_alpha(0.5)
        self.graph_area.canvas.show()  # update the canvas where the data is beeing shown

    def toolbar_toggle(self):
        """
        Display or remove the toolbar from the GUI
        :return:
        """
        if self.toolbar_status:  # there is a toolbar, so remove it
            self.toolbar.pack_forget()
            self.toolbar_status = False
        else:  # no toolbar yet so add one
            self.toolbar.pack(side='left', anchor='w')
            self.toolbar_status = True

    def legend_handler(self, event):
        """
        :param event:
        :return:
        """
        if event.x > (0.8 * self.winfo_width()):  # if mouse is clicked on the right side
            print "on right side"
            legend_top.DataLegendTop(self)

    def resize_x(self, x_low, x_high):
        """
        Change the scale of the x axis
        :param x_low: lower limit on x axis
        :param x_high: upper limit on x axis
        :return:
        """
        self.graph_area.axis.set_xlim([x_low, x_high])
        self.graph_area.canvas.show()

    def resize_y(self, _current_limit):
        """
        Change the scale of the y axis
        :param _current_limit: most current (positive or negative)
        :return:
        """
        self.graph_area.axis.set_ylim(-_current_limit, _current_limit)
        self.graph_area.canvas.show()


def debug_show(x_data, y_data):
    print "debug showing"
    print len(x_data)
    print len(y_data)
    print y_data[:10]
    print y_data[-10:]
    print y_data[2000:2100]
