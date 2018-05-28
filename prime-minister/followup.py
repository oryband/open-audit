#!/usr/bin/env python

import json
import itertools
import re
import sys

import yaml


# regex for detecting TOC opening header "תוכן העניינים"
# allowing for some missing redundant characters and padding spaces
TOC_START_RE = re.compile(r'^\s*תוכן [ה]?עני[י]?נים\s*$')

# regex for detecting TOC end (not including this line).
# this is the instance of "פרק ראשון"
TOC_END_RE = re.compile(r'^\s*פרק\s+ראשון\s*$')

# regexes for detecting a TOC chapter number in text form
# WITHOUT any following title, for example:
#
# פרק שני
TOC_CHAPTER_NUMBER_RE = re.compile(r'^\s*(פרק\s+\w+)\s*$')

# regexes for detecting a TOC chapter number and a following title and number, for example:
#
# פרק חמישי - מוסדות המדינה, חברות ממשלתיות  <-- THIS
#
# ותאגידים  <-- THIS
#
# הרשות להגנת הצרכן ולסחר הוגן והמועצה הישראלית לצרכנות
#
# 1.  פעילות הרשות להגנת הצרכן ולסחר הוגן והמועצה הישראלית לצרכנות...151
#
# NOTE there is a chance for false positives here: if the second line was
# missing, the third line will be counted as part of the title if though it's an office.
#
# the easiest solution for this that i thought of is the following:
# - construct a list of common chapter alternative names e.g. מוסדות המדינה | מוסדות המדינה ותאגידים
#   then tokenize them first (as chapters)
# - fetch all office names from state-comptroller output files,
#   and in addition construct a common office alternative names e.g. משרד הבטחון | משרד הב_י_טחון
#   then tokenize them second (as offices)
TOC_CHAPTER_TITLE_RE = re.compile(r'^\s*(פרק\s+\w+)\s+-\s+(.+)$')

# regex for detecting a TOC chapter office, for example:
# פרק חמישי - מוסדות המדינה, חברות ממשלתיות
#
# ותאגידים
#
# הרשות להגנת הצרכן ולסחר הוגן והמועצה הישראלית לצרכנות  <--- THIS
#
# 1.  פעילות הרשות להגנת הצרכן ולסחר הוגן והמועצה הישראלית לצרכנות...151
TOC_CHAPTER_OFFICE_RE = re.compile(r'^\s*(.*)\s*$')

# regex for detecting a TOC item in the form of:
#
# 1.  החברה לאיתור והשבת נכסים של נספי השואה בע"מ ופעולות המדינה לאיתור
#     ולהשבה של נכסי
#         הנספים.....................................................49
#
# NOTE we're ignoring the multiple dots and page number, and taking just the
# text.
TOC_CHAPTER_ITEM_RE_START = re.compile(r'^\s*\d+\.\s+(.+?)(?:\.{3,}\d+)?$')
TOC_CHAPTER_ITEM_RE_CONTINUE = re.compile(r'^\s*(.*)\s*$')
TOC_CHAPTER_ITEM_RE_END = re.compile(r'^\s*(.+?)\.{3,}\d+$')

# regex for joining TOC items which are split across multiple lines.
# should be used with re.sub() for removing newlines
# and truncating extra spaces.
TOC_ITEM_JOIN_RE = re.compile(r'\n\s*')

# regex searching for office names being discussed in a chapter.
CHAPTER_TOPIC_DISCUSSED_OFFICES_RE = re.compile(r'^\s*הגופים המבוקרים:\s(.+)$')

# regex searching for defect number (or numbers) in the beginning of a paragraph.
# for example: '2. bla bla bla' will fetch "2".
DEFECT_NUMBER_RE = re.compile(r'^\s*(\d+)\S*')

DEFECT_HEADER_RE = re.compile(r'^\s*ליקוי\s*$')

# regex for getting entire line without the first word
# (which is a defect number)
DEFECT_DESCRIPTION_RE = re.compile(r'^\s*\S+\s+(.*)')

# similar regex to DEFECT_NUMBER_RE but for defect reply.
# note some replies correspond to multiple defects in a single paragraph,
# and mention a range of defect numbers.
#
# For example: '2-4. bla bla bla' will fetch ["2", "4"]
# and means this reply corresponds to defects #2,#3,#4
DEFECT_REPLY_NUMBER_RE = re.compile(r'^\s*(\d+)(?:-(\d+))?\S*')

DEFECT_REPLY_HEADER_RE = re.compile(r'^\s*תגובה(?:\s+כללית)?\s*$')


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


def get_defect_number(line):
    """Get defect description from line, ignoring defect description."""
    words = line.split()
    match = DEFECT_NUMBER_RE.search(words[0])
    reply_number_str = match.group(1)
    return int(reply_number_str)


def get_defect_body(line):
    """Get defect description from line, ignoring defect number."""
    return DEFECT_DESCRIPTION_RE.search(line).group(1)


def get_reply_number_range(line):
    """Get reply number range from line, ignoring defect description.

    Note some replies correspond to multiple defects in a single paragraph,
    and mention a range of multiple defect numbers.

    For example: '2-4. bla bla bla' will fetch ["2", "4"]
    and means this reply corresponds to defects #2,#3,#4
    """
    words = line.split()
    match = REPLY_NUMBER_RE.search(words[0])
    defect_number_start_str = match.group(1)
    try:
        # process defect number range end if found
        second_number_end_str = match.group(2)
    except IndexError:
        second_number_end_str = None
    return int(defect_number_start_str), second_number_end_str


def get_reply_body(line):
    """Get defect reply from line, ignoring defect number.

    Note we're using the same regex as in get_defect_body().
    This is intentional since the text structure is similiar.
    """
    return DEFECT_DESCRIPTION_RE.search(line).group(1)


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
        if TOC_START_RE.search(txt) is not None:
            line['type'] = TOKEN_TOC_HEADER
            toc_start_line_num = line_num
            continue

        if TOC_END_RE.search(txt) is not None:
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
        if TOC_CHAPTER_NUMBER_RE.search(txt) is not None:
            line['type'] = TOKEN_TOC_CHAPTER_NUMBER
            continue
        if tokenized_toc_lines[i-1]['type'] == TOKEN_TOC_CHAPTER_TITLE_START:
            line['type'] = TOKEN_TOC_CHAPTER_TITLE_CONTINUE
            continue
        if TOC_CHAPTER_TITLE_RE.search(txt) is not None:
            line['type'] = TOKEN_TOC_CHAPTER_TITLE_START
            continue

    # run over TOC lines again, and tokenize chapter items
    for i, line in enumerate(tokenized_toc_lines):
        # skip tokenized lines
        if line['type'] is not None:
            continue

        txt = line['text'].strip()
        if TOC_CHAPTER_ITEM_RE_START.search(txt) is not None:
            line['type'] = TOKEN_TOC_CHAPTER_ITEM_START
            continue
        if TOC_CHAPTER_ITEM_RE_END.search(txt) is not None:
            line['type'] = TOKEN_TOC_CHAPTER_ITEM_CONTINUE
            continue
        if (tokenized_toc_lines[i-1]['type'] in [TOKEN_TOC_CHAPTER_ITEM_START, TOKEN_TOC_CHAPTER_ITEM_CONTINUE] and
                TOC_CHAPTER_ITEM_RE_END.search(txt) is None):
            line['type'] = TOKEN_TOC_CHAPTER_ITEM_CONTINUE
            continue


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
        if CHAPTER_TOPIC_DISCUSSED_OFFICES_RE.search(txt.strip()) is not None:
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

        if DEFECT_HEADER_RE.search(line['text']) is not None:
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

        if DEFECT_REPLY_HEADER_RE.search(line['text']) is not None:
            line['type'] = TOKEN_DEFECT_REPLY_HEADER


def tokenize_chapter_topics(tokenized_lines, state_comptroller_defects):
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
    tokenize_chapter_topics(tokenized_lines, state_comptroller_defects)
    # TODO this is what's left
    tokenize_defect_bodies(tokenized_lines)
    # TODO buggy function:
    tokenize_defect_reply_bodies(tokenized_lines)

    return tokenized_lines


def get_state_comptroller_offices_and_defects(path):
    """Load state-comptroller prefix.json output and return all offices and defects mentioned.

    Used for determining office names and defect chapter topics in this prime-minister report.
    """
    with open(path, 'r') as f:
        d = json.load(f)

    offices = d['offices_to_defects'].keys()
    defects = set(itertools.chain(*d['offices_to_defects'].values())) | set(itertools.chain(*d['keywords_to_defects'].values()))

    return offices, defects


def print_tokens(tokenized_lines):
    """Iterate all tokenized lines and prints their content."""
    for line in tokenized_lines:
        txt = line['text']
        typ = line['type']

        if typ == TOKEN_DEFECT_SECTION_START:
            continue

        elif typ == TOKEN_DEFECT_BODY_START:
            number = get_defect_number(txt)
            body = get_defect_body(txt)

            print('DEFECT START', '({})'.format(number), body)

        elif typ == TOKEN_DEFECT_BODY_CONTINUE:
            print('DEFECT CONTINUE', txt)

        elif typ == TOKEN_REPLY_SECTION_START:
            continue

        elif typ == TOKEN_REPLY_OFFICE_NAME:
            print('DEFECT OFFICE NAME', txt)
            continue

        elif typ == TOKEN_REPLY_BODY_START:
            number_start_str, number_end_str = get_reply_number_range(txt)
            start = int(number_start_str)
            if number_end_str is not None:
                end = int(number_end_str)
                number_range = list(range(start, end)) + [end]
            else:
                number_range = [start]

            body = get_reply_body(txt)

            print('REPLY START', '({})'.format(number_range), body)

        elif typ == TOKEN_REPLY_BODY_CONTINUE:
            print('REPLY CONTINUE', txt)

        elif typ == TOKEN_TOPIC_START:
            print('TOPIC START', txt)

        elif typ == TOKEN_TOPIC_CONTINUE:
            print('TOPIC CONTINUE', txt)


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        LINES = [l for l
                 in f.readlines()
                 if l.strip() != '']  # filter empty lines

    TOKENIZED_LINES = tokenize(LINES, sys.argv[2], sys.argv[3])
    # print_tokens(TOKENIZED_LINES)
