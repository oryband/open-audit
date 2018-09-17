#!/usr/bin/env python

import sys

import regex


def get_defect_number(line):
    """Get defect description from line, ignoring defect description."""
    words = line.split()
    match = regex.DEFECT_NUMBER_RE.search(words[0])
    reply_number_str = match.group(1)
    return int(reply_number_str)


def get_defect_body(line):
    """Get defect description from line, ignoring defect number."""
    return regex.DEFECT_DESCRIPTION_RE.search(line).group(1)


def get_reply_number_range(line):
    """Get reply number range from line, ignoring defect description.

    Note some replies correspond to multiple defects in a single paragraph,
    and mention a range of multiple defect numbers.

    For example: '2-4. bla bla bla' will fetch ["2", "4"]
    and means this reply corresponds to defects #2,#3,#4
    """
    words = line.split()
    match = regex.DEFECT_REPLY_NUMBER_RE.search(words[0])
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
    return regex.DEFECT_DESCRIPTION_RE.search(line).group(1)
