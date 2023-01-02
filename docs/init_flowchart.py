# Copyright (c) 2022 Kyle Lopin (Naresuan University) <kylel@nu.ac.th>

"""
Make a flowchart to show how the GUI starts up
"""

__author__ = "Kyle Vitautas Lopin"

# installed libraries
import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm
from schemdraw.flow import *

with schemdraw.Drawing() as d:
    d.config(unit=1, fontsize=10)
    d += (start := Start(w=5, h=1).label("run amp_gui.py"))
    d += Arrow().down().label("Call ElectroChemGui()")
    # make this process wide to not cut off the figure
    d += Process(w=13, h=1.5).label("get device parameters from\nproperties.DeviceParameters")
    d += Arrow().down()
    d += Process(w=6, h=1.5).label("make the device from\nusb_comm.AmpUsb()")
    d += Arrow().down()
    d += Process(w=6, h=1.5).label("initialize CV Frame")
    d += Arrow().down().label("Call cv_frame.CVFrame()")
    d += (d1 := Decision(w=7, h=4, E="    Yes\n"
                                     "assume this\n"
                                     "is the start",
                         S="No", fontsize=10).label("does initialize==True"))

    d += Arrow().down()
    d += (p2 := Process(w=10, h=2.5).label("Initialize amp_frame.AmpFrame\n"
                                           "doesn't send device parameters"))
    d += Arrow().right(d.unit*4).at(d1.E)
    d += (p1 := Process(w=10, h=3).label("send device parameters using\n"
                                        "cv_frame.CVFrame.USBHandler in\n"
                                        "send_cv_parameters"))
    d += Arrow(reverse=True).right().at(p2.E).tox(p1.S)
    d += Line().up().to(p1.S)
    d += Arrow().down().at(p2.S)
    d += Process(w=12, h=3).label("Initialize asv_frame.ASVFrame\n"
                                  "parent class is cv_frame.CVFrame\n"
                                  "with initialize set to False so it\n"
                                  "won't send new parameters")
    d += Arrow().down()
    d += Process(w=8, h=2).label("Setup the Connect button\n"
                                 "with device status")
    d += Arrow().down()
    d += Process(w=8, h=2).label("Make option menus")
