from typing import Optional

import celery.result
import motor.motor_asyncio
import redis

from betor.celery.app import celery_app
from betor.entities import Job, RawItem
from betor.repositories import JobMonitorRepository, RawItemsRepository


class InsertOrUpdateRawItemService:
    def __init__(
        self,
        mongodb_client: motor.motor_asyncio.AsyncIOMotorClient,
        redis_client: redis.Redis,
    ):
        self.raw_items_repository = RawItemsRepository(mongodb_client)
        self.job_monitor_repository = JobMonitorRepository(redis_client)

    async def insert_or_update(
        self,
        raw_item: RawItem,
        job_monitor_id: Optional[str] = None,
        job_index: Optional[str] = None,
    ):
        await self.raw_items_repository.insert_or_update(raw_item)
        result: celery.result.AsyncResult = celery_app.signature(
            "process_raw_item"
        ).delay(raw_item["provider_slug"], raw_item["provider_url"])
        if job_monitor_id and job_index:
            self.job_monitor_repository.add_job(
                job_monitor_id, Job(type="celery-task", id=result.id)
            )
