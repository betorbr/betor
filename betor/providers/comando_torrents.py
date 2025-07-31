from .provider import Provider

comando_torrents = Provider(
    "comando-torrents",
    "https://comando.la",
    "{base_url}/page/{page}/",
    "{base_url}/?q={qs}",
)
