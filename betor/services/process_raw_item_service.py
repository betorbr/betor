import asyncio
from typing import List, Optional, TypedDict
from uuid import uuid4

import celery.result
import motor.motor_asyncio
import redis
import torf

from betor.celery.app import celery_app
from betor.entities import BaseItem, Item, Job, RawItem
from betor.exceptions import JobMonitorNotFound
from betor.repositories import ItemsRepository, JobMonitorRepository, RawItemsRepository
from betor.settings import store_torrent_file_settings

from .determines_imdb_tmdb_ids_service import DeterminesIMDbTMDBIdsService


class ProcessRawItemReturn(TypedDict):
    base_item: BaseItem
    items: List[Item]


class ProcessRawItemService:
    def __init__(
        self,
        mongodb_client: motor.motor_asyncio.AsyncIOMotorClient,
        redis_client: redis.Redis,
    ):
        self.raw_items_repository = RawItemsRepository(mongodb_client)
        self.items_repository = ItemsRepository(mongodb_client)
        self.job_monitor_repository = JobMonitorRepository(redis_client)
        self.determines_imdb_tmdb_ids_service = DeterminesIMDbTMDBIdsService(
            mongodb_client
        )

    async def process(
        self,
        provider_slug: str,
        provider_url: str,
        job_monitor_id: Optional[str] = None,
    ) -> ProcessRawItemReturn:
        raw_item = await self.raw_items_repository.get(provider_slug, provider_url)
        assert raw_item, f"Raw Item not found {provider_slug=} {provider_url=}"
        imdb_id, tmdb_id, item_type = (
            await self.determines_imdb_tmdb_ids_service.determines(raw_item)
        )
        base_item = BaseItem(
            provider_slug=raw_item["provider_slug"],
            provider_url=raw_item["provider_url"],
            imdb_id=imdb_id,
            tmdb_id=tmdb_id,
            item_type=item_type,
        )
        if not base_item["imdb_id"] and not base_item["tmdb_id"]:
            return ProcessRawItemReturn(base_item=base_item, items=[])
        tasks = [
            self.process_raw_item_magnet_uri(
                raw_item,
                base_item,
                magnet_uri,
                job_monitor_id=job_monitor_id,
            )
            for magnet_uri in raw_item["magnet_uris"]
        ]
        results = await asyncio.gather(*tasks)
        return ProcessRawItemReturn(
            base_item=base_item,
            items=[result for result in results if result is not None],
        )

    async def process_raw_item_magnet_uri(
        self,
        raw_item: RawItem,
        base_item: BaseItem,
        magnet_uri: str,
        job_monitor_id: Optional[str] = None,
    ) -> Optional[Item]:
        try:
            magnet = torf.Magnet.from_string(magnet_uri)
        except torf.MagnetError:
            return None
        item = Item(
            **base_item,
            id=None,
            hash=None,
            inserted_at=None,
            updated_at=None,
            magnet_uri=magnet_uri,
            magnet_xt=magnet.xt,
            magnet_dn=magnet.dn,
            torrent_name=None,
            torrent_files=None,
            torrent_size=None,
            download_path=None,
            torrent_num_peers=None,
            torrent_num_seeds=None,
            languages=[],
            episodes=[],
            seasons=[],
        )
        await self.items_repository.insert_or_update(item)
        if retrieve_item := await self.items_repository.get(
            item["provider_slug"], item["provider_url"], item["magnet_xt"]
        ):
            if (
                not retrieve_item["torrent_name"]
                or not retrieve_item["torrent_files"]
                or not retrieve_item["torrent_size"]
                or (
                    store_torrent_file_settings.enabled
                    and not retrieve_item["download_path"]
                )
            ):
                self.queue_update_item_torrent_info(
                    retrieve_item, job_monitor_id=job_monitor_id
                )
            self.queue_update_item_torrent_trackers_info(
                retrieve_item, job_monitor_id=job_monitor_id
            )
            self.queue_update_item_languages_info(retrieve_item)
            self.queue_update_item_episodes_info(retrieve_item)
            return retrieve_item
        return item

    def queue_update_item_languages_info(self, item: Item):
        celery_app.signature("update_item_languages_info").delay(item["id"])

    def queue_update_item_episodes_info(self, item: Item):
        celery_app.signature("update_item_episodes_info").delay(item_id=item["id"])

    def queue_update_item_torrent_info(
        self, item: Item, job_monitor_id: Optional[str] = None
    ) -> str:
        job_index = str(uuid4())
        result: celery.result.AsyncResult = celery_app.signature(
            "update_item_torrent_info"
        ).delay(item["magnet_uri"], job_monitor_id=job_monitor_id, job_index=job_index)
        if not job_monitor_id:
            return job_index
        try:
            self.job_monitor_repository.add_job(
                job_monitor_id,
                Job(
                    type="celery-task",
                    name="update_item_torrent_info",
                    id=result.id,
                ),
                job_index=job_index,
            )
        except JobMonitorNotFound:
            pass
        return job_index

    def queue_update_item_torrent_trackers_info(
        self, item: Item, job_monitor_id: Optional[str] = None
    ) -> str:
        job_index = str(uuid4())
        result: celery.result.AsyncResult = celery_app.signature(
            "update_item_torrent_trackers_info"
        ).delay(item["magnet_uri"], job_monitor_id=job_monitor_id, job_index=job_index)
        if not job_monitor_id:
            return job_index
        try:
            self.job_monitor_repository.add_job(
                job_monitor_id,
                Job(
                    type="celery-task",
                    name="update_item_torrent_trackers_info",
                    id=result.id,
                ),
                job_index=job_index,
            )
        except JobMonitorNotFound:
            pass
        return job_index
