import re
from typing import Generator, List, Optional, Set, TypeVar

import langcodes
from slugify import slugify

from betor.enum import QualityEnum

T = TypeVar("T")


class Title:
    def __call__(self, values: Optional[List[str]]) -> Optional[str]:
        if not values:
            return None
        value = " ".join(values).strip()
        value = re.sub(r"\s+", " ", value)
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
    URL_REGEX = r"http(s)?://(www.)?imdb.com/([\w]+/)?title/(?P<imdb_id>tt[\d]+)"

    def __call__(self, value: str) -> Generator[str]:
        if url_search := re.search(IMDbIDs.URL_REGEX, value):
            yield url_search.group("imdb_id")
        v = value.strip()
        if v.startswith("tt"):
            yield v
