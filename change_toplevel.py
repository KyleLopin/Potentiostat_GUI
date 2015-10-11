__author__ = 'Kyle Vitautas Lopin'

import logging
import Tkinter as tk
import Amp_GUI

TIA_resistor_values = [20, 30, 40, 80, 120, 250, 500, 1000]
current_limit_values = [50, 33, 25, 12.5, 8.4, 4, 2, 1, 0.5, 0.25, 0.125]


class SettingChanges(tk.Toplevel):
    """
    A modified tkinter toplevel that allows the user to input new voltage ranges to measure and to set
    the frequency
    """

    def __init__(self, _master, cv_graph):
        """
        Initialize the window
        :param _master: tk.Frame, the main window also has the device bound to it
        :return:
        """
        tk.Toplevel.__init__(self, master=_master)
        """Initialize values needed later """
        self._low_volt = 0
        self._high_volt = 0
        self._freq = 0.0
        self._current_range = ""

        self.title("Change Cyclic Voltammetry Settings")

        """make labels and an entry widget for a user to change the starting voltage of the triangle wave"""
        tk.Label(self, text="Starting Voltage: ", padx=10, pady=10).grid(row=0, column=0)
        low_volt = tk.Entry(self)  # entry widget for the user to change the voltage
        low_volt.insert(0, str(_master.operation_params['low_cv_voltage']))  # put the current value in the entry widget
        low_volt.grid(row=0, column=1)
        tk.Label(self, text="mV", padx=10, pady=10).grid(row=0, column=3)

        """make labels and an entry widget for a user to change the ending voltage of the triangle wave"""
        tk.Label(self, text="Ending Voltage: ", padx=10, pady=10).grid(row=1, column=0)
        high_volt = tk.Entry(self)  # entry widget for the user to change the voltage
        high_volt.insert(0, _master.operation_params['high_cv_voltage'])  # put the current value in the entry widget
        high_volt.grid(row=1, column=1)
        tk.Label(self, text="mV", padx=10, pady=10).grid(row=1, column=3)

        """ make labels and an entry widget for a user to change the sweep rate of the triangle wave"""
        tk.Label(self, text="Sweep Rate: ", padx=10, pady=10).grid(row=2, column=0)
        freq = tk.Entry(self)  # entry widget for the user to change the voltage
        freq.insert(0, _master.operation_params['sweep_rate'])  # put the current value in the entry widget
        freq.grid(row=2, column=1)
        tk.Label(self, text="V/s", padx=10, pady=10).grid(row=2, column=3)

        """make labels and option menu for the user to change current range the device detects"""
        tk.Label(self, text="Current Range: ", padx=10, pady=10).grid(row=3, column=0)
        self.current_options = tk.StringVar(self)

        self.current_option_list = [u'\u00B150 \u00B5A',  # there are sometimes problems with encoding with this
                                    u'\u00B133 \u00B5A',
                                    u'\u00B125 \u00B5A',
                                    u'\u00B112.5 \u00B5A',
                                    u'\u00B18.3 \u00B5A',
                                    u'\u00B14 \u00B5A',
                                    u'\u00B12 \u00B5A',
                                    u'\u00B11 \u00B5A',
                                    u'\u00B10.5 \u00B5A',
                                    u'\u00B10.25 \u00B5A',
                                    u'\u00B10.125 \u00B5A']

        current_option_list_index = TIA_resistor_values.index(_master.operation_params['TIA_resistor'])
        self.current_options.set(self.current_option_list[current_option_list_index])

        current = tk.OptionMenu(self, self.current_options, *self.current_option_list)
        current.grid(row=3, column=1)

        # make a button that will take the entry values and call a function to properly convert them and
        # send the correct values to the amperometry microcontroller
        tk.Button(self,
                  text='Save Changes',
                  command=lambda: self.save_cv_changes(low_volt.get(),
                                                       high_volt.get(),
                                                       freq.get(),
                                                       self.current_options.get(),
                                                       _master, cv_graph)).grid(row=4, column=0)

        # make a button to exit the toplevel by destroying it
        tk.Button(self,
                  text='Exit',
                  command=lambda: self.destroy()).grid(row=4, column=1)

    def save_cv_changes(self, _low_volt, _high_volt, _freq, _range, _master, cv_graph):
        """
        Commit all changes the user entered
        :param _low_volt: user inputted value, should be an integer that will be the lower level of the triangle wave
        :param _high_volt: user inputted value, should be an integer that will be the upper level of the triangle wave
        :param _freq: user inputted value, should be a float that will be the rate of change of the triangle wave
        :param _range: string from self.current_option_list that the user picked
        :param _master: main window of the program, used so that the operational parameters of the main window
         can be changed
        :return: the parameters are updated in the main windows operational_params dictionary
        """
        """ Save the voltage and frequency parameters to the current instance so they don't have to passed
        all the time to the functions  """
        self._low_volt = _low_volt
        self._high_volt = _high_volt
        self._freq = _freq
        self._current_range = _range

        """ set a flag that tells the program to send a parameter change to the MCU
         turn this flag off if there is a problem later on and the MCU should not be sent new parameters"""
        changing_flag = True

        """ try to convert the voltages to integers and sweep rate to a float """
        try:
            self._low_volt = int(self._low_volt)
            self._high_volt = int(self._high_volt)
            self._freq = float(self._freq)
            # don't have to check current range cause it was chosen from an option menu
        except ValueError:  # user input values failed
            logging.info("Error in data input format")
            changing_flag = False  # if the inputted data is not correct, change the flag so that the program will
            # not try to send bad data to the MCU

        """ check for changes to any of the values, do not bother the amplifier if there is no update """
        if self.sweep_param_is_changed(_master.operation_params):
            """ make sure the lower amplitude is lower than the high amplitude
            and that there were no errors from the user """
            if (self._low_volt < self._high_volt) and changing_flag:
                """ update the operation_params dict for the master and send all the parameters to the MCU """
                self.save_changed_settings(_master)
                _master.device.send_cv_parameters()
                """ change the axis of the graph to fit the voltage values """
                x_lim_low = _master.operation_params['low_cv_voltage']
                x_lim_high = _master.operation_params['high_cv_voltage']
                cv_graph.resize_x(x_lim_low, x_lim_high)
            else:
                logging.debug("no change of settings low > high")

        """ figure out if the current range has changed and update the device if it has
        NOTE: not the best solution but there are some encoding errors on the other ways tried"""
        position = self.current_option_list.index(_range)  # get user's choice from the option menu
        max_tia_setting = 7  # max value you an send the TIA in the device
        if position > max_tia_setting:  # the largest setting change the ADC gain but not the TIA value
            adc_gain_setting = position % max_tia_setting  # the last 3 settings increase the adc gain setting
            tia_position = max_tia_setting  # but leaves the TIA setting at the highest setting available
        else:
            tia_position = position  # the setting to send to the MCU is the same as the index
            adc_gain_setting = 0  # the gain setting is 0 for no gain on the adc

        """ Check if the gain setting has changed and the TIA resistor value should be updated """
        if _master.operation_params['TIA_resistor'] is not TIA_resistor_values[tia_position]:
            _master.device.usb_write('A' + str(tia_position) + '|' + str(adc_gain_setting))  # update device
            _master.operation_params['TIA_resistor'] = TIA_resistor_values[tia_position]  # update program
            logging.debug("TIA resistor changed to: %s", _master.operation_params['TIA_resistor'])

            """ Change the value for the current limits displayed to the user and update the graph's scale """
            _master.current_varstr.set(self.current_option_list[position])
            cv_graph.resize_y(current_limit_values[position])
        logging.debug('position: %s', position)
        """ destroy the top level now that every is saved and updated """
        self.destroy()

    def sweep_param_is_changed(self, _old_params):
        """
        Check to see if any of the parameters of the cyclic voltammetry have been changed
        :param _old_params:
        :return:
        """
        if (self._low_volt != _old_params['low_cv_voltage']
           or self._high_volt != _old_params['high_cv_voltage']
           or self._freq != _old_params['sweep_rate']):

            logging.debug("sweep_param is_changed")
            return True
        else:
            logging.debug("sweep_param are not changed")
            return False

    def save_changed_settings(self, _master):
        """
        Update all of the main programs operations_params settings so the User's choices will be remembered
        :param _master: The main program to save the data to
        :return:
        """
        logging.debug("change saved settings called")
        _master.operation_params['low_cv_voltage'] = self._low_volt
        _master.operation_params['high_cv_voltage'] = self._high_volt
        _master.operation_params['sweep_rate'] = self._freq
        Amp_GUI.update_param_dict()
        _master.cv_label_update()
        logging.debug("updating new operational params to:")
        logging.debug(_master.operation_params)


class ChangeCompareValue(tk.Toplevel):

    def __init__(self, _master):
        tk.Toplevel.__init__(self, _master)
        self.title("Change PWM timing compare value")

        tk.Label(self, text="Enter value to place in timing PWM compare register").pack(side='top')
        tk.Label(self, text="Value must be between 500 and "
                            +str(_master.operation_params['PWM_period'])).pack(side='top')
        tk.Label(self, text="Current value is "
                            + str(_master.operation_params['PWM_compare'])).pack(side='top')
        value_varstring = tk.StringVar()
        value_varstring.set(_master.operation_params['PWM_compare'])
        value_box = tk.Entry(self, textvariable=value_varstring)
        value_box.pack(side='top')

        button_frame = tk.Frame(self)
        button_frame.pack(side='top')

        tk.Button(button_frame, text="Quit", command=lambda: self.destroy()).pack(side='left')

        tk.Button(button_frame, text="Send",
                  command=lambda: self.compare_reg_change(_master, value_varstring.get())).pack(side='left')

        logging.error("put in here something to check if the number for compare is correct")

    def compare_reg_change(self, master, _value):


        master.device.write_timer_compare(_value)