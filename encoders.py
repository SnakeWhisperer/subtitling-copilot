import re
import html


def encode_VTT(contents):

    VTT_lines = []
    VTT_lines.append('WEBVTT')

    subtitles = contents['cues']
    regions = contents['regions']

    if regions:
        for key in regions.keys():
            VTT_lines.append('\n\n' + regions[key].__str__())

    for subtitle in subtitles:
        VTT_lines.append('\n\n' + subtitle.__str__())

    return VTT_lines


def encode_SRT(subtitles):

    srt_lines = []
    first = True

    i = 0
    
    while i < len(subtitles) - 1:
        srt_lines.append(subtitles[i].__str__() + '\n\n')
        i += 1

    srt_lines.append(subtitles[i].__str__())

    # for subtitle in subtitles:
    #     if first:
    #         srt_lines.append(subtitle.__str__())
    #         first = False
        
    #     else:
    #         srt_lines.append('\n\n' + subtitle.__str__())

    return srt_lines