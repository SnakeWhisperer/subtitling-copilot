import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText


root = tk.Tk()
root.configure(background='#606060')

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
win_x = int((screen_w / 2) - 600)
win_y = int((screen_h / 2) - 400)


root.geometry(f'1200x700+{win_x}+{win_y}')

root.minsize(1200, 800)

active_option = 0
drawn = False

def option_hover(event):
    event.widget.config(bg='#454545')

def option_leave(event):
    event.widget.config(bg='#645eeb')

def OST_leave(event):
    if active_option != 0:
        event.widget.config(bg='#606060')
    else:
        event.widget.config(bg='#645eeb')


def browse_single_file():
    browsed_file = filedialog.askopenfilename()
    if browsed_file:
        print(browsed_file)

def browse_multiple_files():
    browsed_files = filedialog.askopenfilenames()
    if browsed_files:
        print(browsed_files)

def browse_dir():
    browsed_dir = filedialog.askdirectory()
    if browsed_dir:
        print(browsed_dir)



def OST_click(event):
    global active_option
    global drawn
    if active_option != 0:
        drawn = False
    active_option = 0
    print(drawn)

def QC_click(event):
    global active_option
    global drawn
    if active_option != 1:
        drawn = False
    active_option = 1
    print(active_option)

def prefix_click(event):
    global active_option
    global drawn
    if active_option != 2:
        drawn = False
    active_option = 2

def issues_click(event):
    global active_option
    global drawn
    if active_option != 3:
        drawn = False
    active_option = 3


print(active_option)




OST_button = tk.Label(root, text="OST", height=2, width=20, pady=30, bg='#645eeb', fg='white')
QC_button = tk.Label(root, text="Quality check", height=2, width=20, pady=30,bg='#606060', fg='white')
prefix_button = tk.Label(root, text="Pre-fix", height=2, width=20, pady=30, bg='#606060', fg='white')
issues_button = tk.Label(root, text="Issues", height=2, width=20, pady=30, bg='#606060', fg='white')
canvas = tk.Canvas(root, bg='white')
canvas.grid(column=1, row=0, columnspan=7, rowspan=9, sticky='nsew')
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(8, weight=1)


OST_button.grid(column=0, row=0, rowspan=2, sticky='we')
OST_button.bind('<Motion>', option_hover)
OST_button.bind('<Leave>', OST_leave)
OST_button.bind('<Button-1>', OST_click)

QC_button.grid(column=0, row=2, rowspan=2, sticky='we')
QC_button.bind('<Motion>', option_hover)
QC_button.bind('<Leave>', option_leave)
QC_button.bind('<Button-1>', QC_click)

prefix_button.grid(column=0, row=4, rowspan=2, sticky='we')
prefix_button.bind('<Motion>', option_hover)
prefix_button.bind('<Leave>', option_leave)
prefix_button.bind('<Button-1>', prefix_click)

issues_button.grid(column=0, row=6, rowspan=2, sticky='we')
issues_button.bind('<Motion>', option_hover)
issues_button.bind('<Leave>', option_leave)
issues_button.bind('<Button-1>', issues_click)




# Extract OSTs    
OST_ext_label = tk.Label(canvas, text="Extract OSTs", bg='white', padx=30)
lang_dir_label_1 = tk.Label(canvas, text='Select file(s):', bg='white', padx=60)
lang_dir_entry_1 = tk.Entry(canvas, width=80, borderwidth=2)
lang_dir_browse_1 = tk.Button(canvas, text='Browse', height=1, width=15, command=browse_multiple_files)
OST_ext_save_to_label = tk.Label(canvas, text='Save OSTs to...', bg='white', padx=60)
OST_ext_save_to_entry = tk.Entry(canvas, width=80, borderwidth=2)
OST_ext_save_browse_butt = tk.Button(canvas, text='Browse', height=1, width=15, command=browse_dir)
var_del_OSTs = tk.IntVar()
del_OSTs = tk.Checkbutton(canvas, text='Delete OSTs from files', variable=var_del_OSTs, bg='white')
var_save_OSTs = tk.IntVar()
save_OSTs = tk.Checkbutton(canvas, text='Save extracted OSTs', variable=var_save_OSTs, bg='white')





# Quality check
QC_label = tk.Label(canvas, text="Quality check", bg='white', padx=30)

print(drawn)
if not drawn:
    if active_option == 0:
        print(active_option)
        print('There')
        canvas.grid_columnconfigure(2, weight=1)
        canvas.grid_rowconfigure(18, weight=1)

        empty_col = tk.Label(canvas, text='', bg='white', padx=30)
        empty_col.grid(column=2, row=0)

        OST_ext_label.grid(column=0, row=1, sticky='w', pady=(15, 0))
        lang_dir_label_1.grid(column=0, row=2, sticky='w')
        lang_dir_entry_1.grid(column=0, row=3, sticky='w', padx=60)
        lang_dir_browse_1.grid(column=1, row=3)
        OST_ext_save_to_label.grid(column=0, row=4, sticky='w')
        OST_ext_save_to_entry.grid(column=0, row=5, sticky='w', padx=60)
        OST_ext_save_browse_butt.grid(column=1, row=5)

        del_OSTs.grid(column=2, row=3, sticky='w', padx=(60, 0))
        save_OSTs.grid(column=2, row= 5, sticky='w', padx=(60, 0))

    elif active_option == 1:
        print('QC')
        OST_ext_label.grid_forget()
        
        QC_label.grid(column=0, row=1, sticky='w', pady=(15, 0))
        pass
    elif active_option == 2:
        pass
    elif active_option == 3:
        pass



root.mainloop()