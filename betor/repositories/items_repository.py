import hashlib
import json
from collections import OrderedDict
from datetime import datetime
from typing import Literal, Optional

import motor.motor_asyncio

from betor.settings import database_mongodb_settings
from betor.types import Item


class ItemsRepository:
    HASH_FIELD = "hash"
    INSERTED_AT_FIELD = "inserted_at"
    UPDATED_AT_FIELD = "updated_at"

    @classmethod
    def calculate_hash(cls, item: Item) -> int:
        item_data = cls.build_item_data(item)
        raw = json.dumps(item_data)
        return int(hashlib.sha1(raw.encode()).hexdigest(), 16) % (10**8)

    @classmethod
    def build_item_data(cls, item: Item) -> dict:
        return OrderedDict(
            (
                k,
                v,
            )
            for k, v in sorted(item.items(), key=lambda kv: kv[0])
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
        return self.database["items"]

    async def get(self, provider_slug: str, provider_url: str) -> Optional[Item]:
        result = await self.collection.find_one(
            {"provider_slug": provider_slug, "provider_url": provider_url}
        )
        if not result:
            return None
        return {
            "id": result.get("_id"),
            "hash": result.get(ItemsRepository.HASH_FIELD),
            "provider_slug": result["provider_slug"],
            "provider_url": result["provider_url"],
            "inserted_at": result.get(ItemsRepository.INSERTED_AT_FIELD),
            "updated_at": result.get(ItemsRepository.UPDATED_AT_FIELD),
            "imdb_id": result.get("imdb_id"),
            "magnet_links": result.get("magnet_links", []),
            "languages": result.get("languages", []),
            "qualitys": result.get("qualitys", []),
            "title": result.get("title"),
            "translated_title": result.get("translated_title"),
            "raw_title": result.get("raw_title"),
            "year": result.get("year"),
        }

    async def insert_or_update_item(
        self, item: Item
    ) -> Literal["inserted", "updated", "no_change"]:
        retrieved = await self.get(item["provider_slug"], item["provider_url"])
        if not retrieved:
            await self.insert_item(item)
            return "inserted"
        if retrieved.get("hash") != ItemsRepository.calculate_hash(item):
            await self.update_item(item)
            return "updated"
        return "no_change"

    async def insert_item(self, item: Item, hash: Optional[str] = None):
        await self.collection.insert_one(
            {
                **ItemsRepository.build_item_data(item),
                ItemsRepository.HASH_FIELD: hash
                or ItemsRepository.calculate_hash(item),
                ItemsRepository.INSERTED_AT_FIELD: datetime.now(),
                ItemsRepository.UPDATED_AT_FIELD: None,
            }
        )

    async def update_item(self, item: Item):
        await self.collection.update_one(
            {
                "provider_slug": item["provider_slug"],
                "provider_url": item["provider_url"],
            },
            {
                "$set": {
                    **ItemsRepository.build_item_data(item),
                    ItemsRepository.HASH_FIELD: ItemsRepository.calculate_hash(item),
                    ItemsRepository.UPDATED_AT_FIELD: datetime.now(),
                }
            },
        )
