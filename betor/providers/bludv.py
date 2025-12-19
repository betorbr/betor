from .provider import Provider

bludv = Provider(
    "bludv",
    "https://bludv-v1.xyz",
    "{base_url}/page/{page}/",
    "{base_url}/?s={qs}",
    "{base_url}/page/{page}/?s={qs}",
    append_domains=["bludv.net"],
    cf_clearance_domain=".bludv-v1.xyz",
)
