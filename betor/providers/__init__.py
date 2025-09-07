from typing import Literal, TypeAlias

from .bludv import bludv
from .comando_torrents import comando_torrents
from .provider import Provider
from .torrent_dos_filmes import torrent_dos_filmes

PROVIDERS = [
    comando_torrents,
    bludv,
    torrent_dos_filmes,
]

ProviderSlug: TypeAlias = Literal["comando-torrents", "bludv", "torrent-dos-filmes"]

__all__ = [
    "Provider",
    "ProviderSlug",
    "bludv",
    "comando_torrents",
    "torrent_dos_filmes",
]
