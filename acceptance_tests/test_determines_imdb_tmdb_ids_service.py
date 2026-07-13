from typing import List, Optional
from unittest import mock

import motor.motor_asyncio
import pytest

from betor.entities import ProviderURLIMDBMapping, RawItem
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
            [
                ProviderURLIMDBMapping(
                    id=None,
                    inserted_at=None,
                    updated_at=None,
                    provider_url="http://www.test.com/movie01/",
                    imdb_id="tt38681832",
                )
            ],
            "tt38681832",
            "1560681",
            ItemType.movie,
        ),
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
                translated_title="As Cores do Mal: Preto",
                raw_title=None,
                year=2026,
                cast=None,
            ),
            [None],
            "tt38681832",
            "1560681",
            ItemType.movie,
        ),
        (
            RawItem(
                id=None,
                hash=None,
                inserted_at=None,
                updated_at=None,
                provider_slug="starck-filmes",
                provider_url="https://www.starckfilmes-v20.com/catalog/origem-4-temporada-2026-19-04-2026/",
                imdb_id=None,
                tmdb_id=None,
                magnet_uris=[],
                languages=[],
                qualitys=[],
                title="From",
                translated_title=None,
                raw_title="Origem 4ª Temporada Torrent (2026) Dual Áudio Download",
                year=2026,
                cast=None,
            ),
            [None],
            "tt9813792",
            "124364",
            ItemType.tv,
        ),
        (
            RawItem(
                id=None,
                hash=None,
                inserted_at=None,
                updated_at=None,
                provider_slug="test",
                provider_url="http://www.test.com/tv01/",
                imdb_id="tt9813792",
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
            "tt9813792",
            "124364",
            ItemType.tv,
        ),
        (
            RawItem(
                id=None,
                hash=None,
                inserted_at=None,
                updated_at=None,
                provider_slug="sem-torrent",
                provider_url="https://semtorrent.com/filme/anjos-da-guerra/",
                imdb_id=None,
                tmdb_id=None,
                magnet_uris=[],
                languages=["ru", "pt"],
                qualitys=["Unknown"],
                title=None,
                translated_title="ANJOS DA GUERRA",
                raw_title="Anjos da Guerra Dublado 1080P WEB-DL",
                year=2026,
                cast=["Тихон Жизневский"],
            ),
            [None],
            "tt37544092",
            "1275255",
            ItemType.movie,
        ),
        (
            RawItem(
                id=None,
                hash=None,
                inserted_at=None,
                updated_at=None,
                provider_slug="comando-torrents",
                provider_url="https://comando1.com/origem-4a-temporada-2026-dual-audio-web-dl-1080p/",
                imdb_id="tt9813792",
                tmdb_id=None,
                magnet_uris=[],
                languages=["en", "pt"],
                qualitys=["Unknown"],
                title="FROM",
                translated_title="Origem",
                raw_title="Origem 4ª Temporada (2026) Dual Áudio WEB-DL 1080p",
                year=None,
                cast=None,
            ),
            [None],
            "tt9813792",
            "124364",
            ItemType.tv,
        ),
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
        imdb_id, imdb_score_value, tmdb_id, tmdb_score_value, item_type = (
            await service.determines(raw_item)
        )
    assert imdb_id == expected_imdb_id
    assert tmdb_id == expected_tmdb_id
    assert item_type == expected_item_type
