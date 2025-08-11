import pytest
from faker import Faker

from betor.types import RawItem


@pytest.fixture
def fake() -> Faker:
    return Faker()


@pytest.fixture
def raw_item(request: pytest.FixtureRequest, fake: Faker) -> RawItem:
    raw_item = RawItem(
        id=None,
        hash=None,
        inserted_at=None,
        updated_at=None,
        provider_slug=fake.slug(),
        provider_url=fake.url(),
        imdb_id=None,
        tmdb_id=None,
        magnet_links=[],
        languages=[],
        qualitys=[],
        title=None,
        translated_title=None,
        raw_title=None,
        year=None,
    )
    if request.param and isinstance(request.param, dict):
        raw_item.update(request.param)
    return raw_item
