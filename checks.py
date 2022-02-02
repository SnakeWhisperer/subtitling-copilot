import copy, re, os, csv

from decoders import decode_VTT, decode_SRT, parse_VTT
from encoders import encode_VTT
from reader import read_text_file, hash_file
from classes import Timecode
from utils import get_frame_rate


# def get_NF_glyph_list():

#     glyph_list = []

#     with open('NGL2-Final-External-Use.xlsx - Copy of NGL2_Source.csv', encoding='utf-8-sig') as glyphs:
#         csv_reader = csv.reader(glyphs, delimiter=',')
#         line_count = 0

#         for row in csv_reader:
#             if not re.search('^0x', row[0]):
#                 print(row)
#             else:
#                 int_val = int(row[0], 16)
#                 glyph_list.append(chr(int_val))

#     return glyph_list
        

def check_sort(file_name, old=True):

    ext = os.path.splitext(file_name)

    if ext == '.vtt':
        if old:
            subs = decode_VTT(read_text_file(file_name))['subtitles']
        else:
            subs = parse_VTT(file_name)['cues']

    elif ext == '.srt':
        subs = decode_SRT(read_text_file(file_name))

    else:
        print(
            f'File format {ext} is invalid or not currently supported.'
            f'Operation aborted.'
        )
        return

    issues = {}

    for i in range(1, len(subs)):
        if (subs[i].start_time.total_seconds
            < subs[i-1].start_time.total_seconds):
            # Frobnicate
            issues[f'{subs[i].number}'] = (
                "Start time is less than the previous subtitle's start time.")

    return


def batch_quality_check(files_dir, videos_dir='', sc_dir='', shot_changes=True,
                        CPS=True, s_format='', CPS_limit=25, frame_rate=24,
                        CPS_spaces=False, CPL=True, CPL_limit=42,
                        max_lines=2, min_duration=0.833,
                        max_duration=7, ellipses=True, gaps=True,
                        report=False, report_name='', old=True,
                        glyphs=True, check_TCFOL=True, check_OST=True, GUI=True):

    # Check subtitle format.
    if s_format and s_format.lower() not in ['vtt', 'srt']:
        print('The specified format is invalid or not supported.')
        return
    
    # glyph_list = get_NF_glyph_list()
    glyph_list = []

    current_dir = os.getcwd()
    os.chdir(videos_dir)
    all_videos = os.listdir()
    video_files = []

    # Filter all files that are not videos.
    for video in all_videos:
        video_ext = os.path.splitext(video)[-1]

        if video_ext != '.mp4':
            print('Currently can only work with .mp4 files.')
            return
        else:
            video_files.append(video)

    # video_files = sorted(video_files)
    os.chdir(files_dir)
    all_files = os.listdir()
    sub_files = []

    for f_file in all_files:
        ext = os.path.splitext(f_file)[-1]

        if ((not s_format and ext in ['.vtt', '.srt'])
            or (s_format and ext == f'.{s_format}')):
            sub_files.append(f_file)

    # sub_files = sorted(sub_files)

    if report and not report_name:
        print('Please specify a name and extension for the report file.')
        return

    elif GUI or (report and report_name):
        rep_ext = os.path.splitext(report_name)[-1]

        if report and rep_ext not in ['.txt']:
            print('The extension of the report file '
                  'is invalid or not supported.')
            return

        else:
            report_cont = [
                '-'*160,
                f'Quality report for {ext} files '
                f'in the directory {files_dir}',
                '-'*160,
                '\n',
                '-'*120,
                'Files checked',
                '\n'
            ]
            report_cont.extend(sub_files)
            report_cont.extend([
                '\n',
                '-'*120,
                'Settings used:',
                '\n',
                f'Characters-per-second limit: {CPS_limit}',
                f'Include spaces in characters per second: {CPS_spaces}',
                f'Characters-per-line limit: {CPL_limit}',
                f'Max. lines per subtitle: {max_lines}',
                f'Min. subtitle duration: {min_duration} seconds',
                f'Max. subtitle duration: {max_duration} seconds',
                f'Use ellipses instead of three dots: {ellipses}',
                '\n',
                '-'*120,
                '\n'
            ])

    for i, sub_file in enumerate(sub_files):
        # print(sub_file)
        # Only for debugging purposes
        if i == 0:
            hello = 2
        
        if report or GUI:
            report_cont.extend([
                '-'*120,
                '\n',
                sub_file,
                '\n'
            ])
        elif not GUI:
            print(sub_file)
            print('\n')

        # video_name = videos_dir + '\\' + video_files[i]
        video_name = os.path.join(videos_dir, video_files[i])
        frame_rate = get_frame_rate(video_name)

        single_report = quality_check(
            sub_file,
            video_name=video_name,
            sc_dir=sc_dir,
            shot_changes=shot_changes,
            CPS=CPS,
            CPS_limit=CPS_limit,
            CPS_spaces=CPS_spaces,
            CPL=CPL,
            CPL_limit=CPL_limit,
            frame_rate=frame_rate,
            max_lines=max_lines,
            min_duration=min_duration,
            max_duration=max_duration,
            ellipses=ellipses,
            gaps=gaps,
            batch=True,
            report=report,
            old=old,
            glyph_list=glyph_list,
            check_TCFOL=check_TCFOL,
            check_OST=check_OST,
            GUI=GUI
        )

        if report or GUI:
            report_cont.append(single_report)
            report_cont.append('\n\n')
        else:
            print('\n', '-'*70)

    os.chdir(current_dir)

    if report:
        with open(report_name, 'w', encoding='utf-8-sig') as report_file:
            for line in report_cont:
                report_file.write(line)
                report_file.write('\n')

    return report_cont
  

def quality_check(file_name, video_name='', sc_dir='', shot_changes=True,
                  CPS=True, CPS_limit=25, CPS_spaces=False, CPL=True,
                  CPL_limit=42, frame_rate=24, max_lines=2, min_duration=0.833,
                  max_duration=7, ellipses=True, gaps=True, batch=False,
                  report=False, report_name='', old=True,
                  glyphs=False, glyph_list=[], check_TCFOL=True, check_OST=True,
                  GUI=True):

    # print(f'Currently checking {file_name}')
    ext = os.path.splitext(file_name)[-1]

    if ext == '.vtt':
        if old:
            subs = decode_VTT(read_text_file(file_name),
                            frame_rate=frame_rate)['subtitles']
        else:
            subs = parse_VTT(file_name, frame_rate=frame_rate)['cues']

    elif ext == '.srt':
        subs = decode_SRT(read_text_file(file_name), frame_rate=frame_rate)

    else:
        print(
            f'File format {ext} is invalid or not currently supported.'
            f'Operation aborted.'
        )
        return

    if shot_changes:
        if not video_name:
            print('Cannot check shot changes if video name is not passed.')
            return
        else:
            hash_name = hash_file(video_name)
            sc_name = sc_dir + '\\' + hash_name + '.scenechanges'
        
        sc_list = read_text_file(sc_name)

        for m in range(len(sc_list)):
            sc_list[m] = float(sc_list[m].strip())

    general = {}
    warnings = {}

    for i, sub in enumerate(subs):
        error_counter = 1

        # Check CPS.
        if (CPS
            and ((not CPS_spaces and sub.CPS_ns > CPS_limit)
                 or (CPS_spaces and sub.CPS > CPS_limit))):

            if not CPS_spaces:
                sub_CPS = sub.CPS_ns
            else:
                sub_CPS = sub.CPS

            general[f'{sub.number}_{error_counter}'] = (
                f'Reading speed limit exceeded ({sub_CPS} CPS)')

            error_counter += 1

        # Check CPL.
        for j, length in enumerate(sub.line_lengths):
            if (CPL and length > CPL_limit):
                general[f'{sub.number}_{error_counter}'] = (
                    f'Line length limit exceeded '
                    f'(line {j+1}: {sub.line_lengths[j]} characters)'
                )

                error_counter += 1

        # Check number of lines.
        # NOTE: With the new parser, this can be done
        #       with the length of the untagged text.
        if ((old and len(sub.text) > max_lines)
            or (not old and len(sub.untagged_text) > max_lines)):
            general[f'{sub.number}_{error_counter}'] = (
                f'Maximum number of lines exceeded ({len(sub.untagged_text)} lines)'
            )

            error_counter += 1

        # Check minimum duration.
        if sub.get_duration() < min_duration:
            general[f'{sub.number}_{error_counter}'] = (
                f'Subtitle lasts less than the minimum duration '
                f'({sub.get_duration()} seconds)'
            )

            error_counter += 1

        # Check maximum duration.
        if sub.get_duration() > max_duration:
            general[f'{sub.number}_{error_counter}'] = (
                f'Subtitle exceeds the maximum duration '
                f'({sub.get_duration()} seconds)'
            )

            error_counter += 1
        
        # Check if text fits in one line.
        if (check_TCFOL and len(sub.untagged_text) > 1
            and sub.total_length < CPL_limit and not sub.dialogue):
            #
            general[f'{sub.number}_{error_counter}'] = (
                f'Text can fit in one line'
            )

            error_counter += 1

        # Check ellipses.
        if ellipses and '...' in sub.text:
            general[f'{sub.number}_{error_counter}'] = (
                f'Subtitle uses three dots (...) '
                f'instead of ellipsis character (…)'
            )
            
            error_counter += 1
        
        if glyphs:
            for line in sub.untagged_text:
                for char in line:
                    if char not in glyph_list:
                        general[f'{sub.number}_{error_counter}'] = (
                            f'Invalid character (char).'
                        )

                        error_counter += 1

        # # NOTE: There is another loop above.
        # #       Having two loops don't really seem very efficient.
        # #       Now that the WebVTT class has the text attribute
        # #       as a single string, this can be done without a loop.
        # for line in sub.text:
        #     if ellipses and '...' in line:
        #         general[f'{sub.number}_{error_counter}'] = (
        #             f'Subtitle uses three dots (...) '
        #             f'instead of ellipsis character (…)'
        #         )
                
        #         error_counter += 1
        
        # Check gaps.
        if gaps:
            # Only for debugging purposes
            # if i == 73:
            #     hello = 2
            gap_errors = check_gaps_one(i, subs, error_counter=error_counter)

            if gap_errors:
                general = {**general, **gap_errors}

        # Check shot changes.
        if shot_changes:
            # Only for debugging purposes
            # if i == 26:
            #     hello = 2

            shot_errors, shot_warnings = check_shot_changes(
                sub.start_time,
                sub.end_time,
                sub.number,
                sub,
                sc_list,
                frame_rate=frame_rate,
                error_counter=error_counter
            )

            if shot_errors:
                general = {**general, **shot_errors}
            if shot_warnings:
                warnings = {**warnings, **shot_warnings}

        if check_OST:
            check_text = ' '.join(sub.untagged_text)
            if sub.line == 20:
                if (not re.search('^\[.+\]$', check_text)
                    or check_text.upper() != check_text):
                    # Error in OST
                    general[f'{sub.number}_{error_counter}'] = (
                        f'Error in OST'
                    )
                    error_counter += 1

            else:
                if (re.search('^\[.+\]$', check_text)
                    and check_text.upper() != check_text):
                    # Possible OST not raised.
                    warnings[f'{sub.number}_{error_counter}'] = (
                        f'Possible OST not raised to the top of the screen.'
                    )
                    error_counter += 1

                # # Checks for '[OST TEST].'
                # if re.search('^\[.*\][\.,]*$', check_text):
                #     general[f'{sub.number}_{error_counter}'] = (
                #         f'Punctuation found outside of brackets in OST.'
                #     )
                #     error_counter += 1

                # # Checks for '[OST TEST'
                # if re.search('^\[+[A-ZÀ-Ý ]{2,}$', check_text):
                #     general[f'{sub.number}_{error_counter}'] = (
                #         f'Missing closing square brackets in OST.'
                #     )
                #     error_counter += 1

                # # Checks for 'OST TEST]'
                # if re.search('[A-ZÀ-Ý ]{2,}\]+$', check_text):
                #     general[f'{sub.number}_{error_counter}'] = (
                #         f'Missing opening square brackets in OST.'
                #     )
                #     error_counter += 1

                # # Checks for 'OST TEST'
                # if re.search('^[A-ZÀ-Ý ]{2,}$', check_text):
                #     general[f'{sub.number}_{error_counter}'] = (
                #         f'Missing opening and closing square brackets in OST.'
                #     )
                #     error_counter += 1



    single_rep = ''
    
    # If there are errors...
    if general:
        single_rep += '- Issues\n\n\t#\t\t\tIssue description\n\n'

        for key in list(general.keys()):
            current_line = '\t'
            actual_key = re.search('\d+', key).group()
            current_line += actual_key

            if len(actual_key) > 3:
                current_line += '\t\t'
            else:
                current_line += '\t\t\t'

            current_line += general[key]
            single_rep += current_line + '\n'

    # If there are warnings...
    if warnings:
        single_rep += '\n\n- Warnings\n\n\t#\t\t\tWarning\n\n'

        for key in list(warnings.keys()):
            current_line = '\t'
            actual_key = re.search('\d+', key).group()
            current_line += actual_key

            if len(actual_key) > 3:
                current_line += '\t\t'
            else:
                current_line += '\t\t\t'

            current_line += warnings[key]
            single_rep += current_line + '\n'

    if general or warnings:
        
        if not report and not GUI:
            # print('Here')
            print(single_rep)

        elif GUI or (report and batch):
            # print('There')
            return single_rep

        elif report and not batch:
            pass

    else:
        return('\n\n\tNo issues found.')
        # print('\n\n\tNo issues found.')


def check_gaps_one(index, subtitles, invalid_range=(3,11), error_counter=1,
                   frame_rate=24, sorted=False, snapped=False,
                   fix=False, ext_q=False, off_forward=False):
    """[summary]

    NOTE: Make sure to review the calls to this function
          in the quality check so that the snapped argument
          is considered when it is to be used differently.
    Now also fixes gaps with the correct arguments.

    Parameters
    ----------
    index : [type]
        [description]
    subtitles : [type]
        [description]
    invalid_range : tuple, optional
        [description], by default (3,11)
    error_counter : int, optional
        [description], by default 1
    frame_rate : int, optional
        [description], by default 24
    sorted : bool, optional
        [description], by default False
    snapped : bool, optional
        [description], by default False

    Returns
    -------
    [type]
        [description]
    """

    
    gap_errors = {}

    for j in range(len(subtitles)):
        
        if j != index:
            if snapped:
                gap = (
                    subtitles[j].start_time.total_rendered_frames_s
                    - subtitles[index].end_time.total_rendered_frames_s)
            else:
                gap = (
                    subtitles[j].start_time.total_rendered_frames_r
                    - subtitles[index].end_time.total_rendered_frames_r)

            # if index == 23:
                # print(gap)

            if ((gap >= invalid_range[0] and gap <= invalid_range[1])
                or (gap >= 0 and gap < 2)):
                # Frobnicate
                if fix and gap >= invalid_range[0] and gap <= invalid_range[1]:
                    offset = ((subtitles[j].start_time.total_seconds
                               - (2 / frame_rate))
                              - subtitles[index].end_time.total_seconds)

                    subtitles[index].end_time.offset(offset)

                # NOTE: Careful here.
                #       The end time cannot be offset blindly,
                #       because there could be a shot change nearby.
                elif fix and gap >= 0 and gap < 2:
                    offset = (subtitles[index].end_time.total_seconds
                              - (subtitles[j].start_time.total_seconds
                                 - (2 / frame_rate)))

                    if off_forward:
                        print('Offsetting for {subtitles[index].number}')
                        subtitles[j].start_time.offset(offset)
                    else:
                        subtitles[index].end_time.offset(-offset)

                else:
                    if gap == 1:
                        error_message = f'Invalid gap ({gap} frame)'
                    else:
                        error_message = f'Invalid gap ({gap} frames)'

                    gap_errors[
                        f'{subtitles[index].number}_{error_counter}'] = (
                            error_message)

                    error_counter += 1

            elif fix and ext_q:
                pass

    if fix:
        return None
    else:
        return gap_errors


def check_shot_changes(start_time, end_time, sub_num,
                       subtitle, shot_change_list,
                       frame_rate=24, error_counter=1):

    # NOTE: Change this depending on how 25 fps is treated.
    half_second = frame_rate // 2

    shot_errors = {}
    shot_warnings = {}
    start_errors = False
    end_errors = False

    start_nearest = nearest_shot_change(
        shot_change_list,
        start_time.total_rendered_frames_r,
        frame_rate=frame_rate,
        half_second=half_second
    )

    end_nearest = nearest_shot_change(
        shot_change_list,
        end_time.total_rendered_frames_r,
        frame_rate=frame_rate,
        half_second=half_second,
        end_time=True
    )

    # Only for debugging purposes.
    if end_nearest == 10:
        hello = 12

    if start_nearest:

        start_messages, start_errors, error_counter = check_near_shot_changes(
            sub_num,
            start_nearest,
            start_time.total_rendered_frames_r,
            shot_change_list,
            frame_rate=frame_rate,
            end_time=False,
            error_counter=error_counter
        )

    else:
        start_messages = False

    if end_nearest:

        end_messages, end_errors, error_counter = check_near_shot_changes(
            sub_num,
            end_nearest,
            end_time.total_rendered_frames_r,
            shot_change_list,
            frame_rate=frame_rate,
            end_time=True,
            error_counter=error_counter
        )

    else:
        end_messages = False

    if start_errors:
        shot_errors = start_messages
    elif start_messages:
        shot_warnings = start_messages

    if end_errors:
        shot_errors = {**shot_errors, **end_messages}
    elif end_messages:
        shot_warnings = {**shot_warnings, **end_messages}

    return shot_errors, shot_warnings


def nearest_shot_change(shot_change_list, time, frame_rate=24,
                        half_second=12, end_time=False, gaps=False):
    """[summary]

    Parameters
    ----------
    shot_change_list : [type]
        [description]
    time : [type]
        [description]
    frame_rate : int, optional
        [description], by default 24
    half_second : int, optional
        [description], by default 12
    end_time : bool, optional
        [description], by default False
    gaps : bool, optional
        Means that the function was called to obtain the nearest
        shot change that can affect the offset to fix gaps,
        by default False

    Returns
    -------
    [type]
        [description]
    """
    
    # Variables for the binary search.
    low = 0
    high = len(shot_change_list) - 1
    mid = 0

    # Only for debugging purposes
    if end_time:
        hello = 2

    while low <= high:
        mid = (high + low) // 2

        # NOTE: Careful here.  See that the snapped frame is being used.
        mid_frame = Timecode(
            shot_change_list[mid],
            frame_rate=frame_rate).total_rendered_frames_s

        # See if the time is at least half a second
        # past the currently checked shot change
        # for timing-to-shot-change checks (gaps=False).
        # Or if the time is at least half a second plus two frames
        # past the currently checked shot change
        # for fixing gaps (gaps=True).
        # Applies the same for start times and end times.
        if ((not gaps and mid_frame <= time - half_second)
            or (gaps and mid_frame <= time - half_second - 2)):
            low = mid + 1

        # See if the time is at least half a second
        # before the shot change for start times
        # or half a second plus one frame
        # before the shot change for end times.
        elif ((mid_frame >= time + half_second and not end_time)
              or (mid_frame >= time + half_second + 1 and end_time)):

            high = mid - 1

        else:
            return mid

    return None


def check_near_shot_changes(sub_num, first_found, time, shot_change_list,
                            frame_rate=24, end_time=False, error_counter=1,
                            ret_list=False, gaps=False):
    """[summary]

    Parameters
    ----------
    sub_num : [type]
        [description]
    first_found : [type]
        [description]
    time : int
        The time in frames.
    shot_change_list : [type]
        [description]
    frame_rate : int, optional
        [description], by default 24
    end_time : bool, optional
        [description], by default False
    """

    near_list = []
    shot_messages = {}
    half_second = frame_rate // 2

    search_back = True
    search_ind = first_found
    on_shot_start_right = False
    on_shot_end_right = False

    while True:
        shot_frame = Timecode(
            shot_change_list[search_ind],
            frame_rate=frame_rate).total_rendered_frames_r

        frame_diff = time - shot_frame

        # Start or end time incorrectly after the shot change.
        if frame_diff > 0 and frame_diff <= half_second - 1:

            if frame_diff == 1:
                plu_sing = f'{abs(frame_diff)} frame after'
            elif frame_diff > 0:
                plu_sing = f'{abs(frame_diff)} frames after'
            else:
                plu_sing = f'on'

            if end_time:
                error_message = (
                    f'The subtitle ends {plu_sing} a shot change'
                )

            else:
                error_message = (
                    f'The subtitle starts {plu_sing} a shot change'
                )

            shot_messages[f'{sub_num}_{error_counter}'] = error_message
            error_counter += 1

        # Start or end time incorrectly before the shot change.
        elif ((frame_diff >= -(half_second - 1)
               and frame_diff < 0 and not end_time)
              or (frame_diff >= -half_second and frame_diff != -2
                  and frame_diff <= 0 and end_time)):

            if frame_diff == 1:
                plu_sing = f'{abs(frame_diff)} frame before'
            elif frame_diff < 0:
                plu_sing = f'{abs(frame_diff)} frames before'
            else:
                plu_sing = f'on'

            if end_time:
                error_message = (
                    f'The subtitle ends {plu_sing} a shot change'
                )
            
            else:
                error_message = (
                    f'The subtitle starts {plu_sing} a shot change'
                )

            shot_messages[f'{sub_num}_{error_counter}'] = error_message
            error_counter += 1

        # ONLY TO FIX GAPS.
        # Time (start or end?) in the range of half a second
        # plus one frame after a shot change.
        elif (ret_list and gaps
              and (frame_diff > 0 and frame_diff <= half_second + 1)):
            near_list.append(search_ind)

        # Start time correctly on the shot change.
        elif frame_diff == 0 and not end_time:
            on_shot_start_right = True

        # End time correctly on the shot change.
        elif frame_diff == -2 and end_time:
            on_shot_end_right = True

        # Start or end time half a second or more past the shot change
        # while searching back.  Stop searching back
        # and start searching forward.
        elif frame_diff >= half_second and search_back:
            search_back = False
            search_ind = first_found

        # Start time half a second before the shot change
        # or end time half a second plus one frame
        # before the shot change while searching forward.
        # Stop searching.
        elif ((frame_diff <= -half_second and not end_time)
              or (frame_diff <= -(half_second + 1) and end_time)):
            break

        if search_back and search_ind >= 1:
            search_ind -= 1

        elif search_back:
            search_back = False
            search_ind = first_found + 1

        elif search_ind <= len(shot_change_list) - 2:
            search_ind += 1

        else:
            break

    if ret_list:
        return near_list

    # Return shot messages as errors.
    elif (shot_messages
          and ((end_time and not on_shot_end_right)
               or (not end_time and not on_shot_start_right))):
        return shot_messages, True, error_counter

    # Return shot messages as warnings.
    elif shot_messages:
        return shot_messages, False, error_counter

    # Return no messages.
    else:
        return False, False, error_counter






def check_sort(file_name):

    subs = parse_VTT(file_name)['cues']
    out_of_order = []

    for i, sub in enumerate(subs):

        if i == 0:
            continue
        if sub.start_time.total_seconds < subs[i-1].start_time.total_seconds:
            out_of_order.append(i)
        
    if out_of_order:
        for number in out_of_order:
            print(f'Start time of subtitle {subs[number].number} is less than the previous.')

    else:
        print('File is correctly sorted by start time.')


def batch_check_sort(directory):

    original_dir = os.getcwd()
    os.chdir(directory)
    file_list = os.listdir()

    for fi in file_list:
        name, ext = os.path.splitext(fi)

        if ext == '.vtt':
            print('-', fi)
            print('\n')
            check_sort(fi)
            print('\n\n')

    os.chdir(original_dir)