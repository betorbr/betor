import asyncio

from celery import Task

from betor.databases.mongodb import get_mongodb_client
from betor.services import ProcessRawItemService

from .app import celery_app


def _process_raw_item(provider_slug: str, provider_url: str):
    mongodb_client = get_mongodb_client()
    service = ProcessRawItemService(mongodb_client)
    return asyncio.run(service.process(provider_slug, provider_url))


process_raw_item: Task = celery_app.task(_process_raw_item)
