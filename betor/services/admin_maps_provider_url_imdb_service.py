from typing import TypedDict

import motor.motor_asyncio

from betor.entities import ProviderURLIMDBMapping
from betor.repositories import ProviderURLIMDBMappingRepository
from betor.types import InsertOrUpdateResult


class AdminMapsProviderURLIMDBResult(TypedDict):
    provider_url_imdb_mapping: ProviderURLIMDBMapping
    insert_or_update_result: InsertOrUpdateResult


class AdminMapsProviderURLIMDBService:
    def __init__(self, mongodb_client: motor.motor_asyncio.AsyncIOMotorClient):
        self.provider_url_imdb_mapping_repository = ProviderURLIMDBMappingRepository(
            mongodb_client
        )

    async def maps(
        self, provider_url: str, imdb_id: str
    ) -> AdminMapsProviderURLIMDBResult:
        provider_url_imdb_mapping = ProviderURLIMDBMapping(
            id=None,
            inserted_at=None,
            updated_at=None,
            provider_url=provider_url,
            imdb_id=imdb_id,
        )
        insert_or_update_result = (
            await self.provider_url_imdb_mapping_repository.insert_or_update(
                provider_url_imdb_mapping
            )
        )
        provider_url_imdb_mapping_retrieved = (
            await self.provider_url_imdb_mapping_repository.get(provider_url)
        )
        assert provider_url_imdb_mapping_retrieved
        return AdminMapsProviderURLIMDBResult(
            provider_url_imdb_mapping=provider_url_imdb_mapping_retrieved,
            insert_or_update_result=insert_or_update_result,
        )
