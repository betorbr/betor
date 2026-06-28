from typing import List, Optional
from unittest import mock

import motor.motor_asyncio
import pytest

from betor.entities import RawItem
from betor.enums import ItemType
from betor.services import DeterminesIMDbTMDBIdsService


@pytest.fixture()
def mongodb_client_mock():
    return mock.MagicMock(spec=motor.motor_asyncio.AsyncIOMotorClient)


@pytest.mark.parametrize(
    (
        "raw_item",
        "mapping_get_side_effect",
        "expected_imdb_id",
        "expected_tmdb_id",
        "expected_item_type",
    ),
    [
        (
            RawItem(
                id=None,
                hash=None,
                inserted_at=None,
                updated_at=None,
                provider_slug="test",
                provider_url="http://www.test.com/movie01/",
                imdb_id=None,
                tmdb_id=None,
                magnet_uris=[],
                languages=[],
                qualitys=[],
                title=None,
                translated_title=None,
                raw_title=None,
                year=None,
                cast=None,
            ),
            [None],
            None,
            None,
            None,
        )
    ],
)
@pytest.mark.asyncio
async def test_determines(
    mongodb_client_mock,
    raw_item: RawItem,
    mapping_get_side_effect: List,
    expected_imdb_id: Optional[str],
    expected_tmdb_id: Optional[str],
    expected_item_type: Optional[ItemType],
):
    service = DeterminesIMDbTMDBIdsService(mongodb_client_mock)
    with mock.patch.object(
        service.provider_url_imdb_mapping_repository,
        "get",
        new_callable=mock.AsyncMock,
        side_effect=mapping_get_side_effect,
    ):
        imdb_id, tmdb_id, item_type = await service.determines(raw_item)
    assert imdb_id == expected_imdb_id
    assert tmdb_id == expected_tmdb_id
    assert item_type == expected_item_type
