from typing import TypedDict

import motor.motor_asyncio

from betor.entities import RawItem
from betor.enums import ItemType
from betor.exceptions import RawItemNotFound
from betor.repositories import ItemsRepository, RawItemsRepository

from .determines_imdb_tmdb_ids_service import DeterminesIMDbTMDBIdsService


class AdminDeterminesIMDBTMDBIdResult(TypedDict):
    raw_item: RawItem
    imdb_id: str
    tmdb_id: str
    item_type: ItemType


class AdminDeterminesIMDBTMDBIdService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.raw_items_repository = RawItemsRepository(mongodb_client)
        self.items_repository = ItemsRepository(mongodb_client)
        self.determines_imdb_tmdb_ids_service = DeterminesIMDbTMDBIdsService()

    async def determines(self, provider_url: str) -> AdminDeterminesIMDBTMDBIdResult:
        raw_item = await self.raw_items_repository.get_by_provider_url(provider_url)
        if not raw_item:
            raise RawItemNotFound()
        imdb_id, tmdb_id, item_type = (
            await self.determines_imdb_tmdb_ids_service.determines(raw_item)
        )
        if not imdb_id or not tmdb_id or not item_type:
            raise ValueError(f"{imdb_id=} {tmdb_id=} {item_type=}")
        await self.items_repository.update_provider_url_imdb_tmdb_id(
            provider_url, imdb_id, tmdb_id, item_type
        )
        return AdminDeterminesIMDBTMDBIdResult(
            raw_item=raw_item, imdb_id=imdb_id, tmdb_id=tmdb_id, item_type=item_type
        )
