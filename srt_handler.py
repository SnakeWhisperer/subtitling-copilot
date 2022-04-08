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


def convert_to_JSON(subtitles):
    """_summary_

    Parameters
    ----------
    subtitles : _type_
        _description_
    """

    out_string = '[\n'

    for i, sub in enumerate(subtitles):
        current_json = sub.to_JSON().split('\n')
        for j, line in enumerate(current_json):
            if j == len(current_json) - 1 and i < len(subtitles) - 1:
                final_comma = ','
            else:
                final_comma = ''
            out_string += f'\t{line}{final_comma}\n'

    out_string += ']'

    return out_string