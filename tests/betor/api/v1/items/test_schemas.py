from datetime import datetime
from unittest import mock

from betor.api.v1.items.schemas import ItemSchema
from betor.entities import Item


def test_download_url_uses_itorrent_when_enabled_and_uploaded(item: Item):
    payload = {
        **item,
        "magnet_xt": "urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c",
        "itorrent_uploaded_at": datetime.now(),
    }

    with mock.patch(
        "betor.api.v1.items.schemas.itorrent_settings",
        mock.Mock(
            download_enabled=True,
            public_download_base_url="http://itorrents.net/torrent",
        ),
    ):
        schema = ItemSchema.model_validate(payload)
        assert (
            schema.download_url
            == "http://itorrents.net/torrent/DD8255ECDC7CA55FB0BBF81323D87062DB1F6D1C.torrent"
        )


def test_download_url_falls_back_when_enabled_but_upload_date_is_null(item: Item):
    payload = {
        **item,
        "download_path": "foo.torrent",
        "itorrent_uploaded_at": None,
    }

    with mock.patch(
        "betor.api.v1.items.schemas.itorrent_settings",
        mock.Mock(
            download_enabled=True,
            public_download_base_url="http://itorrents.net/torrent",
        ),
    ):
        with mock.patch(
            "betor.api.v1.items.schemas.store_torrent_file_settings",
            mock.Mock(public_download_base_url="https://example.com/downloads"),
        ):
            schema = ItemSchema.model_validate(payload)
            assert schema.download_url == "https://example.com/downloads/foo.torrent"


def test_download_url_falls_back_to_current_behavior_when_itorrent_disabled(item: Item):
    payload = {
        **item,
        "download_path": "bar.torrent",
        "itorrent_uploaded_at": datetime.now(),
    }

    with mock.patch(
        "betor.api.v1.items.schemas.itorrent_settings",
        mock.Mock(
            download_enabled=False,
            public_download_base_url="http://itorrents.net/torrent",
        ),
    ):
        with mock.patch(
            "betor.api.v1.items.schemas.store_torrent_file_settings",
            mock.Mock(public_download_base_url="https://example.com/downloads"),
        ):
            schema = ItemSchema.model_validate(payload)
            assert schema.download_url == "https://example.com/downloads/bar.torrent"
