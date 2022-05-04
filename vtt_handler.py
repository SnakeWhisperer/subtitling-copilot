
import re
import os
import xlsxwriter

import srt_handler

from decoders import decode_VTT, parse_VTT
from reader import read_text_file
from classes import Timecode
from exceptions import FormatError
from encoders import encode_VTT
from srt_handler import renumber


def save_VTT_subs(file_name, contents):

    VTT_lines = encode_VTT(contents)

    with open(file_name, 'w', encoding='utf-8-sig') as new_file:
        for line in VTT_lines:
            new_file.write(line)

    return


def merge_subs(file_name_one, file_name_two, save_dir):
    # ONLY FOR FILES AND OSTS

    vtt_one = parse_VTT(file_name_one)['cues']
    vtt_two = parse_VTT(file_name_two)['cues']

    resulting_vtt = vtt_one + vtt_two

    sort_VTT(resulting_vtt)

    save_file_name = file_name_one.split('/')[-1]
    save_file_name = save_dir + '/' + save_file_name
    VTT_cont = {'stylesheets': [], 'regions': {}, 'cues': resulting_vtt}

    save_VTT_subs(save_file_name, VTT_cont)



def batch_merge_subs(file_dir_one, file_dir_two, save_dir):
    # ONLY FOR FILES AND OSTS
    original_dir = os.getcwd()
    
    os.chdir(file_dir_one)
    file_list_one = os.listdir()
    sub_list_one = []

    os.chdir(file_dir_two)
    file_list_two = os.listdir()
    sub_list_two = []

    os.chdir(original_dir)

    for item in file_list_one:
        name, ext = os.path.splitext(item)
        if ext == '.vtt':
            sub_list_one.append(item)
        print(item)

    for item in file_list_two:
        name, ext = os.path.splitext(item)
        if ext == '.vtt':
            sub_list_two.append(item)
        print(item)

    for i, file_name in enumerate(sub_list_one):
        full_file_one = file_dir_one + '/' + sub_list_one[i]
        full_file_two = file_dir_two + '/' + sub_list_two[i]
        merge_subs(full_file_one, full_file_two, save_dir)
    



def sort_VTT(file_name):
    
    if type(file_name) == str:
        name, ext = os.path.splitext(file_name)
        if ext == '.vtt':
            vtt_subs = parse_VTT(file_name)['cues']

    elif type(file_name) == list:
        vtt_subs = file_name

    # Insertion Sort
    # NOTE: Check this and make sure you understand it
    #       and that it's the most efficient algorithm.
    for step in range(1, len(vtt_subs)):
        key = vtt_subs[step]
        j = step - 1

        while (j >= 0
               and key.start_time.total_seconds
                   < vtt_subs[j].start_time.total_seconds):
            
            vtt_subs[j+1] = vtt_subs[j]
            j = j - 1

        vtt_subs[j + 1] = key


    