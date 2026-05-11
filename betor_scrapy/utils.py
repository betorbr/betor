import base64
import itertools
import re
from typing import Generator, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests
from slugify import slugify

from betor.settings import flaresolverr_settings
from betor_scrapy.items import ScrapyItem

FIELD_TOKENS = {
    "translated_title": ["titulo-traduzido"],
    "title": ["titulo-original", "nome-original"],
    "imdb_rating": ["imdb"],
    "year": ["lancamento"],
    "qualitys": ["qualidade"],
    "languages": ["idioma", "audio"],
    "genres": ["genero", "generos"],
    "format": ["formato"],
    "subtitles": ["legenda"],
    "size": ["tamanho"],
    "duration": ["duracao"],
    "audio-quality": ["qualidade-do-audio"],
    "video-quality": ["qualidade-de-video"],
    "server": ["servidor"],
    "classificacao": ["classificacao"],
}
ALL_FIELD_TOKENS_VALUES = list(itertools.chain(*FIELD_TOKENS.values()))


def extract_fields(informacoes_text: List[str]) -> Generator[Tuple[str, str]]:
    current_field: Optional[str] = None
    for i, token_value in enumerate([slugify(t) for t in informacoes_text]):
        if token_value in ALL_FIELD_TOKENS_VALUES:
            current_field = next(k for k, v in FIELD_TOKENS.items() if token_value in v)
            continue
        if not current_field or current_field not in ScrapyItem.fields.keys():
            continue
        value = informacoes_text[i]
        cleaned_value = re.sub(r"^(:\W)", "", value)
        if current_field == "languages":
            for v in re.split(r"[,|/]", cleaned_value):
                yield current_field, v
            continue
        yield current_field, cleaned_value


class UnlockSystemAds:
    PROTECTED_URLS_PREFIXES = [
        "https://www.systemads.org/get.php?id=",
        "https://superadsgo.xyz/get.php?id=",
        "https://superadsgo1.xyz/get.php?id=",
        "https://www.systemads.xyz/get.php?id=",
        "https://systemads.net/go.php?id=",
    ]

    @classmethod
    def unlock_protected_redirect_link(cls, redirect_url: str) -> str:
        parsed = urlparse(redirect_url)
        qs = parse_qs(parsed.query)
        id_values = qs.get("id")
        if not id_values:
            raise ValueError("id value not found")
        id_value = "".join(id_values)[::-1]
        try:
            return base64.b64decode(id_value).decode()
        except Exception as e:
            raise ValueError("can't decode base64 value") from e

    @classmethod
    def request_protected_url_content(cls, url: str) -> str:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        if response.status_code == 403 and "cf-mitigated" in response.headers:
            if not flaresolverr_settings.base_url:
                raise ValueError(
                    f"Access forbidden to protected URL: {url}, configure flaresolverr settings to bypass Cloudflare protection"
                )
            flaresolverr_response = requests.post(
                f"{flaresolverr_settings.base_url}/v1",
                json={"cmd": "request.get", "url": url},
            )
            if flaresolverr_response.status_code == 200:
                return (
                    flaresolverr_response.json().get("solution", {}).get("response", "")
                )
            raise ValueError(f"Failed to fetch protected URL via flaresolverr: {url}")
        raise ValueError(f"Failed to fetch protected URL: {url}")

    @classmethod
    def unlock_encrypted_protected_link(cls, url: str) -> str:
        response_content = cls.request_protected_url_content(url)
        redirect_url = None
        for line in response_content.splitlines():
            if "?id=" in line:
                start = line.find("https://")
                end = line.find('"', start)
                if start != -1 and end != -1:
                    redirect_url = line[start:end]
                    break
        if not redirect_url:
            raise ValueError("Redirect URL not found in response")
        return cls.unlock_protected_redirect_link(redirect_url)

    @classmethod
    def unlock_protected_link(cls, url: str) -> str:
        try:
            return cls.unlock_protected_redirect_link(url)
        except ValueError:
            return cls.unlock_encrypted_protected_link(url)
