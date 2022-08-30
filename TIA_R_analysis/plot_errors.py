# Copyright (c) 2020 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""

"""

__author__ = "Kyle Vitatus Lopin"

# installed libraries
import matplotlib.pyplot as plt
import pandas as pd

plt.style.use("seaborn")
fig, (ax1, ax2) = plt.subplots(ncols=2, nrows=1, figsize=(7, 4))
data = pd.read_csv("figure6_errors.csv")
time = data.iloc[:, 0]
print(time)
ax1.plot(time, data.iloc[:, 1], color='black', label="With compensation")
ax1.plot(time, data.iloc[:, 2], color='red', label="No compensation")
ax1.annotate('A)', (-0.27, 1.05), xycoords='axes fraction', size=18)
ax1.legend()
ax1.set_ylabel("Voltage error (mV)")
ax1.set_xlabel("Time (seconds)")

# ax2.plot(time, data.iloc[:, 1], color='black', label="With compensation")
ax2.plot(time, data.iloc[:, 2], color='red', label="No compensation")
ax2.set_ylim([-10, 10])
ax2.set_xlabel("Time (seconds)")
ax2.annotate('B)', (-0.27, 1.05), xycoords='axes fraction', size=18)
ax2.legend()

plt.tight_layout()
plt.show()
