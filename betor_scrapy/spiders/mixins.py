import json

import scrapy.http


class TitleJSONLDMixin:
    @classmethod
    def extract_title_json_ld(cls, response: scrapy.http.TextResponse):
        for script in response.xpath(
            "//script[@type='application/ld+json']//text()"
        ).getall():
            try:
                data = json.loads(script)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get("@type") in {"Movie", "TVSeries"}:
                return data
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") in {
                        "Movie",
                        "TVSeries",
                    }:
                        return item
        return None
