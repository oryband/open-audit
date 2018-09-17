#!/usr/bin/env python
"""Process tokens from tokenize.py and turn them into text objects.

These objects could then be stored in a database and eventually displayed on a website.
"""
import sys

from tokenize import tokenize
import tokens


def group_tokens(tokenized_lines):
    """Iterate over tokenized lines and group them into token groups related to one another."""
    token_groups = []
    for line in tokenized_lines:
        typ, txt = line['type'], line['text']

        if typ in [tokens.TOKEN_TOC_CHAPTER_NUMBER_WITH_TITLE_CONTINUE,
                   tokens.TOKEN_TOC_CHAPTER_ITEM_MULTI_LINE_CONTINUE,
                   tokens.TOKEN_CHAPTER_TOPIC_TITLE_CONTINUE,
                   tokens.TOKEN_CHAPTER_TOPIC_DISCUSSED_OFFICES_CONTINUE,
                   tokens.TOKEN_DEFECT_BODY_CONTINUE,
                   tokens.TOKEN_DEFECT_REPLY_BODY_CONTINUE,
                   ]:
            token_groups[-1].append(line)

            continue

        token_groups.append([line])

    return token_groups


def text_objects_from_token_groups(token_groups):
    current_chapter, current_topic = None, None
    for token_group in token_groups:
        first_token_type = token_group[0]['type']
        first_token_text = token_group[0]['text']

        if first_token_type == tokens.TOKEN_CHAPTER_NUMBER:
            chapter_number_text = first_token_text.split()[1]
            chapter_number = chapter_text_to_number(chapter_number_text)
            print(chapter_number)


def chapter_text_to_number(text):
    """Receive chapter number in text form and return its number."""
    for i, number_text in enumerate(['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שביעי', 'שמיני', 'תשיעי'],
                                    1):
        if text == number_text:
            return i

    raise RuntimeError('unexpected chapter text {}, cannot convert to number'.format(text))


def demo():
    with open(sys.argv[1], 'r') as f:
        lines = [l for l
                 in f.readlines()
                 if l.strip() != '']  # filter empty lines

    tokenized_lines = tokenize(lines, sys.argv[2], sys.argv[3])
    token_groups = group_tokens(tokenized_lines)

    text_objects_from_token_groups(token_groups)


if __name__ == '__main__':
    demo()
