import pytest
from unittest import mock

from betor.utils import extract_magnet_info_hash, jaccard_similarity


class TestJaccardSimilarity:
    @pytest.mark.parametrize(
        (
            "a",
            "b",
            "expected",
        ),
        [
            ("foo", "foo", 1.0),
            ("foo", "bar", 0.0),
            ("foo test", "foo foo", 0.5),
        ],
    )
    def test_expected(self, a: str, b: str, expected: float):
        assert jaccard_similarity(a, b) == expected


class TestExtractMagnetInfoHash:
    def test_returns_hex_info_hash_for_hex_magnet(self):
        magnet_uri = (
            "magnet:?xt=urn:btih:dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c&dn=test"
        )

        assert extract_magnet_info_hash(magnet_uri) == "dd8255ecdc7ca55fb0bbf81323d87062db1f6d1c"

    def test_returns_hex_info_hash_for_base32_magnet(self):
        mock_magnet = mock.Mock(infohash="MFRGGZDFMZTWQ2LKNNWG23TPOBYXE43U")
        with mock.patch("betor.utils.torf.Magnet.from_string", return_value=mock_magnet):
            assert (
                extract_magnet_info_hash("magnet:?xt=urn:btih:any")
                == "6162636465666768696a6b6c6d6e6f7071727374"
            )

    def test_returns_none_for_invalid_magnet(self):
        assert extract_magnet_info_hash("invalid") is None
