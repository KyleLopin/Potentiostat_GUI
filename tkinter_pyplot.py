__author__ = 'Kyle Vitautas Lopin'


import Tkinter as tk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NavToolbar
#matplotlib.use("TkAgg")



class pyplot_embed(tk.Frame):

    def __init__(self, plt_props, _master, _params):

        tk.Frame.__init__(self, master=_master)
        self.init(plt_props, _params)
        self.toolbar_status = False

    def init(self, plt_props, _params):
        self.figure_bed = plt.figure(figsize=(7, 3.5))
        self.axis = self.figure_bed.add_subplot(111)

        for key, value in plt_props.iteritems():
            eval("plt." + key + "(" + value + ")")
        # self.axis.set_axis_bgcolor('red')
        if "xlim" not in plt_props:
            plt.xlim(_params['low_cv_voltage'], _params['high_cv_voltage'])
        # calculate the current limit that can be reached, which depends on the resistor value of the TIA
        # assume the adc can read +- 1V (1000 mV)
        current_limit = 1000 / _params['TIA_resistor']  # units: (mV/kohms) micro amperes
        plt.ylim(-current_limit, current_limit)
        self.figure_bed.set_facecolor('white')
        self.canvas = FigureCanvasTkAgg(self.figure_bed, master=self)
        self.canvas._tkcanvas.config(highlightthickness=0)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='top')

    def display_data(self, x_data, y_data):
        print len(x_data)
        print len(y_data)
        print y_data[-10:]
        print y_data[2000:2100]
        self.axis.plot(x_data, y_data)
        self.canvas.show()

    def toolbar_toggle(self):
        if self.toolbar_status:  # there is a toolbar, so remove it
            self.toolbar.destroy()
            self.toolbar_status = False
        else:  # no toolbar yet so add one
            self.toolbar = NavToolbar(self.canvas, self)
            self.toolbar.update()
            self.toolbar_status = True

    def resize_x(self, _params):
        print "in resize"
        print _params
        self.axis.set_xlim([_params['low_cv_voltage'], _params['high_cv_voltage']])
        # plt.xlim([_params['low_cv_voltage'], _params['high_cv_voltage']])
        self.canvas.show()

    def resize_y(self, _current_limit):
        self.axis.set_ylim(-_current_limit, _current_limit)
        self.canvas.show()