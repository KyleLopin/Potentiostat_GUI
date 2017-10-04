__author__ = 'Kyle Vitautas Lopin'

"""
Custom class that will attempt to make a matplotlib graph to display data and embed the graph into a tkinter frame
If the user does not have matplotlib or one of its dependencies installed the program will instead make a tkinter Canvas
"""
# TODO: is unused?

import Tkinter as tk
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# import matplotlib.pyplot as plt

class data_display(tk.Frame):

    def __init__(self, parent_frame, plt_props=None):
        """
        Check if the user has matplotlib and all its depenencies installed
        :param parent:
        :return:
        """
        tk.Frame.__init__(self, master=parent_frame)
        if self.matplotlib_ready():
            """ the import statements are scoped so make new ones"""
            import matplotlib
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


            self.figure_bed = plt.figure(figsize=(7, 3.5))
            self.axis = self.figure_bed.add_subplot(111)

            if plt_props:
                for key, value in plt_props.iteritems():
                    eval("plt." + key + "(" + value + ")")
            # self.axis.set_axis_bgcolor('red')
            self.figure_bed.set_facecolor('white')
            self.canvas = FigureCanvasTkAgg(self.figure_bed, master=self)
            self.canvas._tkcanvas.config(highlightthickness=0)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side='top')

            # self.make_matplotlib_area(parent, plt_props)
            self.embed_matplotlib()
            self.type = 'matplotlib'
            # TODO ADD TO THIS
        else:
            graph = tk.Canvas(master=self)
            graph.pack(side='left', expand=True, fill=tk.BOTH)
            self.type = 'canvas'


    def matplotlib_ready(self):
        """
        Check if matplotlib graph can be used, if so import all dependences and return true
        :return: True if a matplotlib graph can be made and embedded, else false
        """
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            print "matplotlib found"
            return True
        except ImportError, e:
            print "No matplotlib"
            return False


    def make_matplotlib_area(self, parent_frame, plt_props=None):
        """
        Make a matplotlib graph and initialize it
        :return: TODO FIGURE THIS OUT
        """

        self.figure_bed = plt.figure(figsize=(7, 3.5))
        self.axis = self.figure_bed.add_subplot(111)

        if plt_props:
            for key, value in plt_props.iteritems():
                eval("plt." + key + "(" + value + ")")
        # self.axis.set_axis_bgcolor('red')
        self.figure_bed.set_facecolor('white')
        self.canvas = FigureCanvasTkAgg(parent_frame, master=self)
        self.canvas._tkcanvas.config(highlightthickness=0)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='top')


    def embed_matplotlib(self):
        """
        Take a matplotlib area and embed it into the self frame
        :return: TODO FIGURE THIS OUT
        """


    def update_graph(self, data):
        """
        Take new data and put it in the graph
        :param data: data to display
        :return:
        """
        if (self.type == 'matplotlib'):
            pass
        else:
            pass