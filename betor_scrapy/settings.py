from typing import Dict, Type, Union

BOT_NAME = "betor_scrapy"
SPIDER_MODULES = ["betor_scrapy.spiders"]
NEWSPIDER_MODULE = "betor_scrapy.spiders"
ADDONS: Dict[Union[str, Type], int] = {}
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1
FEED_EXPORT_ENCODING = "utf-8"
