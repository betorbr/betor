from collections import OrderedDict
from datetime import datetime
from typing import Dict, Optional, cast

import motor.motor_asyncio

from betor.entities import ProviderURLIMDBMapping
from betor.settings import database_mongodb_settings
from betor.types import InsertOrUpdateResult


class ProviderURLIMDBMappingRepository:
    INSERTED_AT_FIELD = "inserted_at"
    UPDATED_AT_FIELD = "updated_at"

    @classmethod
    def parse_result(cls, result: Dict) -> ProviderURLIMDBMapping:
        return ProviderURLIMDBMapping(
            id=str(result["_id"]),
            inserted_at=result.get(ProviderURLIMDBMappingRepository.INSERTED_AT_FIELD),
            updated_at=result.get(ProviderURLIMDBMappingRepository.UPDATED_AT_FIELD),
            provider_url=result["provider_url"],
            imdb_id=result["imdb_id"],
        )

    @classmethod
    def build_data(cls, provider_url_imdb_mapping: ProviderURLIMDBMapping) -> dict:
        return OrderedDict(
            (
                k,
                v,
            )
            for k, v in sorted(provider_url_imdb_mapping.items(), key=lambda kv: kv[0])
            if k not in ["id", "inserted_at", "updated_at"]
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
        return self.database["provider_url_imdb_mapping"]

    async def get(self, provider_url: str) -> Optional[ProviderURLIMDBMapping]:
        result = await self.collection.find_one({"provider_url": provider_url})
        if not result:
            return None
        result_dict = cast(Dict, result)
        return ProviderURLIMDBMappingRepository.parse_result(result_dict)

    async def insert(self, provider_url_imdb_mapping: ProviderURLIMDBMapping):
        await self.collection.insert_one(
            {
                **ProviderURLIMDBMappingRepository.build_data(
                    provider_url_imdb_mapping
                ),
                ProviderURLIMDBMappingRepository.INSERTED_AT_FIELD: datetime.now(),
                ProviderURLIMDBMappingRepository.UPDATED_AT_FIELD: None,
            }
        )

    async def update(self, provider_url_imdb_mapping: ProviderURLIMDBMapping):
        await self.collection.update_one(
            {"provider_url": provider_url_imdb_mapping["provider_url"]},
            {
                "$set": {
                    **ProviderURLIMDBMappingRepository.build_data(
                        provider_url_imdb_mapping
                    ),
                    ProviderURLIMDBMappingRepository.UPDATED_AT_FIELD: datetime.now(),
                }
            },
        )

    async def insert_or_update(
        self, provider_url_imdb_mapping: ProviderURLIMDBMapping
    ) -> InsertOrUpdateResult:
        retrieved = await self.get(provider_url_imdb_mapping["provider_url"])
        if not retrieved:
            await self.insert(provider_url_imdb_mapping)
            return "inserted"
        if retrieved["imdb_id"] != provider_url_imdb_mapping["imdb_id"]:
            await self.update(provider_url_imdb_mapping)
            return "updated"
        return "no_change"
