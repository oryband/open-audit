#!/usr/bin/env python

import json
import itertools
import re
import sys

import yaml

import regex

# token var names

# table of contents
#
# TODO TOKEN_TOC_CHAPTER_TITLE_START includes TOKEN_TOC_CHAPTER_NUMBER
# inside itself. need to assign multiple token types to some lines because of
# this reason
TOKEN_TOC_HEADER = 'TOKEN_TOC_HEADER'
TOKEN_TOC_CHAPTER_NUMBER = 'TOKEN_TOC_CHAPTER_NUMBER'
TOKEN_TOC_CHAPTER_TITLE_START = 'TOKEN_TOC_CHAPTER_TITLE_START'
TOKEN_TOC_CHAPTER_TITLE_CONTINUE = 'TOKEN_TOC_CHAPTER_TITLE_CONTINUE'

TOKEN_TOC_CHAPTER_OFFICE = 'TOKEN_TOC_CHAPTER_OFFICE'

TOKEN_TOC_CHAPTER_ITEM_START = 'TOKEN_TOC_CHAPTER_ITEM_START'
TOKEN_TOC_CHAPTER_ITEM_CONTINUE = 'TOKEN_TOC_CHAPTER_ITEM_CONTINUE'


# chapter topics
TOKEN_CHAPTER_HEADER = 'TOKEN_CHAPTER_HEADER'  # "פרק ראשון"

TOKEN_CHAPTER_OFFICE_NAME = 'TOKEN_CHAPTER_OFFICE_NAME'

TOKEN_CHAPTER_TOPIC_TITLE_START = 'TOKEN_CHAPTER_TOPIC_TITLE_START'
TOKEN_CHAPTER_TOPIC_TITLE_CONTINUE = 'TOKEN_CHAPTER_TOPIC_TITLE_CONTINUE'

TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_START = 'TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_START'
TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_CONTINUE = 'TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_CONTINUE'

# defects
TOKEN_DEFECT_HEADER = 'TOKEN_DEFECT_HEADER'
TOKEN_DEFECT_BODY_START = 'TOKEN_DEFECT_BODY_START'
TOKEN_DEFECT_BODY_CONTINUE = 'TOKEN_DEFECT_BODY_CONTINUE'

# defect replies
TOKEN_DEFECT_REPLY_HEADER = 'TOKEN_DEFECT_REPLY_HEADER'
TOKEN_DEFECT_REPLY_OFFICE_NAME = 'TOKEN_DEFECT_REPLY_OFFICE_NAME'
TOKEN_DEFECT_REPLY_BODY_START = 'TOKEN_DEFECT_REPLY_BODY_START'
TOKEN_DEFECT_REPLY_BODY_CONTINUE = 'TOKEN_DEFECT_REPLY_BODY_CONTINUE'


def get_alternative_office_names(path):
    r"""Read file with alternative office names and return it.

    File is in structure (YAML):

    ---
    מטלות רוחב ומטלות בין-משרדיות:
      - מטלות רוחב
      - מטלות רוחב ומטלות בין משרדיות
    מערכת הבטחון:
      - מערכת הביטחון
    משרדי הממשלה:
      - משרדי ממשלה
    ---

    In the above example, "alternative name x" should be treated
    the same as "name 1".
    """
    with open(path, 'r') as f:
        return yaml.load(f)


def get_state_comptroller_offices_and_defects(path):
    """Load state-comptroller prefix.json output and return all offices and defects mentioned.

    Used for determining office names and defect chapter topics in this prime-minister report.
    """
    with open(path, 'r') as f:
        d = json.load(f)

    offices = d['offices_to_defects'].keys()
    defects = set(itertools.chain(*d['offices_to_defects'].values())) | set(itertools.chain(*d['keywords_to_defects'].values()))

    return offices, defects


# FIXME TOC items in 67b (b NOT a!) are not tokenized because they are תקציר
# chapters (see the first chapter)
def tokenize_toc(tokenized_lines, office_names):
    """Iterate lines and mark ones which are part of the table of contents.

    Return TOC item list, which are used as ending separators for defect sections.
    """
    # we are iterating the TOC sectcion multiple times here
    # and tokenizing different categories in a specific order.
    # see regex comments at the top of this file for more information

    first_episode_encountered_counter = 0
    for line_num, line in enumerate(tokenized_lines):
        if line['type'] is not None:
            continue

        txt = line['text']

        # find TOC start and end lines and tokenize them as such
        if regex.TOC_START_RE.search(txt) is not None:
            line['type'] = TOKEN_TOC_HEADER
            toc_start_line_num = line_num

            # the line identifying the end of the TOC is the the first chapter title,
            # which is also the line coming right after the TOC title
            #
            # generate a regex and search for it from here on to identify
            # the end of the TOC
            toc_end_txt = tokenized_lines[line_num + 1]['text'].strip()

            continue

        try:
            toc_end_txt
        except NameError:
            continue
        else:
            if txt.strip() in toc_end_txt:
                first_episode_encountered_counter += 1
                if first_episode_encountered_counter == 2:
                    # TODO need to tokenize all chapter headers in the document,
                    # this is just the first one
                    line['type'] = TOKEN_CHAPTER_HEADER
                    toc_end_line_num = line_num
                    break

    tokenized_toc_lines = tokenized_lines[toc_start_line_num:toc_end_line_num + 1]

    # run over TOC lines again, and tokenize office names
    for line in tokenized_toc_lines:  # inclusive for end line
        if line['type'] is not None:
            continue

        if line['type'] == TOKEN_TOC_HEADER:
            continue

        if line['text'].strip() in office_names:
            line['type'] = TOKEN_TOC_CHAPTER_OFFICE
            continue

    # run over TOC lines again, and tokenize chapter titles
    #
    # TODO might also need to tokenize chapter number titles e.g. "פרק שני"
    # should probably set multiple line['type'] i.e. the value should be a list
    # of types
    for i, line in enumerate(tokenized_toc_lines):
        # skip tokenized lines
        # or lines coming right after a chapter office line
        if line['type'] is not None or tokenized_toc_lines[i-1]['type'] == TOKEN_TOC_CHAPTER_OFFICE:
            continue

        txt = line['text'].strip()
        next_line_txt = tokenized_toc_lines[i+1]['text'].strip()
        second_next_line_txt = tokenized_toc_lines[i+1]['text'].strip()
        if regex.TOC_CHAPTER_NUMBER_RE.search(txt) is not None:
            line['type'] = TOKEN_TOC_CHAPTER_NUMBER
            continue
        if tokenized_toc_lines[i-1]['type'] == TOKEN_TOC_CHAPTER_TITLE_START:
            line['type'] = TOKEN_TOC_CHAPTER_TITLE_CONTINUE
            continue
        if regex.TOC_CHAPTER_TITLE_RE.search(txt) is not None:
            line['type'] = TOKEN_TOC_CHAPTER_TITLE_START
            continue

    # run over TOC lines again, and tokenize chapter items
    for i, line in enumerate(tokenized_toc_lines):
        # skip tokenized lines
        if line['type'] is not None:
            continue

        txt = line['text'].strip()
        if regex.TOC_CHAPTER_ITEM_RE_START.search(txt) is not None:
            line['type'] = TOKEN_TOC_CHAPTER_ITEM_START
            continue
        if regex.TOC_CHAPTER_ITEM_RE_END.search(txt) is not None:
            line['type'] = TOKEN_TOC_CHAPTER_ITEM_CONTINUE
            continue
        if (tokenized_toc_lines[i-1]['type'] in [TOKEN_TOC_CHAPTER_ITEM_START, TOKEN_TOC_CHAPTER_ITEM_CONTINUE] and
                regex.TOC_CHAPTER_ITEM_RE_END.search(txt) is None):
            line['type'] = TOKEN_TOC_CHAPTER_ITEM_CONTINUE
            continue


def tokenize_chapter_office_names(tokenized_lines, office_names):
    r"""Iterate lines and mark lines containing only office names.

    Most chapters (except special ones) focus on a single office in every sub-chapter:

    רשות המסים בישראל  <-- THIS

    מיסוי הכנסות של תושבי ישראל בחו"ל

    הגופים המבוקרים: רשות המסים, החשב הכללי - משרד האוצר, המוסד לביטוח
    לאומי, בנק ישראל.

    ליקוי

    ---

    Also, office names are sometimes mentioned before in a defect reply

    תגובה

    רשות המסים  <-- This

    2-1 .רשות המסים סובלת ממצוקת כוח אדם, הן בשדה והן במטה. עם זאת
    העוסקים במלאכה מיומנים ומנוסים בתחום ובמידת הצורך נעזרים
    ברפרנטים מהמטה. המשרדים בודקי
    """
    for i, line in enumerate(tokenized_lines):
        if line['type'] is not None:
            continue

        txt = line['text'].strip()
        if txt in office_names:
            if tokenized_lines[i-1]['type'] == TOKEN_DEFECT_REPLY_HEADER:
                line['type'] = TOKEN_DEFECT_REPLY_OFFICE_NAME
            else:
                line['type'] = TOKEN_CHAPTER_OFFICE_NAME


def tokenize_chapter_topic_discussed_offices(tokenized_lines):
    r"""Iterate lines and mark chapter topic lines mentioning office names currently being discussed.

    New topics are introduced in the following structure
    (without the english prefixes):

    topic title: התעשייה האווירית לישראל בע"מ
    \n
    topic subtitle: בקרה על יישום החלטות הדירקטוריון וההנהלה בתעשייה האווירית לישראל בע"מ
    \n
    office names: הגופים המבוקרים: התעשייה האווירית לישראל בע"מ, רשות החברות הממשלתיות.  <-- THIS
    """
    for i, line in enumerate(tokenized_lines):
        if line['type'] is not None:
            continue

        txt = line['text'].strip()
        if regex.CHAPTER_TOPIC_DISCUSSED_OFFICES_RE.search(txt.strip()) is not None:
            line['type'] = TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_START
            continue
        if tokenized_lines[i-1]['type'] in [TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_START, TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_CONTINUE]:
            line['type'] = TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_CONTINUE


def tokenize_defect_headers(tokenized_lines):
    r"""Iterate lines and mark lines opening a new defect section.

    Each defect reply has a "ליקוי" string just before the description:

    ליקוי  <-- THIS

    2. הועלה כי דיווחי התאגידים הבנקאיים לבנק ישראל על העברות כספים של תושבי
    ישראל לחו"ל המבוצעים באמצעותם, משקפים רק חלק מהעברות כספים אלה. למשל, על
    ...

    תגובה

    רשות המסים

    1-2. רשות המסים סובלת ממצוקת כוח אדם, הן בשדה והן במטה. עם זאת העוסקים
    במלאכה מיומנים ומנוסים בתחום ובמידת הצורך נעזרים ברפרנטים מהמטה. המשרדים
    ...
    """
    for line in tokenized_lines:
        if line['type'] is not None:
            continue

        if regex.DEFECT_HEADER_RE.search(line['text']) is not None:
            line['type'] = TOKEN_DEFECT_HEADER


# TODO tokenize office name which comes straight after a defect reply
# (like "רשות המסים" in the func doc comment here)
def tokenize_reply_headers(tokenized_lines):
    r"""Iterate lines and mark lines opening a new defect reply section.

    Each defect reply has a "תגובה" string just before the description:

    ליקוי

    2. הועלה כי דיווחי התאגידים הבנקאיים לבנק ישראל על העברות כספים של תושבי
    ישראל לחו"ל המבוצעים באמצעותם, משקפים רק חלק מהעברות כספים אלה. למשל, על
    ...

    תגובה  <-- THIS

    רשות המסים

    1-2. רשות המסים סובלת ממצוקת כוח אדם, הן בשדה והן במטה. עם זאת העוסקים
    במלאכה מיומנים ומנוסים בתחום ובמידת הצורך נעזרים ברפרנטים מהמטה. המשרדים
    ...
    """
    for line in tokenized_lines:
        if line['type'] is not None:
            continue

        if regex.DEFECT_REPLY_HEADER_RE.search(line['text']) is not None:
            line['type'] = TOKEN_DEFECT_REPLY_HEADER


# TODO BUGGY FUNCTION
def tokenize_chapter_topics(tokenized_lines, state_comptroller_offices, state_comptroller_defects):
    r"""Iterate lines and mark lines opening a new chapter topic.

    New topics are introduced in the following structure
    (without the english prefixes):

    topic title: התעשייה האווירית לישראל בע"מ  <-- THIS
    \n
    topic subtitle: בקרה על יישום החלטות הדירקטוריון וההנהלה בתעשייה האווירית לישראל בע"מ  <-- THIS TOO
    \n
    office names: הגופים המבוקרים: התעשייה האווירית לישראל בע"מ, רשות החברות הממשלתיות.
    """
    for i, line in enumerate(tokenized_lines):
        if line['type'] is not None:
            continue

        txt = line['text'].strip()

        for defect in state_comptroller_defects:
            if txt in defect:
                if tokenized_lines[i-1]['type'] in [TOKEN_CHAPTER_TOPIC_TITLE_START, TOKEN_CHAPTER_TOPIC_TITLE_CONTINUE]:
                    line['type'] = TOKEN_CHAPTER_TOPIC_TITLE_CONTINUE
                else:
                    line['type'] = TOKEN_CHAPTER_TOPIC_TITLE_START

                continue


def tokenize_defect_bodies(tokenized_lines):
    """Iterate through all lines and mark lines which are part of a defect body.

    ליקוי

    ---> THIS:
    2. הועלה כי דיווחי התאגידים הבנקאיים לבנק ישראל על העברות כספים של תושבי
    ישראל לחו"ל המבוצעים באמצעותם, משקפים רק חלק מהעברות כספים אלה. למשל, על
    ...
    """
    for i, line in enumerate(tokenized_lines):
        if line['type'] is not None:
            continue

        prev_line_type = tokenized_lines[i-1]['type']
        if prev_line_type == TOKEN_DEFECT_HEADER:
            line['type'] = TOKEN_DEFECT_BODY_START
            continue
        if prev_line_type in [TOKEN_DEFECT_BODY_START, TOKEN_DEFECT_BODY_CONTINUE]:
            line['type'] = TOKEN_DEFECT_BODY_CONTINUE


def tokenize_defect_reply_bodies(tokenized_lines):
    """Iterate through all lines and mark lines which are part of a defect reply body.

    ליקוי

    8. בתע"א לא נמצאו תימוכין לתשובות שהעבירו מנהלי התע"א לעוזרי המנכ"ל
    ולמנכ"ל בעניין יישום החלטות ההנהלה, לרבות הסיבות לעיכוב ביישומן. כמו כן,
    ...

    תגובה

    התעשייה האווירית

    ---> THIS:
    7-8. עוזר המנכ"ל הינו הגורם האחראי ובעל הסמכות למעקב ואכיפת החלטות
    המנכ"ל. פניות מסוימות בנושא הועברו באופן שוטף למנכ"ל ו/או לבעלי תפקידים
    ...
    """
    for i, line in enumerate(tokenized_lines):
        if line['type'] is not None:
            continue

        prev_line_type = tokenized_lines[i-1]['type']

        if prev_line_type in [TOKEN_DEFECT_REPLY_HEADER, TOKEN_DEFECT_REPLY_OFFICE_NAME]:
            line['type'] = TOKEN_DEFECT_REPLY_BODY_START
            continue
        if prev_line_type in [TOKEN_DEFECT_REPLY_BODY_START, TOKEN_DEFECT_REPLY_BODY_CONTINUE]:
            line['type'] = TOKEN_DEFECT_REPLY_BODY_CONTINUE


def tokenize(lines, alternative_office_names_path, state_comptroller_preface_path):
    r"""Tokenize all lines (by line, not word) according to type.

    The general structure of the document is as follows:

    ליקוי
    \d. <Defect description>
    תגובה
    <Replying entity name>
    <Reply descriptiption>
    """
    tokenized_lines = []
    for line in lines:
        tokenized_lines.append({'text': line, 'type': None})

    alternative_office_names_dict = get_alternative_office_names(alternative_office_names_path)
    alternative_office_names = []
    for name, alternative_names in alternative_office_names_dict.items():
        alternative_office_names.append(name)
        alternative_office_names += alternative_names

    state_comptroller_offices, state_comptroller_defects = get_state_comptroller_offices_and_defects(state_comptroller_preface_path)
    combined_office_names = set(alternative_office_names) | set(state_comptroller_offices)

    tokenize_toc(tokenized_lines, combined_office_names)
    tokenize_defect_headers(tokenized_lines)
    tokenize_reply_headers(tokenized_lines)
    tokenize_chapter_office_names(tokenized_lines, combined_office_names)
    tokenize_chapter_topic_discussed_offices(tokenized_lines)
    # TODO bug in here
    tokenize_chapter_topics(tokenized_lines, state_comptroller_offices, state_comptroller_defects)
    tokenize_defect_bodies(tokenized_lines)
    tokenize_defect_reply_bodies(tokenized_lines)

    return tokenized_lines


# TODO
# def print_tokens(tokenized_lines):
#     """Iterate all tokenized lines and prints their content."""
#     for line in tokenized_lines:
#         txt = line['text']
#         typ = line['type']

#         if typ == TOKEN_DEFECT_SECTION_START:
#             continue

#         elif typ == TOKEN_DEFECT_BODY_START:
#             number = get_defect_number(txt)
#             body = get_defect_body(txt)

#             print('DEFECT START', '({})'.format(number), body)

#         elif typ == TOKEN_DEFECT_BODY_CONTINUE:
#             print('DEFECT CONTINUE', txt)

#         elif typ == TOKEN_REPLY_SECTION_START:
#             continue

#         elif typ == TOKEN_REPLY_OFFICE_NAME:
#             print('DEFECT OFFICE NAME', txt)
#             continue

#         elif typ == TOKEN_REPLY_BODY_START:
#             number_start_str, number_end_str = get_reply_number_range(txt)
#             start = int(number_start_str)
#             if number_end_str is not None:
#                 end = int(number_end_str)
#                 number_range = list(range(start, end)) + [end]
#             else:
#                 number_range = [start]

#             body = get_reply_body(txt)

#             print('REPLY START', '({})'.format(number_range), body)

#         elif typ == TOKEN_REPLY_BODY_CONTINUE:
#             print('REPLY CONTINUE', txt)

#         elif typ == TOKEN_TOPIC_START:
#             print('TOPIC START', txt)

#         elif typ == TOKEN_TOPIC_CONTINUE:
#             print('TOPIC CONTINUE', txt)


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        LINES = [l for l
                 in f.readlines()
                 if l.strip() != '']  # filter empty lines

    TOKENIZED_LINES = tokenize(LINES, sys.argv[2], sys.argv[3])

    for l in TOKENIZED_LINES:
        print(l['type'], l['text'][:30])

    # print_tokens(TOKENIZED_LINES)
