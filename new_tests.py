import spacy, textacy
import copy, re, os

from decoders import parse_VTT
from reader import read_text_file


def get_breakpoints(line, nlp, debug=False):
    doc = nlp(line)

    token_info = []
    preliminar_breakpoints = []
    forbidden_breakpoints = []
    candidate_breakpoints = []
    all_space_indexes = [i for i in range(len(line)) if line[i] == ' ']

    patterns = [{'POS': 'VERB'}, {'POS': 'ADP'}]

    # NOTE: Consider another name.
    verb_phrase_matches = textacy.extract.token_matches(doc, patterns=patterns)
    # verb_phrases = [match for match in verb_phrase_matches]
    verb_phrases = [str(match) for match in verb_phrase_matches]

    # print('Verb phrases: ', verb_phrases)

    for i, token in enumerate(doc):
        # For punctuation
        if token.pos_ == 'PUNCT':
            # NOTE: "and token.text != '-'" is used
            #       because spaCy, by default,
            #       separates hyphenated words.
            #       Find a way to avoid that.
            if token.idx < len(line) - 1 and token.text != '-':
                # preliminar_breakpoints.append(token.idx + 1)
                preliminar_breakpoints.append((token.idx + 1, 10))

        # For prepositions, but may include others (conjunctions, adverbs)
        elif token.pos_ == 'ADP':
            # preliminar_breakpoints.append(token.idx - 1)
            # if i != 0:
            #     print('Here', f'{doc[i-1].text} {token.text}')

            if i != 0 and f'{doc[i-1].text} {token.text}' not in verb_phrases:
                preliminar_breakpoints.append((token.idx - 1, 8))

            forbidden_breakpoints.append(token.idx + len(token.text))

        elif token.pos_ in ['CCONJ', 'SCONJ']:
            if i != 0:
                preliminar_breakpoints.append((token.idx - 1, 9))

            forbidden_breakpoints.append(token.idx + len(token.text))

        # Includes artices.
        elif token.pos_ == 'DET':
            forbidden_breakpoints.append(token.idx + len(token.text))

        # Pronouns
        elif token.pos_ == 'PRON':
            # Do not break a verb from a pronoun
            if i < len(doc) - 1 and (doc[i+1].pos_ == 'VERB' or doc[i+1].pos_ == 'AUX'):
                forbidden_breakpoints.append(token.idx + len(token.text))

        # NOTE: See particles (PART)
        elif token.pos_ == 'PART':
            forbidden_breakpoints.append(token.idx + len(token.text))

        elif token.pos_ == 'VERB':
            # Do not break after a verb if the object of the verb
            # comes right after it and it's a pronoun.
            # Keeps from breaking "leave us."
            # NOTE: This is not in Netflix rules.
            if i < len(doc) - 1 and (doc[i+1].pos_ == 'PRON' and doc[i+1].dep_ == 'dobj'):
                forbidden_breakpoints.append(token.idx + len(token.text))

        elif token.pos_ == 'NUM':
            if i < len(doc) - 1 and doc[i+1].pos_ in ['NOUN']:
                forbidden_breakpoints.append(token.idx + len(token.text))

        elif token.pos_ == 'AUX':
            if i < len(doc) -1 and doc[i+1].pos_ == 'VERB':
                forbidden_breakpoints.append(token.idx + len(token.text))


        current_token_info = (token.text, token.idx, token.pos_, token.tag_, token.dep_)
        token_info.append(current_token_info)
        # print(token.text, token.idx)


    # print('Preliminar breakpoints: ', preliminar_breakpoints)
    # print('Forbidden breakpoints: ', forbidden_breakpoints)
    # print('All spaces: ', all_space_indexes)


    pop_indexes = []

    for index in all_space_indexes:
        ideal = False
        if index not in forbidden_breakpoints:
            for index_info in preliminar_breakpoints:
                if index == index_info[0]:
                    ideal = True
                    candidate_breakpoints.append(index_info)
            if not ideal:
                candidate_breakpoints.append((index, 2))

        # if index in forbidden_breakpoints:
        #     pop_indexes.append(index)

    pop_indexes = sorted(pop_indexes)

    for pop_index in reversed(pop_indexes):
        candidate_breakpoints.pop(pop_index)


    candidate_indexes = [data[0] for data in candidate_breakpoints]
    candidate_values = [data[1] for data in candidate_breakpoints]

    # print('\n')
    # print('Candidate breakpoints: ', candidate_breakpoints)
    # print('Candidate indexes: ', candidate_indexes)
    # print('Candidate values: ', candidate_values)
    # print('\n\n')

    # for info in token_info:
    #     print(info)

    # print('\n\n')


    return candidate_indexes, candidate_values


def clean_indexes(line, candidate_indexes, candidate_values, max_length=42):

    # if max(candidate_values) < 6:
    #     ideal_candidate

    ideal_indexes = []
    ideal_values = []
    balances = []
    lower_balance_list = []

    for i, value in enumerate(candidate_values):
        current_lengths = [candidate_indexes[i], len(line) - candidate_indexes[i]]
        current_balance = min(current_lengths) / max(current_lengths)
        if candidate_indexes[i] < len(line) - candidate_indexes[i]:
            lower_balance = True
        else:
            lower_balance = False

        if (value > 5 and current_balance >= 0.3):
            # Frobnicate
            ideal_indexes.append(candidate_indexes[i])
            ideal_values.append(candidate_values[i])
            balances.append(round(current_balance, 2))
            lower_balance_list.append(lower_balance)

        elif (value < 6 and current_balance >= 0.3):
            ideal_indexes.append(candidate_indexes[i])
            ideal_values.append(candidate_values[i])
            balances.append(round(current_balance, 2))
            lower_balance_list.append(lower_balance)

    if not ideal_indexes:
        return None
    else:
        return ideal_indexes, ideal_values, balances, lower_balance_list


def break_line(line, ideal_indexes, ideal_values, balances, lower_balance_list):
    if max(ideal_values) > 5:
        break_point = ideal_indexes[ideal_values.index(max(ideal_values))]

    else:
        break_point = ideal_indexes[0]
        # if sum(ideal_values)/len(ideal_values) == ideal_values[0]:
        #     for i, index in enumerate(ideal_indexes):


    new_line = line[:break_point] + '\n' + line[break_point+1:]

    return new_line


def segment_line(line, nlp):
    breakpoints = get_breakpoints(line, nlp)
    new_indexes = clean_indexes(line, breakpoints[0], breakpoints[1])
    # print(new_indexes)
    new_line = break_line(line, new_indexes[0], new_indexes[1], new_indexes[2], new_indexes[3])

    return new_line


def segment_subs(filename, nlp):
    # nlp = spacy.load('en_core_web_trf')
    subs = parse_VTT(filename)['cues']

    for sub in subs:
        if len(sub.line_lengths) == 1 and sub.line_lengths[0] > 42:
            print('---------------------------------------')
            print(sub.text)
            print('\n')
            prep_line = sub.text.replace('\n', ' ')
            new_line = segment_line(prep_line, nlp)
            print(new_line)
            print('\n\n')


def replace_VTT_settings(filename, replacements=[]):
    file_list = read_text_file(filename)

    for i, line in enumerate(file_list):
        timestamp_match = re.search(
            '^\s*(\d+:\d\d:\d\d.\d\d\d|\d\d:\d\d.\d\d\d)'
            '\s*-->\s*(\d+:\d\d:\d\d.\d\d\d|\d\d:\d\d.\d\d\d)', line)

        if timestamp_match is not None:
            new_line = re.sub('line:\d+%', f'{replacements[0]}', line)
            file_list[i] = new_line

    return file_list


def batch_replace_VTT_settings(files_list, save_path, replacements=[]):
    new_file_lists = []

    for filename in files_list:
        new_file_list = replace_VTT_settings(filename, replacements=replacements)
        new_filename = os.path.join(save_path, filename.split('\\')[-1])

        with open(new_filename, 'w', encoding='utf-8') as new_file:
            for line in new_file_list:
                new_file.write(line)


