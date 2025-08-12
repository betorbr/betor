import asyncio

from celery import Task

from betor.databases.mongodb import get_mongodb_client
from betor.services import ProcessRawItemService, UpdateItemTorrentInfoService

from .app import celery_app


def _process_raw_item(provider_slug: str, provider_url: str):
    mongodb_client = get_mongodb_client()
    service = ProcessRawItemService(mongodb_client)
    return asyncio.run(service.process(provider_slug, provider_url))


def _update_item_torrent_info(magnet_uri: str):
    mongodb_client = get_mongodb_client()
    service = UpdateItemTorrentInfoService(mongodb_client)
    return asyncio.run(service.update(magnet_uri))


process_raw_item: Task = celery_app.task(_process_raw_item, name="process_raw_item")
update_item_torrent_info: Task = celery_app.task(
    _update_item_torrent_info, name="update_item_torrent_info"
)
