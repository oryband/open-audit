#!/usr/bin/env python
"""Process tokens from tokenize.py and turn them into text objects.

These objects could then be stored in a database and eventually displayed on a website.
"""
import sys

from tokenize import tokenize
import regex
import tokens


def group_tokens(tokenized_lines):
    """Iterate over tokenized lines and group them into token groups related to one another."""
    token_groups = []
    for tokenized_line in tokenized_lines:
        # append lines which belong to the previous token to the previous token
        # object. these are lines tokenized as "..._CONTINUE"
        if tokenized_line['type'] in [tokens.TOC_CHAPTER_NUMBER_WITH_TITLE_CONTINUE,
                                      tokens.TOC_CHAPTER_ITEM_MULTI_LINE_CONTINUE,
                                      tokens.CHAPTER_TOPIC_TITLE_CONTINUE,
                                      tokens.CHAPTER_TOPIC_DISCUSSED_OFFICES_CONTINUE,
                                      tokens.DEFECT_BODY_CONTINUE,
                                      tokens.DEFECT_REPLY_BODY_CONTINUE,
                                      ]:
            token_groups[-1].append(tokenized_line)

            continue

        # otherwise, create a new tokenized line object
        token_groups.append([tokenized_line])

    return token_groups


def text_objects_from_token_groups(token_groups):
    """Iterate over token groups, categorize them into tokens and turn them into dictionaries.

    Tokens in a single group can be (for example) the chapter number and chapter text.
    """
    for token_group in token_groups:
        # initialize new token object
        token_obj = {'type': None, 'text': ""}
        match = None

        # first tokenized line in every token group has special information
        # that needs to be extracted e.g. chapter number from a line that start
        # with the number and continues with the chapter text
        first_type = token_group[0]['type']
        first_text = token_group[0]['text']
        if first_type in [tokens.CHAPTER_NUMBER,
                          tokens.TOC_CHAPTER_NUMBER_WITH_TITLE_START,
                          tokens.TOC_CHAPTER_NUMBER_WITH_TITLE_CROSS_OFFICE]:

            if first_type == tokens.CHAPTER_NUMBER:
                match = regex.TOC_CHAPTER_NUMBER_RE.search(first_text)
            elif first_type == tokens.TOC_CHAPTER_NUMBER_WITH_TITLE_START:
                match = regex.TOC_CHAPTER_NUMBER_WITH_TITLE_RE.search(first_text)
            elif first_type == tokens.TOC_CHAPTER_NUMBER_WITH_TITLE_CROSS_OFFICE:
                match = regex.TOC_CHAPTER_NUMBER_WITH_TITLE_CROSS_OFFICE_RE.search(first_text)

            # fetch chapter number and remember it
            chapter_number_text = match.group(regex.REGEX_GROUP_TOC_CHAPTER_NUMBER)

            current_chapter = chapter_text_to_number(chapter_number_text)
            print('set chapter number to "{}"'.format(current_chapter))
            token_obj['type'] = tokens.OBJ_TOC_CHAPTER

        # iterate all tokenized lines in group and construct the token object
        for tokenized_line in token_group:
            typ, txt = tokenized_line['type'], tokenized_line['text']

            # append lines which belong to the previous token to the previous token
            # object. these are lines tokenized as "..._CONTINUE"
            if typ in [tokens.TOC_CHAPTER_NUMBER_WITH_TITLE_CONTINUE,
                       tokens.TOC_CHAPTER_ITEM_MULTI_LINE_CONTINUE,
                       tokens.CHAPTER_TOPIC_TITLE_CONTINUE,
                       tokens.CHAPTER_TOPIC_DISCUSSED_OFFICES_CONTINUE,
                       tokens.DEFECT_BODY_CONTINUE,
                       tokens.DEFECT_REPLY_BODY_CONTINUE,
                       ]:
                token_obj['text'] += txt

                continue

            if typ == tokens.TOC_CHAPTER_NUMBER:
                continue
            elif typ == tokens.TOC_CHAPTER_NUMBER_WITH_TITLE_START:
                token_obj['text'] = regex.TOC_CHAPTER_NUMBER_WITH_TITLE_RE.search(txt).group(regex.REGEX_GROUP_TEXT)
            elif typ == tokens.TOC_CHAPTER_NUMBER_WITH_TITLE_CROSS_OFFICE:
                token_obj['text'] = regex.TOC_CHAPTER_NUMBER_WITH_TITLE_CROSS_OFFICE_RE.search(txt).group(regex.REGEX_GROUP_TEXT)
            elif typ == tokens.TOC_CHAPTER_OFFICE:
                token_obj['text'] = regex.TOC_CHAPTER_OFFICE_RE.search(txt).group(regex.REGEX_GROUP_TEXT)
            elif typ == tokens.TOC_CHAPTER_ITEM_ONE_LINE:
                token_obj['text'] = regex.TOC_CHAPTER_ITEM_RE_ONE_LINE.search(txt).group(regex.REGEX_GROUP_TEXT)


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
