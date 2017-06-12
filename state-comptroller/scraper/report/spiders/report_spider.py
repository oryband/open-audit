import json
import logging
from os import makedirs
from os.path import basename, splitext, exists
import re
from urllib.parse import urlparse, urlsplit
import xml.etree.ElementTree as et

from slimit import ast
from slimit.parser import Parser
parser = Parser()
from slimit.visitors import nodevisitor

from scrapy import Spider, Request
from scrapy.selector import Selector

from report.spiders.defects_mapping import defects_mapping_from_js_ast
from report.items import (
    ReportPreface,
    ReportChapter,
    ReportTopic,
)


class ReportSpider(Spider):
    """Spider for a single State Comptroller report.

    A report is represented as a single web page within
    the Israeli State Comptroller website.

    Example reports include the yearly reports
    (3 parts i.e. 3 web pages),
    and additional reports dealing with a specific issue.
    """

    # handle_httpstatus_list = [300, 301, 302, 303]  # some pages get redirected

    name = 'report_spider'
    allowed_domains = ['mevaker.gov.il']
    # see parse() docstring for an explanation on this:
    start_urls = ['http://www.mevaker.gov.il/_layouts/15/guardian.search/DigitalLibrarySearchHandler.ashx?method=getAll']

    reports = {}

    def init_report(self, response):
        """Initialize a new report entry.

        This entry is used in parse functions
        to relate between the preface, chapters, topics, etc.

        Returns the report's source url file name,
        which is used as a unique id.

        This is because all other fields are not unique across all reports.
        Everything can be omitted in some report,
        and the url file name is the only globally unique value available.
        """
        # the catalog number is a unique id for each report
        id, _ = splitext(basename(urlsplit(response.url).path))
        self.reports[id] = {
            'domain': '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(response.url)),
        }
        return id

    def set_meta_defects_mappings(self, response, report):
        """Set offices and tags-to-defects mapping from report "header".

        There exists a mapping between offices and the defects they appear in.
        In additiona, another similar mapping exists for keywords
        ("tags") and their related defects.

        These appear as popups in the web page. They are fetched from
        a javascript array variable whose elements are html <div> objects
        containing the defects. fuck me.

        We execute the following actions:
            1. fetch the javascript array string
            2. find the arrays in the string (it contains some more javascript code)
            3. eval the array string into python strings
            4. clear the wrapping <div>s using hacky ways and str.split()
            5. split the defects and fetch their values
        """
        report['offices'] = []
        for td in response.xpath('//*[@id="ctl00_PlaceHolderMain_ReportOfficesMetaData_ControlledBodies"]/table/tr/td'):
            report['offices'] += td.xpath('.//text()').extract()

        report['keywords'] = []
        for td in response.xpath('//*[@id="ctl00_PlaceHolderMain_ReportKeysMetaData_ControlledBodies"]/table/tr/td'):
            report['keywords'] += td.xpath('.//text()').extract()

        # WARNING: Abandon All Hope, Ye Who Enter Here.
        # Seriously, you are entering a world of pain.
        #
        # the offices-to-defects and keywords-to-defects mapping
        # is not part of the original html document.
        # it is added at runtime by javascript code embedded in a "[CDATA[...]]"
        # string inside a <script> element.
        #
        # the mappings we look for are assigned to two javascript array
        # variables.
        # inside each variable is a small html element containing the mapping,
        # somewhat in the structure of:
        # "<div>office name...</div>defect 1</br>defect 2</br>..."
        #
        # yeah, i know. fuck us, right?
        #
        # in order to get around this,
        # we use a javascript parser to build a javascript syntax tree (ast)
        # using the slimit python package.
        # this package includes a syntax tree parser.
        # we fetch the two arrays from the ast, parse them into a small xml
        # tree each, and fetch the elements from the html string.
        #
        # voila!

        # fetch javascript CDATA code string
        js = response.xpath('//*[@id="aspnetForm"]/script[7]/text()').extract_first()
        # parse javascript syntax tree

        try:
            js_ast = parser.parse(js)
        except SyntaxError as e:
            # if parsing failed,
            # dump web page to file for later manual examination
            # and return an empty offices/keywords-to-defects dicts
            # we will fill them out manually later
            dirname = 'errors'
            path = '{}/{}'.format(dirname, basename(urlparse(response.url).path))
            logging.log(logging.ERROR, 'Error in url "%s", dumping to file "%s"', response.url, path)
            if not exists(dirname):
                makedirs(dirname)
            with open(path, 'w') as f:
                f.write(js)

            report['offices_to_defects'] = {}
            report['keywords_to_defects'] = {}
            return

        report['offices_to_defects'], report['keywords_to_defects'] = defects_mapping_from_js_ast(js_ast)

    def parse(self, response):
        """Parse report list."""
        # response body is a json array,
        # whose first element is a string representation of an
        # html table containing all published reports from 1987 till today. wtf.
        reports_table = json.loads(response.body)[0]
        reports_urls = Selector(text=reports_table).xpath('//body/table/tr/td/a/@href').extract()

        for url in reports_urls:
            yield Request(response.urljoin(url), callback=self.parse_report)

    def parse_report(self, response):
        """Parse a single report by calling all other section-specific scrape functions."""
        id = self.init_report(response)
        report = self.reports[id]
        self.set_meta_defects_mappings(response, report)

        yield self.parse_preface(response, id)
        for item in self.parse_chapters(response, id):
            yield item

    def parse_preface(self, response, id):
        """Scrape the report preface section.

        Regardless of the actual topics from this report,
        the preface contains common propeties related to all topics.
        """
        report = self.reports[id]

        return ReportPreface(
            id=id,
            source_url=response.url,

            report_name=response.xpath('//*[@id="ContentSkip"]/div/h1/div/text()').extract_first(),
            report_type=response.xpath('//*[@id="ctl00_PlaceHolderMain_reportDetails_lblReportTypeVal"]/text()').extract_first(),
            catalog_number=response.xpath('//*[@id="ctl00_PlaceHolderMain_reportDetails_lblCatalogNumberVal"]/text()').extract_first(),
            publish_date=response.xpath('//*[@id="ctl00_PlaceHolderMain_reportDetails_lblReportDateVal"]/text()').extract_first(),
            issn_number=response.xpath('//*[@id="ctl00_PlaceHolderMain_reportDetails_lblIssnNumberVal"]/text()').extract_first(),

            # table of contents
            toc_pdf_hebrew_url=response.xpath('//*[@id="ctl00_PlaceHolderMain_reportDetails_reportFilesDiv"]/table/tbody/tr[1]/td[2]/a/@href').extract_first(),
            toc_docx_hebrew_url=response.xpath('//*[@id="ctl00_PlaceHolderMain_reportDetails_reportFilesDiv"]/table/tbody/tr[1]/td[1]/a/@href').extract_first(),

            # intro text
            intro_pdf_hebrew_url=response.xpath('//*[@id="ctl00_PlaceHolderMain_SummaryReport_linkPdfFile"]/@href').extract_first(),
            intro_docx_hebrew_url=response.xpath('//*[@id="ctl00_PlaceHolderMain_SummaryReport_linkWordFile"]/@href').extract_first(),

            # intro text in arabic
            intro_pdf_arabic_url=response.xpath('//*[@id="ctl00_PlaceHolderMain_reportDetails_reportFilesDiv"]/table/tbody/tr[2]/td[2]/a/@href').extract_first(),
            intro_docx_arabic_url=response.xpath('//*[@id="ctl00_PlaceHolderMain_reportDetails_reportFilesDiv"]/table/tbody/tr[2]/td[1]/a/@href').extract_first(),

            offices_to_defects=report['offices_to_defects'],
            keywords_to_defects=report['keywords_to_defects'],

            body=response.xpath('//*[@id="content_summary"]//text()').extract(),
        )

    def parse_chapters(self, response, id):
        """Scrape all report chapters.

        A report is usually structured into chapters,
        and each chapter includes topics concerning specific defects.
        """
        report = self.reports[id]

        for num, (header, content) in enumerate(
                zip(response.xpath('//*[@id="ctl00_PlaceHolderMain_TransformXml_container"]/div[not(starts-with(@id, "chapter_"))]'),
                    response.xpath('//*[@id="ctl00_PlaceHolderMain_TransformXml_container"]/div[starts-with(@id, "chapter_")]')),
                start=1):

            title = header.xpath('./div/h3/a/@title').extract_first()

            yield ReportChapter(
                id=id,
                source_url=response.url,

                chapter_num=num,
                title=title,
                offices=content.xpath('./div[1]/div[1]/div[2]/ul/li/text()').extract(),
                keywords=content.xpath('./div[1]/div[2]/div[2]/ul/li/text()').extract(),
            )

            # scrape chapter topics
            for topic in content.xpath('./div[not(contains(@class, "LibraryContentItem")) and ./div/div[not(contains(@class, "ClearBoth"))]]'):
                yield self.parse_topic(response, id, num, topic)

    def parse_topic(self, response, id, chapter_num, topic):
        """Parse a topic from given chapter."""
        report = self.reports[id]

        return ReportTopic(
            id=id,
            source_url=response.url,
            domain=report['domain'],

            chapter_num=chapter_num,
            title=topic.xpath('./div[1]/div[1]/div[1]/h3/a/text()').extract_first(),
            doc_urls=topic.xpath('./div/div[contains(@class, "Files")]/div/a/@href').extract(),
            office=self.parse_topic_office(topic),
            body=topic.xpath('./div[2]/div[3]/span/p/text()').extract_first(),
        )

    def parse_topic_office(self, topic):
        """Return office for current topic.

        Topic elements starting with "להאזנה" are not offices,
        but in fact links to audio clips.

        I haven't found the logic for when an audio clip exists or not,
        but my guess is when the defect being discussed relates to deaf
        or handicapped people. In any case we ignore this for the time being:

        When finding offices which are of this type, we override them with the
        topic element (office name) before them.
        """
        office_xpath = topic.xpath(u'./preceding-sibling::div[@class="LibraryContentItem"][1]/div[1]/div[1]/h3/a[not(starts-with(text(), "להאזנה"))]')
        office_below_audio_clips_xpath = topic.xpath(u'./preceding-sibling::div[@class="LibraryContentItem"][1]/div[1]/div[1]/h3/a[starts-with(text(), "להאזנה")]')
        office_before_audio_clips_xpath = office_below_audio_clips_xpath.xpath(u'../../../../preceding-sibling::div[@class="LibraryContentItem"][1]/div[1]/div[1]/h3/a[not(starts-with(text(), "להאזנה"))]')

        # if this is an audio clip "office", use the one shown before that.
        if len(office_before_audio_clips_xpath) > 0:
            return office_before_audio_clips_xpath.xpath('./text()').extract_first()
        # otherwise this office is ok
        return office_xpath.xpath('./text()').extract_first()
