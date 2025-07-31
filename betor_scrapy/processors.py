import re
from typing import List, Optional


class Title:
    def __call__(self, values: Optional[List[str]]) -> Optional[str]:
        if not values:
            return None
        value = " ".join(values).strip()
        value = re.sub(r"^(:\W)", "", value)
        value = re.sub(r"\s+", " ", value)
        return value
