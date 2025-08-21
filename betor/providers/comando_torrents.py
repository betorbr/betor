from .provider import Provider

comando_torrents = Provider(
    "comando-torrents",
    "https://comando.la",
    "{base_url}/page/{page}/",
    "{base_url}/?s={qs}",
    "{base_url}/page/{page}/?s={qs}",
    cf_clearance_domain=".comando.la",
)
