import asyncio
from typing import Optional

from celery import Task

from betor.databases.mongodb import get_mongodb_client
from betor.databases.redis import get_redis_client
from betor.entities import TorrentInfo
from betor.services import (
    AddJobResultsService,
    ProcessRawItemService,
    UpdateItemEpisodesInfoService,
    UpdateItemLanguagesInfoService,
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
    result = asyncio.run(
        service.process(
            provider_slug,
            provider_url,
            job_monitor_id=job_monitor_id,
        )
    )
    mongodb_client.close()
    redis_client.close()
    return result


def _update_item_torrent_info(magnet_uri: str, **kwargs):
    mongodb_client = get_mongodb_client()
    service = UpdateItemTorrentInfoService(mongodb_client)
    result = asyncio.run(service.update(magnet_uri))
    mongodb_client.close()
    return result


def _update_item_languages_info(item_id: str, **kwargs):
    mongodb_client = get_mongodb_client()
    service = UpdateItemLanguagesInfoService(mongodb_client)
    result = asyncio.run(service.update(item_id))
    mongodb_client.close()
    return result


def _update_item_episodes_info(magnet_uri: str, torrent_info: TorrentInfo, **kwargs):
    mongodb_client = get_mongodb_client()
    service = UpdateItemEpisodesInfoService(mongodb_client)
    result = asyncio.run(service.update(magnet_uri, torrent_info))
    mongodb_client.close()
    return result


process_raw_item: Task = celery_app.task(
    _process_raw_item,
    base=BetorCeleryTask,
    name="process_raw_item",
    default_retry_delay=15,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
)
update_item_torrent_info: Task = celery_app.task(
    _update_item_torrent_info,
    base=BetorCeleryTask,
    name="update_item_torrent_info",
    soft_time_limit=(5 * 60),
)
update_item_languages_info: Task = celery_app.task(
    _update_item_languages_info,
    base=BetorCeleryTask,
    name="update_item_languages_info",
)
update_item_episodes_info = celery_app.task(
    _update_item_episodes_info,
    base=BetorCeleryTask,
    name="update_item_episodes_info",
)
