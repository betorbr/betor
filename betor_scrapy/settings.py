BOT_NAME = "betor_scrapy"
SPIDER_MODULES = ["betor_scrapy.spiders"]
NEWSPIDER_MODULE = "betor_scrapy.spiders"
ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 1
FEED_EXPORT_ENCODING = "utf-8"
DOWNLOADER_MIDDLEWARES = {
    "betor_scrapy.middlewares.CloudflareDownloaderMiddleware": 551,
    "betor_scrapy.middlewares.CloudflareDownloaderResponseMiddleware": 552,
}
CONCURRENT_REQUESTS_PER_DOMAIN = 2
