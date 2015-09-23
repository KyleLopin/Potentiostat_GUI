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
        self.values = []
        self.raw_values = []
        self.legends = []
        self.colors = []
        self.index = 0  # index to keep track of how many data series are saved so far

    def add_data(self, _voltage, _data, _raw_data, _label=None):
        """
        Add the data self so it can all be saved later
        :param _voltage:
        :param _raw_data:
        :param _data:
        :return:
        """
        if not _label:
            _label1 = "data {}".format(self.index+1)

        data_struct = BaseDataStruct(_voltage, _data, _label1)
        self.values.append(data_struct)
        if _raw_data:
            _raw_data_struct = BaseDataStruct(_voltage, _raw_data, _label1)
            self.raw_values.append(_raw_data_struct)
        self.index += 1  # increment data index so the next data series will be advanced


class BaseDataStruct(object):

    def __init__(self, x, y, label):
        self.x = x
        self.y = y
        self.label = label
