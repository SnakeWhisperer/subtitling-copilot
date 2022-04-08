import copy, os

from classes import Timecode
from reader import read_text_file, hash_file
from decoders import decode_VTT, decode_SRT, parse_VTT, parse_SRT, SRT_text_parser, VTT_text_parser
from checks import nearest_shot_change, check_gaps_one, check_near_shot_changes
from srt_handler import save_SRT_subs
from utils import get_frame_rate

def snap_to_frames(subtitles, frame_rate=24):

    snapped_subtitles = copy.deepcopy(subtitles)

    for i, sub in enumerate(snapped_subtitles):

        # start_frame = sub.start_time.total_rendered_frames_s
        # end_frame = sub.end_time.total_rendered_frames_s

        start_frame = sub.start_time.total_rendered_frames_r
        end_frame = sub.end_time.total_rendered_frames_r

        new_start_time = Timecode(
            start_frame / frame_rate,
            frame_rate=frame_rate
        )

        new_end_time = Timecode(
            end_frame / frame_rate,
            frame_rate=frame_rate
            )

        sub.start_time = new_start_time
        sub.end_time = new_end_time

    return snapped_subtitles


def snap_to_shot_changes(subtitles, frame_rate=24, video_name='',
                         shot_change_dir='', shot_change_list=[]):
    """Calls checks.nearest_shot_change() to find the first shot change
    that's in the invalid range of the subtitle's end and start times.
    
    NOTE: However, this shot change returned is not really necessarily
    the nearest or the furthest shot change.  It's only the first found,
    because the search is a binary search.
    Consider adding capability to evaluate all shot changes
    in the invalid range and decide to which one to snap.

    Parameters
    ----------
    subtitles : [type]
        [description]
    frame_rate : int, optional
        [description], by default 24
    video_name : str, optional
        [description], by default ''
    shot_change_dir : str, optional
        [description], by default ''
    shot_change_list : list, optional
        [description], by default []

    Returns
    -------
    [type]
        [description]
    """

    original_dir = os.getcwd()
    half_second = frame_rate // 2

    if video_name and shot_change_dir and not shot_change_list:
        video_file = video_name.split('\\')[-1]
        video_ext = os.path.splitext(video_name)[-1]

        hash_name = hash_file(video_name)
        sc_name = shot_change_dir + '\\' + hash_name + '.scenechanges'

        shot_change_list = read_text_file(sc_name)

        for i in range(len(shot_change_list)):
            shot_change_list[i] = float(shot_change_list[i].strip())

    else:
        pass

    snapped_subtitles = snap_to_frames(subtitles, frame_rate=frame_rate)

    for j, sub in enumerate(snapped_subtitles):
        
        if j == 77:
            hello = 32

        # NOTE: These two variables get only the first shot change
        #       that is found when doing a binary search.
        #       However, that one might not necessarily be
        #       the only shot change within the forbidden range,
        #       and some may make more sense to snap to than others.
        nearest_start = nearest_shot_change(
            shot_change_list,
            sub.start_time.total_rendered_frames_s,
            frame_rate=frame_rate,
        )

        nearest_end = nearest_shot_change(
            shot_change_list,
            sub.end_time.total_rendered_frames_s,
            frame_rate=frame_rate,
            end_time=True
        )
        
        # If at least one shot change was found
        # within the forbidden range of the start time...
        if nearest_start:
            nearest_start_timecode = Timecode(
                shot_change_list[nearest_start],
                frame_rate=frame_rate
            )
            
            # If the subtitle starts within half a second
            # after the shot change...
            if (sub.start_time.total_seconds
                > nearest_start_timecode.total_seconds):

                if (snapped_subtitles[j-1].end_time.total_seconds
                    > nearest_start_timecode.total_seconds):
                    # Frobnicate
                    offset = (nearest_start_timecode.total_seconds
                              + (half_second / frame_rate)
                              - sub.start_time.total_seconds)

                else:
                    offset = -(sub.start_time.total_seconds
                               - nearest_start_timecode.total_seconds)

                # Offset the start time forward so the subtitle starts
                # half a second after the shot change.
                # NOTE: This only works when the previous subtitle ends
                #       after the shot change, in which case
                #       this start time cannot be offset back.
                #       However, when the previous subtitle does not end
                #       after the shot change, this start time
                #       needs to be offset back to the shot change.
                # offset = (nearest_start_timecode.total_seconds
                #           + (half_second / frame_rate)
                #           - sub.start_time.total_seconds)

            # If the subtitle starts within half a second
            # before the shot change...
            elif (sub.start_time.total_seconds
                  < nearest_start_timecode.total_seconds):
                # If the subtitle starts 8 frames or less
                # before the shot change...
                if ((nearest_start_timecode.total_rendered_frames_s
                     - sub.start_time.total_rendered_frames_s) <= 8):
                    # Snap the start time to the shot change.
                    offset = (nearest_start_timecode.total_seconds
                              - sub.start_time.total_seconds)

                # If the subtitle starts between 9 and 11 frames
                # before the shot change...
                elif ((nearest_start_timecode.total_rendered_frames_s
                       - sub.start_time.total_rendered_frames_s) > 8):
                    # Offset the start time to half a second
                    # before the shot change.
                    offset = -(sub.start_time.total_seconds
                               - (nearest_start_timecode.total_seconds
                                  - (half_second / frame_rate)))

            sub.start_time.offset(offset)

        # If at least one shot change was found
        # within the forbidden range of the end time...
        if nearest_end:
            nearest_end_timecode = Timecode(
                shot_change_list[nearest_end],
                frame_rate=frame_rate
            )
            
            # If the subtitle ends within half a second
            # after the shot change...
            if sub.end_time.total_seconds > nearest_end_timecode.total_seconds:
                # Offset the end time forward so the subtitle ends
                # half a second after the shot change.
                offset = (nearest_end_timecode.total_seconds
                          + (half_second / frame_rate)
                          - sub.end_time.total_seconds)

                # sub.end_time.offset(offset)

            # If the subtitle ends within half a second
            # before the shot change...
            # NOTE: This conditional may not be necessary.
            #       It could work with the two inner conditionals
            #       as elifs at the same level as the previous one.
            elif (sub.end_time.total_seconds
                  < nearest_end_timecode.total_seconds):
                # If the subtitle ends within 2 frames
                # before the shot change...
                if (nearest_end_timecode.total_rendered_frames_s
                    - sub.end_time.total_rendered_frames_s < 2):
                    # Offset back so it ends 2 frames
                    # before the shot change.
                    offset = -(sub.end_time.total_seconds
                               - (nearest_end_timecode.total_seconds
                                  - (2 / frame_rate)))

                # If the subtitle ends more than 2 frames
                # before the shot change but less than half a second
                # plus one frame before it...
                elif (nearest_end_timecode.total_rendered_frames_s
                      - sub.end_time.total_rendered_frames_s > 2):

                    if (snapped_subtitles[j+1].start_time.total_rendered_frames_s
                        < (nearest_end_timecode.total_rendered_frames_s - 8)):
                        # Frobnicate
                        offset = -(sub.end_time.total_seconds
                                   - (nearest_end_timecode.total_seconds
                                      - ((half_second + 2) / frame_rate)))

                    else:
                        offset = ((nearest_end_timecode.total_seconds
                                   - (2 / frame_rate))
                                  - sub.end_time.total_seconds)
                    # Offset forward so it ends 2 frames
                    # before the shot change.
                    # NOTE: This only works when there is no subtitle
                    #       that starts right after this one, because,
                    #       if this happens, it's possible that the next
                    #       subtitle needs to be offset back to start
                    #       half a second before the shot change,
                    #       and there would be an overlap.
                    # offset = ((nearest_end_timecode.total_seconds
                    #            - (2 / frame_rate))
                    #           - sub.end_time.total_seconds)

                    # sub.end_time.offset(offset)

                else:
                    offset = 0

            sub.end_time.offset(offset)

    return snapped_subtitles


def fix_gaps(subtitles, frame_rate=24, ext_q=False, video_name='',
             shot_change_dir='', shot_change_list=[]):
    """This function needs to be run after snapping the subtitles
    to the shot changes.  It needs to shot change list
    because fixing gaps depends on them.

    Parameters
    ----------
    subtitles : [type]
        [description]
    frame_rate : int, optional
        [description], by default 24
    ext_q : bool, optional
        Used to extend end times past the end of the audio
        for better quality, by default False
    video_name : str, optional
        [description], by default ''
    shot_change_dir : str, optional
        [description], by default ''
    shot_change_list : list, optional
        [description], by default []
    """

    half_second = frame_rate // 2

    if video_name and shot_change_dir and not shot_change_list:
        video_file = video_name.split('\\')[-1]
        video_ext = os.path.splitext(video_name)

        hash_name = hash_file(video_name)
        sc_name = shot_change_dir + '\\' + hash_name + '.scenechanges'

        shot_change_list = read_text_file(sc_name)

        for i in range(len(shot_change_list)):
            shot_change_list[i] = float(shot_change_list[i].strip())

    else:
        pass

    for i, sub in enumerate(subtitles):
        off_forward = False
        
        # If it exists, find the first shot change that falls
        # in the forbidden range of the current end time.
        # Call nearest_shot_change with gaps=True
        # so that it considers shot changes that are not necessarily
        # in the forbidden range, but that can affect how the offet
        # is made to fix the gaps.
        nearest_end = nearest_shot_change(
            shot_change_list,
            sub.end_time.total_rendered_frames_s,
            frame_rate=frame_rate,
            gaps=True
        )

        # If there is a shot change
        # in the forbidden range of the end time...
        if nearest_end:
            nearest_end_timecode = Timecode(
                shot_change_list[nearest_end],
                frame_rate=frame_rate,
            )

            # Only for debugging purposes.
            if sub.number == '23':
                print(nearest_end)

            # Get the list of all shot changes
            # that fall in that forbidden range.
            # All shot changes returned will supposedly prevent
            # the end time to be offset back.
            # NOTE: Currently it's not really clear
            #       how this is going to be used.
            near_list = check_near_shot_changes(
                sub.number,
                nearest_end,
                sub.end_time.total_rendered_frames_s,
                shot_change_list,
                frame_rate=frame_rate,
                end_time=True,
                ret_list=True,
                gaps=True
            )

            # The first shot change found in the forbidden range
            # (binary search) is not originally included
            # in the near_list.
            near_list.append(nearest_end)
            near_list = sorted(near_list)

            # Only for debugging purposes.
            if near_list:
                print(f'Forward to fix #{sub.number}')
                off_forward = True

        check_gaps_one(
            i,
            subtitles,
            invalid_range=(3, half_second-1),
            frame_rate=frame_rate,
            snapped=True,
            fix=True,
            off_forward=off_forward
        )


def fix_gaps_nsc(subtitles, frame_rate=24):
    
    half_second = round(frame_rate) // 2

    for i, sub in enumerate(subtitles):
        # Only for debugging purposes.
        if i == 19:
            hello = 2

        if i < len(subtitles) - 1:
            gap = (subtitles[i+1].start_time.total_rendered_frames_s
                - sub.end_time.total_rendered_frames_s)

            offset = 0
            
            if gap < 2 or (gap > 2 and gap <= half_second + 2):
                offset = (
                    (subtitles[i+1].start_time.total_seconds
                     - (2 / frame_rate))
                    - sub.end_time.total_seconds
                )

            elif gap >= half_second * 2:
                offset = half_second / frame_rate

            elif gap < half_second * 2 and gap != 2:
                offset = (
                    (subtitles[i+1].start_time.total_seconds
                     - (half_second / frame_rate))
                    - sub.end_time.total_seconds
                )

        else:
            offset = half_second / frame_rate

        sub.end_time.offset(offset)


def gaps_duckmotion(file_name, frame_rate):

    name = file_name.split('\\')[-1]

    subtitles = decode_SRT(read_text_file(file_name), frame_rate=frame_rate)
    snapped_subtitles = snap_to_frames(subtitles, frame_rate=frame_rate)
    fix_gaps_nsc(snapped_subtitles, frame_rate=frame_rate)

    save_SRT_subs(name, snapped_subtitles)


def fix_TCFOL(subtitles, CPL_limit, extension, file_name=''):

    if file_name:
        name, ext = os.path.splitext(file_name)
    
    for i in range(len(subtitles)):
        if (len(subtitles[i].untagged_text) > 1
            and subtitles[i].total_length < CPL_limit and not subtitles[i].dialogue):
            #
            print(subtitles[i].text)
            text = subtitles[i].text.replace('\n', ' ')

            if extension == '.srt':

                (
                    subtitles[i].tokenized_text,
                    subtitles[i].text,
                    subtitles[i].untagged_text,
                    _
                ) = SRT_text_parser(text)

            elif extension == '.vtt':
                (
                    subtitles[i].tokenized_text,
                    subtitles[i].text,
                    subtitles[i].untagged_text,
                    _
                ) = VTT_text_parser(text)

    if file_name:
        save_SRT_subs(f'{name}__fixed{ext}', subtitles)

    else:
        return subtitles

def fix_min_gaps(subtitles, min_gap=2, frames=True, ignore_overlaps=True):
    
    fixed_subs = copy.deepcopy(subtitles)

    frame_rate = fixed_subs[0].start_time.frame_rate

    for i, sub in enumerate(fixed_subs):
        for j in range(i+1, len(fixed_subs)):
            if frames:
                current_gap = (fixed_subs[j].start_time.total_rendered_frames_r
                               - sub.end_time.total_rendered_frames_r)

                # The usable value in the function
                min_gap_apply = min_gap
            else:
                current_gap = (fixed_subs[j].start_time.total_seconds
                               - sub.end_time.total_seconds)
                current_gap = round(current_gap, 3)
                min_gap_apply = round(min_gap/frame_rate, 3)

            if current_gap < 0 and ignore_overlaps:
                continue

            if current_gap < min_gap_apply:
                if frames:
                    new_end_time = (fixed_subs[j].start_time.total_seconds
                                    - min_gap_apply/frame_rate)
                else:
                    new_end_time = (fixed_subs[j].start_time.total_seconds
                                    - min_gap_apply)

                sub.end_time = Timecode(new_end_time, frame_rate=frame_rate)

    return fixed_subs


def sort(subtitles, by='start'):

    sorted_subs = copy.deepcopy(subtitles)

    # Insertion Sort
    # NOTE: Check this and make sure you understand it
    #       and that it's the most efficient algorithm.
    for step in range(1, len(sorted_subs)):
        key = sorted_subs[step]
        j = step - 1

        while (j >= 0
               and key.start_time.total_seconds
               < sorted_subs[j].start_time.total_seconds):

            sorted_subs[j+1] = sorted_subs[j]
            j = j - 1
        
        sorted_subs[j+1] = key

    return sorted_subs
    
    # if type(file_name) == str:
    #     name, ext = os.path.splitext(file_name)
    #     if ext == '.vtt':
    #         vtt_subs = parse_VTT(file_name)['cues']

    # elif type(file_name) == list:
    #     vtt_subs = file_name

    # # Insertion Sort
    # # NOTE: Check this and make sure you understand it
    # #       and that it's the most efficient algorithm.
    # for step in range(1, len(vtt_subs)):
    #     key = vtt_subs[step]
    #     j = step - 1

    #     while (j >= 0
    #            and key.start_time.total_seconds
    #                < vtt_subs[j].start_time.total_seconds):
            
    #         vtt_subs[j+1] = vtt_subs[j]
    #         j = j - 1

    #     vtt_subs[j + 1] = key


def renumber(subtitles):

    counter = 1

    for subtitle in subtitles:
        subtitle.number = counter
        counter += 1

    return


def replacements(subtitles, repl_dict, extension):


    for i, subtitle in enumerate(subtitles):
        for sub_str in repl_dict.keys():
            new_text = subtitle.text.replace(sub_str, repl_dict[sub_str])
            
            if subtitle.text != new_text:
                if extension == '.srt':

                    (
                        subtitles[i].tokenized_text,
                        subtitles[i].text,
                        subtitles[i].untagged_text,
                        _
                    ) = SRT_text_parser(new_text)

                elif extension == '.vtt':
                    (
                        subtitles[i].tokenized_text,
                        subtitles[i].text,
                        subtitles[i].untagged_text,
                        _
                    ) = VTT_text_parser(new_text)
                
    return subtitles


def batch_fixes(directory, videos_dir, CPL_limit, TCFOL=False,
                snap_frames=False, apply_min_gaps=False, min_gap=2,
                frames=False, ignore_overlaps=True, apply_sort=False,
                ellipses=True):

    original_dir = os.getcwd()

    os.chdir(videos_dir)
    
    all_video_files = os.listdir()

    video_files = []

    for video_name in all_video_files:
        name, ext = os.path.splitext(video_name)
        if ext == '.mp4':
            frame_rate = get_frame_rate(video_name)
            video_files.append([video_name, frame_rate])

    os.chdir(directory)

    all_sub_files = os.listdir()

    sub_files = []

    for file_name in all_sub_files:
        name, ext = os.path.splitext(file_name)
        if ext in ['.srt', '.vtt']:
            sub_files.append(file_name)

    print(video_files)
    print(sub_files)
    for i, file_name in enumerate(sub_files):
        name, ext = os.path.splitext(file_name)
        frame_rate = video_files[i][1]
        if ext == '.srt':
            subs = parse_SRT(file_name, frame_rate=frame_rate)
        elif ext == '.vtt':
            subs = parse_VTT(file_name, frame_rate=frame_rate)
        else:
            continue

        if apply_sort:
            subs = sort(subs)
            renumber(subs)

        if ellipses:
            subs = replacements(subs, {'...': '…'}, ext)

        if TCFOL:
            subs = fix_TCFOL(subs, CPL_limit, ext)

        if snap_frames:
            subs = snap_to_frames(subs, frame_rate=frame_rate)

        if apply_min_gaps:
            subs = fix_min_gaps(subs, min_gap=min_gap,
                                frames=frames, ignore_overlaps=ignore_overlaps)

        if ext == '.srt':
            save_SRT_subs(f'{name}{ext}', subs)
        if ext == '.vtt':
            save_VTT_subs(f'{name}{ext}', subs)


    os.chdir(original_dir)