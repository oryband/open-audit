from datetime import datetime
from html.parser import HTMLParser
from os import makedirs
from os.path import basename, splitext, exists
from urllib.parse import urlparse, urlsplit

from scrapy.exporters import JsonLinesItemExporter
from scrapy.exceptions import NotSupported

from report.items import (
    ReportPreface,
    ReportChapter,
    ReportTopic,
)


class ReportPipeline(object):
    def open_spider(self, spider):
        """Dumps scraped output.

        Spider dumps output into three files: prefaces, chapters, topics.

        Prefaces are the metadata of every report.
        Each report includes chapters,
        where each chapter usually includes multiple topics.

        These three object types are dumped into three separate files
        but are linked together using a unique identifier.
        This unique id is in fact the url, as i've found no other unique
        and consistent object to link with.
        """
        self.html_parser = HTMLParser()

        # dump into a designate dir
        dirname = 'output'
        if not exists(dirname):
            makedirs(dirname)

        self.files = {
            'prefaces': open('{}/prefaces.json'.format(dirname), 'wb'),
            'chapters': open('{}/chapters.json'.format(dirname), 'wb'),
            'topics': open('{}/topics.json'.format(dirname), 'wb'),
        }

        # use JSON Lines format i.e. each line is a json object,
        # separated by newlines
        self.exporters = {name.split('.')[0]: JsonLinesItemExporter(file, ensure_ascii=False)
                          for (name, file) in self.files.items()}
        for exporter in self.exporters.values():
            exporter.start_exporting()

    def close_spider(self, spider):
        for e in self.exporters.values():
            e.finish_exporting()

        for f in self.files.values():
            f.close()

    def process_item(self, item, spider):
        """Dump item to file according to its type."""
        if isinstance(item, ReportPreface):
            return self.process_preface(item)
        elif isinstance(item, ReportChapter):
            return self.process_chapter(item)
        elif isinstance(item, ReportTopic):
            return self.process_topic(item)

    def process_preface(self, item):
        """Dump preface to file."""
        # set specific fields value as None
        # if their value is missing from the webpage
        cleaned_items = {}
        for e in [
                'report_type',

                'toc_pdf_hebrew_url',
                'toc_docx_hebrew_url',

                'intro_pdf_hebrew_url',
                'intro_docx_hebrew_url',

                'intro_pdf_arabic_url',
                'intro_docx_arabic_url',
        ]:
            cleaned_items[e] = item[e].strip() if item[e] is not None else None

        data = {
            # use url file name without extension as id
            # e.g. http://www.mevaker.gov.il/he/Reports/Pages/503.aspx --> '503'
            'id': item['id'],
            'source_url': item['source_url'],

            'report_name': self.html_parser.unescape(item['report_name'].strip()),
            'report_type': cleaned_items['report_type'],

            'catalog_number': (
                item['catalog_number'].strip()
                if item['catalog_number'] is not None and item['catalog_number'] != '-'
                else None
            ),

            'publish_date': (
                datetime.strptime(
                    item['publish_date'].strip(),
                    "%d/%m/%Y").
                strftime("%Y-%m-%d")),

            'issn_number': item['issn_number'].strip() if item['issn_number'] is not None else None,

            'toc_pdf_hebrew_url': cleaned_items['toc_pdf_hebrew_url'],
            'toc_docx_hebrew_url': cleaned_items['toc_docx_hebrew_url'],

            'intro_pdf_hebrew_url': cleaned_items['intro_pdf_hebrew_url'],
            'intro_docx_hebrew_url': cleaned_items['intro_docx_hebrew_url'],

            'intro_pdf_arabic_url': cleaned_items['intro_pdf_arabic_url'],
            'intro_docx_arabic_url': cleaned_items['intro_docx_arabic_url'],

            'offices_to_defects': {
                self.html_parser.unescape(office.strip()): [defect.strip() for defect in defects]
                for (office, defects) in item['offices_to_defects'].items()
            },
            'keywords_to_defects': {
                self.html_parser.unescape(keyword.strip()): [defect.strip() for defect in defects]
                for (keyword, defects) in item['keywords_to_defects'].items()
            },

            'body': ([self.html_parser.unescape(p.strip()) for p in item['body']]
                     or None),
        }

        self.exporters['prefaces'].export_item(data)
        return item

    def process_chapter(self, item):
        """Dump chapter to file."""
        data = {
            'id': item['id'],
            'source_url': item['source_url'],

            'title': self.html_parser.unescape(item['title'].strip()),
            'offices': [self.html_parser.unescape(office.strip()) for office in item['offices']],
            'keywords': [self.html_parser.unescape(keyword.strip()) for keyword in item['keywords']],
        }

        self.exporters['chapters'].export_item(data)
        return item

    def process_topic(self, item):
        """Dump topic to file."""
        def prepend_domain(endpoint):
            return item['domain'][:-1] + endpoint if endpoint is not None else None

        # fetch topic pdf, docx urls
        doc_urls = item['doc_urls']
        pdf_url = docx_url = None
        for d in doc_urls:
            _, ext = splitext(basename(urlsplit(d).path))
            if ext.lower() == '.pdf':
                if pdf_url is not None:
                    raise NotSupported('multiple pdf urls for source url: {}'.format(item['source_url']))
                pdf_url = prepend_domain(d.strip())
            elif ext.lower() == '.docx':
                docx_url = prepend_domain(d.strip())
            else:
                raise NotSupported('unsupported docx url file type: {}'.format(d, ext))

        data = {
            'id': item['id'],
            'source_url': item['source_url'],
            'chapter_num': item['chapter_num'],

            'pdf_url': pdf_url,
            'docx_url': docx_url,

            # the following fields can be empty.
            # some topics only link to pdf/docx with no other content.
            'title': (
                self.html_parser.unescape(item['title'].strip())
                if item['title'] is not None
                else None
            ),
            'office': (
                self.html_parser.unescape(item['office'].strip())
                if item['office'] is not None
                else None
            ),
            'body': (
                self.html_parser.unescape(item['body'].strip())
                if item['body'] is not None
                else None
            ),
        }

        self.exporters['topics'].export_item(data)
        return item
