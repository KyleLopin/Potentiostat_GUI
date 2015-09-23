__author__ = 'HMT'

import Tkinter as tk


class OptionMenu(tk.Menu):

    def __init__(self, master):
        """
        Make the options menu for the application
        :return:
        """
        """ Make the main menu to put all the submenus on """
        menubar = tk.Menu(master)
        """ Make a menus along the top of the gui """
        options_menu = tk.Menu(menubar, tearoff=0)
        file_menu = tk.Menu(menubar, tearoff=0)
        """ Different options the user can change """
        self.make_data_option_menu(options_menu, master)
        self.make_file_option_menu(file_menu, master)

        menubar.add_cascade(label="File", menu=file_menu)  # empty now, to fill later
        menubar.add_cascade(label="Options", menu=options_menu)

        master.config(menu=menubar)

    def make_file_option_menu(self, file_menu, master):
        file_menu.add_command(label="Open",
                              command=lambda: master.open_data())
        file_menu.add_command(label="Save All Data",
                              command=lambda: master.save_all_data())
        file_menu.add_command(label="Select Data to Save",
                              command=lambda: master.save_selected_data())
        file_menu.add_separator()
        file_menu.add_command(label="Quit",
                              command=lambda: master.quit())

    def make_data_option_menu(self, options_menu, master):
        data_option_menu = tk.Menu(options_menu, tearoff=0)
        options_menu.add_cascade(label="Choose data export", menu=data_option_menu)

        data_option_menu.add_cascade(label="Converted data", command=lambda: master.set_data_type("Converted"))
        data_option_menu.add_cascade(label="Raw adc data", command=lambda: master.set_data_type("Raw Counts"))
