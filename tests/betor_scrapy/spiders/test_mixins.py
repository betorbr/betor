import pytest

from betor_scrapy.spiders.mixins import UnlockSystemAdsMixin


class TestUnlockSystemAdsMixin:
    def test_get_allowed_domains(self):
        assert UnlockSystemAdsMixin.get_allowed_domains() == [
            "www.systemads.org",
            "superadsgo.xyz",
            "superadsgo1.xyz",
            "www.systemads.xyz",
            "systemads.net",
        ]

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
    def test_unlock_protected_redirect_link_ok(self, url: str, expected: str):
        assert UnlockSystemAdsMixin.unlock_protected_redirect_link(url) == expected

    def test_unlock_protected_redirect_link_missing_id(self):
        with pytest.raises(ValueError, match="id value not found"):
            UnlockSystemAdsMixin.unlock_protected_redirect_link(
                "https://www.systemads.org/get.php?refsite=bludv"
            )

    def test_unlock_protected_redirect_link_invalid_base64(self):
        with pytest.raises(ValueError, match="can't decode base64 value"):
            UnlockSystemAdsMixin.unlock_protected_redirect_link(
                "https://www.systemads.org/get.php?id=invalid!"
            )

    def test_unlock_encrypted_protected_link_ok(self):
        response_content = (
            'const redirect = "https://redirecionandovoce.info/receber.php?id='
            '0MjMxoDapRnY64mc11Dd49jO0VmbnFWb&amp;utm_source=&amp;utm_medium=&amp;utm_campaign=filmes2024&amp;refsite=";'
        )

        assert (
            UnlockSystemAdsMixin.unlock_encrypted_protected_link(response_content)
            == "magnet:?xt=urn:btih:1234"
        )

    def test_unlock_encrypted_protected_link_no_redirect(self):
        with pytest.raises(ValueError, match="Redirect URL not found in response"):
            UnlockSystemAdsMixin.unlock_encrypted_protected_link(
                "<html><body>No protected redirect here</body></html>"
            )
