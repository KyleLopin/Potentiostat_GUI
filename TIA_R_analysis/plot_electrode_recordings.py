# Copyright (c) 2020 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""

"""

__author__ = "Kyle Vitatus Lopin"

# installed libraries
import matplotlib.pyplot as plt
import pandas as pd

plt.style.use("seaborn-bright")

data = pd.read_excel("Electrode_recordings.xlsx")

print(data)
print(data.columns)
time = data["Time"].iloc[2:20105]

print(time)
time_series = -data.iloc[2:20105, 1:]
print(time_series)
print("columns: ", time_series.columns)
time_columns = ['ch1', 'ch2', 'ch1.1', 'ch2.1', 'ch1.2', 'ch2.2', 'ch1.3', 'ch2.3']
time_columns = ['ch1.3', 'ch1.2', 'ch2.2']

# time_columns = ['ch2', 'ch2.1', 'ch2.2', 'ch2.3']

# ax = time_series.plot(color=['red', 'black', 'red', 'black', 'red', 'black'])

# fig, (ax1, ax2) = plt.subplots(ncols=2, nrows=1, figsize=(10, 6))
fig, (ax2) = plt.subplots(ncols=1, nrows=1, figsize=(4.5, 4.5))
labels = ["Ideal WE potential",
          "Actual WE potential",
          "Voltage Error",
          "D"]
i = 0
for column in time_columns:
    if ".1" in column:
        continue
    color = 'orangered'
    type = " WE"
    restance = u" 2.5k \u03A9"
    style = '--'
    if ".3" in column:
        color = 'red'
        style = '-'
        restance = u" ideal   "
    elif ".2kjlkjl" in column:
        style = '-'
        restance = u" 1.6k \u03A9"
    elif ".2" in column:
        print('kkklk', time_series[column])
        style = ':'
        color = 'red'
        restance = u" 1k \u03A9   "
    if "ch1" in column:
        color = 'gray'
        type = " RE - WE"
        if ".3" in column:
            style = '-'
            color = "black"

    print(column)
    if i == 2:
        ax2.plot(time, -time_series[column],
                 color=color, ls=style, label=labels[i])
    else:
        ax2.plot(time, time_series[column],
                 color=color, ls=style, label=labels[i])
    i += 1
# ax.set_xticklabels(time)
ax2.set_xlabel("Time (seconds)", size=11)
ax2.set_ylabel("Potential (V)", size=11)
ax2.set_title("Voltage Readings of\nElectrodes", size=11)
# ax.set_ylim([-1, 1])
ax2.legend(prop={'size': 9})
# ax2.annotate('B)', (-0.27, 1.05), xycoords='axes fraction', size=18)
cv_data = pd.read_excel("CV_reads_10k.xlsx")

print(cv_data)
voltage = cv_data['voltage'].iloc[:2001] / 1000
print(voltage)
for column in cv_data.columns:
    style = '--'
    color = "forestgreen"
    if column == 'voltage':
        continue
    print(column)
    if 'ideal' in column:
        color = 'black'
        style = ':'
    elif column == '1k':
        color = "red"
        style = '-'
#     ax1.plot(voltage, cv_data[column].iloc[:2001], label=column, color=color, ls=style)
# ax1.set_xlabel("Voltage (V)")
# ax1.set_ylabel("Current (\u00B5A)")
# ax1.set_title("CV reading")
# ax1.legend(title='Analog Routing\nResistance', loc='lower right')
# ax1.annotate('A)', (-0.27, 1.05), xycoords='axes fraction', size=18)

plt.tight_layout()
plt.show()
