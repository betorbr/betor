import hashlib
import json
from collections import OrderedDict
from datetime import datetime
from typing import Literal, Optional

import motor.motor_asyncio

from betor.entities import RawItem
from betor.settings import database_mongodb_settings


class RawItemsRepository:
    HASH_FIELD = "hash"
    INSERTED_AT_FIELD = "inserted_at"
    UPDATED_AT_FIELD = "updated_at"

    @classmethod
    def calculate_hash(cls, raw_item: RawItem) -> int:
        raw_item_data = cls.build_data(raw_item)
        raw = json.dumps(raw_item_data)
        return int(hashlib.sha1(raw.encode()).hexdigest(), 16) % (10**8)

    @classmethod
    def build_data(cls, raw_item: RawItem) -> dict:
        return OrderedDict(
            (
                k,
                v,
            )
            for k, v in sorted(raw_item.items(), key=lambda kv: kv[0])
            if k not in ["id", "hash", "inserted_at", "updated_at"]
        )

    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.mongodb_client = mongodb_client

    @property
    def database(self) -> motor.motor_asyncio.AsyncIOMotorDatabase:
        return self.mongodb_client.get_database(
            database_mongodb_settings.betor_database
        )

    @property
    def collection(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.database["raw_items"]

    async def get(self, provider_slug: str, provider_url: str) -> Optional[RawItem]:
        result = await self.collection.find_one(
            {"provider_slug": provider_slug, "provider_url": provider_url}
        )
        if not result:
            return None
        return RawItem(
            id=str(result["_id"]),
            hash=result.get(RawItemsRepository.HASH_FIELD),
            provider_slug=result["provider_slug"],
            provider_url=result["provider_url"],
            inserted_at=result.get(RawItemsRepository.INSERTED_AT_FIELD),
            updated_at=result.get(RawItemsRepository.UPDATED_AT_FIELD),
            imdb_id=result.get("imdb_id"),
            tmdb_id=result.get("tmdb_id"),
            magnet_uris=result.get("magnet_uris", []),
            languages=result.get("languages", []),
            qualitys=result.get("qualitys", []),
            title=result.get("title"),
            translated_title=result.get("translated_title"),
            raw_title=result.get("raw_title"),
            year=result.get("year"),
        )

    async def insert_or_update(
        self, raw_item: RawItem
    ) -> Literal["inserted", "updated", "no_change"]:
        retrieved = await self.get(raw_item["provider_slug"], raw_item["provider_url"])
        if not retrieved:
            await self.insert(raw_item)
            return "inserted"
        if retrieved.get("hash") != RawItemsRepository.calculate_hash(raw_item):
            await self.update(raw_item)
            return "updated"
        return "no_change"

    async def insert(self, raw_item: RawItem, hash: Optional[str] = None):
        await self.collection.insert_one(
            {
                **RawItemsRepository.build_data(raw_item),
                RawItemsRepository.HASH_FIELD: hash
                or RawItemsRepository.calculate_hash(raw_item),
                RawItemsRepository.INSERTED_AT_FIELD: datetime.now(),
                RawItemsRepository.UPDATED_AT_FIELD: None,
            }
        )

    async def update(self, raw_item: RawItem):
        await self.collection.update_one(
            {
                "provider_slug": raw_item["provider_slug"],
                "provider_url": raw_item["provider_url"],
            },
            {
                "$set": {
                    **RawItemsRepository.build_data(raw_item),
                    RawItemsRepository.HASH_FIELD: RawItemsRepository.calculate_hash(
                        raw_item
                    ),
                    RawItemsRepository.UPDATED_AT_FIELD: datetime.now(),
                }
            },
        )
