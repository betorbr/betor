import itertools
import re
from typing import Generator, List, Optional, Tuple

from slugify import slugify

from betor_scrapy.items import ScrapyItem

FIELD_TOKENS = {
    "translated_title": ["titulo-traduzido"],
    "title": ["titulo-original", "nome-original"],
    "imdb_rating": ["imdb"],
    "year": ["lancamento", "estreia-em"],
    "qualitys": ["qualidade", "resolucao-qualidade"],
    "languages": ["idioma", "audio", "idioma-audio"],
    "genres": ["genero", "generos"],
    "format": ["formato", "formato-do-arquivo"],
    "subtitles": ["legenda"],
    "size": ["tamanho", "tamanho-do-arquivo"],
    "duration": ["duracao"],
    "audio-quality": ["qualidade-do-audio", "audio"],
    "video-quality": ["qualidade-de-video", "video"],
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
