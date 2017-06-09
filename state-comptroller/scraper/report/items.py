import scrapy


class ReportPreface(scrapy.Item):
    """Preface for the report.

    The preface includes introduction text and pdf links,
    along with some beaurocratic data e.g. catalog numbers.
    """

    id = scrapy.Field()  # pointer to related chapters, topics
    source_url = scrapy.Field()  # pointer to report web page

    report_name = scrapy.Field()
    report_type = scrapy.Field()
    catalog_number = scrapy.Field()
    publish_date = scrapy.Field()
    issn_number = scrapy.Field()

    toc_pdf_hebrew_url = scrapy.Field()
    toc_docx_hebrew_url = scrapy.Field()

    intro_pdf_hebrew_url = scrapy.Field()
    intro_docx_hebrew_url = scrapy.Field()

    intro_pdf_arabic_url = scrapy.Field()
    intro_docx_arabic_url = scrapy.Field()

    offices_to_defects = scrapy.Field()
    keywords_to_defects = scrapy.Field()

    body = scrapy.Field()


class ReportChapter(scrapy.Item):
    """Chapter from the report.

    Chapters contain topics, which are the actual objects we are interested in.
    """

    id = scrapy.Field()
    source_url = scrapy.Field()

    title = scrapy.Field()
    offices = scrapy.Field()
    keywords = scrapy.Field()


class ReportTopic(scrapy.Item):
    """Topic from the report.

    topics are grouped by high-level "chapters".

    each topic is USUALLY assigned to an office
    or some other official government entity like רשות המיסים.

    a topic has a title, body, and doc, pdf document links
    with additional information.
    """

    id = scrapy.Field()
    source_url = scrapy.Field()
    # some url fields are missing the domain,
    # we use this field to prepend it before dumping the data
    domain = scrapy.Field()
    chapter_num = scrapy.Field()  # pointer to related chapter

    title = scrapy.Field()
    doc_urls = scrapy.Field()
    office = scrapy.Field()
    body = scrapy.Field()
