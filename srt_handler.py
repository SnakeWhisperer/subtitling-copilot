import re
import html

from encoders import encode_SRT


def save_SRT_subs(file_name, subtitles):

    srt_lines = encode_SRT(subtitles)

    with open(file_name, 'w', encoding='utf-8-sig') as new_file:
        for line in srt_lines:
            new_file.write(line)

    return


def renumber(subtitles):

    counter = 1

    for subtitle in subtitles:
        subtitle.number = counter
        counter += 1

    return