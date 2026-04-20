from unittest.mock import Mock, patch

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
    def test_unlock_protected_redirect_link_ok(self, url: str, expected: str):
        assert BludvSpider.unlock_protected_redirect_link(url) == expected

    @patch("betor_scrapy.spiders.bludv.requests.get")
    @patch.object(BludvSpider, "unlock_protected_redirect_link")
    def test_unlock_encrypted_protected_link_success(self, mock_unlock, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        const abToken  = "6e0af28272b3cbc1994ecd63c44edaa46d35780e1827cd84475f427bb76fadac";
        const redirect = "https://redirecionandovoce.info/receber.php?id=4UTYkZTMiJWYkV2M5EjNlhzMjZTYmNmN5QWYhRzYmZTY1UTN4MDZkpDapRnY64mc11Dd49jO0VmbnFWb&amp;utm_source=&amp;utm_medium=&amp;utm_campaign=filmes2024&amp;refsite=";
        """
        mock_get.return_value = mock_response
        mock_unlock.return_value = "expected_magnet"

        result = BludvSpider.unlock_encrypted_protected_link("http://example.com")

        assert result == "expected_magnet"
        mock_unlock.assert_called_once_with(
            "https://redirecionandovoce.info/receber.php?id=4UTYkZTMiJWYkV2M5EjNlhzMjZTYmNmN5QWYhRzYmZTY1UTN4MDZkpDapRnY64mc11Dd49jO0VmbnFWb&amp;utm_source=&amp;utm_medium=&amp;utm_campaign=filmes2024&amp;refsite="
        )

    @patch("betor_scrapy.spiders.bludv.requests.get")
    def test_unlock_encrypted_protected_link_fetch_fail(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Failed to fetch protected URL"):
            BludvSpider.unlock_encrypted_protected_link("http://example.com")

    @patch("betor_scrapy.spiders.bludv.requests.get")
    def test_unlock_encrypted_protected_link_no_redirect(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No receber here</body></html>"
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Redirect URL not found in response"):
            BludvSpider.unlock_encrypted_protected_link("http://example.com")
