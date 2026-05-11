from .provider import Provider

comando_torrents = Provider(
    "comando-torrents",
    "https://comando1.com/",
    "{base_url}/page/{page}/",
    "{base_url}/?s={qs}",
    "{base_url}/page/{page}/?s={qs}",
    append_domains=["comando.la"],
    cf_clearance_domain=".comando1.com",
)
