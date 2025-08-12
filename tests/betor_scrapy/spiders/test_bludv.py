import pytest

from betor_scrapy.spiders.bludv import BludvSpider


class TestUnlockProtectedLink:
    @pytest.mark.parametrize(
        (
            "url",
            "expected",
        ),
        [
            (
                "https://www.systemads.org/get.php?id=0EWMyUmN1I2N1EDN3MmMzYmMlVDOlBTN2cTZ0UzN0YGM2UzMjNGNyoDapRnY64mc11Dd49jO0VmbnFWb&refsite=bludv",
                "magnet:?xt=urn:btih:24cc3560f4754e7650e85e2f32c74157b56e21a4",
            ),
        ],
    )
    def test_ok(self, url: str, expected: str):
        assert BludvSpider.unlock_protected_link(url) == expected
