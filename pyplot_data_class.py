import logging

__author__ = 'Kyle Vitautas Lopin'


class PyplotData(object):
    """
    Class to contain the data to display in the tkinter_pyplot PyplotEmbed class
    TO DO: FIND BETTER NAMES FOR THIS
    """
    def __init__(self):
        """
        Initialize lists to hold the x-y values, the legend labels and the colors of the lines
        to display
        :return:
        """
        self.x_data = []
        self.y_data = []
        self.y_raw_data = []
        self.label = []
        self.colors = []
        self.notes = []
        self.index = 0  # index to keep track of how many data series are saved so far
        self.name_index = 0

    def add_data(self, _new_x, _new_y, _new_raw_y=None, _label=None):
        """
        Add the data self so it can all be saved later
        :param _voltage:
        :param _raw_data:
        :param _data:
        :return:
        """
        if not _label:
            _label = "data {}".format(self.name_index + 1)
        self.x_data.append(_new_x)
        self.y_data.append(_new_y)
        self.label.append(_label)
        self.notes.append(" ")
        if _new_raw_y:
            self.y_raw_data.append(_new_raw_y)
        self.index += 1  # increment data index so the next data series will be advanced
        self.name_index += 1

    def change_label(self, new_label, index):

        self.label[index] = new_label

    def remove_data(self, _index):
        self.x_data.pop(_index)
        self.y_data.pop(_index)
        self.y_raw_data.pop(_index)
        self.notes.pop(_index)
        self.label.pop(_index)
        self.colors.pop(_index)
        self.index -= 1
