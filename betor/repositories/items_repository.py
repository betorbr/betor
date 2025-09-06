import hashlib
import json
from collections import OrderedDict
from datetime import datetime
from typing import Dict, List, Literal, Optional, Sequence

import motor.motor_asyncio
from bson.objectid import ObjectId

from betor.entities import EpisodesInfo, Item, LanguagesInfo, TorrentInfo
from betor.settings import database_mongodb_settings


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
            if k
            not in [
                "id",
                "hash",
                "inserted_at",
                "updated_at",
                "torrent_name",
                "torrent_num_peers",
                "torrent_num_seeds",
                "torrent_files",
                "languages",
            ]
        )

    @classmethod
    def parse_result(cls, result: Dict) -> Item:
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
            magnet_uri=result["magnet_uri"],
            magnet_xt=result["magnet_xt"],
            magnet_dn=result.get("magnet_dn"),
            torrent_name=result.get("torrent_name"),
            torrent_num_peers=result.get("torrent_num_peers"),
            torrent_num_seeds=result.get("torrent_num_seeds"),
            torrent_files=result.get("torrent_files"),
            torrent_size=result.get("torrent_size"),
            languages=result.get("languages", []),
            episodes=result.get("episodes", []),
        )

    @classmethod
    def parse_results(cls, results: Sequence[Dict]) -> Sequence[Item]:
        return [ItemsRepository.parse_result(r) for r in results]

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
        return ItemsRepository.parse_result(result)

    async def get_by_id(self, item_id: str) -> Optional[Item]:
        result = await self.collection.find_one({"_id": ObjectId(item_id)})
        if not result:
            return None
        return ItemsRepository.parse_result(result)

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

    async def update_torrent_info(self, magnet_uri: str, torrent_info: TorrentInfo):
        await self.collection.update_many(
            {
                "magnet_uri": magnet_uri,
            },
            {
                "$set": {
                    **torrent_info,
                    ItemsRepository.UPDATED_AT_FIELD: datetime.now(),
                }
            },
        )

    async def update_languages_info(self, item_id: str, languages_info: LanguagesInfo):
        await self.collection.update_one(
            {
                "_id": ObjectId(item_id),
            },
            {
                "$set": {
                    **languages_info,
                    ItemsRepository.UPDATED_AT_FIELD: datetime.now(),
                }
            },
        )

    async def get_all_by_magnet_uri(self, magnet_uri: str) -> List[Item]:
        results = await self.collection.find({"magnet_uri": magnet_uri}).to_list()
        return [ItemsRepository.parse_result(result) for result in results]

    async def update_episodes_info(self, magnet_uri: str, episodes_info: EpisodesInfo):
        await self.collection.update_many(
            {
                "magnet_uri": magnet_uri,
            },
            {
                "$set": {
                    **episodes_info,
                    ItemsRepository.UPDATED_AT_FIELD: datetime.now(),
                }
            },
        )
