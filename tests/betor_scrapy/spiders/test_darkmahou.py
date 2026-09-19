import base64
from html import escape
from urllib.parse import parse_qs, quote, urlsplit

import pytest
import torf
from scrapy.http import HtmlResponse, XmlResponse

from betor.providers import PROVIDERS, ProviderSlug, darkmahou
from betor_scrapy.spiders.darkmahou import DarkMahouSpider, decode_magnet_link

HASH = "0123456789abcdef0123456789abcdef01234567"
MAGNET = (
    f"magnet:?xt=urn:btih:{HASH}"
    "&dn=Example%20S02E03%201080p&tr=udp%3A%2F%2Ftracker.example%3A80"
)
BATCH = (
    "magnet:?xt=urn:btih:abcdef0123456789abcdef0123456789abcdef01"
    "&dn=Example%20S02%20%5BBATCH%5D"
)


def redirect(value: str, urlsafe=False, padding=True, quoted=False) -> str:
    encoder = base64.urlsafe_b64encode if urlsafe else base64.b64encode
    encoded = encoder(value.encode()).decode()
    if not padding:
        encoded = encoded.rstrip("=")
    if quoted:
        encoded = quote(encoded, safe="")
    return f"https://otakufilmes.org/encurtar/redirect.php?url={encoded}"


@pytest.mark.parametrize("urlsafe", [False, True])
@pytest.mark.parametrize("padding", [False, True])
@pytest.mark.parametrize("quoted", [False, True])
def test_redirect_variants(urlsafe, padding, quoted):
    # Exercise literal '+' and '/' in Base64 and their URL-safe equivalents.
    magnet = f"magnet:?xt=urn:btih:{HASH}&dn=>>>???ação"
    assert decode_magnet_link(redirect(magnet, urlsafe, padding, quoted)) == magnet


def test_direct_magnet_preserves_name_and_trackers():
    assert decode_magnet_link(MAGNET) == MAGNET
    parsed = torf.Magnet.from_string(decode_magnet_link(redirect(MAGNET)))
    assert parsed.xt == f"urn:btih:{HASH}"
    assert parsed.dn == "Example S02E03 1080p"


@pytest.mark.parametrize(
    "href",
    [
        "",
        "magnet:?dn=missing-hash",
        "magnet:?xt=urn:btih:invalid",
        "https://example.org/video.torrent",
        "https://example.org/redirect.php",
        "https://example.org/redirect.php?url=",
        "https://example.org/redirect.php?url=%%%",
        "https://example.org/redirect.php?url=/w==",
        "https://example.org/redirect.php?url=a",
        redirect("https://example.org/file.torrent"),
        redirect("javascript:alert(1)"),
        redirect(redirect(MAGNET)),
        redirect(MAGNET) + "&url=duplicate",
        redirect(MAGNET).replace("redirect.php", "other.php"),
    ],
)
def test_rejects_invalid_and_non_magnet_destinations(href):
    assert decode_magnet_link(href) is None


def test_provider_registration_and_feed_urls():
    from typing import get_args

    assert darkmahou in PROVIDERS
    assert darkmahou.slug in get_args(ProviderSlug)
    assert darkmahou.get_page_url() == "https://darkmahou.io/feed/"
    assert darkmahou.get_page_url(2) == "https://darkmahou.io/feed/?paged=2"
    assert parse_qs(urlsplit(darkmahou.get_search_url("ação & anime", 3)).query) == {
        "s": ["ação & anime"],
        "paged": ["3"],
    }


@pytest.mark.asyncio
async def test_start_uses_deep_and_search_contract():
    spider = DarkMahouSpider(deep="2", q="Example")
    requests = [request async for request in spider.start()]
    assert [request.url for request in requests] == [
        "https://darkmahou.io/feed/?s=Example",
        "https://darkmahou.io/feed/?s=Example&paged=2",
    ]
    assert all("no-cache" in request.flags for request in requests)


def test_feed_follows_post_links_not_guids_and_deduplicates():
    response = XmlResponse(
        url="https://darkmahou.io/feed/",
        body=b"""<rss><channel>
          <item><title>Example</title><link>https://darkmahou.io/example/</link>
            <guid>https://old.example/?p=1</guid></item>
          <item><link>https://darkmahou.io/example/</link></item>
          <item><link>https://external.example/post/</link></item>
          <item><link>javascript:alert(1)</link></item>
          <item><title>No link</title></item>
        </channel></rss>""",
        encoding="utf-8",
    )
    requests = list(DarkMahouSpider().parse(response))
    assert len(requests) == 1
    assert requests[0].url == "https://darkmahou.io/example/"
    assert requests[0].cb_kwargs == {"feed_title": "Example"}
    assert "no-cache" in requests[0].flags


def test_empty_or_non_feed_response_yields_no_requests():
    spider = DarkMahouSpider()
    for body in (b"<rss><channel/></rss>", b"<html>Maintenance</html>"):
        response = XmlResponse(
            url="https://darkmahou.io/feed/", body=body, encoding="utf-8"
        )
        assert list(spider.parse(response)) == []


def test_post_preserves_releases_and_uses_existing_raw_item_contract():
    body = f"""
        <h1 class="entry-title">Example <em>Anime</em></h1>
        <div class="info-content"><div class="spe">
          <span><b>Lançado:</b> jan 04, 2025</span>
          <span><b>Lançado em:</b> setembro 19, 2026</span>
          <span><b>Elenco:</b><a class="casts">Actor</a></span>
          <span><b>Legendas:</b>PT-BR, Multisubs</span>
        </div><a href="https://www.imdb.com/title/tt1234567/">IMDb</a></div>
        <div class="soraddl">
          <a href="{escape(MAGNET, quote=True)}">Episode</a>
          <a href="{escape(redirect(MAGNET), quote=True)}">Duplicate</a>
          <a href="{escape(redirect(BATCH), quote=True)}">Batch</a>
          <a href="{escape(redirect('https://example.org/file'), quote=True)}">File</a>
          <a href="https://example.org/redirect.php?url=bad">Invalid</a>
        </div>
        <div id="comments"><a href="magnet:?xt=urn:btih:{'f' * 40}">Spam</a></div>
    """
    response = HtmlResponse(
        url="https://darkmahou.io/example/", body=body.encode(), encoding="utf-8"
    )
    items = list(DarkMahouSpider().parse_item(response))
    assert len(items) == 1
    raw = items[0].to_raw_item()
    assert raw["provider_slug"] == "darkmahou"
    assert raw["provider_url"] == response.url
    assert raw["raw_title"] == "Example Anime"
    assert raw["title"] == "Example Anime"
    assert raw["year"] == 2025
    assert raw["imdb_id"] == "tt1234567"
    assert raw["cast"] == ["Actor"]
    assert raw["magnet_uris"] == [MAGNET, BATCH]
    # Subtitle labels must not be promoted to audio languages for every release.
    assert raw["languages"] == []


def test_post_without_supported_downloads_is_not_emitted():
    response = HtmlResponse(
        url="https://darkmahou.io/example/",
        body=b'<h1 class="entry-title">Example</h1><div class="soraddl"></div>',
        encoding="utf-8",
    )
    assert list(DarkMahouSpider().parse_item(response)) == []


def test_post_uses_feed_title_when_heading_is_missing():
    response = HtmlResponse(
        url="https://darkmahou.io/example/",
        body=f'<div class="soraddl"><a href="{escape(MAGNET)}">Get</a></div>'.encode(),
        encoding="utf-8",
    )
    item = list(DarkMahouSpider().parse_item(response, feed_title="Example"))[0]
    assert item["raw_title"] == "Example"
