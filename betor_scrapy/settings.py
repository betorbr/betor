from betor.settings import flaresolverr_settings

BOT_NAME = "betor_scrapy"
SPIDER_MODULES = ["betor_scrapy.spiders"]
NEWSPIDER_MODULE = "betor_scrapy.spiders"
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 1
FEED_EXPORT_ENCODING = "utf-8"
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": 100,
    "betor_scrapy.middlewares.CloudflareDownloaderMiddleware": 551,
    "betor_scrapy.middlewares.CloudflareDownloaderResponseMiddleware": 552,
}
CONCURRENT_REQUESTS = 4
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
