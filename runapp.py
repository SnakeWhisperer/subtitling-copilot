import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import tkinter.font as tkFont
from functools import partial

from mc_helper import batch_gen_CPS_sheet

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



class App:

    def __init__(self):
        self.root = tk.Tk()
        self.root.configure(background='#606060')

        self.option_font = tkFont.Font(size=11, weight='bold')
        self.header_1_font = tkFont.Font(size=15, weight='bold', slant='italic')
        self.results_font = tkFont.Font(size=12, weight='bold')
        self.sub_header_font = tkFont.Font(size=10)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_x = int((screen_w / 2) - 800)
        win_y = int((screen_h / 2) - 450)

        self.root.geometry(f'1200x700+{win_x}+{win_y}')
        self.root.minsize(1600, 900)


        self.OST_button = tk.Label(self.root, text="OST", height=2, width=18, pady=30, bg='#606060', fg='white', font=self.option_font)
        self.QC_button = tk.Label(self.root, text="Batch QC", height=2, width=18, pady=30,bg='#606060', fg='white', font=self.option_font)
        self.prefix_button = tk.Label(self.root, text="Pre-fix", height=2, width=18, pady=30, bg='#606060', fg='white', font=self.option_font)
        self.issues_button = tk.Label(self.root, text="Issues", height=2, width=18, pady=30, bg='#606060', fg='white', font=self.option_font)
        self.canvas = tk.Canvas(self.root, bg='white', highlightthickness=0)
        self.canvas.grid(column=1, row=0, columnspan=7, rowspan=9, sticky='nsew')
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(8, weight=1)


        def save_OSTs_ext_check():
            if not self.var_save_OSTs.get():
                self.OST_ext_save_to_entry.configure(state='disabled')
            # else:
            #     self.OST_ext_save_to_entry.configure(state='normal')

        def browse_OST_ext_dir():
            browsed_dir = filedialog.askdirectory()
            if browsed_dir:
                self.ext_OST_lang_path = browsed_dir
                self.lang_dir_entry_1.configure(state='normal')
                self.lang_dir_entry_1.delete('0', tk.END)
                self.lang_dir_entry_1.insert('1', browsed_dir)
                self.lang_dir_entry_1.configure(state='disabled')


        def browse_dir_save_ext_OSTs():
            if self.var_save_OSTs.get():
                browsed_dir = filedialog.askdirectory()
                if browsed_dir:
                    self.ext_OST_save_dir = browsed_dir
                    self.OST_ext_save_to_entry.configure(state='normal')
                    self.OST_ext_save_to_entry.delete('0', tk.END)
                    self.OST_ext_save_to_entry.insert('1', browsed_dir)
                    self.OST_ext_save_to_entry.configure(state='disabled')

        def extract_OSTs():
            if not self.ext_OST_lang_path:
                self.OST_errors += 'Cannot extract OSTs. Please provide a directory for the VTT files.\n'
            if not self.ext_OST_save_dir and self.var_save_OSTs.get():
                self.OST_errors += 'Cannot extract and save OSTs. Please provide a directory to save the extracted OSTs.\n'
            
            if self.OST_errors:
                self.OST_results.configure(state='normal')
                self.OST_results.delete('1.0', tk.END)
                self.OST_results.insert('1.0', self.OST_errors)
                self.OST_results.configure(state='disabled')
                self.OST_errors = ''

            elif (self.ext_OST_lang_path
                  and ((self.ext_OST_save_dir and self.var_save_OSTs.get())
                       or (not self.ext_OST_save_dir
                           and not self.var_save_OSTs.get()))):
                self.OST_results.configure(state='normal')
                self.OST_results.delete('1.0', tk.END)
                self.OST_results.insert('1.0', 'OSTs extracted successfully')
                self.OST_results.configure(state='disabled')

        def browse_dir_sub_merge():
            browsed_dir = filedialog.askdirectory()
            if browsed_dir:
                self.merge_sub_dir = browsed_dir
                self.lang_dir_entry_2.configure(state='normal')
                self.lang_dir_entry_2.delete('0', tk.END)
                self.lang_dir_entry_2.insert('1', browsed_dir)
                self.lang_dir_entry_2.configure(state='disabled')
                

        def browse_dir_OST_merge():
            browsed_dir = filedialog.askdirectory()
            if browsed_dir:
                self.merge_OST_dir = browsed_dir
                self.OST_dir_entry.configure(state='normal')
                self.OST_dir_entry.delete('0', tk.END)
                self.OST_dir_entry.insert('1', browsed_dir)
                self.OST_dir_entry.configure(state='disabled')

        def browse_dir_merge_save():
            browsed_dir = filedialog.askdirectory()
            if browsed_dir:
                self.save_merge_OST_dir = browsed_dir
                self.save_to_entry.configure(state='normal')
                self.save_to_entry.delete('0', tk.END)
                self.save_to_entry.insert('1', browsed_dir)
                self.save_to_entry.configure(state='disabled')

        def merge_OSTs():
            pass



        def browse_audit_files():
            browsed_files = filedialog.askopenfilenames()
            if browsed_files:
                self.OST_audit_files = ''
                for i in range(len(browsed_files)):
                    self.OST_audit_files += browsed_files[i] + '\n'
                self.OST_audit_files = self.OST_audit_files.strip()

                self.OST_audit_entry.configure(state='normal')
                self.OST_audit_entry.delete('1.0', tk.END)
                self.OST_audit_entry.insert('1.0', self.OST_audit_files)
                self.OST_audit_entry.configure(state='disabled')

        def browse_gen_OST_save():
            browsed_dir = filedialog.askdirectory()
            if browsed_dir:
                self.OST_gen_save_dir = browsed_dir
                self.OST_gen_save_to_entry.configure(state='normal')
                self.OST_gen_save_to_entry.delete('0', tk.END)
                self.OST_gen_save_to_entry.insert('1', browsed_dir)
                self.OST_gen_save_to_entry.configure(state='disabled')
            

        def generate_OSTs():
            pass



        def browse_tar_path():
            browsed_files = filedialog.askopenfilenames()
            if browsed_files:
                file_names = ''
                for i in range(len(browsed_files)):
                    file_names += browsed_files[i] + '\n'

                self.tar_files = file_names.strip()
                self.target_files_field.configure(state='normal')
                self.target_files_field.delete('1.0', tk.END)
                self.target_files_field.insert('1.0', self.tar_files)
                self.target_files_field.configure(state='disabled')

        def browse_en_path():
            browsed_files = filedialog.askopenfilenames()
            if browsed_files:
                file_names = ''
                for i in range(len(browsed_files)):
                    file_names += browsed_files[i] + '\n'
                
                self.en_files = file_names.strip()
                self.source_files_field.configure(state='normal')
                self.source_files_field.delete('1.0', tk.END)
                self.source_files_field.insert('1.0', self.en_files)
                self.source_files_field.configure(state='disabled')

        def save_issue_sheet():
            file_name = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=(('MS Excel File', '*.xlsx'),)
            )
            self.save_to = file_name
            # self.save_to_entry.configure(state='normal')
            # self.save_to_entry.delete('1.0', tk.END)
            self.issues_save_to_entry.insert(0, self.save_to)
            self.issues_save_to_entry.configure(state='disabled')


        def gen_issue_sheet():
            if not self.tar_files:
                self.issues_errors += 'Cannot generate issue spreadsheet. Please select at least one target file.\n'
            if not self.en_files:
                self.issues_errors += 'Cannot generate issue spreadsheet. Please select at least one English file.\n'
            if not self.save_to:
                self.issues_errors += 'Cannot generate issue spreadsheet. Please select a file name and path for the spreadsheet.\n'

            if self.tar_files and self.en_files:
                en_files_list = self.en_files.split('\n')
                tar_files_list = self.tar_files.split('\n')

                if len(en_files_list) > len(tar_files_list):
                    self.issues_errors += 'Cannot generate issue spreadsheet. Received more source files than target files.'
                elif len(tar_files_list) > len(en_files_list):
                    self.issues_errors += 'Cannot generate issue spreadsheet. Received more target files than source files.'


            if self.issues_errors:
                self.issues_results.configure(state='normal')
                self.issues_results.delete('1.0', tk.END)
                self.issues_results.insert('1.0', self.issues_errors)
                self.issues_results.configure(state='disabled')
                self.issues_errors = ''
                return
            else:
                self.issues_results.configure(state='normal')
                self.issues_results.delete('1.0', tk.END)
                self.issues_results.configure(state='disabled')
                print('Here')
                en_path = self.en_files.split('\n')[0].split('/')
                en_path = '\\'.join(en_path[:-1])
                tar_path = self.tar_files.split('\n')[0].split('/')
                tar_path = '\\'.join(tar_path[:-1])

                en_files_list.sort()
                tar_files_list.sort()                
                
                result = batch_gen_CPS_sheet(en_files_list, tar_files_list, self.save_to, old=False)
                
                if type(result) == str:
                    self.issues_results.configure(state='normal')
                    self.issues_results.delete('1.0', tk.END)
                    self.issues_results.insert('1.0', result)
                    self.issues_results.configure(state='disabled')
                    self.issues_errors = ''
                    return

                else:
                    self.issues_results.configure(state='normal')
                    self.issues_results.delete('1.0', tk.END)
                    self.issues_results.insert('1.0', f'Issue spreadsheet generated successfully.\n{self.save_to}')
                    self.issues_results.configure(state='disabled')
        

        self.active_option = 10


        # || OST widgets

        # Extract OSTs
        self.var_del_OSTs = tk.IntVar()
        self.var_save_OSTs = tk.IntVar()

        self.OST_ext_label = tk.Label(self.canvas, text="Extract OSTs", bg='white', padx=30, font=self.option_font)
        self.lang_dir_label_1 = tk.Label(self.canvas, text='Subtitle file(s) directory:', bg='white', padx=60)
        self.lang_dir_entry_1 = tk.Entry(self.canvas, width=100, borderwidth=2)
        self.lang_dir_browse_1 = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_OST_ext_dir)
        self.OST_ext_save_to_label = tk.Label(self.canvas, text='Save OSTs to...', bg='white', padx=60)
        self.OST_ext_save_to_entry = tk.Entry(self.canvas, width=100, borderwidth=2)
        self.OST_ext_save_browse_butt = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_dir_save_ext_OSTs)

        self.del_OSTs = tk.Checkbutton(self.canvas, text='Delete OSTs from files', variable=self.var_del_OSTs, bg='white')
        self.save_OSTs = tk.Checkbutton(self.canvas, text='Save extracted OSTs', variable=self.var_save_OSTs, bg='white', command=save_OSTs_ext_check)

        self.extract_OSTs_button = tk.Button(self.canvas, text='Extract', height=1, width=15, command=extract_OSTs)


        # Merge with OSTs
        self.OST_merge_label = tk.Label(self.canvas, text="Merge files and OSTs", bg='white', padx=30, font=self.option_font)
        self.lang_dir_label_2 = tk.Label(self.canvas, text='Language directory:', bg='white', padx=60)
        self.lang_dir_entry_2 = tk.Entry(self.canvas, width=100, borderwidth=2)
        self.lang_dir_browse_2 = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_dir_sub_merge)
        self.OST_dir_label = tk.Label(self.canvas, text='OST directory:', bg='white', padx=60)
        self.OST_dir_entry = tk.Entry(self.canvas, width=100, borderwidth=2)
        self.OST_dir_browse_butt = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_dir_OST_merge)
        self.save_to_label = tk.Label(self.canvas, text='Save merged files to...', bg='white', padx=60)
        self.save_to_entry = tk.Entry(self.canvas, width=100, borderwidth=2)
        self.save_to_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_dir_merge_save)
        self.merge_OSTs_button = tk.Button(self.canvas, text='Merge', height=1, width=15, command=merge_OSTs)


        # Generate OSTs

        self.var_single_audit_file = tk.IntVar()

        self.OST_gen_label = tk.Label(self.canvas, text="Generate OSTs", bg='white', padx=30, font=self.option_font)
        self.OST_audit_label = tk.Label(self.canvas, text='OST Audit file(s):', bg='white', padx=60)
        # self.OST_audit_entry = tk.Entry(self.canvas, width=80, borderwidth=2)
        self.OST_audit_entry = ScrolledText(self.canvas, bg='white', fg='black', width=75, height=4, borderwidth=2, wrap='none')
        self.browse_audit_button = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_audit_files)
        self.OST_gen_save_to_label = tk.Label(self.canvas, text="Save OSTs to...", bg='white', padx=60)
        self.OST_gen_save_to_entry = tk.Entry(self.canvas, width=100, borderwidth=2)
        self.OST_gen_save_browse_butt = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_gen_OST_save)
        self.OST_gen_button = tk.Button(self.canvas, text='Generate', height=1, width=15, command=generate_OSTs)
        self.single_audit_file = tk.Checkbutton(self.canvas, text='Single audit file', variable=self.var_single_audit_file, bg='white')

        self.OST_line_1 = ''
        self.OST_line_1_1 = ''
        self.OST_line_2 = ''
        self.OST_line_2_2 = ''
        self.OST_line_3 = ''
        self.OST_line_3_3 = ''


        # || QC widgets

        self.QC_label = tk.Label(self.canvas, text='Batch Quality check', bg='white', padx=30)
        self.files_label = tk.Label(self.canvas, text='Subtitle file(s)', bg='white', padx=60)
        self.files_entry = tk.Entry(self.canvas, width=80, borderwidth=2)
        self.files_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_multiple_files)
        self.videos_label = tk.Label(self.canvas, text='Video(s)', bg='white', padx=60)
        self.videos_entry = tk.Entry(self.canvas, width=80, borderwidth=2)
        self.videos_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_multiple_files)
        self.sc_label = tk.Label(self.canvas, text='Scene changes directory', bg='white', padx=60)
        self.sc_entry = tk.Entry(self.canvas, width=80, borderwidth=2)
        self.sc_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_dir)

        # QC settings

        self.settings_label = tk.Label(self.canvas, text='QC settings', bg='white', padx=30)
        self.CPS_label = tk.Label(self.canvas, text='Max. CPS', bg='white', padx=60)
        self.CPS_var = tk.StringVar()
        self.CPS_entry = tk.Spinbox(self.canvas, from_=0.00, to=99.00, format="%.2f", increment=0.1, textvariable=self.CPS_var, width=5, wrap=True)
        self.CPS_spaces_var = tk.IntVar()
        self.CPS_check = tk.Checkbutton(self.canvas, text='Count spaces for CPS', variable=self.CPS_spaces_var, bg='white', padx=90)
        self.CPL_label = tk.Label(self.canvas, text='Max. CPL', bg='white', padx=60)
        self.CPL_limit_var = tk.IntVar()
        self.CPL_entry = tk.Spinbox(self.canvas, from_=0, to=100, textvariable=self.CPL_limit_var, width=5, wrap=True)
        self.max_lines_label = tk.Label(self.canvas, text='Max. lines', bg='white', padx=60)
        self.max_lines_var = tk.IntVar()
        self.max_lines_entry = tk.Spinbox(self.canvas, from_=0, to=100, textvariable=self.max_lines_var, width=5, wrap=True)
        self.min_duration_label = tk.Label(self.canvas, text='Min. duration (ms)', bg='white', padx=60)
        self.min_duration_var = tk.IntVar()
        self.min_duration_entry = tk.Spinbox(self.canvas, from_=0, to=100000, textvariable=self.min_duration_var, width=5, wrap=True)
        self.max_duration_label = tk.Label(self.canvas, text='Max. duration (ms)', bg='white', padx=60)
        self.max_duration_var = tk.IntVar()
        self.max_duration_entry = tk.Spinbox(self.canvas, from_=0, to=100000, textvariable=self.max_duration_var, width=5, wrap=True)
        self.ellipses_var = tk.IntVar()
        self.ellipsis_check = tk.Checkbutton(self.canvas, text='Check ellipses', variable=self.ellipses_var,bg='white')
        self.gaps_var = tk.IntVar()
        self.gaps_check = tk.Checkbutton(self.canvas, text='Check gaps', variable=self.gaps_var, bg='white')
        self.shot_changes_var = tk.IntVar()
        self.shot_changes_check = tk.Checkbutton(self.canvas, text='Check timing to shot changes', variable=self.shot_changes_var, bg='white')
        self.print_report_var = tk.IntVar()
        self.save_report_check = tk.Checkbutton(self.canvas, text='Save report', variable=self.print_report_var, bg='white')


        # || Issues widgets

        self.gen_issue_sheet_label = tk.Label(self.canvas, text='Generate issue spreadsheet', bg='white', padx=30, font=self.header_1_font)
        self.target_files_label = tk.Label(self.canvas, text='Target file(s)', bg='white', padx=60, font=self.sub_header_font)
        self.target_files_field = ScrolledText(self.canvas, bg='white', fg='black', width=110, height=6, borderwidth=2, wrap='none')
        # self.browse_tar_files_action = partial(browse_multiple_files, 'tar_files')
        self.target_files_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_tar_path)
        self.source_files_label = tk.Label(self.canvas, text='Source file(s)', bg='white', padx=60, font=self.sub_header_font)
        self.source_files_field = ScrolledText(self.canvas, bg='white', fg='black', width=110, height=6, borderwidth=2, wrap='none')
        self.source_files_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_en_path)
        self.save_spreadsheet_label = tk.Label(self.canvas, text='Save issue spreadsheet to...', bg='white', padx=60, font=self.sub_header_font)
        self.issues_save_to_entry = tk.Entry(self.canvas, width=110, borderwidth=2)
        self.issues_save_to_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=save_issue_sheet)
        self.generate_excel_button = tk.Button(self.canvas, text='Generate', height=1, width=15, padx=30, command=gen_issue_sheet)
        


        # self.CPS_label = tk.Label()



        # Results

        self.OST_results_label = tk.Label(self.canvas, text='Results', bg='white', padx=30, font=self.results_font)
        self.OST_results = ScrolledText(self.canvas, bg='white', fg='black')

        self.QC_results_label = tk.Label(self.canvas, text='Results', bg='white', padx=30, font=self.results_font)
        self.QC_results = ScrolledText(self.canvas, bg='white', fg='black')

        self.prefix_results_label = tk.Label(self.canvas, text='Results', bg='white', padx=30, font=self.results_font)
        self.prefix_results = ScrolledText(self.canvas, bg='white', fg='black')

        self.issues_results_label = tk.Label(self.canvas, text='Results', bg='white', padx=30, font=self.results_font)
        self.issues_results = ScrolledText(self.canvas, bg='white', fg='black')
        # results.grid(column=0, columnspan=3, row=18, pady=25, padx=25, sticky='nsew')
        # results.insert('1.0', 'Test\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\n')
        # results.configure(state='disabled')

        def option_hover(event):
            event.widget.config(bg='#383838')

        def option_leave(event):
            event.widget.config(bg='#606060')

        def OST_leave(event):
            if self.active_option != 0:
                event.widget.config(bg='#606060')


        def OST_click(event):
            if self.active_option != 0:
                self.active_option = 0

                # Forget QC
                self.QC_label.grid_forget()
                self.files_label.grid_forget()
                self.files_entry.grid_forget()
                self.files_browse.grid_forget()
                self.videos_label.grid_forget()
                self.videos_entry.grid_forget()
                self.videos_browse.grid_forget()
                self.sc_label.grid_forget()
                self.sc_entry.grid_forget()
                self.sc_browse.grid_forget()
                self.settings_label.grid_forget()
                self.CPS_label.grid_forget()
                self.CPS_entry.grid_forget()
                self.CPS_check.grid_forget()
                self.CPL_label.grid_forget()
                self.CPL_entry.grid_forget()
                self.max_lines_label.grid_forget()
                self.max_lines_entry.grid_forget()
                self.min_duration_label.grid_forget()
                self.min_duration_entry.grid_forget()
                self.max_duration_label.grid_forget()
                self.max_duration_entry.grid_forget()
                self.ellipsis_check.grid_forget()
                self.gaps_check.grid_forget()
                self.shot_changes_check.grid_forget()
                self.QC_results_label.grid_forget()
                self.QC_results.grid_forget()

                # Forget issues
                self.gen_issue_sheet_label.grid_forget()
                self.target_files_label.grid_forget()
                self.target_files_field.grid_forget()
                self.target_files_browse.grid_forget()
                self.source_files_label.grid_forget()
                self.source_files_field.grid_forget()
                self.source_files_browse.grid_forget()
                self.save_spreadsheet_label.grid_forget()
                self.issues_save_to_entry.grid_forget()
                self.issues_save_to_browse.grid_forget()
                self.generate_excel_button.grid_forget()
                self.issues_results_label.grid_forget()
                self.issues_results.grid_forget()






                event.widget.config(bg='#383838')
                self.canvas.grid_columnconfigure(2, weight=0)
                self.canvas.grid_columnconfigure(3, weight=0)
                self.canvas.grid_columnconfigure(4, weight=1)
                self.canvas.grid_rowconfigure(10, weight=0)
                self.canvas.grid_rowconfigure(17, weight=0)
                self.canvas.grid_rowconfigure(20, weight=1)

                # self.empty_col = tk.Label(self.canvas, text='', bg='white', padx=30)
                # self.empty_col.grid(column=3, row=0)

                self.del_OSTs.grid(column=3, row=3, sticky='w', padx=(30, 0))
        
        
                self.save_OSTs.grid(column=3, row= 5, sticky='w', padx=(30, 0))
                self.OST_ext_label.grid(column=0, row=1, sticky='w', pady=(25, 0))
                self.lang_dir_label_1.grid(column=0, row=2, sticky='w', pady=(15, 0))
                self.lang_dir_entry_1.grid(column=0, columnspan=2, row=3, sticky='w', padx=(60, 0))
                self.lang_dir_browse_1.grid(column=2, row=3, padx=45)
                self.OST_ext_save_to_label.grid(column=0, row=4, sticky='w')
                self.OST_ext_save_to_entry.grid(column=0, columnspan=2, row=5, sticky='w', padx=(60, 0))
                self.OST_ext_save_to_entry.configure(state='disabled')
                self.OST_ext_save_browse_butt.grid(column=2, row=5, padx=45)
                self.extract_OSTs_button.grid(column=4, row=5, padx=30, sticky='s')


                self.OST_merge_label.grid(column=0, row=6, sticky='w', pady=(40, 0))
                self.lang_dir_label_2.grid(column=0, row=7, sticky='w', pady=(15, 0))
                self.lang_dir_entry_2.grid(column=0, columnspan=2, row=8, sticky='w', padx=(60, 0))
                self.lang_dir_entry_2.configure(state='disabled', disabledbackground='white')
                self.lang_dir_browse_2.grid(column=2, row=8, padx=45)
                self.OST_dir_label.grid(column=0, row=9, sticky='w')
                self.OST_dir_entry.grid(column=0, columnspan=2, row=10, sticky='w', padx=(60, 0))
                self.OST_dir_entry.configure(state='disabled', disabledbackground='white')
                self.OST_dir_browse_butt.grid(column=2, row=10, padx=45)
                self.save_to_label.grid(column=0, row=11, sticky='w')
                self.save_to_entry.grid(column=0, columnspan=2, row=12, sticky='w', padx=(60, 0))
                self.save_to_entry.configure(state='disabled', disabledbackground='white')
                self.save_to_browse.grid(column=2, row=12, padx=45)
                self.merge_OSTs_button.grid(column=4, row=12, padx=30, sticky='s')


                self.OST_gen_label.grid(column=0, row=13, sticky='w', pady=(40, 0))
                self.OST_audit_label.grid(column=0, row=14, sticky='w', pady=(15, 0))
                self.OST_audit_entry.grid(column=0, columnspan=2, row=15, sticky='w', padx=(60, 0))
                self.OST_audit_entry.configure(state='disabled')
                self.browse_audit_button.grid(column=2, row=15, padx=45, sticky='s')
                self.OST_gen_save_to_label.grid(column=0, row=16, sticky='w')
                self.OST_gen_save_to_entry.grid(column=0, columnspan=2, row=17, sticky='w', padx=(60, 0))
                self.OST_gen_save_to_entry.configure(state='disabled', disabledbackground='white')
                self.OST_gen_save_browse_butt.grid(column=2, row=17, padx=45)
                self.OST_gen_button.grid(column=4, row=17, padx=30, sticky='s')
                self.single_audit_file.grid(column=3, row=15, sticky='w', padx=(30, 0))

                self.OST_results_label.grid(column=0, row=19, sticky='w', pady=(30, 0))
                self.OST_results.grid(column=0, columnspan=5, row=20, pady=25, padx=25, sticky='nsew')
                self.OST_results.configure(state='disabled')

                self.ext_OST_lang_path = ''
                self.ext_OST_save_dir = ''
                self.merge_sub_dir = ''
                self.merge_OST_dir = ''
                self.save_merge_OST_dir = ''
                self.OST_audit_files = ''
                self.OST_gen_save_dir = ''

                self.OST_errors = ''

                self.lang_dir_entry_1.configure(state='disabled')
                self.lang_dir_entry_1.configure(disabledbackground='white')
                self.OST_ext_save_to_entry.configure(disabledbackground='white')

                self.OST_line_1 = self.canvas.create_line(50, 38, 1370, 38, fill='black', width=2)
                self.OST_line_1_1 = self.canvas.create_line(1370, 38, 1370, 160, fill='black', width=2)
                self.OST_line_2 = self.canvas.create_line(50, 210, 1370, 210, fill='black', width=2)
                self.OST_line_2_2 = self.canvas.create_line(1370, 210, 1370, 380, fill='black', width=2)
                self.OST_line_3 = self.canvas.create_line(50, 430, 1370, 430, fill='black', width=2)
                self.OST_line_3_3 = self.canvas.create_line(1370, 430, 1370, 600, fill='black', width=2)



        def QC_click(event):
            if self.active_option != 1:
                self.active_option = 1

                event.widget.config(bg='#383838')
                self.canvas.grid_columnconfigure(4, weight=0)
                self.canvas.grid_columnconfigure(2, weight=1)
                self.canvas.grid_columnconfigure(3, weight=0)
                self.canvas.grid_rowconfigure(10, weight=0)
                self.canvas.grid_rowconfigure(20, weight=0)
                self.canvas.grid_rowconfigure(17, weight=1)

                # self.empty_col = tk.Label(self.canvas, text='', bg='white', padx=30)
                # self.empty_col.grid(column=2, row=0)

                
                # Forget OSTs
                self.del_OSTs.grid_forget()
                self.save_OSTs.grid_forget()
                self.OST_ext_label.grid_forget()
                self.lang_dir_label_1.grid_forget()
                self.lang_dir_entry_1.grid_forget()
                self.lang_dir_browse_1.grid_forget()
                self.OST_ext_save_to_label.grid_forget()
                self.OST_ext_save_to_entry.grid_forget()
                self.OST_ext_save_browse_butt.grid_forget()
                self.OST_merge_label.grid_forget()
                self.lang_dir_label_2.grid_forget()
                self.lang_dir_entry_2.grid_forget()
                self.lang_dir_browse_2.grid_forget()
                self.OST_dir_label.grid_forget()
                self.OST_dir_entry.grid_forget()
                self.OST_dir_browse_butt.grid_forget()
                self.save_to_label.grid_forget()
                self.save_to_entry.grid_forget()
                self.save_to_browse.grid_forget()
                self.OST_gen_label.grid_forget()
                self.OST_audit_label.grid_forget()
                self.OST_audit_entry.grid_forget()
                self.browse_audit_button.grid_forget()
                self.OST_gen_save_to_label.grid_forget()
                self.OST_gen_save_to_entry.grid_forget()
                self.OST_gen_save_browse_butt.grid_forget()
                self.OST_results_label.grid_forget()
                self.OST_results.grid_forget()
                self.extract_OSTs_button.grid_forget()
                self.merge_OSTs_button.grid_forget()
                self.OST_gen_button.grid_forget()
                self.single_audit_file.grid_forget()

                self.canvas.delete(self.OST_line_1)
                self.canvas.delete(self.OST_line_1_1)
                self.canvas.delete(self.OST_line_2)
                self.canvas.delete(self.OST_line_2_2)
                self.canvas.delete(self.OST_line_3)
                self.canvas.delete(self.OST_line_3_3)


                # Forget issues
                self.gen_issue_sheet_label.grid_forget()
                self.target_files_label.grid_forget()
                self.target_files_field.grid_forget()
                self.target_files_browse.grid_forget()
                self.source_files_label.grid_forget()
                self.source_files_field.grid_forget()
                self.source_files_browse.grid_forget()
                self.save_spreadsheet_label.grid_forget()
                self.issues_save_to_entry.grid_forget()
                self.issues_save_to_browse.grid_forget()
                self.generate_excel_button.grid_forget()
                self.issues_results_label.grid_forget()
                self.issues_results.grid_forget()


                self.QC_label.grid(column=0, row=1, sticky='w', pady=(15, 0))
                self.files_label.grid(column=0, row=2, sticky='w')
                self.files_entry.grid(column=0, columnspan=2, row=3, sticky='w', padx=60)
                self.files_browse.grid(column=2, row=3)
                self.videos_label.grid(column=0, row=4, sticky='w')
                self.videos_entry.grid(column=0, columnspan=2, row=5, sticky='w', padx=60)
                self.videos_browse.grid(column=2, row=5)
                self.sc_label.grid(column=0, row=6, sticky='w')
                self.sc_entry.grid(column=0, columnspan=2, row=7, sticky='w', padx=60)
                self.sc_browse.grid(column=2, row=7)
                
                self.settings_label.grid(column=0, row=8, sticky='w')
                self.CPS_label.grid(column=0, row=9, sticky='w')
                self.CPS_entry.grid(column=1, row=9, sticky='w')
                self.CPS_check.grid(column=0, row=10, sticky='w')
                self.CPL_label.grid(column=0, row=11, sticky='w')
                self.CPL_entry.grid(column=1, row=11, sticky='w')
                self.max_lines_label.grid(column=0, row=12, sticky='w')
                self.max_lines_entry.grid(column=1, row=12, sticky='w')
                self.min_duration_label.grid(column=0, row=13, sticky='w')
                self.min_duration_entry.grid(column=1, row=13, sticky='w')
                self.max_duration_label.grid(column=0, row=14, sticky='w')
                self.max_duration_entry.grid(column=1, row=14, sticky='w')
                self.ellipsis_check.grid(column=2, row=9, sticky='w')
                self.gaps_check.grid(column=2, row=10, sticky='w')
                self.shot_changes_check.grid(column=2, row=11, sticky='w')

                self.QC_results_label.grid(column=0, row=16, sticky='w', pady=(30, 0))
                self.QC_results.grid(column=0, columnspan=4, row=17, pady=25, padx=25, sticky='nsew')
                self.QC_results.insert('1.0', 'Test\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\n')
                self.QC_results.configure(state='disabled')

        def prefix_click(event):

            if self.active_option != 2:
                self.active_option = 2

                self.OST_ext_label.grid_forget()
                self.lang_dir_label_1.grid_forget()
                self.lang_dir_entry_1.grid_forget()
                self.lang_dir_browse_1.grid_forget()
                self.OST_ext_save_to_label.grid_forget()
                self.OST_ext_save_to_entry.grid_forget()
                self.OST_ext_save_browse_butt.grid_forget()
                self.del_OSTs.grid_forget()
                self.save_OSTs.grid_forget()

                self.OST_merge_label.grid_forget()
                self.lang_dir_label_2.grid_forget()
                self.lang_dir_entry_2.grid_forget()
                self.lang_dir_browse_2.grid_forget()
                self.OST_dir_label.grid_forget()
                self.OST_dir_entry.grid_forget()
                self.OST_dir_browse_butt.grid_forget()
                self.save_to_label.grid_forget()
                self.save_to_entry.grid_forget()
                self.save_to_browse.grid_forget()

                self.OST_gen_label.grid_forget()
                self.OST_audit_label.grid_forget()
                self.OST_audit_entry.grid_forget()
                self.browse_audit_button.grid_forget()
                self.OST_gen_save_to_label.grid_forget()
                self.OST_gen_save_to_entry.grid_forget()
                self.OST_gen_save_browse_butt.grid_forget()
            

        def issues_click(event):
            if self.active_option != 3:
                self.active_option = 3

                event.widget.config(bg='#383838')
                self.canvas.grid_columnconfigure(2, weight=0)
                self.canvas.grid_columnconfigure(3, weight=1)
                self.canvas.grid_columnconfigure(4, weight=0)
                self.canvas.grid_rowconfigure(17, weight=0)
                self.canvas.grid_rowconfigure(20, weight=0)
                self.canvas.grid_rowconfigure(10, weight=1)

                # Forget OSTs
                self.del_OSTs.grid_forget()
                self.save_OSTs.grid_forget()
                self.OST_ext_label.grid_forget()
                self.lang_dir_label_1.grid_forget()
                self.lang_dir_entry_1.grid_forget()
                self.lang_dir_browse_1.grid_forget()
                self.OST_ext_save_to_label.grid_forget()
                self.OST_ext_save_to_entry.grid_forget()
                self.OST_ext_save_browse_butt.grid_forget()
                self.OST_merge_label.grid_forget()
                self.lang_dir_label_2.grid_forget()
                self.lang_dir_entry_2.grid_forget()
                self.lang_dir_browse_2.grid_forget()
                self.OST_dir_label.grid_forget()
                self.OST_dir_entry.grid_forget()
                self.OST_dir_browse_butt.grid_forget()
                self.save_to_label.grid_forget()
                self.save_to_entry.grid_forget()
                self.save_to_browse.grid_forget()
                self.OST_gen_label.grid_forget()
                self.OST_audit_label.grid_forget()
                self.OST_audit_entry.grid_forget()
                self.browse_audit_button.grid_forget()
                self.OST_gen_save_to_label.grid_forget()
                self.OST_gen_save_to_entry.grid_forget()
                self.OST_gen_save_browse_butt.grid_forget()
                self.OST_results_label.grid_forget()
                self.OST_results.grid_forget()
                self.extract_OSTs_button.grid_forget()
                self.merge_OSTs_button.grid_forget()
                self.OST_gen_button.grid_forget()
                self.single_audit_file.grid_forget()

                self.canvas.delete(self.OST_line_1)
                self.canvas.delete(self.OST_line_1_1)
                self.canvas.delete(self.OST_line_2)
                self.canvas.delete(self.OST_line_2_2)
                self.canvas.delete(self.OST_line_3)
                self.canvas.delete(self.OST_line_3_3)

                # Forget QC
                self.QC_label.grid_forget()
                self.files_label.grid_forget()
                self.files_entry.grid_forget()
                self.files_browse.grid_forget()
                self.videos_label.grid_forget()
                self.videos_entry.grid_forget()
                self.videos_browse.grid_forget()
                self.sc_label.grid_forget()
                self.sc_entry.grid_forget()
                self.sc_browse.grid_forget()
                self.settings_label.grid_forget()
                self.CPS_label.grid_forget()
                self.CPS_check.grid_forget()
                self.CPL_label.grid_forget()
                self.CPL_entry.grid_forget()
                self.max_lines_label.grid_forget()
                self.min_duration_label.grid_forget()
                self.max_duration_label.grid_forget()
                self.ellipsis_check.grid_forget()
                self.gaps_check.grid_forget()
                self.shot_changes_check.grid_forget()
                self.CPS_entry.grid_forget()
                self.CPL_entry.grid_forget()
                self.max_lines_entry.grid_forget()
                self.min_duration_entry.grid_forget()
                self.max_duration_entry.grid_forget()
                self.QC_results_label.grid_forget()
                self.QC_results.grid_forget()

                self.gen_issue_sheet_label.grid(column=0, row=1, sticky='w', pady=(15, 0))
                self.target_files_label.grid(column=0, row=2, sticky='w', pady=(25, 0))
                self.target_files_field.grid(column=0, columnspan=2, row=3, pady=(15, 0), padx=60, sticky='nsew')
                self.target_files_browse.grid(column=2, row=3, sticky='sw')
                self.source_files_label.grid(column=0, row=4, sticky='w', pady=(25, 0))
                self.source_files_field.grid(column=0, columnspan=2, row=5, pady=(15, 0), padx=60, sticky='nsew')
                self.source_files_browse.grid(column=2, row=5, sticky='sw')
                self.save_spreadsheet_label.grid(column=0, row=6, sticky='w', pady=(25, 0))
                self.issues_save_to_entry.grid(column=0, columnspan=2, row=7, padx=60, pady=(15, 0), sticky='nsew')
                self.issues_save_to_browse.grid(column=2, row=7, sticky='sw')
                self.generate_excel_button.grid(column=3, row=7, sticky='s')
                
                # self.issues_results_label.grid(column=0, row=8, sticky='w', pady=(30, 0))
                self.issues_results_label.grid(column=0, row=9, sticky='w', pady=(30, 0))
                self.issues_results.grid(column=0, columnspan=4, row=10, pady=25, padx=25, sticky='nsew')
                # self.results.insert('1.0', 'Test\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\n')
                self.issues_results.configure(state='disabled')

                self.tar_files = ''
                self.en_files = ''
                self.save_to = ''
                self.issues_errors = ''
                self.issues_results_text = ''



        self.OST_button.grid(column=0, row=0, rowspan=2, sticky='we')
        self.OST_button.bind('<Motion>', option_hover)
        self.OST_button.bind('<Leave>', OST_leave)
        self.OST_button.bind('<Button-1>', OST_click)

        self.QC_button.grid(column=0, row=2, rowspan=2, sticky='we')
        self.QC_button.bind('<Motion>', option_hover)
        self.QC_button.bind('<Leave>', option_leave)
        self.QC_button.bind('<Button-1>', QC_click)

        self.prefix_button.grid(column=0, row=4, rowspan=2, sticky='we')
        self.prefix_button.bind('<Motion>', option_hover)
        self.prefix_button.bind('<Leave>', option_leave)
        self.prefix_button.bind('<Button-1>', prefix_click)

        self.issues_button.grid(column=0, row=6, rowspan=2, sticky='we')
        self.issues_button.bind('<Motion>', option_hover)
        self.issues_button.bind('<Leave>', option_leave)
        self.issues_button.bind('<Button-1>', issues_click)


    def run(self):
        self.root.mainloop()



App().run()