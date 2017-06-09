BOT_NAME = 'hasadna'

SPIDER_MODULES = ['report.spiders']
NEWSPIDER_MODULE = 'report.spiders'

USER_AGENT = 'open-audit (++http://hasadna.org.il)'

ROBOTSTXT_OBEY = True

ITEM_PIPELINES = {
    'report.pipelines.ReportPipeline': 300,
}

HTTPCACHE_ENABLED = True
HTTPCACHE_ALWAYS_STORE = True  # state-comptroller website asks not cache it. well, fuck that

COMPRESSION_ENABLED = False

# LOG_ENABLED = False
LOG_LEVEL = 'ERROR'
