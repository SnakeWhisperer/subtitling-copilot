import re, os, xlsxwriter, srt_handler, openpyxl, copy, docx

from decoders import decode_VTT, parse_VTT, VTT_text_parser
from reader import read_text_file
from classes import Timecode, WebVTT
from exceptions import FormatError
from encoders import encode_VTT
from srt_handler import renumber
from vtt_handler import save_VTT_subs


def get_fast_texts(en_file_name='', tar_file_name='', class_path='',
                   span_start='', span_end='', OST=False, seg=False,
                   CPS_limit=25, old=True):
    """Print texts from the two files passed in the time span provided
    with 'span_start' and 'span_end'.

    Currently working only with VTTs and originally written to get
    the text for subtitles with reading speed issues, in English
    and the target language, to paste for LL reduction (MasterClass).

    Parameters
    ----------
    en_file_name : str, optional
        Path to the English file.
        Optional because this function was thought to be called
        by a batch function, by default ''
    tar_file_name : str, optional
        Path to the target language file.
        Optional because this function was thought to be called
        by a batch function, by default ''
    class_path : str, optional
        Path to the whole class containing all subfolders.
        Not really used apparently. Maybe delete later, by default ''
    span_start : str, optional
        Has the format MM:SS, by default ''
    span_end : str, optional
        Has the format MM:SS, by default ''
    OST : bool, optional
        True to include OSTs. False to exclude them, by default False
    seg : bool, optional
        True to use the subtitle segmentation
        in the offending subtitles. False to not include linebreaks,
        by default False
    CPS_limit : int, optional
        Used when 'seg' is True to detect the offending subtitles,
        by default 25
    """
    

    # Decode both the target language file and the source file.
    if old:
        en_subs = decode_VTT(read_text_file(en_file_name))['subtitles']
        tar_subs = decode_VTT(read_text_file(tar_file_name))['subtitles']
    else:
        en_subs = parse_VTT(en_file_name)['cues']
        tar_subs = parse_VTT(tar_file_name)['cues']

    # Dissect the span_start and span_end to get the minutes
    # and seconds values.
    start_mins, start_secs = [int(x.group())
        for x in re.finditer('\d+', span_start)]
    end_mins, end_secs = [int(x.group())
        for x in re.finditer('\d+', span_end)]

    # Get the start and end of the span in seconds.
    span_start_secs = start_mins * 60 + start_secs
    span_end_secs = end_mins * 60 + end_secs

    # Get the length of the longest file to use in the iterations.
    longest_file = max(len(en_subs), len(tar_subs))

    # Flags to indicate the loop if the function
    # should collect the corresponding texts.
    # NOTE: This—and the code that uses it in the loop—might not be
    #       very efficient. Maybe just collect the text
    #       if the subtitle display time falls in the time span.
    collect_en = False
    collect_tar = False

    # Preallocate the output text strings.
    en_text = ''
    tar_text = ''

    # Flag to indicate that the previous subtitle in the loop
    # exceeds the reading speed limit.
    offending = False

    # Store the lineabreaks to use in f-strings.
    # NOTE: For some reason, f-strings don't really work
    #       with backslashes.
    nl = '\n'

    for i in range(longest_file):
        # Means that the current source subtitle
        # falls into the time span.
        # Checks if the loop is still in the range of the length
        # and that collect_en has not been set to avoid
        # setting over and over.
        # NOTE: Doesn't seem very efficient.  See note above.
        if (i < len(en_subs) and not collect_en
            and en_subs[i].start_time.total_seconds >= span_start_secs
            and en_subs[i].end_time.total_seconds <= span_end_secs):
            # Flag to collect the english text
            collect_en = True

        # Means that the loop exceeded the length
        # of the source subtitles or that the current subtitle
        # is beyond the time span.
        elif (i >= len(en_subs)
              or en_subs[i].end_time.total_seconds > span_end_secs):
            collect_en = False

        # Means that the current target subtitle
        # falls into the time span.
        # Checks if the loop is still in the range of the length
        # and that collect_tar has not been set to avoid
        # setting over and over.
        # NOTE: Doesn't seem very efficient.  See note above.
        if (i < len(tar_subs) and not collect_tar
            and tar_subs[i].start_time.total_seconds >= span_start_secs
            and tar_subs[i].end_time.total_seconds <= span_end_secs):
            # Flag to collect target text
            collect_tar = True

        # Means that the loop has exceeded the length
        # of the target subtitles or that the current subtitle
        # is beyond the time span.
        elif (i >= len(tar_subs)
              or tar_subs[i].end_time.total_seconds > span_end_secs):
            collect_tar = False

        # Collect the source text according to the flag
        # that was set above, and if the subtitle is not an OST,
        # depending on the OST argument.
        if collect_en:
            if (not OST and en_subs[i].line == 'auto') or OST:
                    en_text += ' '.join(en_subs[i].untagged_text) + ' '

        # Collect the target text according to the flag
        # that was set above, and if the subtitle is not an OST,
        # depending on the OST argument.      
        if collect_tar:
            if (not OST and tar_subs[i].line == 'auto') or OST:

                # If the function is supposed to segment
                # offending subtitles ('seg' argument),
                # see if the subtitle exceeds the reading speed limit.
                if seg and tar_subs[i].CPS_ns > CPS_limit:
                    
                    # If the previous subtitle exceeds
                    # the reading speed limit, start
                    # with an empty string.  This is because
                    # the linebreaks after the segmented text
                    # are always appended, so there is no need
                    # to append them at the beginning of the next one,
                    # whether it is offending or not.
                    if offending:
                        off_text = ''

                    # Start with two linebreaks otherwise.
                    # Also set the offending flag to use it
                    # in the next iteration.
                    else:
                        off_text = nl*2
                        offending = True
                    
                    # Get the offending text segmented.
                    # Note the two linebreaks at the end.
                    off_text = (
                        f"{off_text}{nl.join(tar_subs[i].untagged_text)}"
                        f"{nl*2}")

                    # Append the offending text to the whole text
                    # of the target file.
                    tar_text += off_text

                # If the function is not supposed to segment
                # offending subtitles ('seg' argument),
                # there is no actual need to see if the subtitle exceeds
                # the reading speed limit.
                # Just get the text from the target file as long
                # as it is in the time span.
                # NOTE: Maybe convert tar_text to a list to avoid
                #       having that trailing space automatically.
                else:                    
                    tar_text += ' '.join(tar_subs[i].untagged_text) + ' '
                    offending = False

    print(f'{"-"*20}\nen:\n\n{en_text}\n\n\n\ntarget:\n\n{tar_text}\n{"-"*20}')

    return


def batch_gen_CPS_sheet(en_path, tar_path, out_name, OST=False, seg=False,
                        CPS=True, CPS_limit=25, CPL=True, CPL_limit=42,
                        lines=True, max_lines=2, old=True, GUI=True):
    """Generates a .xlsx spreadsheet with the text corresponding
    to reading speed issues and some context,
    in the target language and in the source language.
    In this case, it is a spreadsheet for all the reading speed issues
    in a class, not in a single video/file.

    Parameters
    ----------
    en_path : str
        The path to the directory where all the source language files
        are located.
    tar_path : str
        The path to the directory where all the target language files
        are located.
    out_name : str
        The name or path of the .xlsx file to be created.
    CPS_limit : int, optional
        The reading speed limit, by default 25
    """

    
    # It's necessary to store the original directory
    # so that the function can go back to it before returning.
    original_dir = os.getcwd()

    # NOTE: See how you can improve this.
    workbook = xlsxwriter.Workbook(out_name)
    worksheet = workbook.add_worksheet()
    worksheet.set_column(2, 2, 18)
    worksheet.set_column(3, 5, 50)
    worksheet.set_column(6, 6, 35)
    header_format = workbook.add_format({'border': 2})
    header_format.set_bg_color('#DEE6EF')
    header_format.set_align('center')
    header_format.set_bold()
    header_format.set_font_size(13)
    worksheet.write(1, 1, 'File', header_format)
    worksheet.write(1, 2, 'Time span', header_format)
    worksheet.write(1, 3, 'Source', header_format)
    worksheet.write(1, 4, 'Target', header_format)
    worksheet.write(1, 5, 'Fix', header_format)
    worksheet.write(1, 6, 'Notes', header_format)


    if not GUI:
        os.chdir(tar_path)
        
        # All files including everything that's not a subtitle file.
        all_tar_files = os.listdir()
        tar_sub_files = []

        os.chdir(en_path)
        # All files including everything that's not a subtitle file.
        all_en_files = os.listdir()
        en_sub_files = []

        os.chdir(original_dir)
    
    else:
        all_tar_files = tar_path
        tar_sub_files = []
        all_en_files = en_path
        en_sub_files = []


    row_count = 2

    num_files = max(len(all_tar_files), len(all_en_files))

    # Get all the .vtt files in the passed directories.
    # This is to ensure no mismatch arises when going
    # from target langauge file to source language file.
    for i in range(num_files):
        
        if i < len(all_tar_files):
            tar_ext = os.path.splitext(all_tar_files[i])[-1]

            if tar_ext == '.vtt':
                tar_sub_files.append(all_tar_files[i])
        
        if i < len(all_en_files):
            en_ext = os.path.splitext(all_en_files[i])[-1]

            if en_ext == '.vtt':
                en_sub_files.append(all_en_files[i])

    if GUI:
        if len(tar_sub_files) > len(en_sub_files):
            return 'Cannot generate issue spreadsheet. Received more target VTT files than source VTT files.'
        elif len(en_sub_files) > len(tar_sub_files):
            return 'Cannot generate issue spreadsheet. Received more source VTT files than target VTT files.'
    
    # NOTE: This loop assumes a complete and absolute match
    #       between all the files in the source language list
    #       and the target language list.
    for j in range(len(tar_sub_files)):
        # name_short = re.search('[^_]+_[^_]+', tar_sub_files[i])

        if not GUI:
            en_file_name = en_path + r'\\' + en_sub_files[j]
            tar_file_name = tar_path + r'\\' + tar_sub_files[j]
        else:
            en_file_name = en_sub_files[j]
            tar_file_name = tar_sub_files[j]
            # print('The files')
            # print(en_file_name)
            # print(tar_file_name)

        # Add any reading speed issue to the generated sheet.
        row_count = gen_CPS_sheet(
            en_file_name,
            tar_file_name,
            workbook=workbook,
            worksheet=worksheet,
            OST=OST,
            seg=seg,
            CPS=CPS,
            CPS_limit=CPS_limit,
            CPL=CPL,
            CPL_limit=CPL_limit,
            lines=lines,
            max_lines=max_lines,
            row_count=row_count,
            batch=True,
            old=old,
            GUI=GUI
        )

    workbook.close()

    return
        

def gen_CPS_sheet(en_file_name, tar_file_name, workbook=None, worksheet=None,
                  OST=False, seg=False, CPS=True, CPS_limit=25, CPL=True,
                  CPL_limit=42, lines=True, max_lines=2,
                  batch=False, row_count=2, old=True, GUI=True):
    """Generates or writes to a .xlsx file with the text
    with reading speed issues and previous and subsequent segments
    for context.

    Parameters
    ----------
    en_file_name : str
        Path or name of the source file.
    tar_file_name : str
        Path or name of the target file.
    workbook : Workbook or NoneType, optional
        A Workbook from the xlsxwriter module if this function is called
        by the batch_gen_CPS_sheet() function.  Or None if it is called
        directly by the user, by default None
    worksheet : Worksheet or NoneType, optional
        A Worksheet from the xlsxwriter module if this function
        is called by the batch_gen_CPS_sheet() function.
        Or None if it is called directly by the user, by default None
    OST : bool, optional
        True to include OSTs. False to exclude them, by default False
    seg : bool, optional
        True to use the subtitle segmentation
        in the offending subtitles. False to not include linebreaks,
        by default False
    CPS_limit : int, optional
        Used when 'seg' is True to detect the offending subtitles,
        by default 25
    batch : bool, optional
        Indicates the function that it is being called for batch work,
        by default False
    row_count : int, optional
        Keeps the count of the rows in the worksheet.
        Used only for batch work, by default 2

    Returns
    -------
    Nothing or int
        When called for batch work, row_count,
        so that the calling function can keep track of the rows.
    """

    if not GUI:
        # The video name extracted from the absolute path
        # to the English file.
        video_name = en_file_name.split('\\')[-1]
        # Short name with the code for the class and the video number,
        # like JH_102.
        name_short = re.search('[^_]+_[^_]+', video_name).group()
    else:
        video_name = en_file_name.split('/')[-1]
        name_short = re.search('[^_]+_[^_]+', video_name).group()

    print(name_short)
    # Only for debugging purposes
    # if name_short == 'BC_09':
    #     hello = 234

    # If not called for batch work, it means that a Workbook
    # and a Worksheet need to be created.
    # Otherwise the workbook and worksheet will exist already
    # and be received as arguments.
    if not batch:
        workbook = xlsxwriter.Workbook('test_2.xlsx')
        worksheet = workbook.add_worksheet()
        worksheet.set_column(2, 2, 18)
        worksheet.set_column(3, 5, 62)

    # Decode both files.
    if old:
        en_subs = decode_VTT(read_text_file(en_file_name))['subtitles']
        tar_subs = decode_VTT(read_text_file(tar_file_name))['subtitles']
    else:
        en_subs = parse_VTT(en_file_name)['cues']
        tar_subs = parse_VTT(tar_file_name)['cues']

    # The list of subtitle numbers that exceed the reading speed limit.
    # This is used because, when getting the context
    # for an offending subtitle,
    # it's possible to find another offending subtitle in that context.
    # In this case, that subtitle number needs to be appended here
    # so that the next iterations ignore it.
    # NOTE: The need for this might be avoided
    #       if a while loop is used instead.
    offending_list = []
    nl = '\n'
    off_text = ''
    cell_en_text = ''

    # Create and adjust the formats to be used in the worksheet.
    cell_format = workbook.add_format({'text_wrap': True, 'border': 1})
    other_format = workbook.add_format({
        'align': 'center',
        'text_wrap': True,
        'border': 1
    })
    notes_format = workbook.add_format({
        'text_wrap': True,
        'align': 'vcenter',
        'bold': True,
        'border': 1
    })
    other_format.set_align('vcenter')
    cell_format.set_align('vcenter')
    bold = workbook.add_format({'bold': True})
    red = workbook.add_format({'font_color': 'red'})
    red_underlined = workbook.add_format({
        'font_color': 'red', 'underline': True})
    bold_red = workbook.add_format({'bold': True, 'font_color': 'red'})
    bold_red_underlined = workbook.add_format({
        'bold': True,
        'font_color': 'red',
        'underline': True
    })

    code_nums = {
        1: bold,
        2: red,
        3: red_underlined,
        4: bold_red,
        5: bold_red_underlined
    }

    # Since the cases actually arise from the target files,
    # the iterations are done over the subtitles in it.
    for i in range(len(tar_subs)):

        severity_list = []

        # Only for debugging purposes.
        if name_short == 'BI_104' and i == 133:
            print('Here')
            pass

        CPL_offending = False
        CPL_offending_lines = []

        if CPL:
            for m, length in enumerate(tar_subs[i].line_lengths):
                if length > CPL_limit:
                    CPL_offending = True
                    CPL_offending_lines.append(m+1)

        # See if the subtitle is not an OST,
        # depending on the OST argument, and then check if it exceeds
        # the reading speed limit.
        if ((not OST and tar_subs[i].line == 'auto')
            and ((tar_subs[i].CPS_ns > CPS_limit and CPS)
                 or (CPL and CPL_offending))):

            if CPS and (tar_subs[i].CPS_ns > CPS_limit):
                severity_list.append(str(tar_subs[i].CPS_ns) + ' CPS')
            
            # If the current subtitle has not been already registered
            # in a cell with another one, go ahead with the processing.
            if i not in offending_list:
                # Register the current subtitle in the tracking list.
                offending_list.append(i)
                
                # NOTE: Apparently not used anywhere.
                #       Delete if this is the case.
                mid_time = (
                    (tar_subs[i].end_time.total_seconds
                    - tar_subs[i].start_time.total_seconds) / 2
                ) + tar_subs[i].start_time.total_seconds

                # Call the function to get the context
                # for the target file.
                # Store the text before the offending subtitle,
                # the text after the offending subtitle,
                # the start and end of the time span,
                # and the offending list updated.
                (
                    cont_tar_bkw,
                    cont_tar_fwd,
                    span_start,
                    span_end,
                    offending_list,
                    severity_list
                ) = get_CPS_context(
                    i, tar_subs, True, CPS=CPS, CPS_limit=CPS_limit,
                    CPL=CPL, CPL_limit=CPL_limit, lines=lines,
                    max_lines=max_lines, offending_list=offending_list,
                    severity_list=severity_list, OST=OST
                )

                if tar_subs[i].CPS_ns > CPS_limit and not CPL_offending:
                    off_text = [
                        nl*2,
                        1,
                        (nl).join(tar_subs[i].untagged_text)
                    ]

                elif tar_subs[i].CPS_ns <= CPS_limit and CPL_offending:
                    off_text = [nl*2]
                    for n in range(len(tar_subs[i].untagged_text)):
                        if n + 1 in CPL_offending_lines:
                            off_text.extend([
                                2,
                                tar_subs[i].untagged_text[n],
                                4,
                                f'   ({len(tar_subs[i].untagged_text[n])} chars)'
                            ])
                        else:
                            off_text.append(tar_subs[i].untagged_text[n])

                        if n < len(tar_subs[i].untagged_text) - 1:
                            off_text.append(nl)

                elif tar_subs[i].CPS_ns > CPS_limit and CPL_offending:
                    off_text = [nl*2]
                    for o in range(len(tar_subs[i].untagged_text)):
                        if o + 1 in CPL_offending_lines:
                            off_text.extend([
                                4,
                                tar_subs[i].untagged_text[o],
                                4,
                                f'   ({len(tar_subs[i].untagged_text[o])} chars)'
                            ])
                        else:
                            off_text.extend([
                                1,
                                tar_subs[i].untagged_text[o],
                            ])

                        if o < len(tar_subs[i].untagged_text) - 1:
                            off_text.append(nl)

                if cont_tar_bkw:
                    cell_tar_text = [cont_tar_bkw] + off_text + cont_tar_fwd
                else:
                    cell_tar_text = off_text + cont_tar_fwd

                empty = False

                for seg in range(len(cell_tar_text)):
                    if cell_tar_text[seg] is None or cell_tar_text[seg] == 1:
                        cell_tar_text[seg] = bold

                    elif cell_tar_text[seg] == 2:
                        cell_tar_text[seg] = red

                    elif cell_tar_text[seg] == 4:
                        cell_tar_text[seg] = bold_red

                    if cell_tar_text[seg] == '':
                        empty = True


                # if empty:
                #    print('\n\n\n')
                #    print(cell_tar_text)
                #    print('\n\n\n')

                """
                # Join the whole target text that goes
                # into the worksheet cell.
                cell_tar_text = (
                    cont_tar_bkw + nl*2
                    + (nl).join(tar_subs[i].untagged_text) + cont_tar_fwd
                )

                """
                
                # if i == 191:
                #     hello = 2

                cell_en_text = get_en_context(en_subs, span_start, span_end)

                if severity_list:
                    severity_list = (
                        '-'*10 + '\nSeverity:\n\n'
                        + '\n\n'.join(severity_list) + '\n' + '-'*10
                    )
                else:
                    severity_list = ''

                # This is the string that will be printed
                # to the worksheet for tracking purposes.
                time_span = (
                    Timecode(span_start).print_VTT_2()[:5]
                    + ' --> ' + Timecode(span_end).print_VTT_2()[:5]
                )

                # These commented lines were a test to add bold
                # to the offending text.
                
                worksheet.write_rich_string(
                    row_count,
                    4,
                    *cell_tar_text,
                    cell_format
                )

                # worksheet.write(row_count, 4, cell_tar_text, cell_format)
                worksheet.write(row_count, 3, cell_en_text, cell_format)
                worksheet.write(row_count, 2, time_span, other_format)
                worksheet.write(row_count, 1, name_short, other_format)
                worksheet.write(row_count, 5, '', cell_format)
                worksheet.write(row_count, 6, severity_list, notes_format)
                worksheet.set_row(row_count, 250)

                # NOTE: Is there an actual need for this?
                #       Apparently not.
                cell_en_text = ''
                row_count += 1

            else:
                continue 

    # If the function wasn't called for batch work,
    # the workbook needs to be closed here.
    # Return nothing in this case.
    if not batch:
        workbook.close()
        return
    
    # For batch work, the row count needs to be returned,
    # so that the calling function knows where to continue.
    else:
        return row_count


def get_en_context(en_subs, span_start, span_end, OST=False):
    """Basically just gets the joined text from subtitles
    in the specified time span.

    Parameters
    ----------
    en_subs : list
        Contains the subtitle objects.
    span_start : float
        Start time of the span.
    span_end : float
        End time of the span.
    OST : bool, optional
        True to include OSTs. False to exclude them, by default False

    Returns
    -------
    str
        The joined text of the subtitles in the specified time span.
    """

    cell_en_text = ''
    first = True
    first_ind = 1

    for j in range(len(en_subs)):

        # if j == 247:
        #     hello = 23
        
        if (en_subs[j].start_time.total_seconds > span_start
            and en_subs[j].end_time.total_seconds < span_end):
            # Always get the index of the first subtitle in the span.            
            if first:
                first_ind = j
                first = False

            # Get the joined text of the current subtitle
            # depending on the OST argument and whether it is an OST.
            # NOTE: Some other conditionals need to be included here.
            if not OST and en_subs[j].line == 'auto':
                cell_en_text += ' ' + ' '.join(en_subs[j].untagged_text)

        # Break once a subtitle beyond
        # the specified time span is reached.
        # || Commented only temporarily, probably.
        # elif en_subs[j].end_time.total_seconds >= span_end:
        #     break

    # See if the first subtitle in the specified time span
    # starts a sentence.  Done by checking if the previous subtitle
    # ends in a sentence ending.
    first_ind -= 1
    ending = True
    ending_SDH = False
    while first_ind >= 0:
        if en_subs[first_ind].line == 'auto' and en_subs[first_ind].untagged_text:
            ending = re.search(
                '"?[.!?]"?\s*$',
                en_subs[first_ind].untagged_text[-1]
            )

            ending_SDH = re.search(
                '\]\s*$',
                en_subs[first_ind].untagged_text[-1]
            )
            break

        else:
            first_ind -= 1

    # if first_ind > 0:
    #     ending = re.search(
    #         '"?[.!?]"?\s*$',
    #         en_subs[first_ind-1].untagged_text[-1]
    #     )
        
    # else:
    #     ending = True

    # If the first subtitle in the specified time span
    # does not start a sentence, get rid of the substring
    # before the first full sentence in the joined text.
    # print(en_subs[first_ind])
    if not ending and not ending_SDH:
        inner_sent_ending = re.search('"?[.!?]"?\s*', cell_en_text)
        if inner_sent_ending:
            end_ind = re.search('"?[.!?]"?\s*', cell_en_text).end()
            cell_en_text = cell_en_text[end_ind:]

    # Get rid of any leading spaces in the joined text.
    # NOTE: Would strip() work here?
    cell_en_text = re.sub('^\s*', '', cell_en_text)

    return cell_en_text


def get_CPS_context(offending_sub, subs, target, CPS=True, CPS_limit=25,
                    CPL=True, CPL_limit=42, lines=True, max_lines=2,
                    offending_list=[], severity_list=[], OST=False):
    """Gets some text before and after a subtitle
    in the target file language, most of the time whole sentences. 

    Parameters
    ----------
    offending_sub : int
        The zero-based index of the offending subtitle.
    subs : list
        List of the subtitles. Currently only WebVTT.
    target : [type]
        NOTE: Apparently not really used. Don't even remember the type.
    CPS_limit : int or float
        The reading speed limit.
    offending_list : list
        The list of offending subtitles (indices)
        to be updated and returned.
    OST : bool, optional
        True to include OSTs. False to exclude them, by default False

    Returns
    -------
    str
        cont_bkw. Some text before the offending subtitle for context.

    str
        cont_fwd. Some text after the offending subtitle for context.

    float
        span_start.

    float
        span_end

    list
        offending_list. Updated to be used by the calling function.
    """
    # Flags to indicate the code where to look for context.
    forward = False
    backward = False

    # Count the number of sentences took for context.
    sents_fwd = 0
    sents_bkw = 0

    # Preallocate the context variables.
    cont_fwd = []
    cont_bkw = []

    # Only for debugging purposes.
    # if offending_sub == 191:
    #     hello = 234

    nl = '\n'

    # Determine where to look for context.
    if offending_sub == 0:
        # Don't look for context in subtitles before.
        forward = True
        span_start = 0.0
    
    elif offending_sub > 0 and offending_sub < len(subs):
        # Look for context in subtitles before or after.
        forward = True
        backward = True

    else:
        # Don't look for context in subtitles after.
        backward = True
        span_end = subs[offending_sub].end_time.total_seconds + 3

    # Looping variables to look for context.
    i = offending_sub - 1
    j = offending_sub + 1
    chars_bkw = 0

    # Get context from previous subtitles if they exist
    # and if the number of collected sentences is less than 2
    # and if there are subtitles before to get context.
    # NOTE: Update comment
    while backward and i >= 0 and (sents_bkw < 2 or chars_bkw < 130):
        # The text of the current subtitle being processed for context.
        sub_bkw_text = ''
        
        # See if the subtitle is not an OST and collect its text,
        # or if the OST argument has been passed as True.
        if (not OST and subs[i].line == 'auto') or OST:
            sub_bkw_text = ' '.join(subs[i].untagged_text)
            # Collected backwards because the check is made backwards.
            cont_bkw.insert(0, sub_bkw_text)
            # This is the lowest index of a subtitle
            # that was taken for context.
            last_ind_bkw = i
            chars_bkw += len(sub_bkw_text)

        # See if there is a sentence ending in the subtitle whose text
        # was just collected and increment the sentence count.
        if (re.search('[.?!]\W', sub_bkw_text)
            or re.search('[.?!]\s*[»"]*\s*$', sub_bkw_text)):
            # if '.' in sub_bkw_text or '?' in sub_bkw_text or '!' in sub_bkw_text:
            sents_bkw += 1
        
        i -= 1

    if offending_sub == 174:
        hello =23
    if backward:
        span_start = subs[i+1].start_time.total_seconds - 1
        cont_bkw = ' '.join(cont_bkw)

        # See if the last subtitle taken backwards for context starts
        # a sentence at the beginning.
        # If not, get rid of the sentence ending at the beginning.
        # (Clean incomplete sentences at the beginning).
        if i >= 0:
            bkw_end_match = re.search(
                '»*\s*[.?!]\s*[»"]*\s*$',
                ' '.join(subs[i].untagged_text)
            )

            bkw_end_match_2 = re.search('…$', ' '.join(subs[i].untagged_text))

            if not bkw_end_match and not bkw_end_match_2:
                first_sent_ind = re.search(
                    '»*\s*[.?!][\s*»*"*]+\s*',
                    cont_bkw
                ).end()

                cont_bkw = cont_bkw[first_sent_ind:]

        if cont_bkw:
            cont_bkw = cont_bkw[re.search('[^.?!»\s]', cont_bkw).span()[0]:]
        cont_bkw = cont_bkw.strip()

    else:
        cont_bkw = ''

    CPS_offending = False
    CPL_offending = False
    CPL_offending_lines = []
    append_nl = True

    # Get context from subsequent subtitles if they exist,
    # and if the number of collected sentences is less than 2.
    while forward and j < len(subs) and sents_fwd < 2:
        sub_fwd_text = ''
        sub_fwd_text_list = []

        if CPL:
            for m, length in enumerate(subs[j].line_lengths):
                if length > CPL_limit:
                    CPL_offending = True
                    CPL_offending_lines.append(m+1)

        # Check if the subtitle is an OST,
        # and collect as offending text depending on the OST argument
        # and the reading speed.
        if ((not OST and subs[j].line == 'auto')
            and ((CPS and subs[j].CPS_ns > CPS_limit) or CPL_offending)):

            if subs[j].CPS_ns > CPS_limit:
                severity_list.append(str(subs[j].CPS_ns) + ' CPS')

            # Set True to indicate that the next subtitle,
            # if it's not CPS-offending, should have two linebreaks
            # before its text.
            append_nl = True
            offending_list.append(j)

            if CPS and subs[j].CPS_ns > CPS_limit and not CPL_offending:
                CPS_offending = True
                sub_fwd_text += (nl*2) + nl.join(subs[j].untagged_text)
                sub_fwd_text_list = [
                    nl*2,
                    1,
                    (nl).join(subs[j].untagged_text)
                ]

            elif subs[j].CPS_ns <= CPS_limit and CPL_offending:
                sub_fwd_text += (nl*2) + nl.join(subs[j].untagged_text)
                sub_fwd_text_list = [nl*2]
                for n in range(len(subs[j].untagged_text)):
                    if n + 1 in CPL_offending_lines:        
                        sub_fwd_text_list.extend([
                            2,
                            subs[j].untagged_text[n],
                            4,
                            f'   ({len(subs[j].untagged_text[n])} chars)'
                        ])
                    else:
                        sub_fwd_text_list.append(subs[j].untagged_text[n])

                    if n < len(subs[j].untagged_text) - 1:
                        sub_fwd_text_list.append(nl)

            elif subs[j].CPS_ns > CPS_limit and CPL_offending:
                CPS_offending = True
                sub_fwd_text_list = [nl*2]
                for o in range(len(subs[j].untagged_text)):
                    if o + 1 in CPL_offending_lines:
                        sub_fwd_text_list.extend([
                            4,
                            subs[j].untagged_text[o],
                            4,
                            f'    ({len(subs[j].untagged_text[o])} chars)'
                        ])
                    else:
                        sub_fwd_text_list.extend([
                            1,
                            subs[j].untagged_text[o]
                        ])
                    
                    if o < len(subs[j].untagged_text) - 1:
                        sub_fwd_text_list.append(nl)                    

        elif not OST and subs[j].line == 'auto':
            # Use two linebreaks if the text comes
            # from a CPS-offending subtitle.
            if append_nl:
                # sub_fwd_text = nl * 2
                sub_fwd_text = ''
                sub_fwd_text_list = [nl*2]
                append_nl = False
                
            else:
                sub_fwd_text = ' '
            sub_fwd_text += ' '.join(subs[j].untagged_text)
            sub_fwd_text_list.append(sub_fwd_text)

        # if CPS_offending or CPL_offending:
        #     cont_fwd.append(None)
        
        if sub_fwd_text:
            cont_fwd.extend(sub_fwd_text_list)

        # Increment the sentence count if a sentence ending
        # if found in the subtitle that was just collected.
        if ((re.search('[.?!]\W', sub_fwd_text)
             or re.search('[.?!]\s*[»"]*\s*$', sub_fwd_text))
            and not (CPS_offending or CPL_offending)):
            # if (('.' in sub_fwd_text or '?' in sub_fwd_text or '!' in sub_fwd_text)
            # Frobnicate
            sents_fwd += 1

        CPS_offending = False
        CPL_offending = False
        
        j += 1

    # cont_fwd = ' '.join(cont_fwd)

    # Get the span end time to be returned.
    # Get rid of incomplete sentences at the end of the text.
    if forward:
        span_end = subs[j-1].end_time.total_seconds + 1
        """
        fwd_end_match = re.search(
            '["»]*\s*[.?!]\s*[»"]*\s*$',
            cont_fwd
        )

        
        if not fwd_end_match:
            last_sent_ind = re.search(
                # NOTE: See
                # https://stackoverflow.com/questions/33232729/how-to-search-for-the-last-occurrence-of-a-regular-expression-in-a-string-in-pyt?noredirect=1&lq=1
                '(?s:.*)[.?!][\s*»*"*]+\s*',
                cont_fwd
            ).end() - 1

            cont_fwd = cont_fwd[:last_sent_ind]
            # NOTE: This is not being used because it stripped
            #       leading whitespaces too, removing the linebreaks
            #       for the offending text.
            # cont_fwd = cont_fwd.strip()

        """


    return (cont_bkw, cont_fwd, span_start,
            span_end, offending_list, severity_list)


def extract_subs(file_name, span_start, span_end,
                 OST=False, OST_only=False, out_name='', old=True):



    if OST_only:
        OST = True

    in_ext = os.path.splitext(file_name)[-1]

    if in_ext == '.vtt':
        if old:
            in_subs = decode_VTT(read_text_file(file_name))['subtitles']
        else:
            in_subs = parse_VTT(file_name)['cues']
        in_vtt = True
        in_srt = False
    
    elif file_ext == '.srt':
        in_subs = decode_SRT(read_text_file(file_name))
        in_vtt = False
        in_srt = True

    else:
        raise FormatError('Input file extension can only be .vtt or .srt')

    out_subs = []

    out_ext = os.path.splitext(out_name)[-1]

    if out_ext == '.vtt':
        out_vtt = True
        out_srt = False

    elif out_ext == '.srt':
        out_vtt = False
        out_srt = True
    
    elif out_name:
        raise FormatError('Output file extension can only be .vtt or .srt')

    else:
        out_vtt = in_vtt
        out_srt = in_srt


    if type(span_start) == str and type(span_end) == str:
        # Dissect the span_start and span_end to get the minutes
        # and seconds values.
        # NOTE: What if the user inputs '61:00'?
        #       Need to handle that.
        start_mins, start_secs = [int(x.group())
            for x in re.finditer('\d+', span_start)]
        end_mins, end_secs = [int(x.group())
            for x in re.finditer('\d+', span_end)]

        # Get the start and end of the span in seconds.
        span_start_secs = start_mins * 60 + start_secs
        span_end_secs = end_mins * 60 + end_secs

    elif (type(span_start) == int and type(span_end) == int):
        span_start_secs = span_start
        span_end_secs = span_end

    for sub in in_subs:
        if (sub.start_time.total_seconds >= span_start_secs
            and sub.end_time.total_seconds <= span_end_secs):

            # NOTE: SRT files might trip over positioning.
            # NOTE: Check the line values that actually count as OST,
            #       because there are some values
            #       that shouldn't count as OSTs.
            if in_vtt and ((not OST and not OST_only and sub.line == 'auto')
                           or (OST and not OST_only)
                           or (OST and OST_only and sub.line != 'auto')):
                # NOTE: Maybe do a deep copy here.
                if out_vtt:
                    out_subs.append(sub)
                elif out_srt:
                    out_subs.append(sub.to_SRT())

            elif in_srt:
                # NOTE: Maybe do a deep copy here.
                if out_vtt:
                    out_subs.append(sub.to_VTT())
                elif out_srt:
                    out_subs.append(sub)

        elif sub.end_time.total_seconds > span_end_secs:
            break

    if not out_subs:
        print('No subtitles found in the specified range.')
    
    elif not out_name:
        for out_sub in out_subs:
            print(out_sub)
    else:
        if out_vtt:
            save_subs(out_name, out_subs)

        elif out_srt:
            renumber(out_subs)
            srt_handler.save_subs(out_name, out_subs)


def pre_fix(file_name, lang, old=True):

    REPLACEMENTS = {
        '@@@': '</i>',
        '@@': '<i>',
        r'\.{3}': '…',
        '<br>': ' ',
        '<em>': '<i>',
        '</em>': '</i>',
        '‑': '-'
    }

    name, ext = os.path.splitext(file_name)

    file_list = read_text_file(file_name)
    file_string = ''.join(file_list)

    for key in REPLACEMENTS.keys():
        file_string = re.sub(key, REPLACEMENTS[key], file_string)

    file_list = file_string.split('\n')
    file_list = [j + '\n' for j in file_list]
    if old:
        subtitles = decode_VTT(file_list)['subtitles']
    else:
        subtitles = parse_VTT(file_name)['cues']

    empty_subs = {}
    isolated_at = {}
    isolated_hash = {}
    invalid_hyphens = {}
    invalid_dashes = {}

    for n, sub in enumerate(subtitles):
        error_counter = 1
        if not re.search('\S', ' '.join(sub.text)):
            empty_subs[f'{sub.number}_{error_counter}'] = (
                f'Subtitle is empty'
            )
            error_counter += 1

        if len(sub.text) == 1 and re.search('^-', sub.text[0]):
            invalid_hyphens[f'{sub.number}_{error_counter}'] = (
                f'Invalid hyphen.'
            )
            error_counter += 1

        elif (len(sub.text) == 2
              and (re.search('^[—–]', sub.text[0])
                   or re.search('^[—–]', sub.text[1]))):

            invalid_dashes[f'{sub.number}_{error_counter}'] = (
                f'Invalid dashes'
            )
            error_counter += 1

    if empty_subs:
        print('Empty subtitles:\n')
        for key in empty_subs.keys():
            print(f'-{key}')
            print('\n')

    if invalid_hyphens:
        print('Invalid hyphens:\n')
        for key in invalid_hyphens.keys():
            print(f'-{key}')
            print('\n')

    if invalid_dashes:
        print('Invalid dashes:\n')
        for key in invalid_dashes.keys():
            print(f'-{key}')
            print('\n')

    save_VTT_subs(f'{name}__fixed{ext}', subtitles)



def download_status(book_name):


    workbook = openpyxl.load_workbook(book_name)
    sheets = workbook.sheetnames


def check_OSTs(directory, old=True):
    
    
    original_dir = os.getcwd()
    os.chdir(directory)

    file_list = os.listdir()
    for sub_file in file_list:
        OST_errors = []
        sub_errors = []

        name, ext = os.path.splitext(sub_file)

        if ext == '.vtt':
            if old:
                vtt_subs = decode_VTT(read_text_file(sub_file))['subtitles']
            else:
                vtt_subs = parse_VTT(sub_file)['cues']

            for i, sub in enumerate(vtt_subs):
                tag_match = re.search('^\[.*\]$', ''.join(sub.untagged_text))

                if sub.line == 20 and not tag_match:
                    OST_errors.append(i)
                
                elif sub.line == 'auto' and tag_match:
                    OST_errors.append(i)

            if OST_errors:
                print(sub_file)
                print('\n\n')

                for error in OST_errors:
                    print(vtt_subs[error])

    os.chdir(original_dir)


def check_GEMs(directory):

    oiriginal_dir = os.getcwd()
    os.chdir(directory)

    all_files = os.listdir()

    for di in all_files:
        if os.path.isdir(di):
            new_dir = directory + '\\' + di
            os.chdir(new_dir)

            in_files = os.listdir()


def NAS_consist(directory, old=True):

    original_dir = os.getcwd()
    os.chdir(directory)
    lang = directory.split('\\')[-1]
    lang_cont = [lang, '\n\n\n']

    file_list = os.listdir()
    for sub_file in file_list:

        name, ext = os.path.splitext(sub_file)

        if ext == '.vtt':
            lang_cont.append(sub_file)
            lang_cont.append('\n\n')
            if old:
                vtt_subs = decode_VTT(read_text_file(sub_file))['subtitles']
            else:
                vtt_subs = parse_VTT(sub_file)['cues']
            
            for i, sub in enumerate(vtt_subs):
                if ('<i>' in ' '.join(sub.text) or '"' in ' '.join(sub.text)
                    or '“' in ' '.join(sub.text) or '”' in ' '.join(sub.text)
                    or '«' in ' '.join(sub.text) or '»' in ' '.join(sub.text)):

                    lang_cont.append(sub.__str__())
                    lang_cont.append('\n\n\n\n')

            lang_cont.append('\n\n')

    ending = '-' * 100
    lang_cont.append(ending)
    lang_cont.append('\n')

    os.chdir(original_dir)

    return lang_cont


def NAS_consist_batch(file_name, directories, look_up=[]):

    with open(file_name, 'w', encoding='utf-8-sig') as const_file:
        for directory in directories:
            # contents = NAS_consist(directory)
            contents = italics_consist(directory, look_up)
            for line in contents:
                const_file.write(line)


def italics_consist(directory, look_up, old=True):

    original_dir = os.getcwd()
    os.chdir(directory)
    lang = directory.split('\\')[-1]
    lang_cont = [lang, '\n\n\n']

    file_list = os.listdir()
    for sub_file in file_list:

        name, ext = os.path.splitext(sub_file)

        if ext == '.vtt':
            lang_cont.append(sub_file)
            lang_cont.append('\n\n')
            if old:
                vtt_subs = decode_VTT(read_text_file(sub_file))['subtitles']
            else:
                vtt_subs = parse_VTT(sub_file)['cues']
            
            open_tag = False
            time_span = ''
            for i, sub in enumerate(vtt_subs):

                for tag in look_up:
                    if tag in sub.text and not open_tag:
                        open_tag = True
                        time_span += sub.start_time.print_VTT_1()

                    elif tag not in sub.text:
                        if open_tag and sub.line == 'auto':
                            time_span += ' --> ' + vtt_subs[i-1].end_time.print_VTT_1()
                            lang_cont.append(time_span)
                            lang_cont.append('\n\n\n\n')
                            time_span = ''

                        open_tag = False

            lang_cont.append('\n\n')

    ending = '-' * 100
    lang_cont.append(ending)
    lang_cont.append('\n')

    os.chdir(original_dir)

    return lang_cont


def extract_OSTs(file_name, save_OST_dir, batch=False, delete_OSTs=False,
                 save_OSTs=True, old=False):
    """[summary]

    Parameters
    ----------
    file_name : [type]
        [description]
    """

    original_dir = os.getcwd()


    # if not batch:
    #     actual_file_name, ext = os.path.splitext(file_name.split('\\')[-1])
    #     new_file_name = f'{actual_file_name}__OSTs{ext}'
    # else:
    #     pass

    warnings = ''
    errors = ''
    actual_file_name, ext = os.path.splitext(file_name.split('\\')[-1])
    new_file_name = f'{actual_file_name}__OSTs{ext}'

    if old:
        subs = decode_VTT(read_text_file(file_name))['subtitles']
    else:
        subs = parse_VTT(file_name)['cues']

    OSTs = []
    OST_indexes = []
    possible_OSTs = []
    possible_OST_indexes = []

    for i, sub in enumerate(subs):
        check_text = '\n'.join(sub.untagged_text)
        if sub.line == 20:
            possible_OSTs
            possible_OST_indexes.append(i)
            if (re.search('^\[.*\][\.,]*$', check_text)
                or re.search('^\[+[A-ZÀ-Ý ]{2,}', check_text)
                or re.search('[A-ZÀ-Ý ]{2,}\]+$', check_text)
                or re.search('^[A-ZÀ-Ý ]{2,}$', check_text)
                or re.search('^\[.+', check_text)
                or re.search('.+\]$', check_text)):
                # Considered actual OST
                OSTs.append(copy.deepcopy(sub))
                OST_indexes.append(i)                

    if delete_OSTs:
        for j in reversed(OST_indexes):
            subs.pop(j)

        subs_cont = {'stylesheets': [], 'regions': {}, 'cues': subs}
        # save_VTT_subs('Test' + actual_file_name+ext, subs_cont)
        save_VTT_subs(file_name, subs_cont)

    if save_OSTs:
        os.chdir(save_OST_dir)
        short_name_match = re.search('^[\dA-Za-z]+_[\dA-Za-z]+_', actual_file_name)
        if short_name_match:
            short_letters = re.search('[A-Za-z]+', short_name_match.group())
            short_numbers = re.search('\d+', short_name_match.group())

        if short_name_match and short_letters and short_numbers:
            OST_file_name = short_letters.group() + '_' + short_numbers.group() + '_OST.vtt'
        else:
            warnings = f'Could not decode class code for file {file_name}. Saving OST file as {new_file_name}'
            OST_file_name = new_file_name

        OST_cont = {'stylesheets': [], 'regions': {}, 'cues': OSTs}
        # save_VTT_subs('Test' + new_file_name, OST_cont)
        save_VTT_subs(OST_file_name, OST_cont)
        os.chdir(original_dir)

    return (warnings, errors)


def batch_extract_OSTs(lang_path, save_OST_dir,
                       delete_OSTs=False, save_OSTs=True):
    """[summary]

    Parameters
    ----------
    lang_path : [type]
        [description]
    """

    global_errors = {}
    global_warnings = {}

    original_dir = os.getcwd()
    # os.chdir(lang_path)
    # parent_dir = os.path.dirname(lang_path)

    # parent_dir = r'\\'.join(lang_path.split('\\')[:-1])
    # lang = lang_path.split('\\')[-1]
    # new_dir = parent_dir + r'\\' + lang+'__Auto_OSTs' 
    # os.mkdir(new_dir)

    os.chdir(lang_path)
    all_sub_files = os.listdir()
    sub_files = []

    # NOTE: No check is being made here for files that are not .vtt.

    for i, sub_file in enumerate(all_sub_files):
        name, ext = os.path.splitext(sub_file)

        if ext == '.vtt':
            full_file_name = lang_path + '\\' + sub_file
            warnings, errors = extract_OSTs(
                full_file_name,
                save_OST_dir=save_OST_dir,
                batch=True,
                delete_OSTs=delete_OSTs,
                save_OSTs=save_OSTs
            )

            if warnings:
                global_warnings[full_file_name] = warnings
            if errors:
                global_errors[full_file_name] = errors

    os.chdir(original_dir)
    
    if global_errors or global_warnings:
        return (global_warnings, global_errors)

    else:
        return False


    

def TM_fixes(directory, lookup):

    original_dir = os.getcwd()
    os.chdir(directory)
    file_list = os.listdir()

    output = ', '.join(lookup) + '\n\n'

    for sub_file in file_list:
        file_string = '\n'.join(read_text_file(sub_file))
        appended = False

        for word in lookup:
            if word in file_string:
                if not appended:
                    output += '\n' + sub_file + '\n\n'
                    appended = True

                output += word + '\n'

    os.chdir(original_dir)

    print(output)


def count_CPS(directory, CPS_limit=25):

    original_dir = os.getcwd()

    os.chdir(directory)

    file_list = os.listdir()

    for sub_file in file_list:
        print(sub_file)
        print('\n')
        counter = 0
        subs = parse_VTT(sub_file)['cues']
        for sub in subs:
            if sub.CPS_ns > CPS_limit:
                counter += 1

        print(counter)
        print('\n\n')

    


def get_OSTs(directory, save_OSTs_dir, files=True):

    original_path = os.getcwd()
    if not files:
        os.chdir(directory)

        file_list = os.listdir()
    else:
        file_list = directory

    OST_files = []

    for fi in file_list:
        name, ext = os.path.splitext(fi)
        if ext == '.docx':
            counter = 1
            seen_time = False
            cue_text = ''
            OSTs_raw = []
            OSTs = []
            doc = docx.Document(fi)
            for para in doc.paragraphs:

                if re.search('\s*\d\d:\d\d\s*', para.text):

                    if seen_time:
                        OSTs_raw.append((start_time, end_time, cue_text))
                        cue_text = ''

                    va = 2
                    seen_time = True
                    values = [float(value.group()) for value in re.finditer('\d+', para.text)]
                    start_seconds = values[0] * 60 + values[1]
                    start_time = Timecode(start_seconds)
                    end_time = Timecode(start_seconds + 4)
                    
                    va = 2
                
                elif seen_time:
                    if para.text:
                        if not cue_text:
                            cue_text += para.text
                        else:
                            cue_text += '\n' + para.text
                    else:
                        va = 2
                        OSTs_raw.append((start_time, end_time, cue_text))
                        seen_time = False
                        cue_text = ''


            if seen_time:
                OSTs_raw.append((start_time, end_time, cue_text))

            for OST in OSTs_raw:
                raw_text = OST[2]

                if not re.search('^\s*\[', raw_text):
                    raw_text = '[' + raw_text
                if not re.search('\]\s*$', raw_text):
                    raw_text = raw_text + ']'
                
                raw_text = raw_text.upper()
                text = VTT_text_parser(raw_text)

                va = 2
                OSTs.append(
                    WebVTT(
                        counter,
                        text[1],
                        text[0],
                        text[2],
                        OST[0],
                        OST[1],
                        line=20,
                        snap_to_lines=False
                    )
                )
                counter += 1

                va = 2
            
            OST_name = name.split('/')[-1]
            OST_file_name = save_OSTs_dir + '\\' + OST_name + '.vtt'
            save_VTT_subs(OST_file_name, {'regions': [], 'styles': [], 'cues': OSTs})

    os.chdir(original_path)


def get_OSTs_single(file_name, save_OST_dir, GUI=True):

    illegal_chars = ['#', '%', '&', '{', '}', '\\', '<', '>', '*', "?", '/',
                     ' ', '$', '!', "'", '"', ':', '@', '+', '`', '|', '=']

    if GUI:
        act_file_name = file_name.split('/')[-1]
    else:
        act_file_name = file_name.split('\\')[-1]

    name_prefix = re.search('^\s*[a-zA-Z0-9]+_', act_file_name).group()
    name_prefix = name_prefix.strip()

    doc = docx.Document(file_name)

    cue_text = ''
    seen_time = False
    OSTs_raw = []

    for para in doc.paragraphs:

        new_file = True

        if re.search('^\s*\d+\.', para.text):
            
            if OSTs_raw:
                OSTs = []
                counter = 1
                for OST in OSTs_raw:
                    raw_text = OST[2]

                    if not re.search('^\s*\[', raw_text):
                        raw_text = '[' + raw_text
                    if not re.search('\]\s*$', raw_text):
                        raw_text = raw_text + ']'
                    
                    raw_text = raw_text.upper()

                    text = VTT_text_parser(raw_text)

                    va = 2
                    OSTs.append(
                        WebVTT(
                            counter,
                            text[1],
                            text[0],
                            text[2],
                            OST[0],
                            OST[1],
                            line=20,
                            snap_to_lines=False
                        )
                    )
                    counter += 1

                    va = 2
                
                save_VTT_subs(OST_name, {'regions': [], 'styles': [], 'cues': OSTs})



            # OST_name = para.text + '.vtt'
            file_number = re.search('\d+', para.text).group()
            if len(file_number) == 1:
                OST_name = name_prefix + '10' + file_number + '_OST.vtt'
            else:
                OST_name = name_prefix + '1' + file_number + '_OST.vtt'


            for char in illegal_chars:
                if char in OST_name:
                    OST_name = OST_name.replace(char, '_')

            # OST_name = save_OST_dir + '\\' + OST_name
            OST_name = save_OST_dir + '/' + OST_name
            print(OST_name)

            new_file = False
            OSTs = []
            OSTs_raw = []
            continue

        if re.search('\s*\d\d:\d\d\s*', para.text):

            if seen_time:
                OSTs_raw.append((start_time, end_time, cue_text))
                cue_text = ''

            va = 2
            seen_time = True
            values = [float(value.group()) for value in re.finditer('\d+', para.text)]
            start_seconds = values[0] * 60 + values[1]
            start_time = Timecode(start_seconds)
            end_time = Timecode(start_seconds + 4)
            
            va = 2

        elif seen_time:
            if para.text:
                if not cue_text:
                    cue_text += para.text
                else:
                    cue_text += '\n' + para.text
            else:
                va = 2
                OSTs_raw.append((start_time, end_time, cue_text))
                seen_time = False
                cue_text = ''

    if seen_time:
        OSTs_raw.append((start_time, end_time, cue_text))

        for OST in OSTs_raw:
            raw_text = OST[2]

            if not re.search('^\s*\[', raw_text):
                raw_text = '[' + raw_text
            if not re.search('\]\s*$', raw_text):
                raw_text = raw_text + ']'
            
            raw_text = raw_text.upper()

            text = VTT_text_parser(raw_text)

            va = 2
            OSTs.append(
                WebVTT(
                    counter,
                    text[1],
                    text[0],
                    text[2],
                    OST[0],
                    OST[1],
                    line=20,
                    snap_to_lines=False
                )
            )
            counter += 1

            va = 2
        
        save_VTT_subs(OST_name, {'regions': [], 'styles': [], 'cues': OSTs})


