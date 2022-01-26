import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText


root = tk.Tk()
root.configure(background='#606060')

def OST_options():
    OST_ext_label = tk.Label(root, text="Extract OSTs", fg='black')
    OST_merge_label = tk.Label(root, text="Merge file and OSTs", fg='black')
    OST_gen_label = tk.Label(root, text="Generate OSTs", fg='black')

    OST_ext_label.grid(column=1, row=0)
    OST_merge_label.grid(column=1, row=1)
    OST_gen_label.grid(column=1, row=2)

    # Extract OSTs
    # Merge OSTs
    # Generate OSTs
    pass

def QC_options():
    QC_label = tk.Label(root, text="Quality check")
    chars_line_label = tk.Label(root, text="")
    max_lines_label = tk.Label(root, text="")
    max_duration_label = tk.Label(root, text="")
    min_duration_label = tk.Label(root, text="")
    chars_sec_label = tk.Label(root, text="")
    min_gap_label = tk.Label(root, text="")
    gap_label = tk.Label(root, text="")
    shot_changes_label = tk.Label(root, text="")
    OST_label = tk.Label(root, text="")

    pass

def prefix_options():
    pass

def issues_options():
    pass

# https://www.geeksforgeeks.org/how-to-set-a-tkinter-window-with-a-constant-size/
# https://stackoverflow.com/questions/14910858/how-to-specify-where-a-tkinter-window-opens

screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()
win_x = int((screen_w / 2) - 600)
win_y = int((screen_h / 2) - 350)

root.geometry(f'1200x700+{win_x}+{win_y}')

root.minsize(1200, 700)

# canvas = tk.Canvas(root, width=1200, height=700)
# canvas.grid(columnspan=3)

# NOTE: What are the units of the height and width and pady
#       and padx arguments? They don't seem to be the same.

# OST_button = tk.Button(root, text="OST", height=2, width=20, pady=30, command=OST_options)
# QC_button = tk.Button(root, text="Quality check", height=2, width=20, pady=30, command=QC_options)
# prefix_button = tk.Button(root, text="Pre-fix", height=2, width=20, pady=30, command=prefix_options)
# issues_button = tk.Button(root, text="Issues", height=2, width=20, pady=30, command=issues_options)
# test_label = tk.Label(root, text="Test label", bg='#606060', fg='white')


OST_button = tk.Label(root, text="OST", height=2, width=20, pady=30, bg='#606060', fg='white')
QC_button = tk.Label(root, text="Quality check", height=2, width=20, pady=30,bg='#606060', fg='white')
prefix_button = tk.Label(root, text="Pre-fix", height=2, width=20, pady=30, bg='#606060', fg='white')
issues_button = tk.Label(root, text="Issues", height=2, width=20, pady=30, bg='#606060', fg='white')
canvas = tk.Canvas(root, bg='white')
canvas.grid(column=1, row=0, columnspan=7, rowspan=9, sticky='nsew')
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(8, weight=1)

# 0 for OSTs
# 1 for Quality check
# 2 for prefix
# 3 for issues

active_option = 10


def browse_single_file():
    browsed_file = filedialog.askopenfilename()
    if browsed_file:
        global var_del_OSTs
        print(var_del_OSTs.get())
        print(browsed_file)

def browse_multiple_files():
    browsed_files = filedialog.askopenfilenames()
    if browsed_files:
        global var_del_OSTs
        print(var_del_OSTs.get())
        print(browsed_files)

def browse_dir():
    browsed_dir = filedialog.askdirectory()
    if browsed_dir:
        print(browsed_dir)


def option_hover(event):
    event.widget.config(bg='#383838')

def option_leave(event):
    event.widget.config(bg='#606060')

def OST_leave(event):
    if active_option != 0:
        event.widget.config(bg='#606060')


# OST widgets and variables

var_del_OSTs = tk.IntVar()
var_save_OSTs = tk.IntVar()
# OST_first = True
# QC_first = True
# prefix_first = True
# issues_first = True

OST_ext_label = tk.Label(canvas, text="Extract OSTs", bg='white', padx=30)
lang_dir_label_1 = tk.Label(canvas, text='Select file(s):', bg='white', padx=60)
lang_dir_entry_1 = tk.Entry(canvas, width=80, borderwidth=2)
lang_dir_browse_1 = tk.Button(canvas, text='Browse', height=1, width=15, command=browse_multiple_files)
OST_ext_save_to_label = tk.Label(canvas, text='Save OSTs to...', bg='white', padx=60)
OST_ext_save_to_entry = tk.Entry(canvas, width=80, borderwidth=2)
OST_ext_save_browse_butt = tk.Button(canvas, text='Browse', height=1, width=15, command=browse_dir)

del_OSTs = tk.Checkbutton(canvas, text='Delete OSTs from files', variable=var_del_OSTs, bg='white')
save_OSTs = tk.Checkbutton(canvas, text='Save extracted OSTs', variable=var_save_OSTs, bg='white')




QC_label = tk.Label(canvas, text='Quality check', bg='white', padx=30)
print(var_del_OSTs.get())

def OST_click(event):
    global OST_first
    global active_option
    global OST_ext_label
    global var_del_OSTs


    
    global QC_label
    global var_save_OSTs
    if active_option != 0:
        active_option = 0
        print('Here')

        QC_label.grid_forget()

        event.widget.config(bg='#383838')
        canvas.grid_columnconfigure(2, weight=1)
        canvas.grid_rowconfigure(18, weight=1)

        empty_col = tk.Label(canvas, text='', bg='white', padx=30)
        empty_col.grid(column=2, row=0)

        # Extract OSTs    
        # OST_ext_label = tk.Label(canvas, text="Extract OSTs", bg='white', padx=30)
        
        del_OSTs.grid(column=2, row=3, sticky='w', padx=(60, 0))
        
        
        save_OSTs.grid(column=2, row= 5, sticky='w', padx=(60, 0))

        
        OST_ext_label.grid(column=0, row=1, sticky='w', pady=(15, 0))
        lang_dir_label_1.grid(column=0, row=2, sticky='w')
        lang_dir_entry_1.grid(column=0, row=3, sticky='w', padx=60)
        lang_dir_browse_1.grid(column=1, row=3)
        OST_ext_save_to_label.grid(column=0, row=4, sticky='w')
        OST_ext_save_to_entry.grid(column=0, row=5, sticky='w', padx=60)
        OST_ext_save_browse_butt.grid(column=1, row=5)
            
        

        


        # Merge with OSTs
        OST_merge_label = tk.Label(canvas, text="Merge files and OSTs", bg='white', padx=30)
        lang_dir_label_2 = tk.Label(canvas, text='Language directory:', bg='white', padx=60)
        lang_dir_entry_2 = tk.Entry(canvas, width=80, borderwidth=2)
        lang_dir_browse_2 = tk.Button(canvas, text='Browse', height=1, width=15, command=browse_dir)
        OST_dir_label = tk.Label(canvas, text='OST directory:', bg='white', padx=60)
        OST_dir_entry = tk.Entry(canvas, width=80, borderwidth=2)
        OST_dir_browse_butt = tk.Button(canvas, text='Browse', height=1, width=15, command=browse_dir)
        save_to_label = tk.Label(canvas, text='Save merged files to...', bg='white', padx=60)
        save_to_entry = tk.Entry(canvas, width=80, borderwidth=2)
        save_to_browse = tk.Button(canvas, text='Browse', height=1, width=15, command=browse_dir)

        OST_merge_label.grid(column=0, row=6, sticky='w', pady=(30, 0))
        lang_dir_label_2.grid(column=0, row=7, sticky='w')
        lang_dir_entry_2.grid(column=0, row=8, sticky='w', padx=60)
        lang_dir_browse_2.grid(column=1, row=8)
        OST_dir_label.grid(column=0, row=9, sticky='w')
        OST_dir_entry.grid(column=0, row=10, sticky='w', padx=60)
        OST_dir_browse_butt.grid(column=1, row=10)
        save_to_label.grid(column=0, row=11, sticky='w')
        save_to_entry.grid(column=0, row=12, sticky='w', padx=60)
        save_to_browse.grid(column=1, row=12)
        

        # Generate OSTs
        OST_gen_label = tk.Label(canvas, text="Generate OSTs", bg='white', padx=30)
        OST_audit_label = tk.Label(canvas, text='OST Audit file(s):', bg='white', padx=60)
        OST_audit_entry = tk.Entry(canvas, width=80, borderwidth=2)
        browse_audit_button = tk.Button(canvas, text='Browse', height=1, width=15, command=browse_single_file)
        OST_gen_save_to_label = tk.Label(canvas, text="Save OSTs to...", bg='white', padx=60)
        OST_gen_save_to_entry = tk.Entry(canvas, width=80, borderwidth=2)
        OST_gen_save_browse_butt = tk.Button(canvas, text='Browse', height=1, width=15, command=browse_dir)    
        
        OST_gen_label.grid(column=0, row=13, sticky='w', pady=(30, 0))
        OST_audit_label.grid(column=0, row=14, sticky='w')
        OST_audit_entry.grid(column=0, row=15, sticky='w', padx=60)
        browse_audit_button.grid(column=1, row=15)
        OST_gen_save_to_label.grid(column=0, row=16, sticky='w')
        OST_gen_save_to_entry.grid(column=0, row=17, sticky='w', padx=60)
        OST_gen_save_browse_butt.grid(column=1, row=17)


        # Results

        results = ScrolledText(canvas, bg='white', fg='black')
        results.grid(column=0, columnspan=3, row=18, pady=25, padx=25, sticky='nsew')
        results.insert('1.0', 'Test\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\n')
        results.configure(state='disabled')
    
def QC_click(event):
    global active_option
    global OST_ext_label
    global QC_label
    if active_option != 1:
        active_option = 1

        event.widget.config(bg='#383838')
        canvas.grid_columnconfigure(2, weight=1)
        canvas.grid_rowconfigure(18, weight=1)

        empty_col = tk.Label(canvas, text='', bg='white', padx=30)
        empty_col.grid(column=2, row=0)

        
        
        OST_ext_label.grid_forget()
        QC_label.grid(column=0, row=1, sticky='w', pady=(15, 0))

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

issues_button.grid(column=0, row=6, rowspan=2, sticky='we')
issues_button.bind('<Motion>', option_hover)
issues_button.bind('<Leave>', option_leave)


root.mainloop()


# 32:32
# Use tk.Entry(root, width=50, bg=, fg=) for text entries.
# 