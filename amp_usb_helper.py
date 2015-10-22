__author__ = 'Kyle Vitautas Lopin'

import logging
import usb.util
import usb_comm
import pyplot_data_class as data_class

""" set the constants here that the functions need """
running_delay = 2000
failure_delay = 500
complete_message = "Done"
fail_count_threshold = 2
virtual_ground_shift = 1024
packet_size = 32

user_sets_label_after_run = False

def initialize(device):
    """
    generic function that should be called after initialing connecting to a device in usb_comm file

    for the amperometry project it is sending the initial cyclic voltammetry parameters to the device upon connecting
    :param device: device to initialize
    :return:
    """
    send_cv_parameters(device)


def send_cv_parameters(device):
    """
    Send the parameters that the amperometric device should use to perform a cyclic voltammetry sweep
    the data needed calculate the values to send should be in a dictionary of the form
    device.params['low_cv_voltage'] which is the lowest voltage (in mV) of the triangle waveform
    device.params['high_cv_voltage'] which is the highest voltage (in mV) of the triangle waveform
    device.params['sweep_rate'] which is the speed (in V/s) that the voltage should be changed

    Note: the values sending to the device have to be padded with 0's so they are the
    proper size for the device to interpret

    :param device: device from usb_comm class that is being used to communicate with
    :return: will add to the device.params dict the following values
    ['usb_count'] which is how many data values to expect back into to device when receiving data
    ['actual_low_volt'] the lowest voltage the device will give to the electrode
    ['actual_high_volt'] the highest voltage the device will give to the electrode
    ['volt_increment'] the amount a 1 bit increase in the PIDAC will increase the voltage at the electrode
    """
    """ convert the values for the params dictionary into the values the device needs;
    this part is done on the computer side to save MCU code length """
    formatted_low_volt, low_dac_value = device.format_voltage(device.params['low_cv_voltage'])
    formatted_high_volt, high_dac_value = device.format_voltage(device.params['high_cv_voltage'])
    formatted_freq_divider, pwm_period = device.format_divider(device.params['sweep_rate'])

    device.master.operation_params['PWM_period'] = pwm_period

    """ send those values to the device in the proper format for the PSoC amperometry device """
    to_amp_device = '|'.join(["S", formatted_low_volt, formatted_high_volt, formatted_freq_divider])

    """save how many data points should be recieved back from the usb """
    device.params['usb_count'] = 2*(high_dac_value - low_dac_value+1)

    """ calculate what the actual voltage the device will make.  This will be slightly different from the
    user input because pidac has 11 bits of resolution """
    pidac_resistor = device.params['PIDAC_resistor']  # kilohms - resistor used to convert the current
    low_pidac_i_output = low_dac_value * device.params['smallest_increment_pidac']
    device.params['actual_low_volt'] = low_pidac_i_output * pidac_resistor

    high_pidac_i_output = high_dac_value * device.params['smallest_increment_pidac']
    device.params['actual_high_volt'] = high_pidac_i_output * pidac_resistor

    device.params['volt_increment'] = device.params['smallest_increment_pidac'] * pidac_resistor

    device.usb_write(to_amp_device)

    """ Write to the timing PWM compare register so the dac adc timing is correct """
    compare_value = pwm_period / 2
    write_timer_compare(device, compare_value)


def write_timer_compare(device, value):
    logging.debug("compare value is %s", value)
    device.master.operation_params['PWM_compare'] = int(value)
    _formatted_value = '{0:05d}'.format(int(value))
    device.usb_write('C|'+_formatted_value)


def run_scan(device, canvas, master):
    """
    This will run a cyclic voltammetry scan. To do this it follows the steps
    1) sent 'R' to the microcontroller to run the scan and collect the data
    2) wait for the scan to run and poll the amperometry device to see if its ready for data
    3) Check if the device is done by receiving the correct message back
    4) sent 'EX' to the device, this make the amperometry device export the data in chunks (size defined in
    USB_IN_BYTE_SIZE (IN, as in 'in' the computer) from the channel number described use in X.  NOTE: the X
    is a string of an int so '0', '1', '2', or '3' works
    5) read the IN_ENDPOINT until all the data is send to the this program

    :param device:
    :param canvas:
    :param master:  master (root) gui
    :return: the adc data array from the amperometric device
    """
    device.usb_write('R')  # step 1
    if device.working:
        logging.debug("device reading")
        device.master.after(running_delay, lambda: run_scan_continue(device, canvas))  # step 2
    else:
        logging.debug("Couldn't find out endpoint to send message to run")
        master.attempt_reconnection()


def run_scan_continue(device, canvas, fail_count=0):
    """
    The callback for run_scan.  This is called after the device should be done with the scan and is ready
    to export the data.   The parts of the run cyclic voltammetry scan this functions run is part 3-5 listed in
    run_scan.
    :param canvas: the widget that is called to display the data
    :return:
    """
    check_message = device.usb_read_message()  # step 3

    if check_message == complete_message:
        get_and_display_data_from_export_channel(device, canvas)
    else:
        """ wait a little longer and retry, after a certain amount of time, timeout """
        if fail_count < fail_count_threshold:
            device.master.after(failure_delay, lambda: run_scan_continue(device, canvas, fail_count+1))  # retry step 2
        logging.error("Failed to run the scan")


def get_and_display_data_from_export_channel(device, canvas, _channel=None):
    if not _channel:
        _channel = device.params['adc_channel']  # if no channel sent, use the one saved in parameters dict

    """ the correct complete message was received so attempt to collect the data """
    device.usb_write('E'+str(_channel))  # step 4

    """ Get the raw data from the ADC.  this has to be modified to get the actual current values """
    raw_data = get_data(device)
    if not raw_data:  # if something is wrong just return
        return
    """ call function to convert the raw ADC values into the current that passed through the working electrode """
    data = process_data(device, raw_data)

    logging.info('TODO: still binding data to main and not custom class, fix this')
    device.master.current_data = data
    x_line = make_x_line(device.params['actual_low_volt'],
                         device.params['actual_high_volt'],
                         device.params['volt_increment'])
    device.master.voltage_data = x_line

    """ Send data to the canvas where it will be saved and displayed """
    canvas.update_data(x_line, data, raw_data)


def get_data(self):
    """
    Get the raw adc counts from the device
    Get the proper amount of data packets from the device
    :return: a list of adc counts
    """
    end_pt = self.device[0][(0, 0)][0]
    full_array = []
    """ calculate how many packets of data to get from the amp device the usb_count param is
    how many data points there are packet_size / 2 is because the data is converted to uint8
    from the uint16 it is acquired in """
    number_packets = self.params['usb_count'] / (packet_size / 2)
    count = 0
    running = True
    while number_packets+1 > count and running:
        try:
            usb_input = self.device.read(end_pt.bEndpointAddress, packet_size)
            _hold = convert_int8_int16(usb_input.tolist())
            full_array.extend(_hold)
            count += 1
        except Exception as e:
            logging.debug("end of ENDPOINT")
            logging.debug(e)
            running = False
    full_array = full_array[:self.params['usb_count']]
    return full_array


def process_data(device, _raw_data):
    """
    Take in the raw adc counts and output the corresponding current values
    :param device: the device that has the data_save_type and TIA_resistor values to properly process the data
    :param _raw_data: raw adc count numbers
    :return: current (micro amperes) values of the adc values
    """
    if device.master.data_save_type == "Converted":
        logging.debug("Converting data")
        number_bits = 12  # resolution of the adc being used
        voltage_range = 2048  # mV
        max_bit_value = 2**number_bits
        num_bits_twos_comp = 16
        twos_rollover = 2**(num_bits_twos_comp - 1)
        twos_subtract = 2**num_bits_twos_comp

        """ Convert the adc number first to the voltage={voltage_range * (float(x) / max_bit_value}
        and then divide by the TIA resistor to get the current
        use 2 different equations, because the delta sigma adc sends the number in twos compliments
        if the adc number is larger than the two rollover value, subtract two_substract from the number
        to get the proper negative integer """
        current = [-((voltage_range * (float(x) / max_bit_value))
                     / device.params['TIA_resistor']) if x < twos_rollover
                   else -((voltage_range * (float(x - twos_subtract) / max_bit_value))
                          / device.params['TIA_resistor']) for x in _raw_data]  # microAmp (mV / kohms)
        return current
    elif device.master.data_save_type == "Raw Counts":
        logging.debug("sending raw data back")
        return _raw_data


def attempt_reconnect(device):
    print "attempting reconnect"
    # usb.util.dispose_resources(device) this doesnt work for some reason
    # self is the master
    # device = usb_comm.AmpUsb(operation_params)


def make_x_line(start, end, inc):
    """
    Make a list of the voltages that are giving to the electrode in a cyclic voltammetry scan
    :param start: start voltage of the CV scan
    :param end: end voltage of the CV scan
    :param inc: the voltage step of the CV scan setting
    :return:
    """
    i = start
    line = []
    while i < end:
        line.append(i - virtual_ground_shift)
        i += inc
    while i > start:
        line.append(i - virtual_ground_shift)
        i -= inc
    return line


def convert_int8_int16(_array):
    """
    Convert an array of uint8 to an array of uint16
    :param _array: list of uint8 values
    :return: list of uint16 values that is half the size of the input array
    """
    new_array = [0]*int(len(_array)/2)
    for i in range(int(len(_array)/2)):
        new_array[i] = _array.pop(0) + _array.pop(0)*256
    return new_array
