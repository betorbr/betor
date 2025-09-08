from betor.settings import flaresolverr_settings

BOT_NAME = "betor_scrapy"
SPIDER_MODULES = ["betor_scrapy.spiders"]
NEWSPIDER_MODULE = "betor_scrapy.spiders"
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 1
FEED_EXPORT_ENCODING = "utf-8"
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": 100,
    "betor_scrapy.middlewares.UARotatorMiddleware": 400,
    "betor_scrapy.middlewares.CloudflareDownloaderMiddleware": 551,
    "betor_scrapy.middlewares.CloudflareDownloaderResponseMiddleware": 552,
}
CONCURRENT_REQUESTS = 2
FLARESOLVERR_BASE_URL = flaresolverr_settings.base_url
ITEM_PIPELINES = {
    "betor_scrapy.pipelines.RawItemsPipeline": 300,
    "betor_scrapy.pipelines.JobMonitorResultsPipeline": 301,
}
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 14400
HTTPCACHE_STORAGE = "betor_scrapy.httpcache.RedisCacheStorage"
HTTPCACHE_POLICY = "betor_scrapy.httpcache.BetorHTTPCachePolicy"
HTTPCACHE_IGNORE_HTTP_CODES = [500]
EXTENSIONS = {
    "betor_scrapy.extensions.FlareSolverrExtension": 500,
}
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
]
