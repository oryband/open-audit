"""Tokenize table of contents (TOC)."""
import regex
import tokens


def tokenize(tokenized_lines, office_names):
    """Iterate lines and mark ones which are part of the table of contents.

    Return TOC item list, which are used as ending separators for defect sections.
    """
    # we are iterating the TOC section multiple times here
    # and tokenizing different categories in a specific order.
    # see regex comments at the top of this file for more information
    tokenized_lines = find_borders(tokenized_lines)
    tokenize_office_names(tokenized_lines, office_names)
    tokenize_chapter_titles(tokenized_lines)
    tokenize_chapter_items(tokenized_lines)

    return tokenized_lines


# TODO XXX this function is still buggy. start line is found AFTER the end line
# in 67b report.
#
# TODO XXX in addition the tokenization of some specific token types in *non*-TOC lines
# in 67a is wrong, go over the document and see
def find_borders(tokenized_lines):
    """Iterate TOC lines and find start and end of TOC section.

    Ignores the summary "תקצירים" section which optionally comes at the beginning
    of the TOC in some reports.
    """
    # we identify the end of the TOC and beginning of actual content of the
    # report by looking at the first TOC title and searching
    # for when it appears again for the second time.
    #
    # this can either be the beginning of the summary chapter,
    # or if the summary doesn't exist in the report - the first chapter.
    toc_start_line_num = None
    toc_end_line_num = None

    # this is used to find the first and second occurences
    # of summary 'תקציר' or 'פרק ראשון' and then we'll know where the TOC titles starts and ends.
    summary_title = None

    for line_num, line in enumerate(tokenized_lines):
        # if both TOC start + end border lines were found,
        # there's nothing left to do
        if toc_start_line_num is not None and toc_end_line_num is not None:
            return tokenized_lines[toc_start_line_num:toc_end_line_num]

        if line['type'] is not None:
            continue

        txt = line['text']

        # find TOC start and end lines and tokenize them as such
        if regex.TOC_START_RE.search(txt) is not None:
            line['type'] = tokens.TOKEN_TOC_HEADER

            continue

        # find optional summary section
        #
        # NOTE this appears only in some reports
        #
        # TODO tokenize this section
        if summary_title is None and regex.TOC_BORDER_IDENTIFIER_SUMMARY_RE.search(txt) is not None:
            # we'll search for this text for the second occurence of the summary title
            summary_title = txt.strip()

            continue

        if summary_title is not None and summary_title.startswith(txt.strip()):
            toc_end_line_num = line_num

            continue

        if regex.TOC_BORDER_IDENTIFIER_FIRST_CHAPTER_RE.search(txt) is not None:
            # set the start line by checking if it isn't defined yet
            if toc_start_line_num is None:
                toc_start_line_num = line_num

                continue

            if toc_end_line_num is None:
                toc_end_line_num = line_num

            continue

    # reaching this line mean we iterated over all document lines and didn't
    # find TOC borders, should be impossible
    raise RuntimeError


def tokenize_office_names(tokenized_lines, office_names):
    """Run over TOC lines and tokenize office names."""
    for line in tokenized_lines:  # inclusive for end line
        if line['type'] is not None:
            continue

        if line['type'] == tokens.TOKEN_TOC_HEADER:
            continue

        if line['text'].strip() in office_names:
            line['type'] = tokens.TOKEN_TOC_CHAPTER_OFFICE
            continue


def tokenize_chapter_titles(tokenized_lines):
    """Run over TOC lines, and tokenize chapter titles."""
    # TODO might also need to tokenize chapter number titles e.g. "פרק שני"
    # should probably set multiple line['type'] i.e. the value should be a list
    # of types
    for i, line in enumerate(tokenized_lines):
        # skip tokenized lines
        # or lines coming right after a chapter office line
        if (line['type'] is not None or
                tokenized_lines[i-1]['type'] == tokens.TOKEN_TOC_CHAPTER_OFFICE):
            continue

        txt = line['text'].strip()
        if regex.TOC_CHAPTER_NUMBER_RE.search(txt) is not None:
            line['type'] = tokens.TOKEN_TOC_CHAPTER_NUMBER
            continue
        if tokenized_lines[i-1]['type'] == tokens.TOKEN_TOC_CHAPTER_TITLE_START:
            line['type'] = tokens.TOKEN_TOC_CHAPTER_TITLE_CONTINUE
            continue
        if regex.TOC_CHAPTER_TITLE_RE.search(txt) is not None:
            line['type'] = tokens.TOKEN_TOC_CHAPTER_TITLE_START
            continue


def tokenize_chapter_items(tokenized_lines):
    """Run over TOC lines and tokenize chapter items."""
    for i, line in enumerate(tokenized_lines):
        # skip tokenized lines
        if line['type'] is not None:
            continue

        txt = line['text'].strip()
        if regex.TOC_CHAPTER_ITEM_RE_START.search(txt) is not None:
            line['type'] = tokens.TOKEN_TOC_CHAPTER_ITEM_START
            continue
        if regex.TOC_CHAPTER_ITEM_RE_END.search(txt) is not None:
            line['type'] = tokens.TOKEN_TOC_CHAPTER_ITEM_CONTINUE
            continue
        if (tokenized_lines[i-1]['type'] in [tokens.TOKEN_TOC_CHAPTER_ITEM_START,
                                             tokens.TOKEN_TOC_CHAPTER_ITEM_CONTINUE] and
                regex.TOC_CHAPTER_ITEM_RE_END.search(txt) is None):
            line['type'] = tokens.TOKEN_TOC_CHAPTER_ITEM_CONTINUE
            continue
