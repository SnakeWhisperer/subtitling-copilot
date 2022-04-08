import os, shutil, re, ffmpeg# cv2

from reader import read_text_file, hash_file
from classes import Timecode, WebVTT
from decoders import parse_VTT


def fps_check(file_name):
    
    file_list = read_text_file(file_name)

    frame_count = 0
    previous_duration = 0
    duration_summation = 0
    durations = []

    for line in file_list:
        if re.search('n:\s*\d+ ', line):
            frame_time = float(re.search('pts_time:\d+\.*\d*', line).group()[9:])
            durations.append(frame_time - previous_duration)
            
            duration_summation += frame_time - previous_duration
            previous_duration = frame_time

    print(len(durations))
    print(duration_summation / len(durations))


# def get_frame_rate(video):
#     cap = cv2.VideoCapture(video)
#     frame_rate = cap.get(cv2.CAP_PROP_FPS)
#     frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#     # print(frame_count)

#     return frame_rate


def video_duration(video):

    probe = ffmpeg.probe(video)
    if probe['streams'][0]['duration'] != probe['streams'][1]['duration']:
        print(f'Warning: {video} has a mismatch between the streams')

    duration = Timecode(float(probe['streams'][0]['duration']))

    return duration.total_seconds, duration.__str__()[:8]


def get_frame_rate(video):
    probe = ffmpeg.probe(video)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    fps = eval(video_info['r_frame_rate'])

    return fps


def batch_get_frame_rates_gui(videos_list):
    frame_rates = []

    for video in videos_list:
        frame_rates.append(get_frame_rate(video))

    return frame_rates


def batch_get_frame_rates(directory):
    original_dir = os.getcwd()
    os.chdir(directory)

    videos = os.listdir()

    for video in videos:
        name, ext = os.path.splitext(video)
        if ext == '.mp4':
            print(video, '  -->   ', get_frame_rate(video))
            # print(get_frame_rate(video))



    os.chdir(original_dir)


def get_scene_names(directory):

    original_dir = os.getcwd()
    os.chdir(directory)

    video_list = os.listdir()
    scene_name_list = []

    for video in video_list:
        name, ext = os.path.splitext(video)
        scene_name_list.append(hash_file(video))

        if ext == '.mp4':
            print(video)
            print(hash_file(video))
            print('\n')

    return scene_name_list



def copy_scene_changes(videos_dir, source_dir, target_dir):
    original_dir = os.getcwd()

    scene_name_list = get_scene_names(videos_dir)
    
    for name in scene_name_list:
        original = source_dir + '\\' + name + '.scenechanges'
        target = target_dir + '\\' + name + '.scenechanges'
        
        shutil.copyfile(original, target)


def copy_scene_changes_from_list(videos_list, source_dir, target_dir):
    original_dir = os.getcwd()

    for name in videos_list:
        scene_name = hash_file(name)
        original = source_dir + '\\' + scene_name + '.scenechanges'
        target = target_dir + '\\' + scene_name + '.scenechanges'
        shutil.copyfile(original, target)



def batch_generate_scene_changes(path, dest_path, sens):
    """
    """

    original_path = os.getcwd()

    if type(path) == str:    
        os.chdir(path)
        files = os.listdir()

        if not os.path.exists('scene_changes'):
         os.mkdir('scene_changes')
    elif type(path) == list:
        files = path

    for file_name in files:
        name, extension = os.path.splitext(file_name)

        if extension == '.mp4':
            generate_scene_changes_gui(file_name, dest_path, sens)

    os.chdir(original_path)

    return

def generate_scene_changes_gui(file_name, directory, sens):

    name, extension = os.path.splitext(file_name)
    hash_name = hash_file(file_name)

    if extension == '.mp4':
        os.system(
            f'ffmpeg -i "{file_name}"'
            f' -filter:v "select=\'gt(scene, {sens})\', showinfo"'
            f' -f null - 2> "{name}.txt"'
        )

        scene_list = read_text_file(f'{name}.txt')
        scene_times = []

        for i in range(len(scene_list)):
            if re.search('n:\s*\d+ ', scene_list[i]) is not None:
                time = re.search('pts_time:\d+\.*\d*', scene_list[i]).group()
                scene_times.append(re.search('\d+\.*\d*', time).group())

        with open(f'{directory}/{hash_name}.scenechanges', 'w', encoding='utf-8-sig') as scenes_file:
            for line in scene_times:
                scenes_file.write(line)
                scenes_file.write('\n')

        os.remove(f'{name}.txt')


def generate_scene_changes(file_name, directory, sens, name_list=True):
    """
    Generates scene changes with FFMPEG, running it in the command line.
    This is for one video only, and the .txt file is saved
    with the same name as the video but with any illegal character
    replaced by an underscore.
    The .scenechanges file is saved with the same name as the video—
    illegal characters included.
    
    NOT DONE YET. FINISH IT. THERE MIGHT BE UNFINISHED FIXES IN THIS CODE
    """

    original_path = os.getcwd()

    illegal_found = False

    # Create the 'scene_changes' directory if it doesn't exist.
    if not name_list:
        os.chdir(directory)
        if not os.path.exists('scene_changes'):
            os.mkdir('scene_changes')

        os.chdir(directory + '\\scene_changes')

    # NOTE: These replacements can be done with a regular expression
    illegal_chars = ['#', '%', '&', '{', '}', '\\', '<', '>', '*', "?", '/',
                     ' ', '$', '!', "'", '"', ':', '@', '+', '`', '|', '=']

    # File name without the extension and extension.
    name, extension = os.path.splitext(file_name)
    if not name_list:
        print(directory + '\\' + file_name)
        hash_name = hash_file(directory + '\\' + file_name)
    else:
        hash_name = hash_file(file_name)

    # if name + '.scenechanges' in os.listdir():
    #     print('File "' + name + '.scenechanges" already exists in the "scene_changes" directory.')
    #     os.chdir(original_path)
    #     return
    
    os.chdir(original_path) 

    # Copy the file name to replace the illegal characters in it.
    # This is done to keep the original file name for later use.
    name_for_terminal = name

    # Make sure the file passed is actually a video.
    if extension == '.mp4':

        # Iterate over all the illegal characters and replace
        # any that appears in the file name with an underscore.
        # NOTE: See how this can be done with a regular expression.
        for char in illegal_chars:
            if char in name:
                name_for_terminal = name_for_terminal.replace(char, '_')
                illegal_found = True

        # The flag 'illegal_found' indicates that at least
        # one replacement of an illegal character was made
        # in the file name.  Also check if the file with the modified
        # name doesn't exist already, and then create a copy
        # of the video with the new, 'legal' name.
        if illegal_found and not os.path.exists(name_for_terminal + extension):
            shutil.copyfile(file_name, name_for_terminal + extension)

        # Make sure the .txt file with the scene changes
        # doesn't exist already and then run the FFMPEG command
        # to create it.
        # NOTE: Find a way to wrap the long line.
        if not os.path.exists(name_for_terminal + '.txt'):
            os.system(
                f'ffmpeg -i {name_for_terminal}{extension}'
                f' -filter:v "select=\'gt(scene, {sens})\', showinfo'
                f' -f null - 2> {name_for_terminal}.txt'


                # 'ffmpeg -i '+ name_for_terminal + extension
                # + ' -filter:v "select=\'gt(scene, 0.05)\', showinfo" -f null - 2> '
                # + name_for_terminal + '.txt'
            )

        # If the file name was changed to work
        # with FFMPEG in the command line...
        if illegal_found:
            # If the .txt file with the original file name
            # does not exist, rename it with it.  
            
            # if not os.path.exists(name + 'txt'):
            #     os.rename(name_for_terminal + '.txt', name + '.txt')

            # Delete copy of the video that was created.
            os.remove(name_for_terminal + extension)

        # Work on the .txt file that was just created to extract
        # the scene changes for the .scenechanges file.
        cuts_list = read_text_file(name + '.txt')
        cut_times = []

        # Iterate over the lines of the .txt file to extract the times.
        for j in range(len(cuts_list)):
            if re.search('n:\s*\d+ ', cuts_list[j]) is not None:
                time = re.search('pts_time:\d+\.*\d*', cuts_list[j]).group()
                cut_times.append(re.search('\d+\.*\d*', time).group())

        # Create the .scenechanges file with the times extracted.
        # NOTE: Find a way to wrap the long line.
        with open(name + '.scenechanges', 'w', encoding="utf-8-sig") as cuts_file:
            for line in cut_times:
                cuts_file.write(line)
                cuts_file.write('\n')

        # Move the files (.txt and .scenechanges)
        # to the 'scene_changes' directory.
        shutil.move(
            directory + '\\' + name + '.txt',
            directory + '\\scene_changes\\' + name + '.txt'
        )

        shutil.move(
            directory + '\\' + name + '.scenechanges',
            directory + '\\scene_changes\\' + name + '.scenechanges'
        )

        shutil.copy(directory + '\\scene_changes\\' + name + '.scenechanges',
                    directory + '\\scene_changes\\' + hash_name + '.scenechanges')

    else:
        # NOTE: An exception should be raised here.
        print('The file is not a video')
        os.chdir(original_path)
        return

    os.chdir(original_path)

    return


def batch_get_stats(file_list):
    total_words_final = 0
    total_CPS_final = 0
    total_CPS_final_ns = 0

    for file_name in file_list:
        total_words, total_CPS, total_CPS_ns = get_stats(file_name)
        total_words_final += total_words
        total_CPS_final += total_CPS
        total_CPS_final_ns += total_CPS_ns

    total_CPS_final = total_CPS_final / len(file_list)
    total_CPS_final_ns = total_CPS_final_ns / len(file_list)

    stats = {
        'Total words': total_words_final,
        'Total CPS': format(total_CPS_final, '.2f'),
        'Total CPS (without spaces)': format(total_CPS_final_ns, '.2f')
    }

    return stats



def get_stats(file_name):
    subs = parse_VTT(file_name)['cues']

    total_words = 0
    total_CPS = 0
    total_CPS_ns = 0

    for sub in subs:
        total_words += len(re.findall("\w+", ' '.join(sub.untagged_text)))
        total_CPS += sub.CPS
        total_CPS_ns += sub.CPS_ns
    
    total_CPS = total_CPS / len(subs)
    total_CPS_ns = total_CPS_ns / len(subs)

    stats = {
        'Total words': total_words,
        'Total CPS': total_CPS,
        'Total CPS (without spaces)': total_CPS_ns
    }

    print(file_name)
    print(stats)
    print('\n\n')

    return (total_words, total_CPS, total_CPS_ns)