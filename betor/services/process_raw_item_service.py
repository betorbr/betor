import asyncio
from typing import List, Optional, TypedDict

import motor.motor_asyncio
import torf

from betor.repositories import ItemsRepository, RawItemsRepository
from betor.types import BaseItem, Item, RawItem

from .determines_imdb_tmdb_ids_service import DeterminesIMDbTMDBIdsService


class ProcessRawItemReturn(TypedDict):
    base_item: BaseItem
    items: List[Item]


class ProcessRawItemService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.raw_items_repository = RawItemsRepository(mongodb_client)
        self.items_repository = ItemsRepository(mongodb_client)
        self.determines_imdb_tmdb_ids_service = DeterminesIMDbTMDBIdsService()

    async def process(
        self, provider_slug: str, provider_url: str
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
            self.process_raw_item_magnet_link(raw_item, base_item, magnet_link)
            for magnet_link in raw_item["magnet_links"]
        ]
        results = await asyncio.gather(*tasks)
        return ProcessRawItemReturn(
            base_item=base_item,
            items=[result for result in results if result is not None],
        )

    async def process_raw_item_magnet_link(
        self, raw_item: RawItem, base_item: BaseItem, magnet_link: str
    ) -> Optional[Item]:
        try:
            magnet = torf.Magnet.from_string(magnet_link)
        except torf.MagnetError:
            return None
        item = Item(
            **base_item,
            id=None,
            hash=None,
            inserted_at=None,
            updated_at=None,
            magnet_link=magnet_link,
            magnet_xt=magnet.xt,
            magnet_dn=magnet.dn,
        )
        await self.items_repository.insert_or_update(item)
        return await self.items_repository.get(
            item["provider_slug"], item["provider_url"], item["magnet_xt"]
        )
