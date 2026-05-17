from .provider import Provider

bludv = Provider(
    "bludv",
    "https://bludv2.xyz",
    "{base_url}/page/{page}/",
    "{base_url}/?s={qs}",
    "{base_url}/page/{page}/?s={qs}",
    append_domains=["bludv.net", "bludv-v1.xyz", "bludv1.xyz", "bludv1.com"],
    cf_clearance_domain=".bludv2.xyz",
)
