import re
from typing import Generator, List, Optional, Set, TypeVar

import langcodes
from slugify import slugify

from betor.enums import QualityEnum

T = TypeVar("T")


class Title:
    def __call__(self, values: Optional[List[str]]) -> Optional[str]:
        if not values:
            return None
        value = " ".join(values).strip()
        value = re.sub(r"\s+", " ", value)
        value = re.sub(r" - [CAM|TS|HD|WEB-DL]+$", "", value)
        value = re.sub(r" - [\d]+ª [Temporada|TEMPORADA]+$", "", value)
        return value


class Quality:
    def __call__(self, value: str) -> QualityEnum:
        for q in QualityEnum:
            if slugify(q) == slugify(value.strip()):
                return q
        return QualityEnum.unknown


class SetIdentity[T]:
    def __call__(self, values: Optional[List[T]]) -> Set[T]:
        return set(values or [])


class Language:
    def __call__(self, value: str) -> Generator[str]:
        v_cleaned = re.sub(r"\s+", " ", value.strip())
        if not v_cleaned:
            return
        try:
            yield langcodes.find(v_cleaned).to_tag()
        except LookupError:
            pass


class IMDbIDs:
    IMDB_URL_REGEX = r"http(s)?://(www.)?imdb.com/([\w]+/)?title/(?P<imdb_id>tt[\d]+)"
    OPENSUBTITLES_URL_REGEX = r"http(s)?://(www.)?opensubtitles.org/pb/search/sublanguageid-pob/imdbid-(?P<imdb_id>[\d]+)"
    YIFYSUBTITLES_URL_REGEX = (
        r"http(s)?://(www.)?yifysubtitles.ch/movie-imdb/(?P<imdb_id>tt[\d]+)"
    )

    def __call__(self, value: str) -> Generator[str]:
        if imdb_url_search := re.search(IMDbIDs.IMDB_URL_REGEX, value):
            yield imdb_url_search.group("imdb_id")
        if opensubtitles_url_search := re.search(
            IMDbIDs.OPENSUBTITLES_URL_REGEX, value
        ):
            imdb_id = opensubtitles_url_search.group("imdb_id")
            yield f"tt{imdb_id}"
        if yifysubtitles_url_search := re.search(
            IMDbIDs.YIFYSUBTITLES_URL_REGEX, value
        ):
            yield yifysubtitles_url_search.group("imdb_id")
        v = value.strip()
        if v.startswith("tt"):
            yield v
