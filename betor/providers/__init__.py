from .bludv import bludv
from .comando_torrents import comando_torrents
from .provider import Provider

PROVIDERS = [
    comando_torrents,
    bludv,
]

__all__ = ["Provider", "bludv", "comando_torrents"]
