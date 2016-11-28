# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

"""Toplevels for the electrochemical device
"""

# standard libraries
import Tkinter as tk

__author__ = 'Kyle Vitautas Lopin'


class VoltageSourceSelect(tk.Toplevel):
    """
    Toplevel for the user to select what voltage souce to use
    """

    def __init__(self, master, current_value):
        tk.Toplevel.__init__(self, master=master)
        self.geometry("300x200")
        self.source_selected = None
        self.master = master
        print 'current value: ', current_value
        if current_value == 0:  # no choice has been made yet
            _label = "No voltage selected yet"
        else:
            _label = "Default"

        tk.Label(self, text=_label).pack(side='top')
        tk.Button(self, text="No capacitor installed", width=20,
                  command=lambda: self.send_selection("VDAC")).pack(side='top')
        tk.Button(self, text="DAC capacitor installed", width=20,
                  command=lambda: self.send_selection("DVDAC")).pack(side='top')
        tk.Button(self, text="Not sure (default)", width=20,
                  command=lambda: self.send_selection("default")).pack(side='top')

        self.lift()
        self.attributes("-topmost", True)

    def send_selection(self, source_selected):
        print 'source: ', source_selected

        if source_selected == 'VDAC':
            self.master.device.usb_write('VS1')

        self.source_selected = source_selected
        self.destroy()
