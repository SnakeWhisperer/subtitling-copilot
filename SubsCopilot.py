import os

import tkinter as tk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import tkinter.font as tkFont
from functools import partial

from mc_helper import batch_gen_CPS_sheet, batch_extract_OSTs, get_OSTs_single, get_OSTs
from vtt_handler import batch_merge_subs
from checks import batch_quality_check

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
        self.root.title('Subtitling Copilot')
        self.root.configure(background='#606060')

        self.option_font = tkFont.Font(size=11, weight='bold')
        self.header_1_font = tkFont.Font(size=15, weight='bold', slant='italic')
        self.results_font = tkFont.Font(size=12, weight='bold')
        self.sub_header_font = tkFont.Font(size=10)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.fixed_w = int(screen_w*0.8)
        self.fixed_h = int(screen_h*0.8)
        self.root.minsize(self.fixed_w, self.fixed_h)
        self.root.maxsize(self.fixed_w, self.fixed_h)
        win_x = int((screen_w / 2) - (self.fixed_w/2))
        win_y = int((screen_h / 2) - (self.fixed_h/2))

        # win_x = int((screen_w / 2) - 800)
        # win_y = int((screen_h / 2) - 450)

        # self.root.geometry(f'1200x700+{win_x}+{win_y}')
        # self.root.minsize(1600, 900)
        # self.root.maxsize(1600, 900)


        self.OST_button = tk.Label(self.root, text="OST", height=2, width=18, pady=30, bg='#606060', fg='white', font=self.option_font)
        self.QC_button = tk.Label(self.root, text="Batch QC", height=2, width=18, pady=30,bg='#606060', fg='white', font=self.option_font)
        # self.prefix_button = tk.Label(self.root, text="Pre-fix", height=2, width=18, pady=30, bg='#606060', fg='white', font=self.option_font)
        self.issues_button = tk.Label(self.root, text="Issues", height=2, width=18, pady=30, bg='#606060', fg='white', font=self.option_font)
        self.canvas = tk.Canvas(self.root, bg='white', highlightthickness=0)
        self.canvas.grid(column=1, row=0, columnspan=7, rowspan=9, sticky='nsew')
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(8, weight=1)


        def round_rectangle(x1, y1, x2, y2, radius=10, **kwargs):
        
            points = [x1+radius, y1,
                    x1+radius, y1,
                    x2-radius, y1,
                    x2-radius, y1,
                    x2, y1,
                    x2, y1+radius,
                    x2, y1+radius,
                    x2, y2-radius,
                    x2, y2-radius,
                    x2, y2,
                    x2-radius, y2,
                    x2-radius, y2,
                    x1+radius, y2,
                    x1+radius, y2,
                    x1, y2,
                    x1, y2-radius,
                    x1, y2-radius,
                    x1, y1+radius,
                    x1, y1+radius,
                    x1, y1]

            return self.canvas.create_polygon(points, **kwargs, smooth=True)


        def save_OSTs_ext_check():
            if not self.var_save_OSTs.get():
                self.OST_ext_save_to_entry.configure(state='disabled')
            # else:
            #     self.OST_ext_save_to_entry.configure(state='normal')

        def overwrite_sub_files():
            if not self.var_overwrite_merged_files.get():
                self.save_to_entry.configure(disabledbackground='white')
            else:
                self.save_to_entry.configure(disabledbackground='light grey')
                self.save_to_entry.configure(state='normal')
                self.save_to_entry.delete('0', tk.END)
                if self.save_merge_OST_dir:
                    self.save_to_entry.insert('1', self.save_merge_OST_dir)
                
                self.save_to_entry.configure(state='disabled')


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

            # print(self.var_save_OSTs.get())
            # print(self.var_del_OSTs.get())
            # print(self.ext_OST_lang_path)
            # print(self.ext_OST_save_dir)
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

            # elif (self.ext_OST_lang_path
            #       and ((self.ext_OST_save_dir and self.var_save_OSTs.get())
            #            or (not self.ext_OST_save_dir
            #                and not self.var_save_OSTs.get()))):

            elif self.var_save_OSTs.get() or self.var_del_OSTs.get():
                total_errors = batch_extract_OSTs(
                    self.ext_OST_lang_path,
                    self.ext_OST_save_dir,
                    save_OSTs=self.var_save_OSTs.get(),
                    delete_OSTs=self.var_del_OSTs.get()
                )

                if total_errors:
                    warnings, errors = total_errors

                    if warnings:
                        warnings_string = ''
                        for warning_key in warnings.keys():
                            warnings_string += 'Warnings\n\n\n'
                            warnings_string += warning_key + '\n\t'
                            warnings_string += warnings[warning_key] + '\n'

                        self.OST_results.configure(state='normal')
                        self.OST_results.delete('1.0', tk.END)
                    

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
            if not self.var_overwrite_merged_files.get():
                browsed_dir = filedialog.askdirectory()
                if browsed_dir:
                    self.save_merge_OST_dir = browsed_dir
                    self.save_to_entry.configure(state='normal')
                    self.save_to_entry.delete('0', tk.END)
                    self.save_to_entry.insert('1', browsed_dir)
                    self.save_to_entry.configure(state='disabled')

        def merge_OSTs():
            if not self.merge_sub_dir:
                self.OST_errors += 'Cannot merge files. Please provide a directory for subtitle files.\n'
            if not self.merge_OST_dir:
                self.OST_errors += 'Cannot merge files. Please provide a directory for OST files.\n'
            if not self.save_merge_OST_dir:
                self.OST_errors += 'Cannot merge files. Please provide a directory to save the resulting VTT.\n'

            original_dir = os.getcwd()

            os.chdir(self.merge_sub_dir)
            sub_dir_list = os.listdir()
            sub_files_list = []

            for item in sub_dir_list:
                name, ext = os.path.splitext(item)
                if ext == '.vtt':
                    sub_files_list.append(item)

            os.chdir(self.merge_OST_dir)
            OST_dir_list = os.listdir()
            OST_files_list = []

            for item in OST_dir_list:
                name, ext = os.path.splitext(item)
                if ext == '.vtt':
                    OST_files_list.append(item)

            os.chdir(original_dir)

            if len(sub_files_list) > len(OST_files_list):
                self.OST_errors += 'Cannot merge files. The number of subtitle files is greater than the number of OST files.\n'
            elif len(OST_files_list) > len(sub_files_list):
                self.OST_errors += 'Cannot merge files. The number of OST files is greater than the number of subtitle files.\n'

            if self.OST_errors:
                self.OST_results.configure(state='normal')
                self.OST_results.delete('1.0', tk.END)
                self.OST_results.insert('1.0', self.OST_errors)
                self.OST_results.configure(state='disabled')
                self.OST_errors = ''

            else:
                if self.var_overwrite_merged_files.get():
                    batch_merge_subs(self.merge_sub_dir, self.merge_OST_dir, self.merge_sub_dir)
                else:
                    batch_merge_subs(self.merge_sub_dir, self.merge_OST_dir, self.save_merge_OST_dir)
            

            



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
            if not self.OST_audit_files:
                self.OST_errors += 'Cannot generate OST files. Please provide one OST .docx file.'
            if not self.OST_gen_save_dir:
                self.OST_errors += 'Cannot generate OST files. Please provide a directory for the generated OST files.'
            
            if self.OST_errors:
                self.OST_results.configure(state='normal')
                self.OST_results.delete('1.0', tk.END)
                self.OST_results.insert('1.0', self.OST_errors)
                self.OST_results.configure(state='disabled')
                self.OST_errors = ''

            else:
                if self.var_single_audit_file.get():
                    OST_audit_files_list = self.OST_audit_files.split('\n')
                    for file_name in OST_audit_files_list:
                        get_OSTs_single(file_name, self.OST_gen_save_dir)
                else:
                    OST_audit_files_list = self.OST_audit_files.split('\n')
                    get_OSTs(OST_audit_files_list, self.OST_gen_save_dir)
                    
                    
        def browse_QC_sub_dir():
            browsed_dir = filedialog.askdirectory()
            if browsed_dir:
                self.QC_sub_dir = browsed_dir
                self.files_entry.configure(state='normal')
                self.files_entry.delete('0', tk.END)
                self.files_entry.insert('1', browsed_dir)
                self.files_entry.configure(state='disabled')


                
        def browse_QC_video_dir():
            browsed_dir = filedialog.askdirectory()
            if browsed_dir:
                self.QC_video_dir = browsed_dir
                self.videos_entry.configure(state='normal')
                self.videos_entry.delete('0', tk.END)
                self.videos_entry.insert('1', browsed_dir)
                self.videos_entry.configure(state='disabled')

        def browse_SC_dir():
            browsed_dir = filedialog.askdirectory()
            if browsed_dir:
                self.QC_SC_dir = browsed_dir
                self.sc_entry.configure(state='normal')
                self.sc_entry.delete('0', tk.END)
                self.sc_entry.insert('1', browsed_dir)
                self.sc_entry.configure(state='disabled')

        def browse_report_save():
            self.report_name = filedialog.asksaveasfilename(
                defaultextension='.txt',
                filetypes=(('Text File', '*.txt'),)
            )

            if self.report_name:
                self.save_report_entry.configure(state='normal')
                self.save_report_entry.delete('0', tk.END)
                self.save_report_entry.insert('1', self.report_name)
                self.save_report_entry.configure(state='disabled')
            
        def run_QC():
            # self.QC_results
            if not self.QC_sub_dir:
                self.QC_errors += 'Cannot run Quality Check. Please provide a directory for the subtitle files.\n'
            if not self.QC_video_dir and self.shot_changes_var.get():
                self.QC_warnings += 'Could not check timing to shot chnages. Please provide a directory for the videos.\n'
            if not self.QC_SC_dir and self.shot_changes_var.get():
                self.QC_warnings += 'Could not check timing to shot changes. Please provide the directory for .scenechanges files.\n'
            if self.save_report_var.get() and not self.report_name:
                self.QC_errors += 'Cannot run Quality Check. Please specify a name and location for the report.'
            
            
            if self.QC_errors:
                self.QC_results.configure(state='normal')
                self.QC_results.delete('1.0', tk.END)
                self.QC_results.insert('1.0', self.QC_errors)
                self.QC_results.configure(state='disabled')
                self.QC_errors = ''
                self.QC_warnings = ''
                return

            else:
                if self.QC_warnings:
                    self.QC_results.configure(state='normal')
                    self.QC_results.delete('1.0', tk.END)
                    self.QC_results.insert('1.0', self.QC_warnings)
                    self.QC_results.configure(state='disabled')
                    self.QC_errors = ''
                    self.QC_warnings = ''

                # print(self.shot_changes_var.get())
                # print(type(self.shot_changes_var.get()))
                # print('\n')
                # print(self.CPS_var.get())
                # print(type(self.CPS_var.get()))
                # print('\n')
                # print(self.CPS_spaces_var.get())
                # print(type(self.CPS_spaces_var.get()))
                # print('\n')
                # print(self.max_lines_var.get())
                # print(type(self.max_lines_var.get()))
                # print('\n')
                # print(self.min_duration_var.get())
                # print(type(self.min_duration_var.get()))
                # print('\n')
                # print(self.max_duration_var.get())
                # print(type(self.max_duration_var.get()))
                # print('\n')
                # print(self.ellipses_var.get())
                # print(type(self.ellipses_var.get()))
                # print('\n')
                # print(self.gaps_var.get())
                # print(type(self.gaps_var.get()))
                # print('\n')
                # print(self.shot_changes_var.get())
                # print(type(self.shot_changes_var.get()))
                # print('\n')
                
                self.check_TCFOL_var.get()

                report = batch_quality_check(
                    self.QC_sub_dir,
                    self.QC_video_dir,
                    self.QC_SC_dir,
                    shot_changes=self.shot_changes_var.get(),
                    CPS=True,
                    CPS_limit=float(self.CPS_var.get()),
                    CPS_spaces=bool(self.CPS_spaces_var.get()),
                    CPL=True,
                    CPL_limit=int(self.CPL_limit_var.get()),
                    max_lines=int(self.max_lines_var.get()),
                    min_duration=float(self.min_duration_var.get())/1000,
                    max_duration=float(self.max_duration_var.get())/1000,
                    ellipses=bool(self.ellipses_var.get()),
                    gaps=bool(self.gaps_var.get()),
                    glyphs=False,
                    old=False,
                    check_TCFOL=bool(self.check_TCFOL_var.get()),
                    report=bool(self.save_report_var.get()),
                    report_name=self.report_name
                )

                # print(report)
                # print(self.save_report_var.get())

                self.QC_results.configure(state='normal')
                self.QC_results.delete('1.0', tk.END)
                self.QC_results.insert('1.0', '\n'.join(report))
                self.QC_results.configure(state='disabled')




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
        
        self.first = True
        self.active_option = 0


        # || OST widgets

        # Extract OSTs
        self.var_del_OSTs = tk.IntVar()
        self.var_save_OSTs = tk.IntVar()

        self.OST_ext_label = tk.Label(self.canvas, text="Extract OSTs", bg='white', padx=30, font=self.header_1_font)
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
        self.var_overwrite_merged_files = tk.IntVar()

        self.OST_merge_label = tk.Label(self.canvas, text="Merge files and OSTs", bg='white', padx=30, font=self.header_1_font)
        self.lang_dir_label_2 = tk.Label(self.canvas, text='Subtitle file(s) directory:', bg='white', padx=60)
        self.lang_dir_entry_2 = tk.Entry(self.canvas, width=100, borderwidth=2)
        self.lang_dir_browse_2 = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_dir_sub_merge)
        self.OST_dir_label = tk.Label(self.canvas, text='OST directory:', bg='white', padx=60)
        self.OST_dir_entry = tk.Entry(self.canvas, width=100, borderwidth=2)
        self.OST_dir_browse_butt = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_dir_OST_merge)
        self.save_to_label = tk.Label(self.canvas, text='Save merged files to...', bg='white', padx=60)
        self.save_to_entry = tk.Entry(self.canvas, width=100, borderwidth=2)
        self.save_to_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_dir_merge_save)
        self.overwrite_merged_files = tk.Checkbutton(self.canvas, text='Overwrite subtitle files', variable=self.var_overwrite_merged_files, bg='white', command=overwrite_sub_files)
        self.merge_OSTs_button = tk.Button(self.canvas, text='Merge', height=1, width=15, command=merge_OSTs)


        # Generate OSTs

        self.var_single_audit_file = tk.IntVar()

        self.OST_gen_label = tk.Label(self.canvas, text="Generate OSTs", bg='white', padx=30, font=self.header_1_font)
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

        self.QC_label = tk.Label(self.canvas, text='Batch Quality check', bg='white', padx=30, font=self.header_1_font)
        self.files_label = tk.Label(self.canvas, text='Subtitle file(s)', bg='white', padx=60)
        self.files_entry = tk.Entry(self.canvas, width=80, borderwidth=2)
        self.files_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_QC_sub_dir)
        self.videos_label = tk.Label(self.canvas, text='Video(s)', bg='white', padx=60)
        self.videos_entry = tk.Entry(self.canvas, width=80, borderwidth=2)
        self.videos_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_QC_video_dir)
        self.sc_label = tk.Label(self.canvas, text='Scene changes directory', bg='white', padx=60)
        self.sc_entry = tk.Entry(self.canvas, width=80, borderwidth=2)
        self.sc_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_SC_dir)
        self.run_QC_button = tk.Button(self.canvas, text='Run QC', height=1, width=15, command=run_QC)

        # QC settings

        self.settings_label = tk.Label(self.canvas, text='QC settings', bg='white', padx=60, font=self.option_font)
        self.CPS_label = tk.Label(self.canvas, text='Max. CPS', bg='white', padx=90)
        self.CPS_var = tk.StringVar()
        self.CPS_var.set('25.0')
        self.CPS_entry = tk.Spinbox(self.canvas, from_=0.00, to=99.00, format="%.2f", increment=0.1, textvariable=self.CPS_var, width=5, wrap=True)
        self.CPS_spaces_var = tk.IntVar()
        self.CPS_check = tk.Checkbutton(self.canvas, text='Count spaces for CPS', variable=self.CPS_spaces_var, bg='white', padx=120)
        self.CPL_label = tk.Label(self.canvas, text='Max. CPL', bg='white', padx=90)
        self.CPL_limit_var = tk.IntVar()
        self.CPL_limit_var.set('42')
        self.CPL_entry = tk.Spinbox(self.canvas, from_=0, to=100, textvariable=self.CPL_limit_var, width=5, wrap=True)
        self.max_lines_label = tk.Label(self.canvas, text='Max. lines', bg='white', padx=90)
        self.max_lines_var = tk.IntVar()
        self.max_lines_var.set('2')
        self.max_lines_entry = tk.Spinbox(self.canvas, from_=0, to=100, textvariable=self.max_lines_var, width=5, wrap=True)
        self.min_duration_label = tk.Label(self.canvas, text='Min. duration (ms)', bg='white', padx=90)
        self.min_duration_var = tk.IntVar()
        self.min_duration_var.set('833')
        self.min_duration_entry = tk.Spinbox(self.canvas, from_=0, to=100000, textvariable=self.min_duration_var, width=5, wrap=True)
        self.max_duration_label = tk.Label(self.canvas, text='Max. duration (ms)', bg='white', padx=90)
        self.max_duration_var = tk.IntVar()
        self.max_duration_var.set('7000')
        self.max_duration_entry = tk.Spinbox(self.canvas, from_=0, to=100000, textvariable=self.max_duration_var, width=5, wrap=True)
        self.ellipses_var = tk.IntVar()
        self.ellipses_var.set(1)
        self.ellipsis_check = tk.Checkbutton(self.canvas, text='Check ellipses', variable=self.ellipses_var,bg='white')
        self.gaps_var = tk.IntVar()
        self.gaps_var.set(1)
        self.gaps_check = tk.Checkbutton(self.canvas, text='Check gaps', variable=self.gaps_var, bg='white')
        self.shot_changes_var = tk.IntVar()
        self.shot_changes_var.set(1)
        self.shot_changes_check = tk.Checkbutton(self.canvas, text='Check timing to shot changes', variable=self.shot_changes_var, bg='white')
        

        self.check_TCFOL_var = tk.IntVar()
        self.check_TCFOL_var.set(1)
        self.TCFOL_check = tk.Checkbutton(self.canvas, text='Check text can fit in one line', variable=self.check_TCFOL_var, bg='white')

        self.check_OST_var = tk.IntVar()
        self.check_OST_var.set(1)
        self.OST_check = tk.Checkbutton(self.canvas, text='Check OSTs', variable=self.check_OST_var, bg='white')

        self.NF_glyph_list_var = tk.IntVar()
        self.NF_glyph_list_var.set(1)
        self.check_NF_glyph_list = tk.Checkbutton(self.canvas, text='Check Netflix Glyph List', variable=self.NF_glyph_list_var, bg='white')

        self.save_report_var = tk.IntVar()
        # self.save_report_var.set(1)
        self.save_report_check = tk.Checkbutton(self.canvas, text='Save report', variable=self.save_report_var, bg='white')
        self.save_report_entry = tk.Entry(self.canvas, width=60, borderwidth=2)
        self.save_report_browse = tk.Button(self.canvas, text='Browse', height=1, width=15, command=browse_report_save)

        


        self.QC_line_1 = ''
        self.QC_line_2 = ''

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
        
        self.issues_line_1 = ''

        # self.CPS_label = tk.Label()



        # Results

        self.OST_results_label = tk.Label(self.canvas, text='Results', bg='white', padx=30, font=self.results_font)
        self.OST_results = ScrolledText(self.canvas, bg='white', fg='black')

        self.QC_results_label = tk.Label(self.canvas, text='Results', bg='white', padx=30, font=self.results_font)
        self.QC_results = ScrolledText(self.canvas, bg='white', fg='black')

        # self.prefix_results_label = tk.Label(self.canvas, text='Results', bg='white', padx=30, font=self.results_font)
        # self.prefix_results = ScrolledText(self.canvas, bg='white', fg='black')

        self.issues_results_label = tk.Label(self.canvas, text='Results', bg='white', padx=30, font=self.results_font)
        self.issues_results = ScrolledText(self.canvas, bg='white', fg='black')
        # results.grid(column=0, columnspan=3, row=18, pady=25, padx=25, sticky='nsew')
        # results.insert('1.0', 'Test\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\nTest\n')
        # results.configure(state='disabled')

        def option_hover(event):
            event.widget.config(bg='#383838')

        def option_leave(event):
            event.widget.config(bg='#606060')

        def OST_hover(event):
            if self.active_option != 0:
                event.widget.config(bg='#383838')

        def OST_leave(event):
            if self.active_option != 0:
                event.widget.config(bg='#606060')
            else:
                event.widget.config(bg='#4953ab')

        def QC_hover(event):
            if self.active_option != 1:
                event.widget.config(bg='#383838')
        
        def QC_leave(event):
            if self.active_option != 1:
                event.widget.config(bg='#606060')
            else:
                event.widget.config(bg='#4953ab')

        def prefix_hover(event):
            if self.active_option != 2:
                event.widget.config(bg='#383838')

        def prefix_leave(event):
            if self.active_option != 2:
                event.widget.config(bg='#606060')
            else:
                event.widget.config(bg='#4953ab')

        def issues_hover(event):
            if self.active_option != 3:
                event.widget.config(bg='#383838')

        def issues_leave(event):
            if self.active_option != 3:
                event.widget.config(bg='#606060')
            else:
                event.widget.config(bg='#4953ab')


        self.ext_OST_lang_path = ''
        self.ext_OST_save_dir = ''
        self.merge_sub_dir = ''
        self.merge_OST_dir = ''
        self.save_merge_OST_dir = ''
        self.OST_audit_files = ''
        self.OST_gen_save_dir = ''

        self.OST_errors = ''



        self.QC_sub_dir = ''
        self.QC_video_dir = ''
        self.QC_SC_dir = ''
        self.QC_errors = ''
        self.QC_warnings = ''
        self.report_name = ''


        self.tar_files = ''
        self.en_files = ''
        self.save_to = ''
        self.issues_errors = ''
        self.issues_results_text = ''
        
        def populate_OST():

            self.canvas.grid_columnconfigure(2, weight=0)
            self.canvas.grid_columnconfigure(5, weight=0)
            self.canvas.grid_columnconfigure(4, weight=1)
            self.canvas.grid_rowconfigure(10, weight=0)
            self.canvas.grid_rowconfigure(19, weight=0)
            self.canvas.grid_rowconfigure(20, weight=1)

            self.OST_button.config(bg='#4953ab')
            self.del_OSTs.grid(column=3, row=3, sticky='w', padx=(30, 0))
        
        
            self.save_OSTs.grid(column=3, row= 5, sticky='w', padx=(30, 0))
            self.OST_ext_label.grid(column=0, row=1, sticky='w', pady=(15, 0))
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
            self.overwrite_merged_files.grid(column=3, row=8, sticky='w', padx=(30, 0))
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
            self.OST_results.grid(column=0, columnspan=5, row=20, pady=30, padx=25, sticky='nsew')
            self.OST_results.configure(state='disabled')

            self.lang_dir_entry_1.configure(state='disabled')
            self.lang_dir_entry_1.configure(disabledbackground='white')
            self.OST_ext_save_to_entry.configure(disabledbackground='white')
            
            # self.OST_line_1 = self.canvas.create_line(30, 50, 1400, 50, fill='black', width=1)
            # self.OST_line_2 = self.canvas.create_line(30, 230, 1400, 230, fill='black', width=1)
            # self.OST_line_3 = self.canvas.create_line(30, 457, 1400, 457, fill='black', width=1)

            self.OST_line_1 = self.canvas.create_line(self.fixed_w*0.02, 50, self.fixed_w*0.88, 50, fill='black', width=1)
            self.OST_line_2 = self.canvas.create_line(self.fixed_w*0.02, 230, self.fixed_w*0.88, 230, fill='black', width=1)
            self.OST_line_3 = self.canvas.create_line(self.fixed_w*0.02, 457, self.fixed_w*0.88, 457, fill='black', width=1)



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
                self.TCFOL_check.grid_forget()
                self.OST_check.grid_forget()
                self.run_QC_button.grid_forget()
                self.check_NF_glyph_list.grid_forget()
                self.save_report_check.grid_forget()
                self.save_report_entry.grid_forget()
                self.save_report_browse.grid_forget()

                self.canvas.delete(self.QC_line_1)
                self.canvas.delete(self.QC_line_2)

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

                self.canvas.delete(self.issues_line_1)






                # event.widget.config(bg='#383838')
                event.widget.config(bg='#4953ab')
                self.QC_button.config(bg='#606060')
                # self.prefix_button.config(bg='#606060')
                self.issues_button.config(bg='#606060')

                populate_OST()

                # self.canvas.grid_columnconfigure(2, weight=0)
                # self.canvas.grid_columnconfigure(5, weight=0)
                # self.canvas.grid_columnconfigure(4, weight=1)
                # self.canvas.grid_rowconfigure(10, weight=0)
                # self.canvas.grid_rowconfigure(17, weight=0)
                # self.canvas.grid_rowconfigure(20, weight=1)

                # self.del_OSTs.grid(column=3, row=3, sticky='w', padx=(30, 0))
        
        
                # self.save_OSTs.grid(column=3, row= 5, sticky='w', padx=(30, 0))
                # self.OST_ext_label.grid(column=0, row=1, sticky='w', pady=(15, 0))
                # self.lang_dir_label_1.grid(column=0, row=2, sticky='w', pady=(15, 0))
                # self.lang_dir_entry_1.grid(column=0, columnspan=2, row=3, sticky='w', padx=(60, 0))
                # self.lang_dir_browse_1.grid(column=2, row=3, padx=45)
                # self.OST_ext_save_to_label.grid(column=0, row=4, sticky='w')
                # self.OST_ext_save_to_entry.grid(column=0, columnspan=2, row=5, sticky='w', padx=(60, 0))
                # self.OST_ext_save_to_entry.configure(state='disabled')
                # self.OST_ext_save_browse_butt.grid(column=2, row=5, padx=45)
                # self.extract_OSTs_button.grid(column=4, row=5, padx=30, sticky='s')


                # self.OST_merge_label.grid(column=0, row=6, sticky='w', pady=(40, 0))
                # self.lang_dir_label_2.grid(column=0, row=7, sticky='w', pady=(15, 0))
                # self.lang_dir_entry_2.grid(column=0, columnspan=2, row=8, sticky='w', padx=(60, 0))
                # self.lang_dir_entry_2.configure(state='disabled', disabledbackground='white')
                # self.lang_dir_browse_2.grid(column=2, row=8, padx=45)
                # self.OST_dir_label.grid(column=0, row=9, sticky='w')
                # self.OST_dir_entry.grid(column=0, columnspan=2, row=10, sticky='w', padx=(60, 0))
                # self.OST_dir_entry.configure(state='disabled', disabledbackground='white')
                # self.OST_dir_browse_butt.grid(column=2, row=10, padx=45)
                # self.save_to_label.grid(column=0, row=11, sticky='w')
                # self.save_to_entry.grid(column=0, columnspan=2, row=12, sticky='w', padx=(60, 0))
                # self.save_to_entry.configure(state='disabled', disabledbackground='white')
                # self.save_to_browse.grid(column=2, row=12, padx=45)
                # self.overwrite_merged_files.grid(column=3, row=8, sticky='w', padx=(30, 0))
                # self.merge_OSTs_button.grid(column=4, row=12, padx=30, sticky='s')


                # self.OST_gen_label.grid(column=0, row=13, sticky='w', pady=(40, 0))
                # self.OST_audit_label.grid(column=0, row=14, sticky='w', pady=(15, 0))
                # self.OST_audit_entry.grid(column=0, columnspan=2, row=15, sticky='w', padx=(60, 0))
                # self.OST_audit_entry.configure(state='disabled')
                # self.browse_audit_button.grid(column=2, row=15, padx=45, sticky='s')
                # self.OST_gen_save_to_label.grid(column=0, row=16, sticky='w')
                # self.OST_gen_save_to_entry.grid(column=0, columnspan=2, row=17, sticky='w', padx=(60, 0))
                # self.OST_gen_save_to_entry.configure(state='disabled', disabledbackground='white')
                # self.OST_gen_save_browse_butt.grid(column=2, row=17, padx=45)
                # self.OST_gen_button.grid(column=4, row=17, padx=30, sticky='s')
                # self.single_audit_file.grid(column=3, row=15, sticky='w', padx=(30, 0))

                # self.OST_results_label.grid(column=0, row=19, sticky='w', pady=(30, 0))
                # self.OST_results.grid(column=0, columnspan=5, row=20, pady=30, padx=25, sticky='nsew')
                # self.OST_results.configure(state='disabled')

                # self.ext_OST_lang_path = ''
                # self.ext_OST_save_dir = ''
                # self.merge_sub_dir = ''
                # self.merge_OST_dir = ''
                # self.save_merge_OST_dir = ''
                # self.OST_audit_files = ''
                # self.OST_gen_save_dir = ''

                # self.OST_errors = ''

                # self.lang_dir_entry_1.configure(state='disabled')
                # self.lang_dir_entry_1.configure(disabledbackground='white')
                # self.OST_ext_save_to_entry.configure(disabledbackground='white')
                
                # self.OST_line_1 = self.canvas.create_line(30, 50, 1400, 50, fill='black', width=1)
                # self.OST_line_2 = self.canvas.create_line(30, 230, 1400, 230, fill='black', width=1)
                # self.OST_line_3 = self.canvas.create_line(30, 457, 1400, 457, fill='black', width=1)


        def QC_click(event):
            if self.active_option != 1:
                self.active_option = 1

                event.widget.config(bg='#4953ab')
                self.OST_button.config(bg='#606060')
                # self.prefix_button.config(bg='#606060')
                self.issues_button.config(bg='#606060')
                self.canvas.grid_columnconfigure(4, weight=0)
                self.canvas.grid_columnconfigure(4, weight=1)
                self.canvas.grid_columnconfigure(3, weight=0)
                self.canvas.grid_rowconfigure(10, weight=0)
                self.canvas.grid_rowconfigure(20, weight=0)
                self.canvas.grid_rowconfigure(19, weight=1)

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
                self.overwrite_merged_files.grid_forget()

                self.canvas.delete(self.OST_line_1)
                # self.canvas.delete(self.OST_line_1_1)
                self.canvas.delete(self.OST_line_2)
                # self.canvas.delete(self.OST_line_2_2)
                self.canvas.delete(self.OST_line_3)
                # self.canvas.delete(self.OST_line_3_3)


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
                self.canvas.delete(self.issues_line_1)


                self.QC_label.grid(column=0, row=1, sticky='w', pady=(15, 0))
                self.files_label.grid(column=0, row=2, sticky='w', pady=(25, 0))
                self.files_entry.grid(column=0, columnspan=2, row=3, sticky='w', padx=60)
                self.files_browse.grid(column=2, row=3)
                self.videos_label.grid(column=0, row=4, sticky='w')
                self.videos_entry.grid(column=0, columnspan=2, row=5, sticky='w', padx=60)
                self.videos_browse.grid(column=2, row=5)
                self.sc_label.grid(column=0, row=6, sticky='w')
                self.sc_entry.grid(column=0, columnspan=2, row=7, sticky='w', padx=60)
                self.sc_browse.grid(column=2, row=7)
                
                self.settings_label.grid(column=0, row=8, sticky='w', pady=(25, 0))
                self.CPS_label.grid(column=0, row=9, sticky='w', pady=(25, 0))
                self.CPS_entry.grid(column=1, row=9, sticky='w', pady=(25, 0))
                self.CPS_check.grid(column=0, row=10, sticky='w')
                self.CPL_label.grid(column=0, row=11, sticky='w')
                self.CPL_entry.grid(column=1, row=11, sticky='w')
                self.max_lines_label.grid(column=0, row=12, sticky='w')
                self.max_lines_entry.grid(column=1, row=12, sticky='w')
                self.min_duration_label.grid(column=0, row=13, sticky='w')
                self.min_duration_entry.grid(column=1, row=13, sticky='w')
                self.max_duration_label.grid(column=0, row=14, sticky='w')
                self.max_duration_entry.grid(column=1, row=14, sticky='w')
                self.ellipsis_check.grid(column=2, row=9, sticky='w', pady=(25, 0))
                self.gaps_check.grid(column=2, row=10, sticky='w')
                self.shot_changes_check.grid(column=2, row=11, sticky='w')
                self.TCFOL_check.grid(column=2, row=12, sticky='w')
                self.OST_check.grid(column=2, row=13, sticky='w')

                self.check_NF_glyph_list.grid(column=2, row=14, sticky='w')
                self.save_report_check.grid(column=3, row=9, sticky='w', padx=(45, 0), pady=(25, 0))
                self.save_report_entry.grid(column=3, row=10, sticky='w', padx=(45, 0))
                self.save_report_browse.grid(column=4, row=10, sticky='w', padx=(25, 0))


                self.run_QC_button.grid(column=4, row=15)

                self.QC_results_label.grid(column=0, row=18, sticky='w', pady=(45, 0))
                self.QC_results.grid(column=0, columnspan=6, row=19, pady=25, padx=25, sticky='nsew')
                self.QC_results.configure(state='disabled')

                # self.QC_line_1 = self.canvas.create_line(30, 50, 1400, 50, fill='black', width=1)
                # self.QC_line_2 = self.canvas.create_line(60, 265, 1400, 265, fill='black', width=1)

                self.QC_line_1 = self.canvas.create_line(self.fixed_w*0.02, 50, self.fixed_w*0.88, 50, fill='black', width=1)
                self.QC_line_2 = self.canvas.create_line(self.fixed_w*0.04, 265, self.fixed_w*0.88, 265, fill='black', width=1)


                # self.QC_rect_1 = round_rectangle(30, 60, 1400, 225, outline='black', fill='white')
                # self.QC_rect_1 = round_rectangle(65, 270, 1400, 475, outline='black', fill='white')

        def prefix_click(event):

            if self.active_option != 2:
                self.active_option = 2

                event.widget.config(bg='#4953ab')
                self.QC_button.config(bg='#606060')
                self.OST_button.config(bg='#606060')
                self.issues_button.config(bg='#606060')

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

                event.widget.config(bg='#4953ab')
                self.QC_button.config(bg='#606060')
                self.OST_button.config(bg='#606060')
                # self.prefix_button.config(bg='#606060')
                self.canvas.grid_columnconfigure(2, weight=0)
                self.canvas.grid_columnconfigure(3, weight=1)
                self.canvas.grid_columnconfigure(4, weight=0)
                self.canvas.grid_rowconfigure(19, weight=0)
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
                self.overwrite_merged_files.grid_forget()

                self.canvas.delete(self.OST_line_1)
                # self.canvas.delete(self.OST_line_1_1)
                self.canvas.delete(self.OST_line_2)
                # self.canvas.delete(self.OST_line_2_2)
                self.canvas.delete(self.OST_line_3)
                # self.canvas.delete(self.OST_line_3_3)

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
                self.TCFOL_check.grid_forget()
                self.OST_check.grid_forget()
                self.run_QC_button.grid_forget()
                self.check_NF_glyph_list.grid_forget()
                self.save_report_check.grid_forget()
                self.save_report_entry.grid_forget()
                self.save_report_browse.grid_forget()

                self.canvas.delete(self.QC_line_1)
                self.canvas.delete(self.QC_line_2)

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

                # self.issues_line_1 = self.canvas.create_line(30, 50, 1400, 50, fill='black', width=1)
                self.issues_line_1 = self.canvas.create_line(self.fixed_w*0.02, 50, self.fixed_w*0.88, 50, fill='black', width=1)
                



        self.OST_button.grid(column=0, row=0, rowspan=2, sticky='we')
        self.OST_button.bind('<Motion>', OST_hover)
        self.OST_button.bind('<Leave>', OST_leave)
        self.OST_button.bind('<Button-1>', OST_click)

        self.QC_button.grid(column=0, row=2, rowspan=2, sticky='we')
        self.QC_button.bind('<Motion>', QC_hover)
        self.QC_button.bind('<Leave>', QC_leave)
        self.QC_button.bind('<Button-1>', QC_click)

        # self.prefix_button.grid(column=0, row=4, rowspan=2, sticky='we')
        # self.prefix_button.bind('<Motion>', prefix_hover)
        # self.prefix_button.bind('<Leave>', prefix_leave)
        # self.prefix_button.bind('<Button-1>', prefix_click)

        self.issues_button.grid(column=0, row=4, rowspan=2, sticky='we')
        self.issues_button.bind('<Motion>', issues_hover)
        self.issues_button.bind('<Leave>', issues_leave)
        self.issues_button.bind('<Button-1>', issues_click)

        populate_OST()


    def run(self):
        self.root.mainloop()



App().run()