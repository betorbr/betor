import itertools
import re
from typing import Generator, List, Optional, Tuple

from slugify import slugify

from betor_scrapy.items import ScrapyItem

FIELD_TOKENS = {
    "translated_title": ["titulo-traduzido"],
    "title": ["titulo-original"],
    "imdb_rating": ["imdb"],
    "year": ["lancamento"],
    "qualitys": ["qualidade"],
    "languages": ["idioma", "audio"],
    "genres": ["genero"],
    "format": ["formato"],
    "subtitles": ["legenda"],
    "size": ["tamanho"],
    "duration": ["duracao"],
    "audio-quality": ["qualidade-do-audio"],
    "video-quality": ["qualidade-de-video"],
    "server": ["servidor"],
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
            for v in re.split(r"[,|]", cleaned_value):
                yield current_field, v
            continue
        yield current_field, cleaned_value
