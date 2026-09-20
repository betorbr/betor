import base64
from typing import Optional

import torf


def jaccard_similarity(a: str, b: str) -> float:
    intersection_cardinality = len(set.intersection(*[set(a.lower()), set(b.lower())]))
    union_cardinality = len(set.union(*[set(a.lower()), set(b.lower())]))
    return intersection_cardinality / float(union_cardinality)


def extract_magnet_info_hash(magnet_uri: str) -> Optional[str]:
    try:
        magnet = torf.Magnet.from_string(magnet_uri)
    except torf.MagnetError:
        return None

    info_hash = magnet.infohash
    if len(info_hash) != 40:
        try:
            info_hash = base64.b32decode(
                info_hash.upper() + "=" * ((8 - len(info_hash) % 8) % 8)
            ).hex()
        except Exception:  # noqa: BLE001
            return None

    if len(info_hash) != 40:
        return None
    if not all(c in "0123456789abcdefABCDEF" for c in info_hash):
        return None
    return info_hash
