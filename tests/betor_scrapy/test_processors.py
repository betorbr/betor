from typing import List

import pytest

from betor.enum import QualityEnum
from betor_scrapy.processors import Quality, Title


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
