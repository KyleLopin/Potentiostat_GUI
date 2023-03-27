# Copyright (c) 2023 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""
Functions to fit I-V curves to a resistance
"""

__author__ = "Kyle Vitautas Lopin"

# installed libraries
import numpy as np
import pandas as pd

CUTOFF = 50


def load_data(filename: str) -> pd.DataFrame:
    data = pd.read_excel(filename, index_col="voltage")
    return data


def remove_cutoff_values(_series: pd.Series) -> pd.DataFrame:
    return _series[(_series < CUTOFF) & (_series > -CUTOFF)]


def fit_lines(_df: pd.DataFrame):
    for column in _df.columns:
        print(column)
        fixed_df = remove_cutoff_values(_df[column])
        # print(fixed_df.values)
        z = np.polyfit(x=fixed_df.index,
                       y=fixed_df.values,
                       deg=1)
        # print(f"z: {z}")
        print(f"Calculated R: {1000/z[0]}")


if __name__ == '__main__':
    data = load_data("Rs.xlsx")
    fit_lines(data)
