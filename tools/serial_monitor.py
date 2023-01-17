# Copyright (c) 2022 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""
Make a simple GUI to put in inputs, in an entry box and receive messages and print them
to the console
"""

__author__ = "Kyle Vitautas Lopin"

# standard libraries
import time
import tkinter as tk

# local files
import usb_comm


class Monitor(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.device = usb_comm.SerialComm()
        self.entry = tk.Entry(self)
        self.entry.pack()
        tk.Button(self, text="Send message", command=self.send_message).pack()
        self.poll_for_input()

    def send_message(self):
        self.device.write_data(self.entry.get())

    def poll_for_input(self):
        self.after(10, self.poll_for_input)
        data = self.device.poll_for_data()
        if data:
            print(f"Got data: {data}")
            print(f"len data: {len(data)}")


if __name__ == '__main__':
    app = Monitor()
    print("check1")
    app.geometry("400x400")
    app.mainloop()
