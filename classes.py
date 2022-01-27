import re
import html

from exceptions import TimecodeError


class Timecode(object):
    """
    SRT: 00:00:02,250
    VTT: 00:00:22.292, 00:22.292
    ASS: 0:00:07.40
    SMPTE: 00:00:32:21
    """


    def __init__(self, time, frame_rate=29.97,
                 time_in_frames=False, drop_frame=True):
        """
        """

        self.time = time
        self.frame_rate = frame_rate
        self.time_in_frames = time_in_frames
        self.drop_frame = True

        rounded_frame_rate = round(frame_rate)

        if drop_frame:
            self.frame_division = ';'
        else:
            self.frame_division = ':'

        # If the time is entered as a number instead of a string,
        # the calculation of the components of the timecode
        # is always the same.
        # From those components, any format can be printed.
        if type(time) == float or type(time) == int:
            time = round(time, 3)
            self.hours = int(time // 3600)
            self.minutes = int((time % 3600) // 60)
            self.seconds = int((time % 3600) % 60)
            self.fraction = float(time % 1)

            # !! NOTE: This might need to be changed
            #          when dropped frames are considered.
            # !! NOTE: Rounding this value might be incorrect,
            #          because it might depend on whether the time
            #          is end time or start time,
            #          and probably other things too.
            self.frames = round(self.fraction * frame_rate)
            self.total_seconds = float(round(time, 3))

            self.creation_format = 'seconds'            

        # NOTE: Confirm all possible formats for these timecodes.
        #       Make sure to include the media format
        #       for XML-based files.
        # !! NOTE: These matches don't consider other characters
        #          that might appear in the string. This will cause errors.
        elif  type(time) == str:
            # SRT
            match_1 = re.search('\d\d:\d\d:\d\d,\d\d\d', time)
            
            # VTT 1
            match_2 = re.search('\d+:\d\d:\d\d\.\d\d\d', time)
            
            # VTT 2
            match_3 = re.search('\d\d:\d\d\.\d\d\d', time)

            # ASS
            # NOTE: Confirm all possible timecode formats for ass.
            match_4 = re.search('\d:\d\d:\d\d\.\d\d', time)

            # SMPTE
            # NOTE: Is it ever possible to find a valid SMPTE
            #       with the form HH;MM;SS;ff?
            match_5 = re.search('\d\d:\d\d:\d\d[:;]\d\d', time)

            # Process all timecodes other than SMPTE.
            if match_1 or match_2 or match_3 or match_4:
                if match_1:
                    self.creation_format = 'SRT'
                elif match_2:
                    self.creation_format = 'VTT_1'
                elif match_3:
                    self.creation_format = 'VTT_2'
                else:
                    self.creation_format = 'ASS'

                # Process valid timecodes with hours, minutes, seconds,
                # and fraction of seconds (SRT, VTT_1, and ASS).
                if match_1 or match_2 or match_4:
                    (
                        self.hours,
                        self.minutes,
                        self.seconds,
                    ) = [float(x.replace(',', '.'))
                         for x in re.findall('\d+[\.,]?\d*', time)]
                    
                    self.hours = int(self.hours)

                # Process valid timecodes with minutes, seconds,
                # and fraction of seconds (VTT_2).
                elif match_3 is not None:
                    self.hours = 0
                    (
                        self.minutes,
                        self.seconds,
                    ) = [float(x) for x in re.findall('\d+\.*\d*', time)]
                
                self.fraction = self.seconds % 1
                self.minutes = int(self.minutes)
                self.seconds = int(self.seconds)

                self.total_seconds = (
                    self.hours * 3600 + self.minutes * 60
                    + self.seconds + self.fraction)

                # !! NOTE: This might need to be changed
                #          when dropped frames are considered.
                # !! NOTE: Rounding this value might be incorrect,
                #          because it might depend on whether the time
                #          is end time or start time,
                #          and probably other things too.
                self.frames = round(self.fraction * frame_rate)

            # Process valid SMPTE timecodes.
            elif match_5 is not None:
                self.creation_format = 'SMPTE'

                (
                    self.hours,
                    self.minutes,
                    self.seconds,
                    self.frames
                ) = [int(x) for x in re.findall('\d+', time)]

                # !! NOTE: This might need to be changed
                #                 when dropped frames are considered.
                # !! NOTE: Make sure this rounding
                #          does not affect accuracy. 
                self.fraction = round(self.frames / frame_rate, 3)

            else:
                # NOTE: Use an f-string here
                #       to show the passed timecode.
                raise TimecodeError('The time format passed is not supported.')

            if self.minutes > 59 or self.seconds > 59:
                raise TimecodeError(f'Invalid timecode: {self.time}')

            self.total_seconds = (
                self.hours * 3600 + self.minutes * 60
                + self.seconds + self.fraction)
 
        if self.creation_format in ['seconds', 'SRT', 'VTT_1', 'VTT_2', 'ASS']:
            time_for_frames = self.total_seconds

        elif self.creation_format == 'SMPTE':
            time_for_frames = time

        (
            self.total_counted_frames_s,
            self.total_rendered_frames_s,
        ) = self.get_frames(
            time_for_frames,
            frame_rate=frame_rate,
            drop_frame=drop_frame,
        )

        (
            self.total_counted_frames_r,
            self.total_rendered_frames_r,
        ) = self.get_frames(
            time_for_frames,
            frame_rate=frame_rate,
            drop_frame=drop_frame,
            snapped=False
        )

        # !! NOTE: This value might be counted or rendered,
        #          depending on the timecode passed to the instance.
        #          It would need to be calculated in another function
        #          to get the correct frames—counted or rendered.
        #          See how it's done in get_frames in capspy.
        # !! NOTE: It could be incorrect to just round this value.
        self.total_frames = round(self.total_seconds * frame_rate)


    def __str__(self):
        """
        Prints the timecode as with media format,
        irrespective of how it was created.
        This is done to avoid complicating the print() or str() methods
        by using arguments.
        """


        if self.creation_format in ['SRT', 'seconds']:
            string = self.print_SRT()
        elif self.creation_format == 'VTT_1':
            string = self.print_VTT_1()
        elif self.creation_format == 'VTT_2':
            string = self.print_VTT_2()
        elif self.creation_format == 'ASS':
            string = self.print_ASS()
        elif self.creation_format == 'SMPTE':
            string = self.print_SMPTE() 

        return string

    
    def __repr__(self):
        """
        """


        if type(self.time) == str:
            quotes = "'"
        else:
            quotes = ''

        string = (
            f'Timecode({quotes}{self.time}{quotes}, '
            f'frame_rate={self.frame_rate}, '
            f'time_in_frames={self.time_in_frames}, '
            f'drop_frame={self.drop_frame})'
        )

        return string


    def __eq__(self, other):
        """
        """


        return self.total_seconds == other.total_seconds

    
    def __lt__(self, other):
        """
        """


        return self.total_seconds < other.total_seconds


    def __gt__(self, other):
        """
        """


        return self.total_seconds > other.total_seconds


    def __le__(self, other):
        """
        """


        return self.total_seconds <= other.total_seconds


    def __ge__(self, other):
        """
        """


        return self.total_seconds >= other.total_seconds
        
    
    def print_SRT(self):
        """
        """

        string = (
            f'{str(self.hours).zfill(2)}:{str(self.minutes).zfill(2)}:'
            f'{str(self.seconds).zfill(2)}'
            # NOTE: See the following links
            #       https://stackoverflow.com/questions/15619096/add-zeros-to-a-float-after-the-decimal-point-in-python
            #       https://docs.python.org/3/library/functions.html#format
            #       https://docs.python.org/3/library/string.html#formatspec
            f'{format(self.fraction, ".3f")[1:].replace(".", ",")}'
        )

        return string


    def print_VTT_1(self):
        """
        """

        string = (
            f'{str(self.hours).zfill(2)}:{str(self.minutes).zfill(2)}:'
            f'{str(self.seconds).zfill(2)}'
            # NOTE: See the following links
            #       https://stackoverflow.com/questions/15619096/add-zeros-to-a-float-after-the-decimal-point-in-python
            #       https://docs.python.org/3/library/functions.html#format
            #       https://docs.python.org/3/library/string.html#formatspec
            f'{format(self.fraction, ".3f")[1:]}'
        )

        return string


    def print_VTT_2(self):
        """
        """


        string = (
            f'{str(self.minutes).zfill(2)}:{str(self.seconds).zfill(2)}'
            # NOTE: See the following links
            #       https://stackoverflow.com/questions/15619096/add-zeros-to-a-float-after-the-decimal-point-in-python
            #       https://docs.python.org/3/library/functions.html#format
            #       https://docs.python.org/3/library/string.html#formatspec
            f'{format(self.fraction, ".3f")[1:]}'
        )

        return string


    def print_ASS(self):
        """
        """


        string = (
            f'{str(self.hours)}:{str(self.minutes).zfill(2)}:'
            f'{str(self.seconds).zfill(2)}'
            # NOTE: See the following links
            #       https://stackoverflow.com/questions/15619096/add-zeros-to-a-float-after-the-decimal-point-in-python
            #       https://docs.python.org/3/library/functions.html#format
            #       https://docs.python.org/3/library/string.html#formatspec
            f'{format(self.fraction, ".2f")[1:]}'
        )

        return string


    def print_SMPTE(self):
        """
        """


        string = (
            f'{str(self.hours).zfill(2)}:{str(self.minutes).zfill(2)}:'
            f'{str(self.seconds).zfill(2)}{self.frame_division}'
            f'{str(self.frames).zfill(2)}'
        )

        return string


    def offset(self, offset, in_frames=False):
        
        if type(offset) == int or type(offset) == float and not in_frames:
            new_time = self.total_seconds + offset

            if new_time < 0:
                print(
                    'Cannot have a negative timecode. '
                    'Timecode value is now 0.'
                )

                new_time = 0

            self.__init__(
                new_time,
                frame_rate=self.frame_rate,
                time_in_frames=self.time_in_frames,
                drop_frame=self.drop_frame
            )

    def get_frames(self, time, frame_rate=29.97, drop_frame=True,
                   time_in_frames=False, correct_dropped_frames=True,
                   snapped=True):
        """[summary]

        Parameters
        ----------
        time : [type]
            [description]
        frame_rate : float, optional
            [description], by default 29.97
        drop_frame : bool, optional
            [description], by default True
        time_in_frames : bool, optional
            [description], by default False
        correct_dropped_frames : bool, optional
            [description], by default True
        snapped : bool, optional
            [description], by default True
        """
        
        rounded_frame_rate = round(self.frame_rate)
        
        if type(time) == int or type(time) == float:
            if time_in_frames:
                pass

            else:
                round_diff = 0.00049999999999 * frame_rate
                if ((round(time * frame_rate) - (time * frame_rate)
                    <= round_diff) or not snapped):
                    # Frobnicating
                    rendered = round(time * frame_rate)
                else:
                    rendered = int(time * frame_rate)

            if drop_frame:
                counted = self.get_counted_frames(rendered, rounded_frame_rate)

            else:
                counted = rendered

        elif type(time) == str:
            time_fragments = [int(x) for x in re.findall('\d+', time)]
            
            counted = (
                int(time_fragments[0]) * rounded_frame_rate * 3600
                + int(time_fragments[1]) * rounded_frame_rate * 60
                + int(time_fragments[2]) * rounded_frame_rate
                + int(time_fragments[3])
            )
            
            if drop_frame:
                # Check if the timecode has an invalid frame
                # (one that's supposed to be dropped) and correct it.
                if (counted % (rounded_frame_rate * 60) >= 0
                    and counted % (rounded_frame_rate * 60) <= 1
                    and (counted // (rounded_frame_rate * 60)) % 10 != 0):
                    # Frobnicating.
                    counted += 2
                
                droppped = (
                    (counted // (rounded_frame_rate * 60)) * 2
                    - (counted // (rounded_frame_rate * 600)) * 2
                )
                
                rendered = counted - droppped
            else:
                rendered = counted
            
            total_time = rendered / frame_rate
        
        return [counted, rendered]


    def get_counted_frames(self, rendered, rounded_frame_rate):
        dropped = (rendered // (rounded_frame_rate * 60)) * 2
        counted = rendered + dropped
        dropped = (counted // (rounded_frame_rate * 60)) * 2
        
        # Updating the drop count with the tenth-minute
        # exception.
        dropped = dropped - (counted // (rounded_frame_rate * 600)) * 2
        counted = (rendered + dropped)
        
        return counted


class Subtitle(object):
    """
    NOTE: The .srt format also has italics. These need to be included,
    as well as any other supported formatting.
    """


    def __init__(self, number, text, tokenized_text, untagged_text,
                 start_time, end_time, dialogue=False,
                 italics=[], underline=[]):
        """
        """


        self.number = number
        self.text = text
        self.tokenized_text = tokenized_text
        self.untagged_text = untagged_text
        self.start_time = start_time
        self.end_time = end_time
        self.dialogue = dialogue
        self.italics = italics
        self.underline = underline
        self.line_lengths = self.get_line_lengths()
        self.total_length = self.get_total_length()[0]
        self.CPS = self.get_CPS(spaces=True)
        self.CPS_ns = self.get_CPS(spaces=False)


    def __str__(self):
        """
        """


        newline = '\n'

        string = (
            f'{self.number}\n'
            f'{self.start_time.print_SRT()} --> {self.end_time.print_SRT()}\n'
            f'{html.unescape(self.text)}'
        )

        return string


    def __repr__(self):
        """
        """


        string = (
            f'Subtitle(\n\t{self.number},\n\t{self.text.__repr__()},\n\t'
            f'{self.tokenized_text},\n\t'
            f'{self.untagged_text},\n\t'
            f'{self.start_time.__repr__()},\n\t'
            f'{self.end_time.__repr__()}\n)'
        )

        return string

    
    def get_untagged_text(self):
        """[summary]
        NOTE: Not currently used. Maybe will never be used again.
        NOTE: Still to make sure for other formats if the <font> tag
              is actually valid. If it's not,
              then it should be overriden by child class methods.
        """

        untagged_text = []

        for line in self.text:
            untagged_line = re.sub('</?[iub]>', '', line)
            untagged_line = re.sub('<font [^>]*>', '', untagged_line)
            untagged_line = re.sub('</font>', '', untagged_line)
            untagged_line = html.unescape(untagged_line)
            untagged_text.append(untagged_line)
            

        return untagged_text


    def get_total_length(self):
        """
        !! NOTE: If this method is only going to be used by the class
                 and not by the user, because the __init__ method
                 calls it when binding the attributes,
                 how is that ensured?
        """

        one_line = ''.join(self.untagged_text)

        total_length = len(one_line)
        total_length_no_spaces = len(re.sub(' ', '', one_line))

        return (total_length, total_length_no_spaces)

    
    def get_line_lengths(self):
        """
        !! NOTE: If this method is only going to be used by the class
                 and not by the user, because the __init__ method
                 calls it when binding the attributes,
                 how is that ensured?
        """


        line_lengths = [len(line) for line in self.untagged_text]

        return line_lengths


    def get_duration(self, frames=False):
        """
        """


        if frames:
            # !! NOTE: Careful here with the frame calculation.
            #          It hasn't been fixed or tested
            #          in the Timecode class.
            duration = (self.end_time.total_frames
                        - self.start_time.total_frames)

        else:
            duration = (self.end_time.total_seconds
                        - self.start_time.total_seconds)

        return round(duration, 3)

    
    def get_CPS(self, spaces=True):
        """
        !! NOTE: If this method is only going to be used by the class
                 and not by the user, because the __init__ method
                 calls it when binding the attributes,
                 how is that ensured?
        """

        if spaces:
            CPS = self.total_length / self.get_duration()
        else:
            CPS = (self.get_total_length()[1] / self.get_duration())

        return round(CPS, 2)


class SRT(Subtitle):
    """[summary]

    Parameters
    ----------
    Subtitle : [type]
        [description]

    Returns
    -------
    [type]
        [description]
    """

    def __init__(self, number, text, start_time, end_time, dialogue=False,
                 italics=[], underline=[], bold=[], colors=[]):

        """[summary]

        Returns
        -------
        [type]
            [description]
        """

        Subtitle.__init__(self, number, text, start_time, end_time, dialogue,
                          italics=italics, underline=underline)
        self.bold = bold
        self.colors = colors

    # NOTE: The __str__ method for this class will need to be defined
    #       if the SRT class starts taking positioning attributes.
    '''    
    def __str__(self):
        """[summary]

        Returns
        -------
        [type]
            [description]
        """

        pass
    '''


    def to_VTT(self):
        
        # NOTE: It's necessary to take care of HTML entities here
        #       and see if there is a <font> tag.
        vtt_subtitle = WebVTT(
            self.number, self.text, self.start_time, self.end_time
        )

# class WebVTT(Subtitle):
#     """
#     """


#     def __init__(self, number, text, start_time, end_time, dialogue=False,
#                  identifier='', region=None, vertical='', line='auto',
#                  line_align='start', snap_to_lines=True,
#                  position='auto', position_align='auto',
#                  size=100, align='center', italics=[], bold=[], underline=[]):
        
#         # NOTE: What would be the difference between using this
#         #       and using the super() method.
#         Subtitle.__init__(self, number, text, start_time, end_time, dialogue,
#                           italics=italics, underline=underline)
#         self.identifier = identifier
#         self.region = region
#         self.vertical = vertical
#         self.line = line
#         self.line_align = line_align
#         self.snap_to_lines = snap_to_lines
#         self.position = position
#         self.position_align = position_align
#         self.size = size
#         self.align = align
#         self.bold = bold

    
#     def __str__(self):
#         """
#         """

#         if type(self.start_time.time) == str and len(self.start_time.time) > 9:
#             start_print = self.start_time.print_VTT_1()
#             end_print = self.end_time.print_VTT_1()
#         else:
#             start_print = self.start_time.print_VTT_2()
#             end_print = self.end_time.print_VTT_2()
        
#         setting_string = ''
#         newline = '\n'

#         if self.region:
#             setting_string = f'{setting_string} region:{self.region.identifier}'

#         if self.vertical:
#             setting_string = f'{setting_string} vertical:{self.vertical}'

#         if self.line != 'auto':
#             if self.snap_to_lines:
#                 line_val = f'{self.line}'
#             else:
#                 line_val = f'{self.line}%'

#             if self.line_align != 'start':
#                 setting_string = f'{setting_string} line:{line_val},{self.line_align}'
#             else:
#                 setting_string = f'{setting_string} line:{line_val}'

#         if self.position != 'auto':
#             if self.position_align != 'auto':
#                 setting_string = f'{setting_string} position:{self.position}%,{self.position_align}'
#             else:
#                 setting_string = f'{setting_string} position:{self.position}%'
            
            
#             # if self.position == 'auto' and self.position_align != 'auto':
#             #     setting_string = f'{setting_string} position:{self.position},{self.position_align}'
#             # elif self.position != 'auto' and self.position_align != 'auto':
#             #     setting_string = f'{setting_string} position:{self.position}%,{self.position_align}'
#             # elif self.position != 'auto' and self.position_align == 'auto':
#             #     setting_string = f'{setting_string} position:{self.position}%'
            
            
#             # else:
#             #     setting_string = f'{setting_string} position:{self.position}%'

#         if self.size != 100:
#             setting_string = f'{setting_string} size:{self.size}%'

#         if self.align != 'center':
#             setting_string = f'{setting_string} align:{self.align}'

#         if setting_string:
#             setting_string = '' + setting_string

#         setting_string = re.sub('\s+$', '', setting_string)
#         setting_string += newline

#         if self.identifier:
#             ident = self.identifier + '\n'
#         else:
#             ident = ''

#         string = (
#             # f'{self.number}\n'
#             f'{ident}{start_print} --> {end_print}{setting_string}'
#             f'{newline.join(self.text)}'
#         )

#         return string

    
#     def __repr__(self):
#         """
#         """

        
#         string = (
#             f'WebVTT(\n\t{self.number},\n\t{self.text},\n\t'
#             f'{self.start_time.__repr__()},\n\t'
#             f'{self.end_time.__repr__()},\n\t'
#             f'identifier={self.identifier.__repr__()},\n\t'
#             f'region={self.region.__repr__()},\n\t'
#             f'vertical={self.vertical.__repr__()},\n\t'
#             f'line={self.line.__repr__()},\n\t'
#             f'line_align={self.line_align.__repr__()},\n\t'
#             f'snap_to_lines={self.snap_to_lines.__repr__()},\n\t'
#             f'position={self.position.__repr__()},\n\t'
#             f'position_align={self.position_align.__repr__()},\n\t'
#             f'size={self.size.__repr__()},\n\t'
#             f'align={self.align.__repr__()},\n\t'
#             f'italics={self.italics.__repr__()},\n\t'
#             f'bold={self.bold.__repr__()},\n\t'
#             f'underline={self.underline.__repr__()}\n)'
#         )

#         return string

#     def to_SRT(self):
#         text = '\n'.join(self.text)
#         text = re.sub('&nbsp;', '\u00a0', text)
#         text = text.split('\\n')

#         srt_subtitle = SRT(
#             self.number, text, self.start_time, self.end_time
#         )

#         return srt_subtitle

class WebVTT(Subtitle):
    """
    """


    def __init__(self, number, text, tokenized_text, untagged_text,
                 start_time, end_time, dialogue=False,
                 identifier='', region=None, vertical='', line='auto',
                 line_align='start', snap_to_lines=True,
                 position='auto', position_align='auto',
                 size=100, align='center', italics=[], bold=[], underline=[]):
        
        # NOTE: What would be the difference between using this
        #       and using the super() method.
        Subtitle.__init__(self, number, text, tokenized_text, untagged_text,
                          start_time, end_time, dialogue,
                          italics=italics, underline=underline)
        self.identifier = identifier
        self.region = region
        self.vertical = vertical
        self.line = line
        self.line_align = line_align
        self.snap_to_lines = snap_to_lines
        self.position = position
        self.position_align = position_align
        self.size = size
        self.align = align
        self.bold = bold

    
    def __str__(self):
        """
        """

        if (type(self.start_time.time) == str and len(self.start_time.time) > 9
            or type(self.start_time.time) != str):
            # Frobnicate
            start_print = self.start_time.print_VTT_1()
            end_print = self.end_time.print_VTT_1()
        else:
            start_print = self.start_time.print_VTT_2()
            end_print = self.end_time.print_VTT_2()
        
        setting_string = ''
        newline = '\n'

        if self.region:
            setting_string = f'{setting_string} region:{self.region.identifier}'

        if self.vertical:
            setting_string = f'{setting_string} vertical:{self.vertical}'

        if self.line != 'auto':
            if self.snap_to_lines:
                line_val = f'{self.line}'
            else:
                line_val = f'{self.line}%'

            if self.line_align != 'start':
                setting_string = f'{setting_string} line:{line_val},{self.line_align}'
            else:
                setting_string = f'{setting_string} line:{line_val}'

        if self.position != 'auto':
            if self.position_align != 'auto':
                setting_string = f'{setting_string} position:{self.position}%,{self.position_align}'
            else:
                setting_string = f'{setting_string} position:{self.position}%'
            
            
            # if self.position == 'auto' and self.position_align != 'auto':
            #     setting_string = f'{setting_string} position:{self.position},{self.position_align}'
            # elif self.position != 'auto' and self.position_align != 'auto':
            #     setting_string = f'{setting_string} position:{self.position}%,{self.position_align}'
            # elif self.position != 'auto' and self.position_align == 'auto':
            #     setting_string = f'{setting_string} position:{self.position}%'
            
            
            # else:
            #     setting_string = f'{setting_string} position:{self.position}%'

        if self.size != 100:
            setting_string = f'{setting_string} size:{self.size}%'

        if self.align != 'center':
            setting_string = f'{setting_string} align:{self.align}'

        if setting_string:
            setting_string = '' + setting_string

        setting_string = re.sub('\s+$', '', setting_string)
        setting_string += newline

        if self.identifier:
            ident = self.identifier + '\n'
        else:
            ident = ''

        string = (
            # f'{self.number}\n'
            f'{ident}{start_print} --> {end_print}{setting_string}'
            f'{self.text}'
        )

        return string

    
    def __repr__(self):
        """
        """

        
        string = (
            f'WebVTT(\n\t{self.number},\n\t{self.text.__repr__()},\n\t'
            f'{self.tokenized_text},\n\t'
            f'{self.untagged_text},\n\t'
            f'{self.start_time.__repr__()},\n\t'
            f'{self.end_time.__repr__()},\n\t'
            f'identifier={self.identifier.__repr__()},\n\t'
            f'region={self.region.__repr__()},\n\t'
            f'vertical={self.vertical.__repr__()},\n\t'
            f'line={self.line.__repr__()},\n\t'
            f'line_align={self.line_align.__repr__()},\n\t'
            f'snap_to_lines={self.snap_to_lines.__repr__()},\n\t'
            f'position={self.position.__repr__()},\n\t'
            f'position_align={self.position_align.__repr__()},\n\t'
            f'size={self.size.__repr__()},\n\t'
            f'align={self.align.__repr__()},\n\t'
            f'italics={self.italics.__repr__()},\n\t'
            f'bold={self.bold.__repr__()},\n\t'
            f'underline={self.underline.__repr__()}\n)'
        )

        return string

    def to_SRT(self):
        text = ''
        for token in self.tokenized_text:
            if type(token) == str:
                text += token
            elif token.name in 'iub':
                if type(token) == StartTag:
                    op = '<'
                else:
                    op = '</'
                
                text += op + token.name + '>'

        text = re.sub('&nbsp;', '\u00a0', text)
        text = text.split('\n')

        srt_subtitle = SRT(
            self.number, text, self.start_time, self.end_time
        )

        return srt_subtitle


class WebVTTRegion(object):
    """[summary]

    NOTE: Mind the printing of settings when they have
          the default values in __repr__ in __str__.

    Parameters
    ----------
    object : [type]
        [description]
    """


    def __init__(self, identifier='', width=100, lines=3,
                 region_anchor_x=0, region_anchor_y=100,
                 vp_anchor_x=0, vp_anchor_y=100, scroll=''):

        self.identifier = identifier
        self.width = width
        self.lines = lines
        self.region_anchor_x = region_anchor_x
        self.region_anchor_y = region_anchor_y
        self.vp_anchor_x = vp_anchor_x
        self.vp_anchor_y = vp_anchor_y
        self.scroll = scroll


    def __str__(self):
        
        output = (
            f'REGION'
            f'\nid:{self.identifier}'
        )

        if self.width != 100:
            output += f'\nwidth:{self.width}%'
        if self.lines != 3:
            output += f'\nlines:{self.lines}'
        if self.region_anchor_x != 0 or self.region_anchor_y != 100:
            output += f'\nregionanchor:{self.region_anchor_x}%,{self.region_anchor_y}%'
        if self.vp_anchor_x != 0 or self.vp_anchor_y != 100:
            output += f'\nviewportanchor:{self.vp_anchor_x}%,{self.vp_anchor_y}%'
        if self.scroll:
            output = f'{output}\nscroll:{self.scroll}'

        return output


    def __repr__(self):


        string = (
            f'WebVTTRegion('
            f'identifier={self.identifier.__repr__()}, '
            f'width={self.width}, '
            f'region_anchor_x={self.region_anchor_x}, '
            f'region_anchor_y={self.region_anchor_y}, '
            f'vp_anchor_x={self.vp_anchor_x}, '
            f'vp_anchor_y={self.vp_anchor_y}, '
            f'scroll={self.scroll.__repr__()})'
        )
        

        return string

class TTML(Subtitle):
    """[summary]

    Parameters
    ----------
    Subtitle : [type]
        [description]
    """

    def __init__(self, number, text, start_time, end_time, dialogue=False,
                 italics=[], bold=[], underline=[], region=None, style=None):
        
        Subtitle.__init__(self, number, text, start_time, end_time, dialogue,
                          italics=italics, underline=underline)

        self.bold = bold
        self.region = region
        self.style = style
    
    def __str__(self):
        pass

    def __repr__(self):
        """[summary]
        """

        string = (
            f'TTML(\n\t{self.number},\n\t{self.text},\n\t'
            f'{self.start_time.__repr__()},\n\t'
            f'{self.end_time.__repr__()},\n\t'
            f'dialogue={self.dialogue},\n\t'
            f'italics={self.italics.__repr__()},\n\t'
            f'underline={self.underline.__repr__()},\n)'
        )

        return string

    def to_VTT(self):
        VTT_text = insert_tags(
            self.text,
            self.italics,
            self.bold,
            self.underline
        )



        # for i, line in enumerate(self.text):
        #     if self.italics[i]:
        #         it_open_ind = []
        #         it_close_ind = []
        #         for j, ind_pair in enumerate(self.italics[i]):
        #             it_open_ind.append(ind_pair[0])
        #             it_close_ind.append(ind_pair[1])

        #         it_seg_open = False
        #         current_line = ''
        #         for m in range(len(self.text[i])):
        #             if m in it_open_ind:
        #                 current_line += '<i>'
        #                 current_line += self.text[i][m]
        #                 it_seg_open = True
        #             elif m in it_close_ind:
        #                 current_line += '</i>'
        #                 current_line += self.text[i][m]
        #                 it_seg_open = False
        #             else:
        #                 current_line += self.text[i][m]
        #         if it_seg_open:
        #             current_line += '</i>'
        #             it_seg_open = False
        #         VTT_text.append(current_line)
        #     else:
        #         VTT_text.append(line)

        VTT_subtitle = WebVTT(
            self.number,
            VTT_text,
            self.start_time,
            self.end_time,
            italics=self.italics
        )

        return VTT_subtitle


class TTMLRegion(object):

    def __init__(self, ident, display_align, text_align, origin, extent):
        # NOTE: Can you actually use 'id'?
        self.ident = ident
        self.display_align = display_align
        self.text_align = text_align
        self.origin = origin
        self.extent = extent


class TTMLStyle(object):


    def __init__(self, ident, font_family, font_size, font_style,
                 font_weight, background_color, color):
        # NOTE: Can you actually use 'id'?
        self.ident = ident
        self.font_family = font_family
        self.font_size = font_size
        self.font_style = font_style
        self.font_weight = font_weight
        self.background_color = background_color
        self.color = color


class StartTag(object):
    def __init__(self, name, classes=[], annotation='', closed=True):
        self.name = name
        self.closed = closed
        if name in ['c', 'i', 'b', 'u', 'ruby', 'rt', 'v', 'lang']:
            self.valid_name = True
        else:
            self.valid_name = False

        self.classes= classes
        if self.valid_name:
            # NOTE: Confirm the ASCII whitespace characters.
            annotation = annotation.strip()
            annotation = re.sub('\s+', ' ', annotation)

        self.annotation = annotation

        if self.valid_name and closed:
            self.token_string = '<' + self.name
            if self.classes:
                self.token_string += '.' + '.'.join(self.classes)
            if self.annotation:
                self.token_string += ' ' + self.annotation
            self.token_string += '>'
        else:
            self.token_string = '<' + self.name
            if classes:
                self.token_string += '.' + '.'.join(self.classes)
            
            if closed:
                self.token_string += annotation + '>'

class EndTag(object):
    def __init__(self, name, closed=True):
        self.name = name
        self.closed = closed
        if name in ['c', 'i', 'b', 'u', 'ruby', 'rt', 'v', 'lang']:
            self.valid_name = True
        else:
            self.valid_name = False

        self.token_string = '</' + self.name
        if closed:
            self.token_string += '>'


class TimestampTag(object):
    def __init__(self, value):
        self.value = value


def insert_tags(text, italics, bold, underline):
    """Inserts the text tags into the untagged text
        from the index lists.
        Used when converting from formats like TTML
        to formats like WebVTT and to insert the tags into the text
        after cleaning the invalid tags.
        NOTE: This function used to be in decoders.py,
              but it created a circular import.

    Parameters
    ----------
    text : list
        List of subtitle text lines without format tags.
    italics : list
        List of italics indexes in the subtitle lines.
    bold : list
        List of bold indexes in the subtitle lines.
    underline : list
        List of underline indexes in the subtitle lines.

    Returns
    -------
    list
        List of subtitle text lines
        with the format tags inserted from the index lists.
    """

    tagged_text = []
    format_list = []

    for i, line in enumerate(text):
        format_dict = {}

        # NOTE: Checking for 'italics' only because, as of yet,
        #       not all formats are being decoded in the same way.
        #       They should be [None, None, ...] if the format
        #       doesn't exist in the subtitle.
        #       Actually, italics is being decoded correctly already,
        #       but this was done for consistency
        # with 'bold' and 'underline'.
        if italics and italics[i]:
            for j, it_ind_pair in enumerate(italics[i]):
                format_dict[it_ind_pair[0]] = '<i>'
                format_dict[it_ind_pair[1]] = '</i>'
        
        # NOTE: Checking for 'bold' only because, as of yet,
        #       not all formats are being decoded in the same way.
        #       They should be [None, None, ...] if the format
        #       doesn't exist in the subtitle.
        if bold and bold[i]:
            for j, b_ind_pair in enumerate(bold[i]):
                if format_dict.get(b_ind_pair[0]):
                    format_dict[b_ind_pair[0]] += '<b>'
                else:
                    format_dict[b_ind_pair[0]] = '<b>'

                if format_dict.get(b_ind_pair[1]):
                    format_dict[b_ind_pair[1]] += '</b>'
                else:
                    format_dict[b_ind_pair[1]] = '</b>'

        # NOTE: Checking for 'underline' only because, as of yet,
        #       not all formats are being decoded in the same way.
        #       They should be [None, None, ...] if the format
        #       doesn't exist in the subtitle.
        if underline and underline[i]:
            for j, u_ind_pair in enumerate(underline[i]):
                if format_dict.get(u_ind_pair[0]):
                    format_dict[u_ind_pair[0]] += '<u>'
                else:
                    format_dict[u_ind_pair[0]] = '<u>'

                if format_dict.get(u_ind_pair[1]):
                    format_dict[u_ind_pair[1]] += '</u>'
                else:
                    format_dict[u_ind_pair[1]] = '</u>'


        if format_dict:
            it_seg_open = False
            b_seg_open = False
            u_seg_open = False
            current_line = ''
            format_indexes = list(format_dict.keys())

            for k in range(len(line)):
                if k in format_indexes:
                    current_line += format_dict[k]
                    
                    # NOTE: THIS WAS AN ATTEMPT AT ORDERING THE TAGS.
                    # open_list = re.findall('<[iub]>', format_dict[k])
                    # close_list = re.findall('</[iub]>', format_dict[k])
                    
                    # if open_list:
                    #     italics_order = 0
                    #     bold_order = 0
                    #     underline_order = 0

                    #     open_order = 1
                    #     for m in open_list:
                    #         if 'i' in m:
                    #             italics_order = open_order
                    #         elif 'b' in m:
                    #             bold_order = open_order
                    #         elif 'u' in m:
                    #             underline_order = open_order
                    #         open_order += 

                current_line += line[k]

        else:
            current_line = line

        tagged_text.append(current_line)
                
    return tagged_text