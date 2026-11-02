from unittest.mock import MagicMock, patch

import pytest

from betor_scrapy.extensions.bludv_unlock_extension import UnlockBludvGateExtension


class TestUnlockBludvGateExtension:
    def test_extract_magnet(self):
        html = '<html><body><script>var u="magnet:?xt=urn:btih:123456&dn=Test";</script></body></html>'
        assert (
            UnlockBludvGateExtension._extract_magnet(html)
            == "magnet:?xt=urn:btih:123456&dn=Test"
        )

    def test_extract_magnet_fallback(self):
        html = (
            '<html><body><a href="magnet:?xt=urn:btih:7890">Download</a></body></html>'
        )
        assert (
            UnlockBludvGateExtension._extract_magnet(html) == "magnet:?xt=urn:btih:7890"
        )

    def test_extract_magnet_none(self):
        html = "<html><body>No magnet here</body></html>"
        assert UnlockBludvGateExtension._extract_magnet(html) is None

    def test_from_crawler_assertion(self):
        crawler = MagicMock()
        crawler.settings.get.return_value = None
        with pytest.raises(
            AssertionError, match="FLARESOLVERR_BASE_URL must be defined"
        ):
            UnlockBludvGateExtension.from_crawler(crawler)

    @patch("betor_scrapy.extensions.bludv_unlock_extension.httpx.post")
    def test_unlock_gate_url_cached_token_success(self, mock_post):
        ext = UnlockBludvGateExtension("https://flaresolverr.betor.top")
        ext.cached_token = "testtoken123"
        ext.session_id = "test-session"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "solution": {
                "response": '<html><script>var u="magnet:?xt=urn:btih:cached";</script></html>'
            }
        }
        mock_post.return_value = mock_response

        spider = MagicMock()
        magnet = ext.unlock_gate_url(
            "https://bludvfilmes2.xyz/gate/go/4ec7175a6d672816?p=81366", spider
        )

        assert magnet == "magnet:?xt=urn:btih:cached"
        mock_post.assert_called_once()
