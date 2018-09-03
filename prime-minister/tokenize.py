#!/usr/bin/env python
"""Tokenize prime minister followup reports."""

import json
import itertools
import re
import sys

import yaml

import regex
import toc
import tokens


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
            if tokenized_lines[i-1]['type'] == tokens.TOKEN_DEFECT_REPLY_HEADER:
                line['type'] = tokens.TOKEN_DEFECT_REPLY_OFFICE_NAME
            else:
                line['type'] = tokens.TOKEN_CHAPTER_OFFICE_NAME


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
            line['type'] = tokens.TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_START
            continue
        if tokenized_lines[i-1]['type'] in [tokens.TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_START,
                                            tokens.TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_CONTINUE]:
            line['type'] = tokens.TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_CONTINUE


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
            line['type'] = tokens.TOKEN_DEFECT_HEADER


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
            line['type'] = tokens.TOKEN_DEFECT_REPLY_HEADER


def tokenize_chapter_numbers(tokenized_lines):
    r"""Iterate lines and mark lines containing only a chapter number:

    פרק שני  <-- THIS

    ניהול ותפעול של אתרי תיירות
    באגן העיר העתיקה בירושלים
    """
    for line in tokenized_lines:
        if line['type'] is not None:
            continue

        if regex.CHAPTER_NUMBER_RE.search(line['text']) is not None:
            line['type'] = tokens.TOKEN_CHAPTER_NUMBER


# TODO after each chapter header (e.g. "פרק ראשןו") there's an optional chapter
# title e.g. "פרק ראשון - היבטים בהיערכות המדינה להגנת המרחב הקיברנט".
# the chapter title is sometimes repeated twice: once in a page of it's own
# similar to a page cover, and then again right before the actual content of
# the chapter. this causes the function to tokenize the chapter title either twice
# or as a single token, with the text repeating itself within the token twice.
# both of these scenarios are wrong, and this needs to be fixed.
# imo the correct solution would be to tokenize the repetition as two separate
# different tokens, and then ignore the first one at later processing.
# there's no other visible way to make the tokenizer understand the first
# occurence is a page cover - since it is sometimes ommitted.
#
# TODO defects descriptions are sometimes written inconsistently (e.g. אזור and איזור)
# whic means they are not properly recognized in this function. might need to
# apply levenstein distances or similar methods to comensate for this
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

        # TODO levenstein here
        for defect in state_comptroller_defects:
            # ignore single words lines since they can create false positives
            if txt in defect and len(txt.split()) > 1:
                if tokenized_lines[i-1]['type'] in [tokens.TOKEN_CHAPTER_TOPIC_TITLE_START,
                                                    tokens.TOKEN_CHAPTER_TOPIC_TITLE_CONTINUE]:
                    line['type'] = tokens.TOKEN_CHAPTER_TOPIC_TITLE_CONTINUE
                else:
                    line['type'] = tokens.TOKEN_CHAPTER_TOPIC_TITLE_START

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
        if prev_line_type == tokens.TOKEN_DEFECT_HEADER:
            line['type'] = tokens.TOKEN_DEFECT_BODY_START
            continue
        if prev_line_type in [tokens.TOKEN_DEFECT_BODY_START,
                              tokens.TOKEN_DEFECT_BODY_CONTINUE]:
            line['type'] = tokens.TOKEN_DEFECT_BODY_CONTINUE


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

        if prev_line_type in [tokens.TOKEN_DEFECT_REPLY_HEADER,
                              tokens.TOKEN_DEFECT_REPLY_OFFICE_NAME]:
            line['type'] = tokens.TOKEN_DEFECT_REPLY_BODY_START
            continue
        if prev_line_type in [tokens.TOKEN_DEFECT_REPLY_BODY_START,
                              tokens.TOKEN_DEFECT_REPLY_BODY_CONTINUE]:
            line['type'] = tokens.TOKEN_DEFECT_REPLY_BODY_CONTINUE


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

    toc.tokenize(tokenized_lines, combined_office_names)
    tokenize_chapter_numbers(tokenized_lines)
    tokenize_defect_headers(tokenized_lines)
    tokenize_reply_headers(tokenized_lines)
    tokenize_chapter_office_names(tokenized_lines, combined_office_names)
    tokenize_chapter_topic_discussed_offices(tokenized_lines)
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

#         if typ == tokens.TOKEN_DEFECT_SECTION_START:
#             continue

#         elif typ == tokens.TOKEN_DEFECT_BODY_START:
#             number = get_defect_number(txt)
#             body = get_defect_body(txt)

#             print('DEFECT START', '({})'.format(number), body)

#         elif typ == tokens.TOKEN_DEFECT_BODY_CONTINUE:
#             print('DEFECT CONTINUE', txt)

#         elif typ == tokens.TOKEN_REPLY_SECTION_START:
#             continue

#         elif typ == tokens.TOKEN_REPLY_OFFICE_NAME:
#             print('DEFECT OFFICE NAME', txt)
#             continue

#         elif typ == tokens.TOKEN_REPLY_BODY_START:
#             number_start_str, number_end_str = get_reply_number_range(txt)
#             start = int(number_start_str)
#             if number_end_str is not None:
#                 end = int(number_end_str)
#                 number_range = list(range(start, end)) + [end]
#             else:
#                 number_range = [start]

#             body = get_reply_body(txt)

#             print('REPLY START', '({})'.format(number_range), body)

#         elif typ == tokens.TOKEN_REPLY_BODY_CONTINUE:
#             print('REPLY CONTINUE', txt)

#         elif typ == tokens.TOKEN_TOPIC_START:
#             print('TOPIC START', txt)

#         elif typ == tokens.TOKEN_TOPIC_CONTINUE:
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
