import asyncio
import logging
from datetime import datetime
from typing import Optional

import httpx
from celery import Task

from betor.databases.mongodb import get_mongodb_client
from betor.databases.redis import get_redis_client
from betor.entities import TorrentInfo
from betor.exceptions import TorrentMetadataTimeout, TorrentTrackersInfoNotFound
from betor.services import (
    AddJobResultsService,
    ProcessRawItemService,
    UpdateItemEpisodesInfoService,
    UpdateItemLanguagesInfoService,
    UpdateItemTorrentInfoService,
    UpdateItemTorrentTrackersInfoService,
)
from betor.settings import tmdb_api_settings

from .app import celery_app

logger = logging.getLogger(__name__)


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
    try:
        return asyncio.run(service.update(magnet_uri))
    except TorrentMetadataTimeout:
        try:
            asyncio.run(
                service.items_repository.record_torrent_failure(
                    magnet_uri,
                    {
                        "occurred_at": datetime.now(),
                        "failure_point": "update_item_torrent_info",
                    },
                )
            )
        except Exception:
            logger.exception("Could not record torrent info failure")
        raise
    finally:
        mongodb_client.close()


def _update_item_languages_info(item_id: str, **kwargs):
    mongodb_client = get_mongodb_client()
    service = UpdateItemLanguagesInfoService(mongodb_client)
    result = asyncio.run(service.update(item_id))
    mongodb_client.close()
    return result


def _update_item_episodes_info(
    item_id: Optional[str] = None,
    magnet_uri: Optional[str] = None,
    torrent_info: Optional[TorrentInfo] = None,
    **kwargs,
):
    mongodb_client = get_mongodb_client()
    service = UpdateItemEpisodesInfoService(mongodb_client)
    result = None
    if magnet_uri and torrent_info:
        result = asyncio.run(service.update_magnet_uri(magnet_uri, torrent_info))
    elif item_id:
        result = asyncio.run(service.update_item(item_id))
    mongodb_client.close()
    return result


def _tmdb_api_request(url: str):
    assert tmdb_api_settings.access_token
    response = httpx.get(
        url, headers={"Authorization": f"Bearer {tmdb_api_settings.access_token}"}
    )
    response.raise_for_status()
    return response.json()


def _update_item_torrent_trackers_info(magnet_uri: str, **kwargs):
    mongodb_client = get_mongodb_client()
    service = UpdateItemTorrentTrackersInfoService(mongodb_client)
    try:
        return asyncio.run(service.update(magnet_uri))
    except TorrentTrackersInfoNotFound:
        try:
            asyncio.run(
                service.items_repository.record_torrent_failure(
                    magnet_uri,
                    {
                        "occurred_at": datetime.now(),
                        "failure_point": "update_item_torrent_trackers_info",
                    },
                )
            )
        except Exception:
            logger.exception("Could not record torrent trackers failure")
        raise
    finally:
        mongodb_client.close()


def _admin_bulk_update_item(item_id: str, **kwargs):
    """
    Admin maintenance task dispatcher for a single item during bulk updates.
    Delegates to AdminBulkUpdateItemService for logic.
    """
    mongodb_client = get_mongodb_client()
    from betor.services.admin_bulk_update_item_service import (
        AdminBulkUpdateItemService,
    )

    service = AdminBulkUpdateItemService(mongodb_client)
    result = asyncio.run(service.process(item_id))
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
tmdb_api_request = celery_app.task(
    _tmdb_api_request,
    name="tmdb_api_request",
    rate_limit=tmdb_api_settings.rate_limit,
)
update_item_torrent_trackers_info = celery_app.task(
    _update_item_torrent_trackers_info,
    base=BetorCeleryTask,
    name="update_item_torrent_trackers_info",
)
admin_bulk_update_item = celery_app.task(
    _admin_bulk_update_item,
    base=BetorCeleryTask,
    name="admin_bulk_update_item",
    default_retry_delay=15,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
)
