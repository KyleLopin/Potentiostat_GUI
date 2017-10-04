__author__ = 'Kyle Vitautas Lopin'

import Tkinter as tk


class ConnectionButton(tk.Button):
    """
    Class that creates a button that will allow the user to connect to the amperometry device if it is available
    This checks if a device is already connected (in which case it does nothing) and attempts to connect if a device
    is not already attached [see method connect for more details]
    The button will be red if no device is connected and green if it is connected, except on mac devices as there
    tcl (or something) does not allow the buttons to be colored
    """
    def __init__(self, frame):
        """

        :param frame: tk.frame that is where the button should be packed into
        :return:
        """
        self.connect_button = tk.Button(frame, command=lambda: self.connect(self.connect_button))

        if self.device.connected:
            self.connect_button["text"] = "Connected"
            self.connect_button.config(bg='green')
        else:
            self.connect_button["text"] = "Not Connected"
            self.connect_button.config(bg='red')
        self.connect_button.pack(side='bottom')