from typing import Literal, TypeAlias

from .bludv import bludv
from .comando_torrents import comando_torrents
from .provider import Provider
from .rede_torrent import rede_torrent
from .starck_filmes import starck_filmes
from .torrent_dos_filmes import torrent_dos_filmes

PROVIDERS = [
    comando_torrents,
    bludv,
    torrent_dos_filmes,
    starck_filmes,
    rede_torrent,
]

ProviderSlug: TypeAlias = Literal[
    "comando-torrents", "bludv", "torrent-dos-filmes", "starck-filmes", "rede-torrent"
]

__all__ = [
    "Provider",
    "ProviderSlug",
    "bludv",
    "comando_torrents",
    "torrent_dos_filmes",
    "starck_filmes",
    "rede_torrent",
]
