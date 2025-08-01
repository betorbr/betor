import re
from typing import List, Optional, Set, TypeVar

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
