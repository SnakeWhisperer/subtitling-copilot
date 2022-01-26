import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText


root = tk.Tk()
root.configure(background='#929292')

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
win_x = int((screen_w / 2) - 600)
win_y = int((screen_h / 2) - 400)


root.geometry(f'1200x700+{win_x}+{win_y}')

root.minsize(1200, 800)


# def option_hover(event):
#     event.widget.config(bg='#645eeb')

# def option_leave(event):
#     event.widget.config(bg='#645eeb')

def browse_files():
    browsed_files = filedialog.askopenfilenames()
    if browsed_files:
        print(browsed_files)

def OST_leave(event):
    event.widget.config(bg='#645eeb')


canvas = tk.Canvas(root, bg='white')
canvas.grid(column=1, row=0, columnspan=7, rowspan=9, sticky='nsew')
canvas.grid_columnconfigure(2, weight=1)
canvas.grid_rowconfigure(2, weight=1)
options_1_label = tk.Label(canvas, text='Tool 1 in Options 1', bg='white', padx=30)
choose_dir_label = tk.Label(canvas, text='Choose file(s)', bg='white', padx=60)
file_browse = tk.Button(canvas, text='Browse', height=1, width=15, command=browse_files)
options_2_label = tk.Label(canvas, text='Tool 1 in Options 2', bg='white', padx=30)


def options_1_click(event):
    global options_1_label
    global choose_dir_label
    global file_browse

    options_2_label.grid_forget()
    options_1_label.grid(column=0, row=0, sticky='w', pady=(30, 0))
    choose_dir_label.grid(column=0, row=1, sticky='w', pady=(30, 0))
    file_browse.grid(column=1, row=1)
    

    

def options_2_click(event):
    global options_2_label
    global choose_dir_label
    global file_browse


    options_1_label.grid_forget()
    options_2_label.grid(column=0, row=0, sticky='w', pady=(30, 0))
    choose_dir_label.grid(column=0, row=1, sticky='w', pady=(30, 0))
    file_browse.grid(column=1, row=1)
    





options_1_button = tk.Label(root, text="Options 1", height=2, width=20, pady=30, bg='#606060', fg='white')
options_2_button = tk.Label(root, text="Options 2", height=2, width=20, pady=30,bg='#606060', fg='white')
# options_3_button = tk.Label(root, text="Options 3", height=2, width=20, pady=30, bg='#606060', fg='white')
# options_4_button = tk.Label(root, text="Options 4", height=2, width=20, pady=30, bg='#606060', fg='white')
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(8, weight=1)

options_1_button.grid(column=0, row=0, rowspan=2, sticky='we')
# options_1_button.bind('<Motion>', option_hover)
# options_1_button.bind('<Leave>', OST_leave)
options_1_button.bind('<Button-1>', options_1_click)

options_2_button.grid(column=0, row=2, rowspan=2, sticky='we')
# options_2_button.bind('<Motion>', option_hover)
# options_2_button.bind('<Leave>', option_leave)
options_2_button.bind('<Button-1>', options_2_click)

# options_3_button.grid(column=0, row=4, rowspan=2, sticky='we')
# # options_3_button.bind('<Motion>', option_hover)
# # options_3_button.bind('<Leave>', option_leave)

# options_4_button.grid(column=0, row=6, rowspan=2, sticky='we')
# # options_4_button.bind('<Motion>', option_hover)
# options_4_button.bind('<Leave>', option_leave)





root.mainloop()