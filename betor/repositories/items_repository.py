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
        item_data = cls.build_data(item)
        raw = json.dumps(item_data)
        return int(hashlib.sha1(raw.encode()).hexdigest(), 16) % (10**8)

    @classmethod
    def build_data(cls, item: Item) -> dict:
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

    async def get(
        self, provider_slug: str, provider_url: str, magnet_xt: str
    ) -> Optional[Item]:
        result = await self.collection.find_one(
            {
                "provider_slug": provider_slug,
                "provider_url": provider_url,
                "magnet_xt": magnet_xt,
            }
        )
        if not result:
            return None
        return Item(
            provider_slug=result["provider_slug"],
            provider_url=result["provider_url"],
            imdb_id=result.get("imdb_id"),
            tmdb_id=result.get("tmdb_id"),
            item_type=result.get("item_type"),
            id=str(result["_id"]),
            hash=result.get(ItemsRepository.HASH_FIELD),
            inserted_at=result.get(ItemsRepository.INSERTED_AT_FIELD),
            updated_at=result.get(ItemsRepository.UPDATED_AT_FIELD),
            magnet_link=result["magnet_link"],
            magnet_xt=result["magnet_xt"],
            magnet_dn=result.get("magnet_dn"),
        )

    async def insert_or_update(
        self, item: Item
    ) -> Literal["inserted", "updated", "no_change"]:
        retrieved = await self.get(
            item["provider_slug"], item["provider_url"], item["magnet_xt"]
        )
        if not retrieved:
            await self.insert(item)
            return "inserted"
        if retrieved.get("hash") != ItemsRepository.calculate_hash(item):
            await self.update(item)
            return "updated"
        return "no_change"

    async def insert(self, item: Item, hash: Optional[str] = None):
        await self.collection.insert_one(
            {
                **ItemsRepository.build_data(item),
                ItemsRepository.HASH_FIELD: hash
                or ItemsRepository.calculate_hash(item),
                ItemsRepository.INSERTED_AT_FIELD: datetime.now(),
                ItemsRepository.UPDATED_AT_FIELD: None,
            }
        )

    async def update(self, item: Item):
        await self.collection.update_one(
            {
                "provider_slug": item["provider_slug"],
                "provider_url": item["provider_url"],
                "magnet_xt": item["magnet_xt"],
            },
            {
                "$set": {
                    **ItemsRepository.build_data(item),
                    ItemsRepository.HASH_FIELD: ItemsRepository.calculate_hash(item),
                    ItemsRepository.UPDATED_AT_FIELD: datetime.now(),
                }
            },
        )
