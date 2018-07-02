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


def find_borders(tokenized_lines):
    """Iterate TOC lines and find start and end of TOC section.

    Ignores the summary "תקצירים" section which optionally comes at the beginning
    of the TOC in some reports.
    """
    # we identify the end of the TOC and beginning of actual content of the
    # report by looking at the first TOC title and searching for it's second
    # instance i.e. when it appears again for the second time.
    #
    # This can either be the beginning of the summary chapter,
    # or if the summary doesn't exist in the report - the first chapter.
    #
    # we use these variables to find the first and second occurences
    # of summary 'תקציר' or 'פרק ראשון' and then we'll know where the TOC titles starts and ends.
    summary_exists = False
    summary_text = None
    toc_border_re_instance_counter = 0

    for line_num, line in enumerate(tokenized_lines):
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
        if (not summary_exists and  # ignore second instance since this is not part of the TOC
                regex.TOC_SUMMARY_RE.search(txt) is not None):
            line['type'] = tokens.TOKEN_TOC_SUMMARY_START

            toc_border_re_instance_counter += 1
            summary_exists = True
            summary_text = txt.strip()

            continue

        # look for the first and second occurences of the the first TOC title,
        # whether it's the summary summary or the first chapter.
        #
        # XXX finish this section: finding the borders what summary chapter
        # appears in the report or when it isn't, and then we need to look for first chapter
        if summary_exists:
            def border_re_condition(txt):
                return summary_text.startswith(txt)
        else:
            def border_re_condition(txt):
                if regex.TOC_END_RE.search(txt) is not None:
                    toc_border_re_instance_counter += 1
                    return True
                return False

        if border_re_condition(txt.strip()):
            if toc_border_re_instance_counter == 1:
                toc_start_line_num = line_num

            elif toc_border_re_instance_counter == 2:
                # TODO need to tokenize all chapter headers in the document,
                # this is just the first one
                if summary_exists:
                    line['type'] = tokens.TOKEN_SUMMARY_HEADER
                else:
                    line['type'] = tokens.TOKEN_CHAPTER_HEADER

                toc_end_line_num = line_num

            else:
                # there shouldn't be more than two instances of 'פרק ראשון'
                raise RuntimeError

            continue

    # the toc section we should process is between the two instances of 'פרק ראשון'
    return tokenized_lines[toc_start_line_num:toc_end_line_num]


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
