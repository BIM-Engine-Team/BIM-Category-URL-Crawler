# Scrapy settings generated from exploration

BOT_NAME = 'architecture_materials_crawler'
SPIDER_MODULES = ['architecture_materials.spiders']
NEWSPIDER_MODULE = 'architecture_materials.spiders'
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_DELAY = 1.5
RANDOMIZE_DOWNLOAD_DELAY = 0.5
USER_AGENT = 'ArchitectureMaterialsCrawler (+http://example.com/bot)'
DEPTH_LIMIT = 5
CLOSESPIDER_PAGECOUNT = 20
ITEM_PIPELINES = {'architecture_materials.pipelines.ValidationPipeline': 300, 'architecture_materials.pipelines.DeduplicationPipeline': 400, 'architecture_materials.pipelines.JsonWriterPipeline': 500}
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
DEFAULT_REQUEST_HEADERS = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'en'}
