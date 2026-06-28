from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, Optional, Sequence, cast

import motor.motor_asyncio
from bson.errors import InvalidId
from bson.objectid import ObjectId

from betor.entities import ProviderURLIMDBMapping
from betor.enums import ProviderURLIMDBMappingSortEnum
from betor.settings import database_mongodb_settings
from betor.types import ApaginateParams, CursorSort, InsertOrUpdateResult


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
    def parse_results(cls, results: Sequence[Dict]) -> Sequence[ProviderURLIMDBMapping]:
        return [
            ProviderURLIMDBMappingRepository.parse_result(result) for result in results
        ]

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

    def apaginate_params(
        self,
        sort: ProviderURLIMDBMappingSortEnum,
        provider_url: Optional[str] = None,
    ) -> ApaginateParams[ProviderURLIMDBMapping]:
        cursor_sort_mapping: Dict[ProviderURLIMDBMappingSortEnum, CursorSort] = {
            ProviderURLIMDBMappingSortEnum.inserted_at_asc: self.INSERTED_AT_FIELD,
            ProviderURLIMDBMappingSortEnum.inserted_at_desc: (
                self.INSERTED_AT_FIELD,
                -1,
            ),
            ProviderURLIMDBMappingSortEnum.updated_at_asc: self.UPDATED_AT_FIELD,
            ProviderURLIMDBMappingSortEnum.updated_at_desc: (
                self.UPDATED_AT_FIELD,
                -1,
            ),
        }
        cursor_sort = cursor_sort_mapping.get(sort)
        assert cursor_sort is not None

        filter_statements: list[Dict[str, Any]] = []
        if provider_url is not None:
            filter_statements.append({"provider_url": provider_url})

        query_filter: Optional[Dict[Any, Any]] = None
        if filter_statements:
            query_filter = (
                {"$and": filter_statements}
                if len(filter_statements) > 1
                else filter_statements[0]
            )

        return (
            self.collection,
            query_filter,
            cursor_sort,
            ProviderURLIMDBMappingRepository.parse_results,
        )

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

    async def delete(self, provider_url_id: str) -> bool:
        try:
            object_id = ObjectId(provider_url_id)
        except InvalidId:
            return False

        result = await self.collection.delete_one({"_id": object_id})
        return bool(result.deleted_count)

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
