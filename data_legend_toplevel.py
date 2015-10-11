__author__ = 'Kyle Vitautas Lopin'


import Tkinter as tk

color_choices = ['black', 'gray', 'red', 'green', 'blue', 'orange', 'magenta']

class DataLegendTop(tk.Toplevel):
    """
    Make a toplevel that will allow the user to change the color

    """

    def __init__(self, _master):

        tk.Toplevel.__init__(self, master=_master)
        legend_entries = []
        delete_selection = []
        var_delete = []
        vert_frame = []  # make a list to keep the vertical frames in
        tk.Label(self, text="Configure Data Legend").pack(side="top")
        print "master index: ", _master.data.index
        for i in range(_master.data.index):
            vert_frame = tk.Frame(self)
            vert_frame.pack(side="top")
            drop_menu = tk.Menubutton(vert_frame, text='Color')
            color_picks = tk.Menu(drop_menu)
            drop_menu.config(menu=color_picks)
            color_picks.add_command(label='1')

            drop_menu.pack(side='left')
            # tk.Label(vert_frame, text='color hold').pack(side="left")
            legend_entries.append(tk.Entry(vert_frame, text="hold"))
            legend_entries[i].pack(side="left")
            var_delete.append(tk.IntVar)
            delete_selection.append(tk.Checkbutton(vert_frame, text="delete", variable=var_delete[i]))
            delete_selection[i].pack(side="left")
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(side='bottom')
        tk.Button(bottom_frame, text='Commit Changes',
                  command=lambda: self.save()).pack(side='left')
        tk.Button(bottom_frame, text='Exit',
                  command=lambda: self.destroy()).pack(side='left')

    def save(self):
        print "saving"
