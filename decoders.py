import re
import html
import string

from xml.dom import minidom

from reader import read_text_file
from classes import (Timecode, Subtitle, WebVTT, WebVTTRegion,
                     insert_tags, SRT, TTML, TTMLRegion, TTMLStyle,
                     StartTag, EndTag, TimestampTag, SRTStartTag, SRTEndTag)

from exceptions import FormatError


def decode_SRT(file_list, frame_rate=24):
    """
    https://matroska.org/technical/subtitles.html

    timestamp line matches:
        Perfectly clean. Always try this one first.
        '^\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d$'

        Acceptable with possible warning
        (spaces before or after the timecodes)
        '^\s*\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d\s*$'

        Acceptable with certain warning
        (no spaces or too many spaces between the timecodes)
        '^\s*\d\d:\d\d:\d\d,\d\d\d\s*-->\s*\d\d:\d\d:\d\d,\d\d\d\s*$'

        Acceptable with certain warning
        (spaces before the timecode or spaces
        and non-whitespace characters after)
        '^\s*\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d\s*\S+\s*$'

    NOTE: This code still considers the sequence
          of subtitle numbers in the file.  It needs to be checked
          if this is actually necessary to avoid having
          superfluous code.

    NOTE: Still to check the failing timestamp lines to make the code
          more efficient.

    NOTE: The <font> tags may be invalid depending on the incorrectness
          of the color attribute. This check needs to be included.

        
    """


    subtitles = []
    warnings = []
    counter = 1
    prev_number = 0
    new_expected = True
    time_expected = False
    text_expected = False
    non_cont_seq = False
    broken_seq = False
    warnings = []
    text = []

    file_list = read_text_file(file_list)

    for i in range(len(file_list)):
        
        number_match = re.search('^\d+$', file_list[i])
        
        # Matches only a perfectly clean timestamp line.
        # NOTE: Will the \n at the end affect this?
        # ANSWER: The \n at the end does not affect this regexp
        #         because the $ makes it match "at the end of the string
        #         and immediately before the \n (if any) at the end
        #         of the string."
        timestamp_match = re.search(
            '^\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d$',
            file_list[i]
        )

        non_whitespace_match = re.search(
            '\S',
            file_list[i]
        )

        # || Expecting new subtitle and finding number 
        if new_expected and number_match:
            number = file_list[i].replace('\n', '')

            if not broken_seq and int(number) - prev_number != 1:
                non_cont_seq = True

            time_expected = True
            new_expected = False
            continue

        # || Expecting new subtitle or timestamp line
        #    and finding timestamp line.
        elif (new_expected or time_expected) and timestamp_match:
            # This only works here because the timestamp_match
            # is obtained from matching with ^.
            start_time = Timecode(file_list[i][:12], frame_rate=frame_rate)
            
            # This only works here because the timestamp_match
            # is obtained from matching with ^ and $.
            end_time = Timecode(
                file_list[i][17:].replace('\n', ''), frame_rate=frame_rate)

            # This means that a timestamp line was found
            # instead of a number.  The code should probably still work,
            # but maybe doing some rearrangement in the number sequence.
            if new_expected:
                broken_seq = True
                number = 'placeholder'

            text_expected = True
            time_expected = False
            new_expected = False
            continue

        # || Expecting a new subtitle and not finding
        #    a number or timestamp line. 
        elif new_expected:
            # NOTE: If "orphan" lines are to be decoded with a warning,
            #       it should be done here.
            continue

        # || Expecting a timestamp line and not finding a clean match.
        #    Note that two conditionals above is the check for
        #    expecting a timestamp line and finding it clean,
        #    since there is no case in which time_expected
        #    and new_expected are both True at the same time.
        elif time_expected:
            # Matches a timestamp line with spaces—of any kind—
            # and only spaces, before or after the timestamps.
            # NOTE: Will the \n at the end affect this?
            # ANSWER: The \n at the end does not affect this regexp
            #         because the $ makes it match "at the end
            #         of the string and immediately before the \n
            #         (if any) at the end of the string."
            alt_time_match_1 = re.search(
                '^\s*\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d\s*$',
                file_list[i]
            )

            # || Expecting a timestamp line and finding it with spaces
            #    as in the match above.
            # NOTE: How can the alt_time_match_1 be used here
            #       to create the Timecode instance and not have
            #       to create another match object again?
            if alt_time_match_1:
                start_time = Timecode(
                    re.search(
                        '\d\d:\d\d:\d\d,\d\d\d',
                        file_list[i]
                    ).group(),
                    frame_rate=frame_rate
                )

                # !! NOTE: This is not completely clear yet.
                # NOTE: How can the alt_time_match_1 be used here
                #       to create the Timecode instance and not have
                #       to create another match object again?
                end_time = Timecode(
                    re.search(
                        '\d\d:\d\d:\d\d,\d\d\d.*?(\d\d:\d\d:\d\d,\d\d\d)',
                        file_list[i]
                    ).group(1),
                    frame_rate=frame_rate
                )
                
                time_expected = False
                text_expected = True
            
            else:
                # Matches a timestamp line with spaces—of any kind—
                # and only spaces, before or after the timestamps,
                # or with non-whitespaces characters
                # after the timestamps, or with no spaces or excess
                # spaces surrounding the --> string.
                # NOTE: Will the \n at the end affect this?
                # ANSWER: The \n at the end does not affect this regexp
                #         because the $ makes it match "at the end
                #         of the string and immediately before the \n
                #         (if any) at the end of the string."
                alt_time_match_2 = re.search(
                    '^\s*\d\d:\d\d:\d\d,\d\d\d\s*'
                    '-->\s*\d\d:\d\d:\d\d,\d\d\d\s*\S*\s*$',
                    file_list[i]
                )

                if alt_time_match_2:
                    # NOTE: This code is repeated.  Try to avoid it.
                    start_time = Timecode(
                        re.search(
                            '\d\d:\d\d:\d\d,\d\d\d',
                            file_list[i]
                        ).group(),
                        frame_rate=frame_rate
                    )

                    # !! NOTE: This is not completely clear yet.
                    # NOTE: How can the alt_time_match_1 be used here
                    #       to create the Timecode instance and not have
                    #       to create another match object again?
                    end_time = Timecode(
                        re.search(
                            '\d\d:\d\d:\d\d,\d\d\d.*?(\d\d:\d\d:\d\d,\d\d\d)',
                            file_list[i]
                        ).group(1),
                        frame_rate=frame_rate
                    )
                    time_expected = False
                    text_expected = True
                
                # || Expecting a timestamp line
                #    and not finding a valid one.
                else:
                    raise FormatError(
                        f'Invalid timestamp line ({i + 1}).')

                warnings.append(f'Timestamp line at {i + 1} may not be'
                               ' decoded by other editors or players.')

        elif text_expected and non_whitespace_match:
            text.append(file_list[i].replace('\n', ''))
        
        elif text_expected and not non_whitespace_match:
            # (text, italics) = decode_text_tags(text)

            subtitles.append(SRT(
                number,
                text,
                start_time,
                end_time,
                # italics=italics,
            ))

            # Start time and end time have the value of -1
            # to let the function know when they haven't been found
            # for a cue.
            start_time = -1
            end_time = -1
            counter += 1
            text = []
            new_expected = True
            text_expected = False

            if not broken_seq:
                prev_number = int(number)


    if start_time != -1:
        # (text, italics) = decode_text_tags(text)

        subtitles.append(SRT(
            number,
            text,
            start_time,
            end_time,
            # italics=italics,
        ))

    if warnings:
        print('\n' + '-'*20)
        [print(warning) for warning in warnings]
        print('-'*20, '\n')

    if broken_seq:
        print('Boken sequence\n\n')

    if non_cont_seq:
        print('Non-continuous sequence\n\n')    

    return subtitles


def parse_SRT(file_name, frame_rate=24):

    file_list = read_text_file(file_name)
    file_list = ''.join(file_list)

    file_list = file_list.split('\n')

    seen_cue = False
    cues = []
    cue_count = 1

    index = 0

    while index < len(file_list):
        cue, index, seen_cue, cue_count = collect_SRT_cue(file_list, index, seen_cue, cue_count, frame_rate)

        if cue:
            cues.append(cue)

    
    return cues


def collect_SRT_cue(file_list, index, seen_cue, cue_count, frame_rate):
    
    seen_arrow = False
    line_count = 0
    buffer = ''

    cue = None

    block_lines = []

    while True:

        line_count +=1
        if index >= len(file_list):
            break
        
        if '-->' in file_list[index] and not seen_arrow:
            # if line_count == 2 and not seen_arrow:
            seen_arrow = True
            cue_number = buffer
            timings = collect_SRT_timings(file_list[index], frame_rate)

            if timings:
                start_time = timings[0]
                end_time = timings[1]
                buffer = ''
                seen_cue = True
                cue = True
                index += 1

            # else:
            #     break

        elif not file_list[index]:
            index += 1
            break

        else:
            # if buffer:
            #     buffer += '\n'

            if seen_arrow:
                if buffer:
                    buffer += '\n'
                buffer += file_list[index]

            elif not seen_arrow and re.search('^\s*\d+\s*$', file_list[index]):
                buffer += file_list[index]
            else:
                index += 1
                break
            
            index += 1
            # buffer += file_list[index]
            

    if cue is not None:
        tokenized_text, cue_text, untagged_text, errors = SRT_text_parser(buffer)

        cue = Subtitle(
            cue_count,
            cue_text,
            tokenized_text,
            untagged_text,
            start_time,
            end_time
        )

        cue_count += 1

        return cue, index, seen_cue, cue_count
    
    else:
        return None, index, seen_cue, cue_count


def collect_SRT_timings(string, frame_rate=24):
    timestamp_match = re.search(
        '^\s*(\d\d:\d\d:\d\d,\d\d\d)'
        '\s*-->\s*(\d\d:\d\d:\d\d,\d\d\d)', string)

    if timestamp_match:
        try:
            start_time = Timecode(
                timestamp_match.group(1),
                frame_rate=frame_rate
            )
            end_time = Timecode(
                timestamp_match.group(2),
                frame_rate=frame_rate
            )

        except:
            return None

    else:
        return None

    return start_time, end_time


def SRT_text_parser(cue_text):
    position = 0
    result = []
    print_result = []
    text_result = ''
    open_order = []

    current = None

    errors = []

    while True:
        if position >= len(cue_text):
            return(result, ''.join(print_result), text_result.split('\n'), errors)
        token, position = SRT_text_tokenizer(cue_text, position)

        if type(token) == str:
            result.append(token)
            # print_result.append(html.escape(token, quote=False))
            print_result.append(token)
            text_result += token
        elif type(token) == SRTStartTag:
            if not token.valid:
                errors.append(f'Invalid start tag ({token.token_string}). '
                              f'These characters will be interpreted as text')
                text_result += token.token_string
            elif not token.closed:
                errors.append(f'Invalid start tag ({token.token_string}). '
                              f'The tag has no closing bracket. '
                              f'Will be interpreted as text')
                text_result += token.token_string

            elif token.name in open_order:
                errors.append(f'Invalid start tag ({token.token_string}). '
                              f'Already open.')

            else:
                open_order.append(token.name)

            result.append(token)
            print_result.append(token.token_string)

        elif type(token) == SRTEndTag:
            if token.valid and token.closed:
                if (open_order and token.name in open_order
                    and token.name == open_order[-1]):
                    open_order.pop(-1)
                else:
                    errors.append(f'Invalid end tag ({token.token_string}). '
                                  f'This tag is not open at this point. '
                                  f'Will be kept by the parser '
                                  f'but ignored by players.')
            elif not token.valid:
                errors.append(f'Invalid end tag ({token.token_string}). '
                              f'These characters will be interpreted as text.')
                text_result += token.token_string
            elif not token.closed:
                errors.append(f'Invalid end tag ({token.token_string}). '
                              f'The tag has no closing bracket. '
                              f'Will be intepreted as text.')
                text_result += token.token_string

            print_result.append(token.token_string)
            result.append(token)

    return result, ''.join(print_result), text_result.split('\n'), errors


def SRT_text_tokenizer(text_string, position):
    tokenizer_state = 1
    result = ''

    buffer = ''

    while True:
        _next = False
        if position >= len(text_string):
            c = None
        else:
            c = text_string[position]

        if tokenizer_state == 1:
            if c == '<':
                if result == '':
                    tokenizer_state = 2
                    _next = True
                else:
                    return result, position

            elif c is None:
                return result, position

            else:
                result += c
                _next = True

        elif tokenizer_state == 2:
            if c == '/':
                tokenizer_state = 4
                _next = True
            else:
                result = c
                tokenizer_state = 3
                _next = True

        elif tokenizer_state == 3:
            if c == '>':
                position += 1
                return SRTStartTag(result), position

            elif c is None:
                return SRTStartTag(result, closed=False), position
            else:
                result += c
                _next = True

        elif tokenizer_state == 4:
            if c == '>':
                position += 1
                return SRTEndTag(result), position
            elif c is None:
                return SRTEndTag(result, closed=False), position
            else:
                result += c
                _next = True

        if _next:
            position += 1


        


def decode_VTT(file_list, frame_rate=24):
    """[summary]

    See https://www.w3.org/TR/webvtt1/#parsing

    Parameters
    ----------
    file_list : [type]
        [description]

    
    NOTE: Pass this somewhere else, maybe the Python Journal.
          
          chr(i) Returns the string representing a character
          whose Unicode code point is the integer i.
          
          ord(c) Given a string representing one Unicode character,
          return an integer representing the Unicode code point
          of that character.

          A value of 0x000A, for example, actually has a type of int;
          thus, it can be passed to the chr() function.

    """

    file_text_header = ''
    
    # Measured with timeit, this block seems to take
    # 29 microseconds to execute.
    # NOTE: Maybe this here https://stackoverflow.com/questions/6116978/how-to-replace-multiple-substrings-of-a-string
    #       will work to do all replacements,
    #       or maybe it's easier and cleaner in the current form.
    # Replace all U+0000 NULL characters
    # by U+FFFD REPLACEMENT CHARACTERs.
    # Replace each U+000D CARRIAGE RETURN U+000A LINE FEED (CRLF)
    # character pair by a single U+000A LINE FEED (LF) character,
    # and all remaining U+000D CARRIAGE RETURN characters
    # by U+000A LINE FEED (LF) characters.
    # See https://www.w3.org/TR/webvtt1/#file-parsing (Step 1)
    file_list = ''.join(file_list)
    file_list = file_list.replace('\u0000', '\ufffd')
    file_list = re.sub('\u000d\u000a?', '\u000a', file_list)
    file_list = file_list.split('\n')

    # !! NOTE: What about the byte order mark?


    # NOTE: Aren't more than one spaces allowed after the header?
    #       This is exacty what the parsing algorithm has
    #       in the formal specification, but MDN has something
    #       a bit different.
    # Steps 2, 4, 5, and 6.
    # NOTE: What about step 3?

    # If there is a match here, group(1) is the WEBVTT signature,
    # group(2) is everything that comes after the signature,
    # and group(3) is the actual signature.
    header_match = re.search('(^WEBVTT)([ \t]([^\n\r]*))?', file_list[0])

    # Here, the length of the line with the signature is checked
    # because the regular expression used will match the signature
    # even if there are illegal characters after it.
    # For example, 'WEBVTTwer'.
    # For lack of a better regular expression
    # and to avoid writing too many checks.
    if (not header_match
        or (header_match.group(2) is None and len(file_list[0]) > 6)):
        # Frobnicate
        raise FormatError(f'The file does not start with the correct'
                          f' WebVTT file signature. ({file_list[0]})')

    # if file_list[0][:7] not in ['WEBVTT', 'WEBVTT ', 'WEBVTT\t']:
    #     raise FormatError('The file does not start with the correct'
    #                       ' WebVTT file signature.')

    # NOTE: Steps 7, 8, 9, and 10 are not very clear yet.
    # NOTE: How do you actually collect the text header if it exists?

    elif file_list[1] != '':
        raise FormatError('No blank line after the signature.')

    # WebVTT signature and blank line after it are correct.
    # Proceed to decode the file.
    else:
        text_header = header_match.group(3)
        
        # All the subtitles.
        subtitles = []
        regions = {}

        # Counts the cues.
        # Will be used to identify the cues internally for now.
        # Later it could be used to store the cue identifiers,
        # depending on what type of data the identifiers can contain.
        # NOTE: Apparently, identifiers can be anything,
        #       so the cue_number should be used for the identifier.
        cue_number = 1
        
        # See comment above.
        cue_identifier = ''
        cue_text = []
        
        # Right after timestamps are registered from a timestamp line,
        # a cue payload is expected.
        # NOTE: confirm that there are no other possible components
        #       after the timestamp line.
        text_expected = False
        region_expected = False
        
        # True when the function is expecting a new cue,
        # either because it's going to process the first cue
        # or because a cue has just ended.
        # NOTE: Confirm a blank line always ends a cue block.
        new_expected = True
        
        # When expecting a new cue, an identifier could be found
        # instead of a timestamp line.  In this case, this flag
        # indicates that the identifier was found
        # and now the timestamp is obligatory.
        time_expected = False


    for i in range(2, len(file_list)):
        
        if new_expected:
            # NOTE: Confirm all possible acceptable cases for this.
            timestamp1_match = re.search(
                '^\d\d:\d\d:\d\d.\d\d\d --> \d\d:\d\d:\d\d.\d\d\d',
                file_list[i]
            )

            timestamp2_match = re.search(
                '^\d\d:\d\d.\d\d\d --> \d\d:\d\d.\d\d\d',
                file_list[i]
            )


            if (not timestamp1_match and not timestamp2_match
                and not time_expected):
                # Frobnicate                
                if re.search('^\s+$', file_list[i]) or file_list[i] == '':
                    continue

                else:
                    # NOTE: Need to consider here
                    #       what to do with comments
                    #       and the string 'NOTE' when it appears
                    #       right before a timestamp line.
                    # !! NOTE: Make sure that \s matches
                    #          all ASCII whitespace.
                    region_match = re.search('^REGION\s*$', file_list[i])
                    style_match = re.search('^STYLE\s*$', file_list[i])


                    if region_match:
                        # NOTE: See which of these bindings
                        #       are unnecessary.
                        region_expected = True
                        time_expected = False
                        new_expected = False
                        text_expected = False
                        region_settings = ''

                    elif style_match:
                        pass
                    else:
                        cue_identifier = file_list[i]
                        time_expected = True

                # NOTE: Evaluate comments here.

            elif timestamp1_match or timestamp2_match:

                if timestamp1_match:
                    start_time = Timecode(
                        file_list[i][:12], frame_rate=frame_rate)
                    end_time = Timecode(
                        file_list[i][17:29], frame_rate=frame_rate)
                    # The length of the timestamp pair is stored
                    # to then use it to check for settings.
                    time_length = len(timestamp1_match.group())

                elif timestamp2_match:
                    start_time = Timecode(
                        file_list[i][:9], frame_rate=frame_rate)
                    end_time = Timecode(
                        file_list[i][14:25], frame_rate=frame_rate)
                    # The length of the timestamp pair is stored
                    # to then use it to check for settings.
                    time_length = len(timestamp2_match.group())

                time_expected = False
                new_expected = False
                text_expected = True

                region = None

                # NOTE: Seems to default to an empty string (horizontal).
                #       This is seen in Chrome and Firefox.
                #       The specification says that it defaults to horizontal,
                #       but it doesn't mention any value for the string
                #       in the settings line.
                vertical = ''

                # Defaults to 'auto'
                line = 'auto'

                # Defaults to 'start'
                line_align = 'start'
                snap_to_lines = True

                # Defaults to 'auto'
                position = 'auto'

                # Defaults to 'auto'
                position_align = 'auto'
                size = 100
                align = 'center'

                # See if the timestamp line has more than just the
                # timestamps—if it has settings...
                # NOTE: Can a timestamp line have a space
                #       after the end time? Note that this check is
                #       considering that space.
                # ANSWER: Apparently not, from what was seen in Chrome,
                #         Firefox, and Opera. The specification
                #         doesn't say anything about that space either.
                # NOTE: Find a more efficient way to do this check.
                if (len(file_list[i]) > time_length
                    and re.search('\S+', file_list[i][time_length:])):

                    (
                        region,
                        vertical,
                        line,
                        line_align,
                        snap_to_lines,
                        position,
                        position_align,
                        size,
                        align
                    ) = decode_VTT_settings(
                        file_list[i][time_length:], i, regions)
                    
                
                # NOTE: This 'continue' might be unnecessary here.
                continue

            elif time_expected:
                print(i)
                raise FormatError('Cue identifier cannot be standalone')

        elif text_expected:
            # A blank line terminates the cue.
            # Thus, store whatever info has been gathered
            # up until this point from the current cue.
            # Note that being at this point means that a cue was found—
            # because of the timestamp line—and there is enough info
            # to store.
            # NOTE: Make sure what is actually considered a blank line,
            #       because this may not be the only case.
            if file_list[i] == '':
                dialogue_lines = 0
                dialogue = False

                for sub_line in cue_text:
                    if re.search('^-', sub_line):
                        dialogue_lines += 1

                if dialogue_lines == len(cue_text):
                    dialogue = True

                cue_text, italics, bold, underline = decode_text_tags(cue_text)

                # NOTE: Identifiers not implemented yet.
                subtitles.append(WebVTT(
                    cue_number,
                    cue_text,
                    start_time,
                    end_time,
                    dialogue=dialogue,
                    identifier=cue_identifier,
                    region=region,
                    vertical=vertical,
                    line=line,
                    line_align=line_align,
                    snap_to_lines=snap_to_lines,
                    position=position,
                    position_align=position_align,
                    size=size,
                    align=align,
                    italics=italics,
                    bold=bold,
                    underline=underline
                ))

                cue_text = []
                text_expected = False
                new_expected = True

                # Start time and end time have the value of -1
                # to let the function know when they haven't been found
                # for a cue.
                start_time = -1
                end_time = -1
                cue_number += 1
                
                # Clear the settings.
                (
                    line,
                    position,
                    vertical,
                    size,
                    align) = [None for n in range(5)]

                continue

            # NOTE: What happens if a timestamp line is inserted
            #       without a blank line from the previous subtitle?
            else:
                cue_text.append(file_list[i])

        elif region_expected:
            if not re.search('^\s*$', file_list[i]):
                region_settings += file_list[i] + ' '
            else:
                # Parse the region settings here.
                (
                    current_region,
                    region_identifier
                ) = decode_VTT_region(region_settings, i)

                regions[region_identifier] = current_region
                region_expected = False
                new_expected = True

    # If, after iterating over all the lines of the file,
    # the start—and end—times have the value of -1,
    # it means that no cue was left without registering.
    # So, having some value in start_time (a timecode, actually),
    # will make the function store whatever info has been gathered
    # about the new cue up until this point.
    if type(start_time) == Timecode:
        dialogue_lines = 0
        dialogue = False

        for sub_line in cue_text:
            if re.search('^-', sub_line):
                dialogue_lines += 1

        if dialogue_lines == len(cue_text):
            dialogue = True

        cue_text, italics, bold, underline = decode_text_tags(cue_text)

        # NOTE: Identifiers not implemented yet.
        subtitles.append(WebVTT(
            cue_number,
            cue_text,
            start_time,
            end_time,
            dialogue=dialogue,
            identifier=cue_identifier,
            region=region,
            vertical=vertical,
            line=line,
            line_align=line_align,
            snap_to_lines=snap_to_lines,
            position=position,
            position_align=position_align,
            size=size,
            align=align,
            italics=italics,
            bold=bold,
            underline=underline
        ))

    VTT_contents = {'regions': regions, 'subtitles': subtitles}
    return VTT_contents



def decode_text_tags(text):
    """Takes a list of subtitle text lines with tags
        of the form '<i></i>' and extracts the indexes
        at which those tags appear.
        Also cleans the text line of invalid tags.
        Currently works with italics (<i></i>), bold (<b></b>),
        and underline (<u></u>).

    NOTE: This needs some more tests. Consider this list
          ['<u>Hello</u>, <i></i>you <b>the<u>re</b>. Yes, </u><b>exactly', 'You</b>. No. <u>Not you</u>']

    Parameters
    ----------
    text : list.
        List of subtitle text lines with format tags.

    Returns
    -------
    list
        First element is the text with the cleaned tags.
        Second element is the italics list.
        Third element is the bold list.
        Fourth element is the underline list.
    """

    # These flags means that there is an ongoing segment open..
    it_opened = False
    b_opened = False
    u_opened = False

    # NOTE: See 4.2.2 in the recommendation.
    #       There is also <c>, <ruby>, <v>, <lang>
    op_tag_list = ['<i>', '<u>', '<b>']
    close_tag_list = ['</i>', '</u>', '</b>']

    it_seg = []
    line_it = []
    italics = []

    b_seg = []
    line_b = []
    bold = []

    u_seg = []
    line_u = []
    underline = []

    new_line = ''
    new_text = []

    # Iterate over the lines of text.
    for line in text:
        i = 0
        # This is used to store the current index of the new line
        # of text, which is different from the index
        # of the input line of text because this new line of text
        # does not contain the text tags.
        current_ind = 0

        # Iterate over all the characters in the line of text.
        while i < len(line):


            if i == 0:
                if it_opened:
                    it_seg.append(current_ind)
                if b_opened:
                    b_seg.append(current_ind)
                if u_opened:
                    u_seg.append(current_ind)
            # -------------------
            # # If there is an italics segment open from a previous line,
            # # then start a segment—to continue the pending one—
            # # right at the beginning of the line.
            # if i == 0 and it_opened:
            #     it_seg.append(current_ind)


            if i+3 <= len(line) and line[i:i+3] in op_tag_list:
                if line[i+1] == 'i' and not it_opened:
                    it_opened = True
                    it_seg.append(current_ind)
                
                elif line[i+1] == 'b' and not b_opened:
                    b_opened = True
                    b_seg.append(current_ind)

                elif line[i+1] == 'u' and not u_opened:
                    u_opened = True
                    u_seg.append(current_ind)

                i += 3
            # -------------------------
            # # If a '<i>' is found...
            # if i+3 <= len(line) and line[i:i+3] == '<i>':
            #     # If there is no ongoing italics segment...
            #     # Keep in mind that, if a '<i>' is found while there is
            #     # an ongoing italics segment, then that '<i>'
            #     # is superfluous and does nothing.
            #     # It is ignored and cleaned up here (when skipped).
            #     if not it_opened:
            #         # Set the flag to indicate
            #         # there is an ongoing italics segment.
            #         it_opened = True
            #         it_seg.append(current_ind)
                
            #     # The looping variable is incremented by 3 to skip
            #     # the rest of the characters of the tag,
            #     # whether the tag is used or ignored (superfluous).
            #     i += 3


            elif i+4 <= len(line) and line[i:i+4] in close_tag_list:
                if line[i+2] == 'i' and it_opened:
                    it_opened = False
                    if it_seg[0] != current_ind:
                        it_seg.append(current_ind)
                        line_it.append(it_seg)
                    it_seg = []

                if line[i+2] == 'b' and b_opened:
                    b_opened = False
                    if b_seg[0] != current_ind:
                        b_seg.append(current_ind)
                        line_b.append(b_seg)
                    b_seg = []

                if line[i+2] == 'u' and u_opened:
                    u_opened = False
                    if u_seg[0] != current_ind:
                        u_seg.append(current_ind)
                        line_u.append(u_seg)
                    u_seg = []

                i += 4
            # -----------------------------
            # # If a '</i>' is found...
            # elif i+4 <= len(line) and line[i:i+4] == '</i>':
            #     # If there is an ongoing italics segment...
            #     # Keep in mind that, if a '</i>' is found
            #     # while there is no ongoing italics segment,
            #     # then that '</i>' is superfluous and does nothing.
            #     # It is ignored and cleaned up here (when skipped).
            #     if it_opened:
            #         # Reset the flag to indicate there is no longer
            #         # an ongoing italics segment.
            #         it_opened = False
            #         if it_seg[0] != current_ind:
            #             it_seg.append(current_ind)
            #             line_it.append(it_seg)
            #             it_seg = []
            #         else:
            #             it_seg = []
                
            #     # The looping variable is incremented by 4 to skip
            #     # the rest of the characters of the tag,
            #     # whether the tag is used or ignored (superfluous).
            #     i += 4

            # If no text tag is found, then this is a text character
            # and should be added to the new line of text.
            else:
                new_line += line[i]
                i += 1
                current_ind += 1

        # If the end of a line is reached with a format segment open,
        # then it is closed here.
        # Note that the format segment open flag is not reset here
        # because it will be used in the next line to open
        # the segment there.  Apparently, the unclosed segments
        # carry over to the next lines until closed or until the end
        # of the last line.
        if it_opened:
            if it_seg[0] != current_ind:
                it_seg.append(current_ind)
                line_it.append(it_seg)
            it_seg = []
        
        if b_opened:
            if b_seg[0] != current_ind:
                b_seg.append(current_ind)
                line_b.append(b_seg)
            b_seg = []

        if u_opened:
            if u_seg[0] != current_ind:
                u_seg.append(current_ind)
                line_u.append(u_seg)
            u_seg = []


        # If, after getting all tag indexes, any format list
        # is still empty—meaning that format is not present
        # in that line—assign None to it
        # for easier processing afterwards.
        if not line_it:
            line_it = None

        if not line_b:
            line_b = None

        if not line_u:
            line_u = None

        italics.append(line_it)
        line_it = []

        bold.append(line_b)
        line_b = []

        underline.append(line_u)
        line_u = []

        new_line = html.unescape(new_line)
        new_text.append(new_line)
        new_line = ''

    return [new_text, italics, bold, underline]


def parse_VTT(file_name, frame_rate=24):

    file_list = read_text_file(file_name)

    # NOTE: Make sure this is necessary by seeing the recommendation.
    file_text_header = ''

    # Step 1.
    file_list = ''.join(file_list)
    file_list = file_list.replace('\u0000', '\ufffd')
    file_list = re.sub('\u000d\u000a?', '\u000a', file_list)
    file_list = file_list.split('\n')

    # Step 2
    position = 0

    # Step 3
    seen_cue = False

    # Steps 4, 5, and 6.
    signature_match = re.search('^WEBVTT[ \t\n]*', file_list[0])
    if not signature_match:
        print('The file does not start with the correct WebVTT signature.')
        return

    # Step 7
    # NOTE: The algorithm doesn't really say what to do
    #       with these code points or what to name the variable.
    # collected_chars = ''
    # while file_list[position] != '\n':
    #     collected_chars += file_list[position]
    #     position += 1

    # Step 12
    # NOTE: Again, doesn't say what to do with these code points.
    # while file_list[position] == '\n':
    #     position += 1

    # Step 13
    regions = {}
    stylesheets = []
    cues = []
    contents = {}
    cue_count = 1

    index = 2
    # Step 14
    while index < len(file_list):

        block, block_type, index, seen_cue = collect_block(
            file_list, index, seen_cue, cue_count, regions, frame_rate)

        if block_type == 'cue':
            cues.append(block)
            cue_count += 1

        elif block_type == 'region':
            regions[block.identifier] = block

        elif block_type == 'stylesheet':
            stylesheets.append(block)

    
    contents['stylesheets'] = stylesheets
    contents['regions'] = regions
    contents['cues'] = cues

    return contents

        
def collect_block(file_list, index, seen_cue, cue_count, regions, frame_rate):
    # NOTE: The algorithm says to bring this variable
    #       from the calling scope.
    # seen_cue = False
    seen_arrow = False
    line_count = 0
    buffer = ''

    cue = None
    region = None
    stylesheet = None

    block_lines = []
    while True:
        line_count += 1
        if index >= len(file_list):
            break

        if '-->' in file_list[index]:
            # NOTE: in_header omitted here.
            if (line_count == 1
                or (line_count == 2 and not seen_arrow)):
                # Frobnicate
                seen_arrow = True
                cue_identifier = buffer    
                timings = collect_VTT_timings(file_list[index], frame_rate)

                if timings:
                    start_time = timings[0]
                    end_time = timings[1]
                    settings = file_list[index][timings[2]:]
                    VTT_settings = decode_VTT_settings(
                        settings,
                        index-1,
                        regions
                    )
                    buffer = ''
                    seen_cue = True
                    cue = True
                    index += 1
            else:
                # NOTE: See how position
                #       and previous positon behave here.
                # NOTE: This means there is an error in the cue.
                #       Interpret it.
                break

        elif not file_list[index]:
            index += 1
            break

        else:
            # NOTE: in_header omitted here.
            if line_count == 2:
                if not seen_cue and re.search('^STYLE\s*$', buffer):
                    # parse style here
                    buffer = ''
                    stylesheet = True
                elif not seen_cue and re.search('^REGION\s*$', buffer):
                    # parse region here
                    buffer = ''
                    region = True
            if buffer:
                buffer += '\n'

            buffer += file_list[index]
            index += 1            
    
    if cue is not None:
        # cue_text = buffer.split('\n')
        tokenized_text, cue_text, untagged_text, errors = VTT_text_parser(buffer)

        cue = WebVTT(
            cue_count,
            cue_text,
            tokenized_text,
            untagged_text,
            start_time,
            end_time,
            identifier=cue_identifier,
            region=VTT_settings[0],
            vertical=VTT_settings[1],
            line=VTT_settings[2],
            line_align=VTT_settings[3],
            snap_to_lines=VTT_settings[4],
            position=VTT_settings[5],
            position_align=VTT_settings[6],
            size=VTT_settings[7],
            align=VTT_settings[8],
            # italics=italics,
            # bold=bold,
            # underline=underline,
        )

        return cue, 'cue', index, seen_cue

    elif stylesheet is not None:
        return stylesheet, 'style', index, seen_cue

    elif region is not None:
        region, identifier = decode_VTT_region(buffer, index)
        return region, 'region', index, seen_cue

    else:
        return None, None, index, seen_cue


def collect_VTT_timings(string, frame_rate=24):


    timestamp_match = re.search(
        '^\s*(\d+:\d\d:\d\d.\d\d\d|\d\d:\d\d.\d\d\d)'
        '\s*-->\s*(\d+:\d\d:\d\d.\d\d\d|\d\d:\d\d.\d\d\d)', string)

    if timestamp_match:
        try:
            start_time = Timecode(
                timestamp_match.group(1),
                frame_rate=frame_rate
            )
            end_time = Timecode(
                timestamp_match.group(2),
                frame_rate=frame_rate
            )
        except:
            return None
    else:
        return None

    return start_time, end_time, timestamp_match.span()[1]
            

def decode_VTT_settings(settings_string, line_number, regions):


    # NOTE: See below, when parsing the 'line' setting
    #       and the 'position' setting, that the usage
    #       and meaning of line_pos and line_pos_val,
    #       and col_pos and col_pos_val, might turn out
    #       to be a bit confusing. Make that a bit more clear.
    # NOTE: What happens when the user passes more than one instance
    #       of one setting? This is currently not considered.
    
    region = None

    # Defaults to 'auto'
    line = 'auto'
    line_pos = None
    line_pos_val = None
    linealign = 'start'
    
    # Defaults to 'start'
    line_align = 'start'
    snap_to_lines = True

    # Defaults to 'auto'
    position = 'auto'
    col_pos = 'auto'
    col_pos_val = None
    col_align = None

    # Defaults to 'auto'
    position_align = 'auto'
    size = 100
    align = 'center'

    # NOTE: Seems to default to an empty string (horizontal).
    #       This is seen in Chrome and Firefox.
    #       The specification says that it defaults to horizontal,
    #       but it doesn't mention any value for the string
    #       in the settings line.
    vertical = ''
    line_align_values = ['start', 'center', 'end']
    col_align_values = ['line-left', 'center', 'line-right']
    align_values = ['start', 'center', 'end', 'left', 'right']

    # The settings are gotten by separating using
    # the spaces, which they all should have.
    # NOTE: No error is being raised here
    #       for incorrect settings.
    # NOTE: Actually, the re match doesn't seem
    #       to be necessary here;
    #       you may have just split the text.
    settings = re.finditer('\S+', settings_string)
    # Used to check validity of the settings names.
    valid_settings = [
        'align',
        'vertical',
        'line',
        'position',
        'size',
        'region'
    ]

    # Iterating over the matches for the settings.
    for setting in settings:
        # Get the index of the ':' to separate
        # the setting name from the value.
        # NOTE: The values of the settings are not
        #       being checked for correctness yet.
        colon_ind = setting.group().find(':')

        # Check if the setting has no ':' or if the ':' is the first
        # or last character in the setting.
        if (colon_ind == -1 or colon_ind == 0
            or colon_ind == (len(setting.group()) - 1)):
            # Ignore this setting
            continue

        else:
            setting_name = setting.group()[:colon_ind]

        # || DECODE REGION SETTING
        if setting_name == 'region':
            setting_value = setting.group()[colon_ind+1:]

            if setting_value in list(regions.keys()):
                region = regions[setting_value]

            else:
                # print(f'Invalid region identifier in line {line_number+1}:')
                # print(f"'{setting_value}'")
                region = None
                continue
        
        # || DECODE VERTICAL SETTING
        elif setting_name == 'vertical':
            setting_value = setting.group()[colon_ind+1:]
            # NOTE: Remember to include the processing
            #       of 'region' when the writing
            #       direction is not horizontal.
            #       See 6.3.
            if setting_value in ['rl', 'lr']:
                vertical = setting_value
            else:
                print(f"Wrong value for the setting"
                      f"'vertical' at line {line_number+1}:")
                print(setting_value)
                continue

        # || DECODE LINE SETTING
        elif setting_name == 'line':
            setting_value = setting.group()[colon_ind+1:]
            comma_ind = setting_value.find(',')
            
            if comma_ind != -1:
                line_pos = setting_value[:comma_ind]
                linealign = setting_value[comma_ind+1:]
            else:
                line_pos = setting_value
            
            # NOTE: How can you join these two regular expressions
            #       into only one?
            value_match_per = re.search('^\d+(\.\d+)?%$', line_pos)
            value_match = re.search('^-?\d+(\.\d+)?$', line_pos)
            
            # !! NOTE: Firefox actually does not ignore
            #          the whole setting, as the specification says,
            #          when the value of linealign is invalid.
            #          Instead, it keeps the value of linepos
            #          and sets linealign to 'start' (default).
            #          This also affects how a repeated line setting
            #          is treated. See the notes in the .md file.
            if (not value_match_per and not value_match
                or (linealign and linealign not in line_align_values)):
                # NOTE: Maybe print some message saying
                #       that the value is incorrect.
                #       Although the specification
                #       does not say that the program
                #       should abort.
                # NOTE: The values for line_pos, line_pos_val,
                #       and line_align are already set to None
                #       at the beginning of the loop.
                #       However, what happens when the user passes
                #       more than one 'line' setting?
                continue
    
            else:
                line_pos_val = float(re.search(
                    '-?\d+(\.\d+)?', line_pos).group())

                if line_pos_val == int(line_pos_val):
                    line_pos_val = int(line_pos_val)
                
                if (value_match_per
                    and (line_pos_val < 0 or line_pos_val > 100)):
                    # NOTE: Maybe print a message here.
                    continue
                elif value_match_per:
                    snap_to_lines = False
                else:
                    snap_to_lines = True

                line = line_pos_val
                line_align = linealign

        # || DECODE POSITION SETTING
        elif setting_name == 'position':
            setting_value = setting.group()[colon_ind+1:]
            comma_ind = setting_value.find(',')
            
            if comma_ind != -1:
                col_pos = setting_value[:comma_ind]
                col_align = setting_value[comma_ind+1:]
            else:
                col_pos = setting_value
                col_align = None
            
            # See that the percent sign is not optional here.
            # This is because the specification
            # does not mention it as optional.
            value_match = re.search('^\d+(\.\d+)?%$', col_pos)

            # NOTE: The specification states that the position's value
            #       remains the special value 'auto'.
            if (not value_match
                or (col_align and col_align not in col_align_values)):
                continue
            else:
                col_pos_val = float(re.search('\d+(\.\d+)?', col_pos).group())
                
                if col_pos_val == int(col_pos_val):
                    col_pos_val = int(col_pos_val)
                
                if (col_pos_val < 0 or col_pos_val > 100):
                    # NOTE: Maybe print a message here.
                    continue
                position = col_pos_val
                position_align = col_align

        # || DECODE SIZE SETTING
        elif setting_name == 'size':
            setting_value = setting.group()[colon_ind+1:]
            value_match = re.search('^\d+(\.\d+)?%$', setting_value)

            if not value_match:
                continue
            else:
                size = float(re.search('\d+(\.\d+)?', setting_value).group())

                if size == int(size):
                    size = int(size)
                # NOTE: It might be unnecessary to check
                #       for negative values here,
                #       because the regular expression
                #       in value_match already excludes them.
                if size < 0 or size > 100:
                    continue

        # || DECODE ALIGN SETTING
        elif setting_name == 'align':
            setting_value = setting.group()[colon_ind+1:]

            if setting_value in align_values:
                align = setting_value

        else:
            print(f'Wrong setting at line {line_number+1}:')
            print(setting_name)
        
        # # Check the correctness of the setting name.
        # elif setting.group()[:ind] not in valid_settings:
        #     print('Wrong setting')
        #     print(setting.group())
        #     return
        
        # Store the values of the settings found.
        # NOTE: Still have to check validity of values.
        #       The setting name must be found exactly
        #       to be able to check the validity
        #       of its value.
        # NOTE: What happens when a setting
        #       appears twice?
        # else:
        #     if setting.group()[:ind] == 'line':
        #         line = setting.group()[ind+1:]
        #     elif setting.group()[:ind] == 'position':
        #         position = setting.group()[ind+1:]
        #     elif setting.group()[:ind] == 'vertical':
        #         vertical = setting.group()[ind+1:]
        #     elif setting.group()[:ind] == 'size':
        #         size = setting.group()[ind+1:]
        #     elif setting.group()[:ind] == 'align':
        #         align = setting.group()[ind+1:]

    # print(line_number)
    # print(f'vertical: {vertical}')
    # print(f'line: {line}, line_pos: {line_pos_val}, line_align: {line_align}, '
    #       f'snap_to_lines: {snap_to_lines}')
    # print(f'position: {position}, col_pos: {col_pos_val}, '
    #       f'col_align: {col_align}')
    # print(f'size: {size}')
    # print(f'align: {align}')

    return (region, vertical, line, line_align, snap_to_lines,
            position, position_align, size, align)


def decode_VTT_region(settings_string, line_number):

    
    identifier = ''
    width = 100
    lines = 3
    region_anchor_x = 0
    region_anchor_y = 100
    vp_anchor_x = 0
    vp_anchor_y = 100
    scroll = ''

    settings = re.finditer('\S+', settings_string)

    valid_settings = [
        'id',
        'width',
        'lines',
        'regionanchor',
        'viewportanchor',
        'scroll'
    ]

    for setting in settings:

        colon_ind = setting.group().find(':')

        if (colon_ind == -1 or colon_ind == 0
            or colon_ind == (len(setting.group()) - 1)):
            # Ignore this setting
            continue
        
        else:
            setting_name = setting.group()[:colon_ind]
            setting_value = setting.group()[colon_ind+1:]

        if setting_name == 'id':
            identifier = setting_value

        elif setting_name == 'width':
            value_match = re.search('^\d+(\.\d+)?%$', setting_value)

            if value_match:
                width = float(re.search('\d+(\.\d+)?', setting_value).group())

                if width == int(width):
                    width = int(width)

        elif setting_name == 'lines':
            value_match = re.search('^\d+$', setting_value)

            if value_match:
                lines = int(re.search('\d+', setting_value).group())

        elif setting_name == 'regionanchor':
            comma_ind = setting_value.find(',')

            if comma_ind != -1:
                anchor_x = setting_value[:comma_ind]
                anchor_y = setting_value[comma_ind+1:]

                value_match_x = re.search('^\d+(\.\d+)?%$', anchor_x)
                value_match_y = re.search('^\d+(\.\d+)?%$', anchor_y)

                region_anchor_x = float(re.search(
                    '\d+(\.\d+)?', anchor_x).group())

                if region_anchor_x == int(region_anchor_x):
                    region_anchor_x = int(region_anchor_x)

                region_anchor_y = float(re.search(
                    '\d+(\.\d+)?', anchor_y).group())

                if region_anchor_y == int(region_anchor_y):
                    region_anchor_y = int(region_anchor_y)

        elif setting_name == 'viewportanchor':
            comma_ind = setting_value.find(',')

            if comma_ind != -1:
                anchor_x = setting_value[:comma_ind]
                anchor_y = setting_value[comma_ind+1:]

                value_match_x = re.search('^\d+(\.\d+)?%$', anchor_x)
                value_match_y = re.search('^\d+(\.\d+)?%$', anchor_y)

                vp_anchor_x = float(re.search(
                    '\d+(\.\d+)?', anchor_x).group())

                if vp_anchor_x == int(vp_anchor_x):
                    vp_anchor_x = int(vp_anchor_x)

                vp_anchor_y = float(re.search(
                    '\d+(\.\d+)?', anchor_y).group())

                if vp_anchor_y == int(vp_anchor_y):
                    vp_anchor_y = int(vp_anchor_y)

        elif setting_name == 'scroll':
            if setting_value == 'up':
                scroll = setting_value

        else:
            print(f'Wrong setting name at line {line_number}:')
            print(setting_name)


    region = WebVTTRegion(
        identifier=identifier,
        width=width,
        lines=lines,
        region_anchor_x=region_anchor_x,
        region_anchor_y=region_anchor_y,
        vp_anchor_x=vp_anchor_x,
        vp_anchor_y=vp_anchor_y,
        scroll=scroll
    )

    return region, identifier


def VTT_text_parser(cue_text):

    # text_string = '\n'.join(cue_text)

    position = 0
    result = []
    print_result = []
    text_result = ''
    # NOTE: This doesn't necessarily match the algorithm.
    current = None
    language_stack = []
    # language ?
    errors = []
    open_order = []

    while True:
        if position >= len(cue_text):
            # result: tokenized text
            # print_result: text. It is the text
            #               that is printed to the file.
            # text_result: untagged_text.
            return (result, ''.join(print_result),
                    text_result.split('\n'), errors)
        token, position = cue_text_tokenizer(cue_text, position)
        if type(token) == str:
            result.append(token)
            print_result.append(html.escape(token, quote=False))
            text_result += token
        elif type(token) == StartTag:

            # ----------------------------------------------------------
            # Different from the actual official algorithm.
            # This parser is not intended to ignore tags
            # that are invalid, but instead to output errors.
            # See commented out below for the actual parser.
            # ----------------------------------------------------------
            
            if not token.valid_name:
                # Invalid start tag
                errors.append(f"Invalid start tag ({token.token_string}). "
                              f'These characters will be interpreted as text '
                              f'but will be ignored by web players.')
                text_result += token.token_string

            elif not token.closed:
                errors.append(f"Invalid start tag ({token.token_string}). "
                              f'The tag has no closing bracket.'
                              f' Will be interpreted as text '
                              f'but ignored by web players.')
                text_result += token.token_string

            elif token.name in open_order:
                errors.append(f'Invalid start tag ({token.token_string}). '
                              f'Already open. '
                              f'These characters will be ignored '
                              f'by web players.')
            else:
                open_order.append(token.name)
            
            result.append(token)
            print_result.append(token.token_string)
            # ----------------------------------------------------------
            # ----------------------------------------------------------


            # ----------------------------------------------------------
            # Actual parser
            # ----------------------------------------------------------
            # if token.name in ['c', 'i', 'b', 'u', 'ruby', 'rt', 'v', 'lang']:
            #     token_string = '<' + token.name
            #     # NOTE: Can classes contain character references?
            #     #       If so, then use html.escape() here.
            #     if token.classes:
            #         token_string += '.' + '.'.join(token.classes)
            #     # NOTE: What about the language?
            #     # NOTE: Can annotations contain character references?
            #     #       If so, then use html.escape() here.
            #     if token.annotation:
            #         token_string += ' ' + token.annotation

            #     token_string += '>'
            #     if token.name in open_order:
            #         print(f'Invalid start tag ({token_string}). Already open.')
            #         print('Will be ignored by parser', end='\n\n')
            #     else:
            #         open_order.append(token.name)
            #         result.append(token)
            #         print_result.append(token_string)

            # ----------------------------------------------------------
            # ----------------------------------------------------------

        elif type(token) == EndTag:
            if token.valid_name and token.closed:
                if (open_order and token.name in open_order
                    and token.name == open_order[-1]):
                    # Valid end tag
                    open_order.pop(-1)
                else:
                    errors.append(f'Invalid end tag ({token.token_string}). '
                                  f'This tag is not open at this point. '
                                  f'Will be kept by the parser '
                                  f'but ignored by web players.')
            elif not token.valid_name:
                errors.append(f"Invalid end tag ({token.token_string}). "
                              f'These characters will be interpreted as text '
                              f'but will be ignored by web players.')
                text_result += token.token_string 
            elif not token.closed:
                errors.append(f"Invalid end tag ({token.token_string}). "
                              f'The tag has no closing bracket.'
                              f' Will be interpreted as text '
                              f'but ignored by web players.')
                text_result += token.token_string

            print_result.append(token.token_string)
            result.append(token)


    return result, ''.join(print_result), text_result.split('\n'), errors

def cue_text_tokenizer(text_string, position):

    # WebVTT data state -> 1
    # HTML character reference in data state -> 2
    # WebVTT tag state -> 3
    # WebVTT start tag state -> 4
    # WebVTT start tag class state -> 5
    # WebVTT start tag annotation state -> 6
    # HTML character reference in annotation state -> 7
    # WebVTT end tag state -> 8
    # WebVTT timestamp tag state -> 9
    
    tokenizer_state = 1
    result = ''
    classes = []
    
    # NOTE: The initialization of buffer
    #       is never mentioned in the algorithm.
    buffer = ''

    while True:
        _next = False
        if position >= len(text_string):
            c = None
        else:
            c = text_string[position]

        # || WebVTT data state
        if tokenizer_state == 1:
            if c == '&':
                # Set tokenizer_state
                # to the "HTML character reference in data state."
                tokenizer_state = 2
                _next = True
            elif c == '<':
                if result == '':
                    # Set tokenizer_state to the "WebVTT tag state."
                    tokenizer_state = 3
                    _next = True
                else:
                    return result, position
            elif c is None:
                return result, position
            else:
                result += c
                _next = True

        # || HTML character reference in data state
        elif tokenizer_state == 2:
            # NOTE: Remember the additional allowed character.
            #       There shouldn't be one here.
            chars, position = consume_HTML_char_ref(text_string, position)
            if not chars:
                result += '&'
            else:
                result += chars

            # Set tokenizer_state to the "WebVTT data state."
            tokenizer_state = 1
            _next = True
        
        # || WebVTT tag state
        elif tokenizer_state == 3:
            # NOTE: Confirm the form feed works.
            if c in ['\t', '\n', '\f', ' ']:
                # !! NOTE: Not in the algorithm,
                #          but used to keep invalid tags.
                buffer = c

                # Set tokenizer_state
                # to the "WebVTT start tag annotation state."
                tokenizer_state = 6
                _next = True
            elif c == '.':
                # Set tokenizer state
                # to the "WebVTT start tag class state."
                tokenizer_state = 5
                _next = True
            elif c == '/':
                # Set tokenizer_state to the "WebVTT end tag state."
                tokenizer_state = 8
                _next = True
            elif re.search('\d', c):
                result = c
                
                # Set tokenizer_state
                # to the "WebVTT timestamp tag state."
                tokenizer_state = 9
                _next = True
            elif c == '>':
                position += 1

                # return a start tag whose tag name is the empty string,
                # with no classes and no annotation,
                # and abort these steps.
                return StartTag(''), position
            elif c is None:
                # return a start tag whose tag name is the empty string,
                # with no classes and no annotation,
                # and abort these steps.
                return StartTag('', closed=False), position
            else:
                result = c

                # Set tokenizer_state to the "WebVTT start tag state."
                tokenizer_state = 4
                _next = True

        # || WebVTT start tag state
        elif tokenizer_state == 4:
            # NOTE: Confirm the form feed works.
            if c in ['\t', '\f', ' ']:
                # !! NOTE: Not in the algorithm,
                #          but used to keep invalid tags.
                buffer = c

                # Set tokenizer_state
                # to the "WebVTT start tag annotation state."
                tokenizer_state = 6
                _next = True
            elif c == '\n':
                buffer = c

                # Set tokenizer_state
                # to the "WebVTT start tag annotation state."
                tokenizer_state = 6
                _next = True
            elif c == '.':
                # Set tokenizer state
                # to the "WebVTT start tag class state."
                tokenizer_state = 5
                _next = True
            elif c == '>':
                position += 1
                return StartTag(result), position
            elif c is None:
                return StartTag(result, closed=False), position
            else:
                result += c
                _next = True

        # || WebVTT start tag class state
        elif tokenizer_state == 5:
            # NOTE: Confirm the form feed works.
            if c in ['\t', '\f', ' ']:
                classes.append(buffer)

                # NOTE: The algorithm has buffer = '',
                #       but this is done to keep invalid tags.
                buffer = c
                
                # Set tokenizer state
                # to the "WebVTT start tag annotation state." 
                tokenizer_state = 6
                _next = True
            elif c == '\n':
                classes.append(buffer)
                buffer = c

                # Set tokenizer_state
                # to the "WebVTT start tag annotation state."
                tokenizer_state = 6
                _next = True
            elif c == '.':
                classes.append(buffer)
                buffer = ''
                _next = True
            elif c == '>':
                position += 1
                classes.append(buffer)

                # ...then return a start tag whose tag name is result,
                # with the classes given in classes but no annotation,
                # and abort these steps.
                return StartTag(result, classes=classes), position
            elif c is None:
                classes.append(buffer)
                
                # ...then return a start tag whose tag name is result,
                # with the classes given in classes but no annotation,
                # and abort these steps.
                return StartTag(result, classes=classes, closed=False), position
            else:
                buffer += c
                _next = True
        
        # || WebVTT start tag annotation state
        elif tokenizer_state == 6:
            if c == '&':
                # Set tokenizer_state
                # to the "HTML character reference in annotation state."
                tokenizer_state = 7
                _next = True
            elif c == '>':
                position += 1

                # NOTE: Strip and whitespace replacement
                #       done in class instantiation.
                
                # ...then, return a start tag whose tag name is result,
                # with the classses given in classes,
                # and with buffer as the annotation,
                # and abort these steps.
                return (StartTag(result, classes=classes, annotation=buffer),
                        position)
            elif c is None:
                # NOTE: Strip and whitespace replacement
                #       done in class instantiation.

                # ...then, return a start tag whose tag name is result,
                # with the classses given in classes,
                # and with buffer as the annotation,
                # and abort these steps.
                return (StartTag(result, classes=classes, annotation=buffer, closed=False),
                        position)
            else:
                buffer += c
                _next = True

        # || HTML character reference in annotation state
        elif tokenizer_state == 7:
            # NOTE: Don't forget the additional allowed character.
            #       ...with the additional character being >
            chars, position = consume_HTML_char_ref(text_string, position)

            if not chars:
                buffer += '&'
            else:
                buffer += chars
            
            # Set tokenizer_state
            # to the "WebVTT start tag annotation state."
            tokenizer_state = 6
            _next = True
        
        # || WebVTT end tag state
        elif tokenizer_state == 8:
            if c == '>':
                position += 1
                return EndTag(result), position
            elif c is None:
                return EndTag(result, closed=False), position
            else:
                result += c
                _next = True

        # || WebVTT timestamp tag state
        elif tokenizer_state == 9:
            # NOTE: Needs attention! Not really tested.
            if c == '>':
                position += 1

                # Return a timestamp tag whose tag name is result
                # and abort these steps.
                return TimestampTag(result), position
            elif c is None:
                # Return a timestamp tag whose tag name is result
                # and abort these steps.
                return TimestampTag(result), position
            else:
                result += c
                _next = True
        
        if _next:
            position += 1


def consume_HTML_char_ref_1(text_string, position, aac=''):
    char_ref = ''
    EO_reference = False
    previous_position = position
    while not EO_reference and position < len(text_string):
        char_ref += text_string[position]
        if text_string[position] == ';':
            EO_reference = True
            break
            
        position += 1

    if EO_reference:
        chars = html.entities.html5.get(char_ref)
    else:
        position = previous_position
        chars = None

    return chars, position

def consume_HTML_char_ref(text_string, position, aac=''):
    char_ref = ''
    entities = list(html.entities.html5.keys())
    matched_entities = []
    dec = False
    hexa = False
    
    i = position + 1

    if text_string[position] == '#':
        current = ''
        if text_string[position+1] in ['x', 'X']:
            i += 1
            hexa = True
        else:
            dec = True

    while i <= len(text_string):
        if not hexa and not dec:
            current = text_string[position:i]
            if current in entities:
                matched_entities.append(current)

        else:
            if ((dec and text_string[i] in string.digits)
                or (hexa and text_string[i].upper()
                    in (string.digits + 'ABCDEF')) or text_string[i] == ';'):
                # Frobnicate
                current += text_string[i]
                if text_string[i] == ';':
                    break
            else:
                i -= 1
                break

        i += 1

    if matched_entities:
        char_ref = html.entities.html5[matched_entities[-1]]
        position += len(matched_entities[-1]) - 1
    elif dec and current:
        char_ref = html.unescape('&#' + current)
        position = i
    elif hexa and current:
        char_ref = html.unescape('&#x' + current)
        position = i
    elif dec or hexa or not matched_entities:
        position -= 1
    
    return char_ref, position


def check_entities():

    entities = list(html.entities.html5.keys())
    new_entities = []

    for entity in entities:
        i = 1
        current = []
        
        while i <= len(entity):
            this = entity[:i]
            if this in entities:
                current.append(this)
            i += 1

        if current:
            new_entities.append(current)

    
    for new_entity in new_entities:
        if len(new_entity) > 1:
            print(new_entity)


    print('-------------------------------------')
    print('\n\n')

    all_chars = []

    for entity in entities:
        if html.entities.html5[entity] not in all_chars:
            all_chars.append(html.entities.html5[entity])

    print(len(all_chars))


def decode_TTML(file_name):
    """[summary]

    Parameters
    ----------
    file_name : [type]
        [description]
    """

    subtitles = []
    regions = []
    styles = []

    dom_tree = minidom.parse(file_name)
    sub_nodes = dom_tree.getElementsByTagName('p')
    style_nodes = dom_tree.getElementsByTagName('style')
    region_nodes = dom_tree.getElementsByTagName('region')
    tt_element = dom_tree.documentElement

    # This is a NamedNodeMap object, contains the attributes
    # of the element, which can be accessed
    # with NamedNodeMap.item(index).  Use the object's 'name'
    # and 'value' attributes.
    tt_attributes_NNM = tt_element.attributes
    tt_attributes = {}

    for o, style_node in enumerate(style_nodes):
        style_atts_NNM = style_node.attributes
        style_atts = {}

        for n in range(style_atts_NNM.length):
            att_name = style_atts_NNM.item(n).name
            att_value = style_atts_NNM.item(n).value

            style_atts[att_name] = att_value

        styles.append(TTMLstyle(
            style_atts.get('xml:id'),
            style_atts.get('tts:fontFamily'),
            style_atts.get('tts:fontSize'),
            style_atts.get('tts:fontStyle'),
            style_atts.get('tts:fontWeight'),
            style_atts.get('tts:backgroundColor'),
            style_atts.get('tts:color')
        ))

    for m, region_node in enumerate(region_nodes):
        region_atts_NNM = region_node.attributes
        region_atts = {}

        for p in range(region_atts_NNM.length):
            att_name = region_atts_NNM.item(p).name
            att_value = region_atts_NNM.item(p).value

            region_atts[att_name] = att_value

        regions.append(TTMLregion(
            region_atts.get('xml:id'),
            region_atts.get('tts:displayAlign'),
            region_atts.get('tts:textAlign'),
            region_atts.get('tts:origin'),
            region_atts.get('tts:extent'),
        ))

    # NOTE: This part still needs to check the validity
    #       of the paramenters in the attributes.
    for i in range(tt_attributes_NNM.length):
        att_name = tt_attributes_NNM.item(i).name
        att_value = tt_attributes_NNM.item(i).value

        tt_attributes[att_name] = att_value

    frame_rate_provided = True

    if 'ttp:frameRate' in list(tt_attributes.keys()):
        frame_rate_match = re.search('\d+', tt_attributes['ttp:frameRate'])
        if frame_rate_match:
            frame_rate = frame_rate_match.group()
            frame_rate = float(frame_rate)
        else:
            print('Invalid value for the frame rate.')
            return
    else:
        frame_rate_provided = False
        frame_rate = 24

    if 'ttp:dropMode' in list(tt_attributes.keys()):
        drop_frame_match = re.search('\w+', tt_attributes['ttp:dropMode'])
        if drop_frame_match:
            drop_frame_value = drop_frame_match.group()
            if drop_frame_value in ['dropNTSC', 'dropPAL']:
                drop_frame = True
            elif drop_frame_value == 'nonDrop':
                drop_frame = False
            else:
                print('Invalid value for the dropMode parameter.')
                return
        else:
            drop_frame = False

    counter = 1
    for j, sub_node in enumerate(sub_nodes):
        subtitles.append(decode_one_TTML(
            sub_node,
            frame_rate,
            drop_frame,
            counter
        ))
        counter += 1

    return {'regions': regions, 'styles':styles, 'subtitles': subtitles}


def decode_one_TTML(subtitle, frame_rate, drop_frame, counter):
    """[summary]

    Parameters
    ----------
    subtitle : [type]
        [description]
    frame_rate : [type]
        [description]
    drop_frame : [type]
        [description]
    counter : [type]
        [description]
    """

    text = []
    current_line = ''
    italics = []
    line_it = []
    it_seg = []

    # The 'xml:id' attribute turns out to be optional.
    # Some files may not have it in their <p> elements (subtitles).
    # NOTE: Will all subtitle always be in <p> elements?
    #       Will they always have the 'id' attribute
    #       with an 'xml' prefix?  Should the abscence
    #       of this prefix be considered an error?
    # NOTE: Will the subtitle IDs always start counting them from 1?
    # sub_id_match = re.search('\d+', subtitle.getAttribute('xml:id'))

    sub_atts_NNM = subtitle.attributes
    sub_atts = {}

    for i in range(sub_atts_NNM.length):
        att_name = sub_atts_NNM.item(i).name
        att_value = sub_atts_NNM.item(i).value

        sub_atts[att_name] = att_value

    start_time = subtitle.getAttribute('begin')
    end_time = subtitle.getAttribute('end')
    region = subtitle.getAttribute('region')

    (
        text,
        current_line,
        italics,
        line_it,
        it_seg
    ) = get_TTML_text(subtitle.childNodes, text, current_line,
                  italics, line_it, it_seg)

    if line_it:
        italics.append(line_it)
    else:
        italics.append(None)
    text.append(current_line)

    start_time = Timecode(
        start_time,
        frame_rate=frame_rate,
        drop_frame=drop_frame
    )

    end_time = Timecode(
        end_time,
        frame_rate=frame_rate,
        drop_frame=drop_frame
    )

    subtitle = TTML(counter, text, start_time, end_time, italics=italics)

    return subtitle


def get_TTML_text(child_nodes, text, current_line, italics, line_it, it_seg):

    for i in range(len(child_nodes)):
        if child_nodes[i].nodeName == '#text':
            current_line += child_nodes[i].nodeValue
        
        # <br> elements end italics segments, lines,
        # and line italics with them.
        elif child_nodes[i].nodeName == 'br':
            # This means there's an italics segment open.
            # It needs to be closed at the end of the line.
            # NOTE: Is there a way to avoid this double check
            #       for italics segment?
            if it_seg:
                it_seg.append(len(current_line))
                line_it.append(it_seg)

            # NOTE: Maybe not exactly here, but see
            #       that the line italics is being empty when there is
            #       no italics in the case of no itlaics in the line,
            #       like this [[], [[1, 14]]].
            #       This might cause inconsistencies later.
            if line_it:
                italics.append(line_it)
                line_it = []
            else:
                italics.append(None)

            # Since this also means that the next line starts
            # inside the <span> element with the italics attribute,
            # it needs to start with an italics segment
            # open at the beginning.
            if it_seg:
                it_seg = [0]
            else:
                it_seg = []
        
            text.append(current_line)
            current_line = ''

        elif child_nodes[i].nodeName == 'span':
            
            if child_nodes[i].getAttribute('tts:fontStyle'):
                # Open the italics segment right at the current index
                # of the line that's being formed.
                it_seg.append(len(current_line))
                (
                    text,
                    current_line,
                    italics,
                    line_it,
                    it_seg
                ) = get_TTML_text(child_nodes[i].childNodes, text,
                                  current_line, italics, line_it, it_seg)

        # In the last node of the subtitle, there's nothing
        # that can close an italics segment and append the line_italics.
        # Also, irrespective of whether the italics segment
        # is empty or not, it needs to be appended to line_italics.
        if i == len(child_nodes) - 1:
            if it_seg:
                it_seg.append(len(current_line))
                line_it.append(it_seg)
                it_seg = []
    
    return text, current_line, italics, line_it, it_seg