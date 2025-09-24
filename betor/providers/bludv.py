from .provider import Provider

bludv = Provider(
    "bludv",
    "https://bludv.org",
    "{base_url}/page/{page}/",
    "{base_url}/?s={qs}",
    "{base_url}/page/{page}/?s={qs}",
    cf_clearance_domain=".bludv.org",
)
