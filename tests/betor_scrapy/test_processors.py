from typing import List

import pytest

from betor.enums import QualityEnum
from betor_scrapy.processors import IMDbIDs, Language, Quality, Title


class TestTitle:
    @pytest.mark.parametrize(
        (
            "value",
            "expected",
        ),
        [
            (
                ["Rick and Morty"],
                "Rick and Morty",
            ),
            (
                [" Rick and  Morty"],
                "Rick and Morty",
            ),
            (
                [" Rick and   Morty"],
                "Rick and Morty",
            ),
            (
                [" Rick and ", "Morty"],
                "Rick and Morty",
            ),
            (
                ["", " Rick and ", "Morty"],
                "Rick and Morty",
            ),
            (
                ["", " Rick and ", "Morty: ", " Starts"],
                "Rick and Morty: Starts",
            ),
        ],
    )
    def test_ok(self, value: List[str], expected: str):
        processor = Title()
        assert processor(value) == expected


class TestQuality:
    @pytest.mark.parametrize(
        (
            "value",
            "expected",
        ),
        [
            (
                "foo",
                QualityEnum.unknown,
            ),
            (
                "SDTV",
                QualityEnum.sdtv,
            ),
            (
                "SDtv",
                QualityEnum.sdtv,
            ),
            (
                " SDtv",
                QualityEnum.sdtv,
            ),
            (
                "Bluray-1080p-Remux",
                QualityEnum.bluray_1080p_remux,
            ),
            (
                " Bluray-1080p  Remux",
                QualityEnum.bluray_1080p_remux,
            ),
        ],
    )
    def test_ok(self, value: str, expected: str):
        processor = Quality()
        assert processor(value) == expected


class TestLanguage:
    @pytest.mark.parametrize(
        (
            "value",
            "expected",
        ),
        [
            (
                "Português",
                ["pt"],
            ),
            (
                "Inglês",
                ["en"],
            ),
        ],
    )
    def test_ok(self, value: str, expected: str):
        processor = Language()
        assert list(processor(value)) == expected


class TestIMDbIDs:
    @pytest.mark.parametrize(
        (
            "value",
            "expected",
        ),
        [
            (
                "https://www.imdb.com/pt/title/tt10548174/",
                ["tt10548174"],
            ),
            (
                "https://www.imdb.com/title/tt10548174/",
                ["tt10548174"],
            ),
            (
                "https://imdb.com/title/tt10548174/",
                ["tt10548174"],
            ),
            (
                "http://imdb.com/title/tt10548174/",
                ["tt10548174"],
            ),
            (
                "tt10548174",
                ["tt10548174"],
            ),
            (
                "10548174",
                [],
            ),
        ],
    )
    def test_ok(self, value: str, expected: str):
        processor = IMDbIDs()
        assert list(processor(value)) == expected
