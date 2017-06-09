#!/usr/bin/env python
"""Fetch offices-to-defects and kewords-to-defects mapping from report webpage.

See report_spider.set_meta_defects_mappings documentation for further info.
"""

import json
import sys
from os.path import basename, splitext

import xml.etree.ElementTree as et
from slimit import ast
from slimit.parser import Parser
from slimit.visitors import nodevisitor


def defects_mapping_from_js_ast(js_ast):
    """Generate offices,keywords-to-defects mappings for JS AST.

    This function is used in the spider,
    but can also be called manually via this script
    on reports that failed parsing due to broken AST,
    after we manually fix them.
    """
    # fetch all array elements from the syntax tree
    js_arrays = [node.children()
                 for node in nodevisitor.visit(js_ast)
                 if isinstance(node, ast.Array)]

    def get_defects_by_keys(data_raw):
        """Fetch key-to-defects from raw html string.

        This is done by building an xml tree from the raw html string,
        and fetching its embedded text.
        """
        res = {}
        for element_raw in data_raw:
            # sometimes data doesn't hold any value.
            # in this case, continue
            try:
                element_raw.value
            except AttributeError:
                continue

            # raw html string looks like this:
            #
            # "<div class='tooltip-title'>משרד הבריאות מופיע ב:</div>היבטים במניעת זיהום של מקורות המים<br/>הפיקוח והבקרה על הפעילות הכספית במרכזים הרפואיים המשלתיים-הכלליים<br/>פעולות הרשויות המקומיות וספקי המים להבטחת איכות מי השתייה<br/>"
            #
            # we parse it into an xml tree.
            # we wrap it with a another <div> element,
            # since its not a valid html: it has tailing </br> elements
            element_ast = et.fromstring('<div>'+element_raw.value[1:-1]+'</div>')

            # remove the "מופיע ב:" part from the "משרד הבריאות מופיע ב:" string
            key_name = element_ast[0].text.split(u'מופיע ב')[0]

            # defects are the tail of the first <div>
            # and all subsequenet <br> elements.
            key_defects = [element_ast[0].tail] + [d.tail for d in element_ast[1:] if d.tail]

            # append key-to-defects mapping to result dictionary
            res[key_name] = key_defects

        return res

    return (get_defects_by_keys(js_arrays[0]),
            get_defects_by_keys(js_arrays[1]),)


if __name__ == '__main__':
    """Generate offices,keywords-to-defects mapping from given CDATA file.

    The file given as argument should contain the CDATA text blob
    taken from the <script> element in the report webpage.

    This script should be executed on reports that failed parsing,
    and after the CDATA was manually fixed and is ready for re-parsing.
    """
    path = sys.argv[1]
    with open(path, 'r') as f:
        cdata = f.read()

    js_ast = Parser().parse(cdata)
    offices, keywords = defects_mapping_from_js_ast(js_ast)
    data = {
        'offices_to_defects': {office.strip(): [defect.strip() for defect in defects]
                               for office, defects in offices.items()},
        'keywords_to_defects': {keyword.strip(): [defect.strip() for defect in defects]
                               for keyword, defects in keywords.items()},
    }

    with open('{}.defects_mapping'.format(basename(path)), 'w') as f:
        print('Creating defects_mapping file {}'.format(f.name))
        json.dump(data, f, ensure_ascii=False)
