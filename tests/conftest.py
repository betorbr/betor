import pytest
import torf
from faker import Faker

from betor.entities import Item, RawItem


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
        magnet_uris=[],
        languages=[],
        qualitys=[],
        title=None,
        translated_title=None,
        raw_title=None,
        year=None,
        cast=None,
    )
    if request.param and isinstance(request.param, dict):
        raw_item.update(request.param)
    return raw_item


@pytest.fixture
def item(request: pytest.FixtureRequest, fake: Faker) -> Item:
    magnet_uri = "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=Big+Buck+Bunny&tr=udp%3A%2F%2Fexplodie.org%3A6969&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969&tr=udp%3A%2F%2Ftracker.empire-js.us%3A1337&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337&tr=wss%3A%2F%2Ftracker.btorrent.xyz&tr=wss%3A%2F%2Ftracker.fastcast.nz&tr=wss%3A%2F%2Ftracker.openwebtorrent.com&ws=https%3A%2F%2Fwebtorrent.io%2Ftorrents%2F&xs=https%3A%2F%2Fwebtorrent.io%2Ftorrents%2Fbig-buck-bunny.torrent"
    magnet = torf.Magnet.from_string(magnet_uri)
    item = Item(
        provider_slug=fake.slug(),
        provider_url=fake.url(),
        imdb_id=None,
        tmdb_id=None,
        item_type=None,
        id=None,
        hash=None,
        inserted_at=None,
        updated_at=None,
        magnet_uri=magnet_uri,
        magnet_xt=magnet.xt,
        magnet_dn=magnet.dn,
        torrent_name=None,
        torrent_num_peers=None,
        torrent_num_seeds=None,
        torrent_files=None,
        torrent_size=None,
        languages=[],
        episodes=[],
        seasons=[],
    )
    if request.param and isinstance(request.param, dict):
        item.update(request.param)
    return item
