from unittest import mock

import motor.motor_asyncio
import pytest

from betor.enums import ItemsSortEnum
from betor.services.list_items_service import ListItemsService


@pytest.fixture
def list_items_service() -> ListItemsService:
    mongodb_client = mock.AsyncMock(spec=motor.motor_asyncio.AsyncIOMotorClient)
    with mock.patch("betor.services.list_items_service.ItemsRepository"):
        return ListItemsService(mongodb_client)


@pytest.mark.parametrize("torrent_is_dying", [True, False])
def test_apaginate_params_filters_by_torrent_is_dying(
    list_items_service: ListItemsService, torrent_is_dying: bool
):
    _, query_filter, _, _ = list_items_service.apaginate_params(
        ItemsSortEnum.inserted_at_desc,
        imdb_id="tt123",
        torrent_is_dying=torrent_is_dying,
    )

    assert query_filter == {
        "$and": [
            {"$or": [{"imdb_id": "tt123"}]},
            {"torrent_is_dying": torrent_is_dying},
        ]
    }


def test_apaginate_params_omits_torrent_is_dying_filter(
    list_items_service: ListItemsService,
):
    _, query_filter, _, _ = list_items_service.apaginate_params(
        ItemsSortEnum.inserted_at_desc,
        imdb_id="tt123",
        torrent_is_dying=None,
    )

    assert query_filter == {"$and": [{"$or": [{"imdb_id": "tt123"}]}]}
