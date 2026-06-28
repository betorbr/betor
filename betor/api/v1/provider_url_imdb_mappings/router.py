from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Response, status
from fastapi_pagination import Page
from fastapi_pagination.ext.motor import apaginate

from betor.api.fast_api import BetorRequest
from betor.enums import ProviderURLIMDBMappingSortEnum
from betor.repositories import ProviderURLIMDBMappingRepository

from .schemas import ProviderURLIMDBMappingSchema

provider_url_imdb_mappings_router = APIRouter()


@provider_url_imdb_mappings_router.get(
    "/",
    response_model=Page[ProviderURLIMDBMappingSchema],
)
async def list_provider_url_imdb_mappings(
    request: BetorRequest,
    sort: ProviderURLIMDBMappingSortEnum = ProviderURLIMDBMappingSortEnum.inserted_at_desc,
    provider_url: Optional[str] = None,
) -> Page[ProviderURLIMDBMappingSchema]:
    repository = ProviderURLIMDBMappingRepository(request.app.mongodb_client)
    collection, query_filter, cursor_sort, transformer = repository.apaginate_params(
        sort,
        provider_url=provider_url,
    )
    return await apaginate(
        collection,
        query_filter=query_filter,
        sort=cursor_sort,
        transformer=transformer,
    )


@provider_url_imdb_mappings_router.delete(
    "/{id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_provider_url_imdb_mapping(
    request: BetorRequest,
    id: str = Path(..., description="ProviderURLIMDBMapping id to delete"),
) -> Response:
    repository = ProviderURLIMDBMappingRepository(request.app.mongodb_client)
    deleted = await repository.delete(id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ProviderURLIMDBMapping not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
