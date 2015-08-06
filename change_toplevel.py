__author__ = 'Kyle Vitautas Lopin'

import Tkinter as tk
import amp_usb

TIA_resistor_values = [20, 30, 40, 80, 120, 250, 500, 1000]
current_limit_values = [50, 33, 25, 12.5, 8.4, 4, 2, 1]

class setting_changes(tk.Toplevel):
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
        # TODO: change the default to the value already chosen
        self.current_option_list = [u'\u00B150 \u00B5A',  # there are sometimes problems with encoding with this
                                    u'\u00B133 \u00B5A',
                                    u'\u00B125 \u00B5A',
                                    u'\u00B112.5 \u00B5A',
                                    u'\u00B18.3 \u00B5A',
                                    u'\u00B14 \u00B5A',
                                    u'\u00B12 \u00B5A',
                                    u'\u00B11 \u00B5A']

        self.current_options.set(self.current_option_list[0])

        current = tk.OptionMenu(self, self.current_options, *self.current_option_list)
        current.grid(row=3, column=1)

        # make a button that will take the entry values and call a function to properly convert them and
        # send the correct values to the amperometry microcontroller
        tk.Button(self,
                  text='Save Changes',
                  command=lambda: self.save_cv_changes(low_volt.get(),
                  high_volt.get(), freq.get(), self.current_options.get(),
                  _master, cv_graph)).grid(row=4, column=0)

        # make a button to exit the toplevel by destroying it
        tk.Button(self,
                  text='Exit',
                  command=lambda : self.destroy()).grid(row=4, column=1)

    def save_cv_changes(self, _low_volt, _high_volt, _freq, _range, _master, cv_graph):
        """

        :param _low_volt: user inputted value, should be an integer that will be the lower level of the triangle wave
        :param _high_volt: user inputted value, should be an integer that will be the upper level of the triangle wave
        :param _freq: user inputted value, should be a float that will be the rate of change of the triangle wave
        :param _master: main window of the program, used so that the operational parameters of the main window
         can be changed
        :return: the parameters are updated in the main windows operational_params dictionary
        """
        #save the voltage and frequency parameters to the current instance so they don't have to passed all the time
        # to the functions
        self._low_volt = _low_volt
        self._high_volt = _high_volt
        self._freq = _freq
        self._current_range = _range

        changing_flag = True  # flag to turn off if for any reason the cyclic voltammetry settings should not be changed

        # try to convert the voltages to integers and sweep rate to a float
        try:
            self._low_volt = int(self._low_volt)
            self._high_volt = int(self._high_volt)
            self._freq = float(self._freq)
            # dont have to check current range cause it was choosen from optionmenu
        except ValueError:
            print "Error in data input format"
            changing_flag = False  # if the inputted data is not correct, change the flag so that the program will
                                   # no try to send bad data to the MCU

        # check for changes to any of the values, do not bother the amplifier if there is no update
        if self.sweep_param_is_changed(_master.operation_params):

            #make sure the lower amplitude is lower than the high amplitude and that there were no errors from the user
            if (self._low_volt < self._high_volt) and changing_flag:
                self.change_saved_settings(_master)
                _master.device.send_cv_parameters()
                cv_graph.resize_x(_master.operation_params)
            else:
                print "no change of settings low > high"
        """ figure out if the current range has changed and update the device if it has
        not the best solution but there are some encoding errors on the other ways tried"""
        position = self.current_option_list.index(_range)
        if _master.operation_params['TIA_resistor'] is not TIA_resistor_values[position]:
            _master.device.usb_write('A' + str(position))
            # self.current_options.set(self.current_option_list[position])
            _master.operation_params['TIA_resistor'] = TIA_resistor_values[position]
            print _master.operation_params['TIA_resistor']
            print 'test1'
            # _master.cv_label_update()
            _master.current_varstr.set(self.current_option_list[position])
            cv_graph.resize_y(current_limit_values[position])
        print 'position: ', position


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
            print "sweep_param is_changed"
            return True
        else:
            return False

    def send_settings(self, _master):
        """
        DEPRECATED, CHECK IF STILL NEEDED
        Convert the input voltages 11 bit numbers to set the parallel current digital to analog converters (PIDACs)
        version 0.1: PIDACs are running on 11 bits with a maximum of 255 uA of current through a fixed 8.2 kohms
        resistor with the output buffered by a voltage following opamp

        The voltage out of the DAC is given by the equation Vout = 8200 ohms * 255 uA * (D / 2**11)
        where D is the integer set by the microcontroller

        to set D use the equation D = (Vout * 2*11) / (8200 ohms * 255 uA)

        TODO: FIX THIS SECTION WHEN THE MCU SIDE IS MORE SET

        :param _low_volt: integer (mV), lowest voltage of the triangle sweep to be given
        :param _high_volt: integer (mV), highest voltage of the triangle
        :param _freq: float (V/s), rate that the voltage of the triangle wave changes
        :return:
        """
        resistor = 8200  # ohms
        max_current = .255  # mA
        _lower_setting = int(( (self._low_volt+1024) * 2**11) / (resistor*max_current))  # mv/(ohms*mA) = mV/mV
        _upper_setting = int(( (self._high_volt+1024) * 2**11) / (resistor*max_current))  # mv/(ohms*mA) = mV/mV
        _range = _upper_setting - _lower_setting
        _data_points = 2 * _range - 1

        # changing the DACs by 1 bit chnages the voltage by 1 mV,
        # therefor the voltage should be stepped 1000 mV/V * rate (V/s)

        _freq_setting = int(round(1000 * self._freq))  #  NOT CORRECT, FIGURE THIS OUT ON MCU SIDE

        print "sending"
        _master.device.usb_write("S|{0:04d}|{1:04d}|{2:06d}".format(_lower_setting, _upper_setting, _freq_setting))
        print "end sending"



    def change_saved_settings(self, _master):

        print "change saved settings called"

        _master.operation_params['low_cv_voltage'] = self._low_volt
        _master.operation_params['high_cv_voltage'] = self._high_volt
        _master.operation_params['sweep_rate'] = self._freq
        _master.update_param_dict()
        _master.cv_label_update()
        print _master.operation_params

