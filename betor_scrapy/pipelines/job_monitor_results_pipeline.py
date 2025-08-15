from typing import Optional

import redis
import scrapy

from betor.databases.redis import get_redis_client
from betor.services import AddJobResultsService
from betor_scrapy.items import ScrapyItem


class JobMonitorResultsPipeline:
    redis_client: Optional[redis.Redis] = None
    add_job_results_service: Optional[AddJobResultsService] = None

    def open_spider(self, spider: scrapy.Spider):
        self.redis_client = get_redis_client()
        self.add_job_results_service = AddJobResultsService(self.redis_client)

    def close_spider(self, spider):
        if self.redis_client:
            self.redis_client.close()

    async def process_item(self, item: ScrapyItem, spider: scrapy.Spider):
        job_monitor_id: Optional[str] = getattr(spider, "job_monitor_id", None)
        job_index: Optional[str] = getattr(spider, "job_index", None)
        if not self.add_job_results_service or not job_monitor_id or not job_index:
            return item
        self.add_job_results_service.add(job_monitor_id, job_index, item)
        return item
