import scrapy.extensions.httpcache


class BetorHTTPCachePolicy(scrapy.extensions.httpcache.DummyPolicy):
    def should_cache_request(self, request):
        return "no-cache" not in request.flags and super().should_cache_request(request)
