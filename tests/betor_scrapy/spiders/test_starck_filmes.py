import pytest

from betor_scrapy.spiders.starck_filmes import StarckFilmesSpider


class TestStarckFilmesUnlock:
    @pytest.mark.parametrize(
        (
            "url",
            "expected_btih",
            "expected_name",
        ),
        [
            (
                "https://filmedl.com/?xid=bnRWRwFyJnPTbXNmVBVkJ0cTOCJjUG9zJ4QTdSJDUG1yb1R3ciBmUl4yb6RiYn5nRzRydpYGaWVDNhprbjZHMXRGIoUuL1ZnOmNT5pgpJ2eTYCNj5BYuOyZDYXAjQlYlM4MkM0ZTEhA2bxOmNT5jYvA5dxJWZT5WJjVGZlYSMWZz50Uuc5bjO31GVoYud3YHY2RTUwlmJkdTYHNjIBQ9J3dTNWJjRGgwJ2JTOTJDNGYBd3JHJTJmJhRGYuJ2PTtUJldGcldibH53J2JhcnYma2FWtwUlaucGZilS5t5vLNcmYGNWVv5ubkdSeHUSJz5hQTYTZ2YXt5UyNuLjUmkH9lJyMpZkbyZWUhVzbpQmcT5mEv8zduMWQz52cjFlZzMSYkZWZ01hclbjbm1n51RvZvdHLWAl5lMjMwZ0MSE0ZlU0MwckMjYS1l5oMXdkRHZUR1IwNtcCRy5EU0wzcuQmMSFTUrAye4RCMi5HUjAycuRmenlDRtIyL2YmNWlCNz5rdEZCVXUUJzFzQMLTLmEj1zUsMuczM3cSVl1iMTLkVmZE5hFlbSdnQCV0UutzYGQ2STlUQhx0cNMiRyZVU0MycmRjem1GF1wuZ9bHNmAz9lc1M0b0OmETNlIlM2JkMnYjRlAyM5PkJXZnVlRkeycHPCBXUsVzbkQ2cSRCUpUyZzRSQi5SUvUycyRmRmci1lUhMyc0RnEnR2IpOubTbiYD15UnJuZTYWJ2JGEoYlYWMX50JuEkb2d3OCVT5uYlY5d2JSUTUmJzdGQHYTIWI951a1JHbTRmJ0NGcpYHYWMX5lI1Mmb0dmEHNlIpM9YkdXYWIlRmMwdkJHZTI0N9cBdmJWFTRjJwaGJ2JTVTNyJBLGJndTlTJlYGbuJWdTVHJrJGehZWaXV3ZkghaubWYi035uJpYpb2bS9SUt5zJpQTcTN3YBQ5NlNDMjQ0kzElJxMTMkJzZGMhY3bWJn5TVuJubGY3Y2VWlu5hYuc2biU3ZmV0ducHYjI219U1dmZWdHRHAwIlJ9MTd0NWEBRlJwMTJkJTYGNlJBMTJkJTZGJ0dGcHJmRTFrJjMGaic25DVuJyYwLmLmFnJvBpb1cmYmxmtpxlbpbmYnV3dzRhZybXYGJWQ2NuarZWZGNXUlIlLuMme0NHEvl2b6OSJTUTYzN5QBJTNTYjJ5kGN2YjOWkS5lUuMybkR3ZmVhFubuYmd25WUv5mdjdWaH5WIjF9ZydQJW",
                "urn:btih:c0e5986b62b68101601eee3598f7a9db47686867",
                "Georgie.e.Mandy.Seu.Primeiro.Casamento.S03E01",
            ),
            (
                "https://filmedl.com/?xid=bi5WUjFyZnRSbnZmR0Vyc0YjOW1jN19rZ4ZHdXADJl1zM1L0cmEm1l4sM6ckY3YnVlRiMpLkamZD50olc3dmZCFmUjYza2Q2MTVGQyN0LjMmNyZDUuIyazRXNmgDFuEub3bmMmVz90Z1JkbTYmNmNBMlNzJjNnkDR2kyO0PSMXUzVykkRwcmYCFjUuUzb0QmNS9GU1MybzRmZiNjUlJyJkRnMnRjRycyP3YXYWVTNkArcwZCJXUmIzRuQuYSPmUUlydyRlaib2U3VyJuRndma2VWF4UscuZGZCxS5v5kZNZGYSlWUl5zLkQmeT9SYy55ZTNyZjUXkzUlQuMTUkYHZ5JhNpbjbmkW5lVvMpdkcWZm5h8jbuZmQS52ZvF0dzcWYj5W1j11ZlZSbHZnA0RlcvMjL01lEoMldwMHMkR0YwUlJwMTMkNiZB50JXcTRmJUFGIjJtaTR2JEVGwyduLHMmJT9hAwY4Z2MWtH5lA0cuciem5DF2Ijc2amN3FCIw5uaEbGV3lUJtFnLMJmLTNjNvUBbuMSMTUSMz1zQTNTVyYEU5FyNSRjQmk0FltuMGbkSmZU9hx1bNbmRm5VNvMldmJWen5GRjwyZ9PSNXZzV0Ukc4cjNC1TU1MzZyQHOSADUlAyM3R0JiEnUlRyMyRkPnYXRlV0MkakczZCIwUuMzbnQmASJuUhcybHR2Vi5iUsbyaGRWlm5jVld2cHY2JWVh4yYud2amtWll0jclZiMS5054Eje2bXO2oT0lYlM5M0J0ETE2J2OGOTYTYWY555J1JTbTJmJGNGYpYWYW5X51Iubmbmd3NHVpIuY9YXd2IWUmFmdwdHJHITI9N9dBdWJWRTRwJwJGJTJTNTNBJBJGJTcTJiJG5GJsJTNTJSJG5GdjbTY3QSBuUldzbHQiJT5hYza5d3NGgjVukhYlb3MHJkRpZobhLSbn5nNpVpcuJ3YTQ2NllBMhO0cDEiAxZlM0MzckMjZ31hJ1bTZmJH5GAvYldWMW5051EjblZmMSNkZpY0YlcXMjIk1mZod1dHNHIiR95wd0cWcyRmUwFzJrQTeSNCUB5yJjRTciJmUGlyJtRTLnJmRGlybzYWdWFCNyUrdzZGQXlTIuEuLzeWMWdzVlctYlZmMWhkthZ5chZmbWRmR05pLvbmdSVW515jJjbTZ2NS0BZlM0Mjc0UjEl10MoNkdDZHMhRlbwMnckVyZuUhYzb2QmlS5hUvcydgRW",
                "urn:btih:7ff60cc42341736dbc3494390b544c3f2d277a00",
                "Georgie.e.Mandy.Seu.Primeiro.Casamento.S03E02",
            ),
        ],
    )
    def test_unlock_filmedl_link_ok(
        self, url: str, expected_btih: str, expected_name: str
    ):
        result = StarckFilmesSpider.unlock_filmedl_link(url)
        assert result is not None
        assert result.startswith("magnet:?")
        assert expected_btih in result
        assert expected_name in result

    def test_unlock_filmedl_link_missing_id(self):
        assert (
            StarckFilmesSpider.unlock_filmedl_link("https://filmedl.com/?refsite=bludv")
            is None
        )

    def test_unlock_filmedl_link_invalid(self):
        assert (
            StarckFilmesSpider.unlock_filmedl_link("https://filmedl.com/?xid=invalid!")
            is None
        )
