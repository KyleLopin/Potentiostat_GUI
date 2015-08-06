__author__ = 'Kyle Vitautas Lopin'

import Tkinter as tk

class canvas_graph_embed(tk.Frame):

    def __init__(self, master, properties):

        tk.Frame.__init__(self, master=master)
        self.graph = tk.Canvas(master=self, width=_properties['width'], height=_properties['height'])
        self.graph.pack(expand=True, fill=tk.BOTH)

        self.height = _properties['height']
        self.width = _properties['width']
        self.draw_axis(_properties)
        self.graph.bind("<Configure>", self.on_resize)

    def draw_axis(self, _props):

        # get the dimensions of where to put the lines and tick marks
        y_origin = .8*self.height
        x_origin = .1*self.width
        x_end = .9*self.width
        y_end = .1*self.height
        # draw x and y axes lines
        self.graph.create_line(x_origin, y_origin, x_end+1, y_origin, width=2)  # x axis
        self.graph.create_line(x_origin, y_origin, x_origin, y_end,  width=2)  # y axis

        #make markings on the x axis
        x_spacing = (x_end-x_origin)
        tick_len = 6
        for i in range(11):
            x = x_origin + (i*x_spacing/10)
            self.graph.create_line(x, y_origin, x, y_origin+tick_len, width=2)


        print 'testing'

    def on_resize(self, event):
        """
        Rescale all the widgets in the Canvas, see
        http://stackoverflow.com/questions/22835289/how-to-get-tkinter-canvas-to-dynamically-resize-to-window-width
        for more details
        :param event:
        :return:
        """
        # get ratio of old and new height
        wscale = float(event.width)/self.width
        hscale = float(event.height)/self.height
        self.width = event.width
        self.height = event.height
        self.graph.scale("all",0,0,wscale,hscale)
