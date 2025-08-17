import asyncio
from typing import Optional

from celery import Task

from betor.databases.mongodb import get_mongodb_client
from betor.databases.redis import get_redis_client
from betor.services import (
    AddJobResultsService,
    ProcessRawItemService,
    UpdateItemTorrentInfoService,
)

from .app import celery_app


class BetorCeleryTask(Task):
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs: dict, einfo):
        job_monitor_id = kwargs.get("job_monitor_id")
        job_index = kwargs.get("job_index")
        if job_monitor_id and job_index:
            redis_client = get_redis_client()
            add_job_results_service = AddJobResultsService(redis_client)
            add_job_results_service.add(job_monitor_id, job_index, retval)
            redis_client.close()


def _process_raw_item(
    provider_slug: str,
    provider_url: str,
    job_monitor_id: Optional[str] = None,
    **kwargs,
):
    mongodb_client = get_mongodb_client()
    redis_client = get_redis_client()
    service = ProcessRawItemService(mongodb_client, redis_client)
    return asyncio.run(
        service.process(
            provider_slug,
            provider_url,
            job_monitor_id=job_monitor_id,
        )
    )


def _update_item_torrent_info(magnet_uri: str, **kwargs):
    mongodb_client = get_mongodb_client()
    service = UpdateItemTorrentInfoService(mongodb_client)
    return asyncio.run(service.update(magnet_uri))


process_raw_item: Task = celery_app.task(
    _process_raw_item,
    base=BetorCeleryTask,
    name="process_raw_item",
    priority=9,
    default_retry_delay=15,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
)
update_item_torrent_info: Task = celery_app.task(
    _update_item_torrent_info,
    base=BetorCeleryTask,
    name="update_item_torrent_info",
    priority=0,
    soft_time_limit=(5 * 60),
)
