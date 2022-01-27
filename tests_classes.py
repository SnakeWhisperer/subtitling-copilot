import tkinter as tk
from tkinter import filedialog


def browse_files():
    browsed_files = filedialog.askopenfilenames()
    if browsed_files:
        print(browsed_files)


class App:

    def __init__(self):
        self.root = tk.Tk()
        self.root.configure(background='#929292')

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_x = int((screen_w / 2) - 600)
        win_y = int((screen_h / 2) - 400)

        self.root.geometry(f'1200x700+{win_x}+{win_y}')
        self.root.minsize(1200, 800)

        self.canvas = tk.Canvas(self.root, bg='white')
        self.canvas.grid(column=1, row=0, columnspan=7, rowspan=9, sticky='nsew')
        self.canvas.grid_columnconfigure(2, weight=1)
        self.canvas.grid_rowconfigure(2, weight=1)
        self.options_1_label = tk.Label(self.canvas, text='Tool 1 in Options 1', bg='white', padx=30)
        self.choose_dir_label = tk.Label(self.canvas, text='Choose file(s)', bg='white', padx=60)
        self.file_entry = tk.Entry(self.canvas, width=80, borderwidth=2)
        self.file_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_files)
        self.options_2_label = tk.Label(self.canvas, text='Tool 1 in Options 2', bg='white', padx=30)

        def options_1_click(event):

            self.options_2_label.grid_forget()
            self.options_1_label.grid(column=0, row=0, sticky='w', pady=(30, 0))
            self.choose_dir_label.grid(column=0, row=1, sticky='w', pady=(30, 0))
            self.file_entry.grid(column=0, columnspan=2, row=2, sticky='w', padx=(60, 0))
            self.file_browse.grid(column=2, row=2)

        def options_2_click(event):

            self.options_1_label.grid_forget()
            self.options_2_label.grid(column=0, row=0, sticky='w', pady=(30, 0))
            self.choose_dir_label.grid(column=0, row=1, sticky='w', pady=(30, 0))
            self.file_browse.grid(column=1, row=1)

        self.options_1_button = tk.Label(self.root, text="Options 1", height=2, width=20, pady=30, bg='#606060', fg='white')
        self.options_2_button = tk.Label(self.root, text="Options 2", height=2, width=20, pady=30, bg='#606060', fg='white')

        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(8, weight=1)

        self.options_1_button.grid(column=0, row=0, rowspan=2, sticky='we')
        self.options_1_button.bind('<Button-1>', options_1_click)

        self.options_2_button.grid(column=0, row=2, rowspan=2, sticky='we')
        self.options_2_button.bind('<Button-1>', options_2_click)

    def run(self):
        self.root.mainloop()


App().run()