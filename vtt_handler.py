
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


def merge_subs(file_name_one, file_name_two):

    vtt_one = parse_VTT(file_name_one)['cues']
    vtt_two = parse_VTT(file_name_two)['cues']

    resulting_vtt = vtt_one + vtt_two


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


    