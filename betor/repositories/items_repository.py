import hashlib
import json
import logging
from collections import OrderedDict
from datetime import UTC, datetime, timedelta
from time import perf_counter
from typing import Dict, List, Optional, Sequence, cast

import motor.motor_asyncio
from bson.errors import InvalidId
from bson.objectid import ObjectId

from betor.entities import (
    EpisodesInfo,
    Item,
    LanguagesInfo,
    TorrentFailure,
    TorrentInfo,
    TorrentTrackersInfo,
)
from betor.enums import ItemType
from betor.settings import database_mongodb_settings
from betor.types import InsertOrUpdateResult


logger = logging.getLogger(__name__)


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
                "torrent_size",
                "torrent_num_peers",
                "torrent_num_seeds",
                "torrent_files",
                "download_path",
                "itorrent_uploaded_at",
                "languages",
                "torrent_failure_history",
                "torrent_failure_days",
                "torrent_is_dying",
                "torrent_is_dead",
            ]
        )

    @classmethod
    def parse_result(cls, result: Dict) -> Item:
        return Item(
            provider_slug=result["provider_slug"],
            provider_url=result["provider_url"],
            imdb_id=result.get("imdb_id"),
            imdb_score_value=result.get("imdb_score_value"),
            tmdb_id=result.get("tmdb_id"),
            tmdb_score_value=result.get("tmdb_score_value"),
            item_type=result.get("item_type"),
            id=str(result["_id"]),
            hash=result.get(ItemsRepository.HASH_FIELD),
            inserted_at=result.get(ItemsRepository.INSERTED_AT_FIELD),
            updated_at=result.get(ItemsRepository.UPDATED_AT_FIELD),
            magnet_uri=result["magnet_uri"],
            magnet_xt=result["magnet_xt"],
            magnet_dn=result.get("magnet_dn"),
            torrent_failure_history=result.get("torrent_failure_history", []),
            torrent_failure_days=result.get("torrent_failure_days", 0),
            torrent_is_dying=result.get("torrent_is_dying", False),
            torrent_is_dead=result.get("torrent_is_dead", False),
            torrent_name=result.get("torrent_name"),
            torrent_files=result.get("torrent_files"),
            torrent_size=result.get("torrent_size"),
            download_path=result.get("download_path"),
            itorrent_uploaded_at=result.get("itorrent_uploaded_at"),
            torrent_num_peers=result.get("torrent_num_peers"),
            torrent_num_seeds=result.get("torrent_num_seeds"),
            languages=result.get("languages", []),
            episodes=result.get("episodes", []),
            seasons=result.get("seasons", []),
        )

    @classmethod
    def parse_results(cls, results: Sequence[Dict]) -> Sequence[Item]:
        return [ItemsRepository.parse_result(r) for r in results]

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def _to_utc_naive(value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value.astimezone(UTC).replace(tzinfo=None)
        return value

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
        try:
            object_id = ObjectId(item_id)
        except InvalidId:
            return None
        result = await self.collection.find_one({"_id": object_id})
        if not result:
            return None
        return ItemsRepository.parse_result(result)

    async def insert_or_update(self, item: Item) -> InsertOrUpdateResult:
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

    async def dump_all_items(self) -> tuple[float, List[Item]]:
        start = perf_counter()
        results = await self.collection.find({}).to_list(length=None)
        items = [ItemsRepository.parse_result(result) for result in results]
        duration = perf_counter() - start
        return duration, items

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

    async def update_item_episodes_info(
        self, item_id: str, episodes_info: EpisodesInfo
    ):
        await self.collection.update_one(
            {
                "_id": ObjectId(item_id),
            },
            {
                "$set": {
                    **episodes_info,
                    ItemsRepository.UPDATED_AT_FIELD: datetime.now(),
                }
            },
        )

    async def list_empty_tmdb_id(self) -> List[Item]:
        results = await self.collection.find({"tmdb_id": None}).to_list()
        return [ItemsRepository.parse_result(result) for result in results]

    async def update_tmdb_id(self, item_id: str, tmdb_id: str):
        await self.collection.update_one(
            {
                "_id": ObjectId(item_id),
            },
            {
                "$set": {
                    "tmdb_id": tmdb_id,
                    ItemsRepository.UPDATED_AT_FIELD: datetime.now(),
                }
            },
        )

    async def update_provider_url_imdb_tmdb_id(
        self,
        provider_url: str,
        imdb_id: Optional[str],
        imdb_score_value: Optional[float],
        tmdb_id: Optional[str],
        tmdb_score_value: Optional[float],
        item_type: Optional[ItemType],
    ):
        await self.collection.update_many(
            {
                "provider_url": provider_url,
            },
            {
                "$set": {
                    "imdb_id": imdb_id,
                    "imdb_score_value": imdb_score_value,
                    "tmdb_id": tmdb_id,
                    "tmdb_score_value": tmdb_score_value,
                    "item_type": item_type,
                    ItemsRepository.UPDATED_AT_FIELD: datetime.now(),
                }
            },
        )

    async def update_torrent_trackers_info(
        self, magnet_uri: str, torrent_trackers_info: TorrentTrackersInfo
    ):
        await self.collection.update_many(
            {
                "magnet_uri": magnet_uri,
            },
            {
                "$set": {
                    **torrent_trackers_info,
                    ItemsRepository.UPDATED_AT_FIELD: datetime.now(),
                }
            },
        )

    def _build_torrent_health_pipeline(
        self, now: datetime, append_failure: Optional[TorrentFailure] = None
    ) -> List[Dict]:
        history_input: Dict = {"$ifNull": ["$torrent_failure_history", []]}
        if append_failure is not None:
            history_input = {
                "$concatArrays": [
                    history_input,
                    [append_failure],
                ]
            }

        window_start = now - timedelta(days=7)
        valid_history = {
            "$filter": {
                "input": history_input,
                "as": "failure",
                "cond": {
                    "$and": [
                        {"$eq": [{"$type": "$$failure.occurred_at"}, "date"]},
                        {"$gte": ["$$failure.occurred_at", window_start]},
                        {"$lte": ["$$failure.occurred_at", now]},
                    ]
                },
            }
        }
        failure_days = {
            "$size": {
                "$setUnion": [
                    {
                        "$map": {
                            "input": valid_history,
                            "as": "failure",
                            "in": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": "$$failure.occurred_at",
                                    "timezone": "UTC",
                                }
                            },
                        }
                    },
                    [],
                ]
            }
        }

        return [
            {"$set": {"torrent_failure_history": valid_history}},
            {
                "$set": {
                    "torrent_failure_days": failure_days,
                    ItemsRepository.UPDATED_AT_FIELD: now,
                }
            },
            {
                "$set": {
                    "torrent_is_dying": {"$gte": ["$torrent_failure_days", 1]},
                    "torrent_is_dead": {"$gte": ["$torrent_failure_days", 5]},
                }
            },
        ]

    async def maintain_torrent_health(self, magnet_uri: str):
        now = ItemsRepository._utc_now()
        await self.collection.update_many(
            {"magnet_uri": magnet_uri},
            self._build_torrent_health_pipeline(now),
        )

    async def record_torrent_failure(self, magnet_uri: str, failure: TorrentFailure):
        now = ItemsRepository._utc_now()
        occurred_at = failure.get("occurred_at")
        append_failure: Optional[TorrentFailure] = None
        if not isinstance(occurred_at, datetime):
            logger.warning(
                "Skipping invalid torrent failure event for %s: occurred_at is not datetime",
                magnet_uri,
            )
        else:
            normalized_occurred_at = ItemsRepository._to_utc_naive(occurred_at)
            if normalized_occurred_at > now:
                logger.warning(
                    "Skipping future torrent failure event for %s: occurred_at=%s now=%s",
                    magnet_uri,
                    occurred_at,
                    now,
                )
                append_failure = None
            else:
                append_failure = cast(
                    TorrentFailure,
                    {**failure, "occurred_at": normalized_occurred_at},
                )

        await self.collection.update_many(
            {"magnet_uri": magnet_uri},
            self._build_torrent_health_pipeline(now, append_failure=append_failure),
        )

    async def count_by_provider_slug_and_item_type(
        self,
    ) -> Dict[tuple[str, Optional[ItemType]], int]:
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "provider_slug": "$provider_slug",
                        "item_type": "$item_type",
                    },
                    "count": {"$sum": 1},
                }
            }
        ]
        results = await self.collection.aggregate(pipeline).to_list(length=None)
        return {
            (result["_id"]["provider_slug"], result["_id"]["item_type"]): result[
                "count"
            ]
            for result in results
        }
