import Tkinter as tk

import change_toplevel

__author__ = 'HMT'


class OptionMenu(tk.Menu):

    def __init__(self, master):
        """
        Make the options menu for the application
        :return:
        """
        """ Make the main menu to put all the submenus on """
        menubar = tk.Menu(master)
        """ Make a menus along the top of the gui """
        file_menu = tk.Menu(menubar, tearoff=0)
        options_menu = tk.Menu(menubar, tearoff=0)
        data_menu = tk.Menu(menubar, tearoff=0)
        developer_menu = tk.Menu(menubar, tearoff=0)
        """ Different options the user can change """
        make_option_menu(options_menu, master)
        make_file_option_menu(file_menu, master)
        make_data_menu(data_menu, master)
        make_developer_menu(developer_menu, master)

        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Data", menu=data_menu)
        menubar.add_cascade(label="Options", menu=options_menu)
        menubar.add_cascade(label="Developers", menu=developer_menu)

        master.config(menu=menubar)


def make_data_menu(data_menu, master):
    data_menu.add_command(label="Delete all data traces",
                          command=lambda: master.delete_all_data_user_prompt())


def make_file_option_menu(file_menu, master):
    file_menu.add_command(label="Open",
                          command=lambda: master.open_data())
    file_menu.add_command(label="Save All Data",
                          command=lambda: master.save_all_data())
    file_menu.add_command(label="Select Data to Save",
                          command=lambda: master.save_selected_data())
    file_menu.add_separator()
    file_menu.add_command(label="Quit",
                          command=lambda: master.quit())


def make_option_menu(options_menu, master):
    data_option_menu = tk.Menu(options_menu, tearoff=0)
    options_menu.add_cascade(label="Choose data export", menu=data_option_menu)
    data_option_menu.add_cascade(label="Converted data", command=lambda: master.set_data_type("Converted"))
    data_option_menu.add_cascade(label="Raw adc data", command=lambda: master.set_data_type("Raw Counts"))

    channel_option_menu = tk.Menu(options_menu, tearoff=0)
    options_menu.add_cascade(label="Choose channel to export", menu=channel_option_menu)
    for i in range(4):
        channel_option_menu.add_cascade(label=str(i), command=lambda: master.set_adc_channel(i))

    user_set_label_options = tk.Menu(options_menu, tearoff=0)
    options_menu.add_cascade(label="Set data label after a scan", menu=user_set_label_options)
    user_set_label_options.add_cascade(label="True", command=lambda: set_user_label_option(master, True))
    user_set_label_options.add_cascade(label="False", command=lambda: set_user_label_option(master, False))

    electrode_config_options = tk.Menu(options_menu, tearoff=0)
    options_menu.add_cascade(label="Set Electrode Configuration", menu=electrode_config_options)
    electrode_config_options.add_cascade(label="Two electrode setting",
                                         command=lambda: master.device.set_electrode_config(2))
    electrode_config_options.add_cascade(label="Three electrode setting",
                                         command=lambda: master.device.set_electrode_config(3))


def set_user_label_option(master, value):
    master.graph.user_sets_labels_after_run = value


def make_developer_menu(developer_menu, master):
    developer_option_menu = tk.Menu(developer_menu, tearoff=0)
    developer_menu.add_cascade(label="Get channel data", menu=developer_option_menu)

    for i in range(4):
            developer_option_menu.add_cascade(label="channel " + str(i),
                                              command=lambda channel=i: master.device.get_export_channel(channel))

    developer_menu.add_cascade(label="Change timing PWM compare value",
                               command=lambda: change_toplevel.ChangeCompareValue(master))

    developer_menu.add_cascade(label="Enter comments into logging file",
                               command=lambda: change_toplevel.EnterLoggingInfo(master))

    developer_menu.add_cascade(label="Add custom TIA resistor",
                               command=lambda: change_toplevel.EnterCustomTIAResistor(master))
