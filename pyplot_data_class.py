# Copyright (c) 2015-2016 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>
# Licensed under the Creative Commons Attribution-ShareAlike  3.0 (CC BY-SA 3.0 US) License

""" Data class to hold cyclic voltammetry data
"""
# standard libraries
import csv
import logging
import traceback

__author__ = 'Kyle Vitautas Lopin'


class PyplotData(object):
    """ Class to contain the data to display in the tkinter_pyplot PyplotEmbed class
    TO DO: FIND BETTER NAMES FOR THIS
    """
    def __init__(self):
        """ Initialize lists to hold the x-y values, the legend labels and the colors of the lines
        to display
        """
        # self.x_data = []
        self.voltage_data = []
        self.time_data = []
        self.current_data = []
        self.y_raw_data = []
        self.label = []
        self.colors = []
        self.notes = []
        self.index = 0  # index to keep track of how many data series are saved so far
        self.name_index = 0

    def add_data(self, new_voltage, new_current, _new_raw_y=None, _label=None):
        """ Add the data self so it can all be saved later
        :param new_voltage: voltages of the data measured
        :param new_current: data of the current measured
        :param _new_raw_y: raw ADC counts
        :param _label: data label
        """
        if not _label:
            _label = "data {}".format(self.name_index + 1)
        self.voltage_data.append(new_voltage)
        self.current_data.append(new_current)
        self.label.append(_label)
        self.notes.append(" ")
        if _new_raw_y:
            self.y_raw_data.append(_new_raw_y)
        else:
            self.y_raw_data.append([0])
        self.index += 1  # increment data index so the next data series will be advanced
        self.name_index += 1
        logging.debug("adding data, index: %i", self.index)

    def change_label(self, new_label, index):
        """ Let the user change the label of a data run
        :param new_label:
        :param index:
        :return:
        """
        self.label[index] = new_label

    def remove_data(self, _index):
        self.voltage_data.pop(_index)
        self.current_data.pop(_index)
        self.y_raw_data.pop(_index)
        self.notes.pop(_index)
        self.label.pop(_index)
        self.colors.pop(_index)
        self.index -= 1

    def save_all_data(self, filename, save_type="Converted"):
        """ Save all the data save
        NOTE: if the voltage range was changed in the run the saved data will be messed up
        :param filename:  filename to save the
        :param save_type:
        :return:
        """
        try:
            # make a csv writer, go through each data point and save the voltage and current at
            # each point, then close the file
            writer = csv.writer(filename, dialect='excel')
            # make the first line of the file with the data labels
            line = ["voltage"]  # first line will be the voltages
            for i in range(self.index):
                line.append(self.label[i])
            writer.writerow(line)
            length = len(self.current_data[0])
            width = self.index
            # the second row are the notes
            line = [" "]  # first line is voltages so it has no notes
            for i in range(self.index):
                line.append(self.notes[i])
            writer.writerow(line)

            # check to see what type of data the user wants to save
            if save_type == "Converted":
                _data_array = self.current_data
            elif save_type == "Raw Counts":
                _data_array = self.y_raw_data

            for i in range(length):
                # this is only take the voltage of the first run
                line[0] = self.voltage_data[0][i]
                for j in range(width):
                    line[j + 1] = _data_array[j][i]
                writer.writerow(line)

            filename.close()

        except Exception as error:
            logging.error("failed saving")
            logging.error(error)
            traceback.print_exc()
            filename.close()
