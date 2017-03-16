# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" Graphical user interface to control PSoC electrochemical device main file
"""
# standard libraries
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NavToolbar
import Tkinter as tk
# local files
import change_toplevel as toplevel

__author__ = 'Kyle Vitautas Lopin'

LEGEND_SPACE_RATIO = 0.9


class PyplotEmbed(tk.Frame):
    """
    Class that will make a tkinter frame with a matplotlib plot area embedded in the frame
    """

    def __init__(self, master, toolbox_frame, plt_props, _master_frame, y_lims, x_low, x_high):
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
        self.l = None
        self.user_sets_labels_after_run = True
        self.label_instance = ""
        # Make an area to graph the data
        self.graph_area = tk.Frame(self)
        self.plotted_lines = [] # make a list to hold the Line2D to display in the graph
        self.data = _master_frame.data  # alias the data for this class to the main data

        self.legend_displayed = False

        # initiate the pyplot area
        self.init_graph_area(plt_props, toolbox_frame, y_lims, x_low, x_high)

        self.toolbar_status = False

    def init_graph_area(self, plt_props, toolbox_frame, y_lim, x_low, x_high):
        """
        take the tkinter Frame (self) and embed a pyplot figure into it
        :param plt_props: dictionary of properties of the pyplot
        :return: bind figure and axis to this instance
        """
        self.graph_area.figure_bed = plt.figure(figsize=(5, 4))
        self.graph_area.axis = plt.subplot(111)
        self.graph_area.axis.format_coord = lambda x, y: ""  # remove the coordinates in the toolbox
        # go through the plot properties and apply each one that is listed
        for key, value in plt_props.iteritems():
            eval("plt." + key + "(" + value + ")")
        # get the limits of the x axis from the parameters if they are not in the properties
        if "xlim" not in plt_props:
            logging.info("setting xlim (low, high): {0}, {1}".format(x_low, x_high))
            plt.xlim(x_low, x_high)

        # calculate the current limit that can be reached, which depends on the resistor value
        #  of the TIAassume the adc can read +- 1V (1000 mV)
        plt.ylim(-y_lim, y_lim)
        # format the graph area, make the canvas and show it
        self.graph_area.figure_bed.set_facecolor('white')
        self.graph_area.canvas = FigureCanvasTkAgg(self.graph_area.figure_bed, master=self)
        self.graph_area.canvas._tkcanvas.config(highlightthickness=0)
        # Make a binding for the user to change the data legend
        # uncomment below to start making a data legend editor
        self.graph_area.canvas.mpl_connect('button_press_event', self.legend_handler)
        # Make the toolbar and then unpack it.  allow the user to display or remove it later
        self.toolbar = NavToolbar(self.graph_area.canvas, toolbox_frame)
        self.toolbar.pack_forget()

        self.graph_area.canvas.draw()
        self.graph_area.canvas.get_tk_widget().pack(side='left', fill=tk.BOTH, expand=1)

    def update_data(self, x_data, y_data, _raw_y_data=None, label=None):
        if self.user_sets_labels_after_run:
            self.data.add_data(x_data, y_data, _raw_y_data)
            self.display_data()
            if not label:
                toplevel.UserSetDataLabel(self)
            else:
                self.change_label(label)
        else:
            self.data.add_data(x_data, y_data, _raw_y_data)
            self.display_data()

    def change_label(self, label, index=None):
        """
        :param label:
        :param index:
        :return:
        """
        if not index:
            index = self.data.index - 1

        self.data.change_label(label, index)
        self.update_legend()

    def add_notes(self, _notes):
        """ Save a note to the data to save with it
        :param _notes: string
        """
        self.data.notes[-1] = _notes

    def display_data_user_input(self, x_data, y_data):
        """ Update the label to what the user inputted, and display the data
        :param x_data: list - x-axis data
        :param y_data: list - y-axis data
        """
        label = self.label_instance
        self.display_data(x_data, y_data, self.data.index-1)

    def display_data(self):
        """ Take in a x and y data set and plot them in the self instance of the pyplot
        :param x_data: x axis data
        :param y_data: y axis data
        :return:
        """
        index = self.data.index - 1  # it was incremented at the end of the add_data method
        x_data = self.data.voltage_data[index]
        y_data = self.data.current_data[index]
        _label = self.data.label[index]
        # if this is the first data series to be added the legend has to be displayed also
        if not self.legend_displayed:
            _box = self.graph_area.axis.get_position()
            self.graph_area.axis.set_position([_box.x0, _box.y0, _box.width * LEGEND_SPACE_RATIO,
                                               _box.height])
            self.legend_displayed = True
        # add the data to the plot area and update the legend
            #  print len(x_data), len(y_data)
            # print self.data.y_raw_data[index]
            # print x_data
            # for i in range(len(x_data)):
            # print x_data[i], self.data.y_raw_data[index][i]
        l = self.graph_area.axis.plot(x_data, y_data, label=_label)
        self.data.colors.append(l[0].get_color())
        self.plotted_lines.append(l)
        self.update_legend()

    def update_amp_data(self, t, y, time_displayed):

        # self.graph_area.axis.clear()
        if not self.l and t:
            self.l, = self.graph_area.axis.plot(t, y)
            self.graph_area.axis.set_xlim(t[-1] - time_displayed, t[-1])
        elif y:
            self.l.set_ydata(y)
            self.l.set_xdata(t)
            self.graph_area.axis.set_xlim(t[-1] - time_displayed, t[-1])
            # self.graph_area.axis.set_ylim(0, 60000)
        self.graph_area.canvas.draw()

    def update_legend(self):
        """ Update the legend and redraw the graph
        """
        handle, labels = self.graph_area.axis.get_legend_handles_labels()

        self.graph_area.axis.legend(handle, self.data.label,
                                    loc='center left',
                                    bbox_to_anchor=(1, 0.5),
                                    title='Data series',
                                    prop={'size': 10},
                                    fancybox=True)  # not adding all this screws it up
        # up for some reason
        self.graph_area.canvas.show()  # update the canvas where the data is being shown

    def delete_all_lines(self):
        """ Remove all the lines from the graph
        """
        logging.debug("deleting all lines")
        while self.plotted_lines:  # remove lines release all the memory
            l = self.plotted_lines.pop(0)
            l.pop().remove()  # self.plotted_lines is a list of list so you have to pop twice
            del l  # see stackoverflow "how to remove lines in a matplotlib"

        # Update the legend with an empty data set but will keep the title and box showing
        # in the graph area
        self.update_legend()

    def delete_a_line(self, index):
        """ Delete a single line from the graph
        :param index:  int, index of which line to delete. the lines are saved in a list called
        self.plotted_lines
        """
        logging.debug("deleting line: %i", index)
        line = self.plotted_lines.pop(index)
        self.data.remove_data(index)
        line.pop().remove()
        del line  # release memory
        self.update_legend()

    def change_line_color(self, _color, index):
        """ Change the color of a line
        :param _color: tkinter color option to change to
        :param index: index of which line in the self.plotted_lines list to change
        """
        self.plotted_lines[index][0].set_color(_color)
        self.data.colors[index] = _color

    def update_graph(self):
        """ Redraw the graoh
        """
        self.graph_area.canvas.show()

    def toolbar_toggle(self):
        """ Display or remove the toolbar from the GUI
        """
        if self.toolbar_status:  # there is a toolbar, so remove it
            self.toolbar.pack_forget()
            self.toolbar_status = False
        else:  # no toolbar yet so add one
            self.toolbar.pack(side='left', anchor='w')
            self.toolbar_status = True

    def legend_handler(self, event):
        """ Bind event of clicking on the data legend to call up a top level to change the data
        style and label
        :param event: click event that occured
        """
        if event.x > (0.82 * self.winfo_width()):  # if mouse is clicked on the right side
            self.master.change_data_labels()

    def resize_x(self, x_low, x_high):
        """ Change the scale of the x axis
        :param x_low: lower limit on x axis
        :param x_high: upper limit on x axis
        """
        self.graph_area.axis.set_xlim([x_low, x_high])
        self.graph_area.canvas.show()

    def resize_y(self, _current_limit):
        """ Change the scale of the y axis
        :param _current_limit: most current (positive or negative)
        """
        self.graph_area.axis.set_ylim(-_current_limit * 1.2, _current_limit * 1.2)
        self.graph_area.canvas.show()
